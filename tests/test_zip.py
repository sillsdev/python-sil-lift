import json
import zipfile
from pathlib import Path

import pytest

import sil_lift
from sil_lift._cli import main

CORPUS_DIR = Path(__file__).parent / "corpus"
PAIR_DIR = CORPUS_DIR / "ranges"  # test20080407.lift + companion, fully clean

PAIR = {
    "test20080407.lift": PAIR_DIR / "test20080407.lift",
    "test20080407.lift-ranges": PAIR_DIR / "test20080407.lift-ranges",
}


def _make_zip(dst: Path, members: dict[str, Path], *, wrap: str | None = None) -> Path:
    with zipfile.ZipFile(dst, "w") as archive:
        for arcname, src in members.items():
            archive.write(src, f"{wrap}/{arcname}" if wrap else arcname)
    return dst


def _names(path: Path) -> set[str]:
    with zipfile.ZipFile(path) as archive:
        return set(archive.namelist())


def test_load_zip_flat_layout(tmp_path: Path) -> None:
    lex = sil_lift.load(_make_zip(tmp_path / "flat.zip", PAIR))
    assert len(lex.entries) == 1
    assert lex.all_ranges()["grammatical-info"].elements  # companion resolved
    assert list(lex.iter_problems()) == []


def test_load_zip_folder_wrapped_layout(tmp_path: Path) -> None:
    lex = sil_lift.load(_make_zip(tmp_path / "wrapped.zip", PAIR, wrap="MyDict"))
    assert len(lex.entries) == 1
    assert list(lex.iter_problems()) == []


def test_load_zip_ignores_macosx_junk(tmp_path: Path) -> None:
    path = tmp_path / "junk.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.write(PAIR_DIR / "test20080407.lift", "MyDict/test20080407.lift")
        archive.write(PAIR_DIR / "test20080407.lift-ranges", "MyDict/test20080407.lift-ranges")
        archive.writestr("__MACOSX/._test20080407.lift", b"apple double junk")
    assert len(sil_lift.load(path).entries) == 1


def test_load_zip_with_explicit_dir_entries(tmp_path: Path) -> None:
    # FieldWorks/Combine archives include explicit directory entries.
    path = tmp_path / "dirs.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("MyDict/", b"")
        archive.write(PAIR_DIR / "test20080407.lift", "MyDict/test20080407.lift")
        archive.write(PAIR_DIR / "test20080407.lift-ranges", "MyDict/test20080407.lift-ranges")
    assert len(sil_lift.load(path).entries) == 1


def test_zip_with_no_lift_errors(tmp_path: Path) -> None:
    path = tmp_path / "empty.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("readme.txt", b"nothing here")
    with pytest.raises(sil_lift.LiftParseError, match=r"no \.lift"):
        sil_lift.load(path)


def test_zip_with_multiple_lift_errors(tmp_path: Path) -> None:
    path = tmp_path / "two.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.write(PAIR_DIR / "test20080407.lift", "a.lift")
        archive.write(PAIR_DIR / "test20080407.lift", "b.lift")
    with pytest.raises(sil_lift.LiftParseError, match=r"multiple \.lift"):
        sil_lift.load(path)


def test_load_bad_zip_errors(tmp_path: Path) -> None:
    bogus = tmp_path / "bogus.zip"
    bogus.write_bytes(b"this is not a zip archive")
    with pytest.raises(sil_lift.LiftParseError, match="not a valid zip"):
        sil_lift.load(bogus)


def test_zip_rejects_path_traversal(tmp_path: Path) -> None:
    path = tmp_path / "evil.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("../evil.lift", b"<lift/>")
    with pytest.raises(sil_lift.LiftParseError, match="unsafe path"):
        sil_lift.load(path)


def test_zip_rejects_oversized_uncompressed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("sil_lift._zip._MAX_UNCOMPRESSED_BYTES", 100)
    package = _make_zip(tmp_path / "big.zip", PAIR)  # declared sizes far exceed 100
    with pytest.raises(sil_lift.LiftParseError, match="exceeds"):
        sil_lift.load(package)


def test_zip_rejects_too_many_entries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sil_lift._zip._MAX_ENTRIES", 1)
    package = _make_zip(tmp_path / "many.zip", PAIR)  # two members
    with pytest.raises(sil_lift.LiftParseError, match="too many entries"):
        sil_lift.load(package)


def test_cli_accepts_zip(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    package = _make_zip(tmp_path / "pkg.zip", PAIR, wrap="Pkg")

    assert main(["validate", str(package)]) == 0
    assert "0 error(s), 0 warning(s)" in capsys.readouterr().out

    assert main(["stats", str(package), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["entries"] == 1

    assert main(["check-media", str(package)]) == 0
    assert "0 missing" in capsys.readouterr().out


def test_save_zip_roundtrip_wrapped(tmp_path: Path) -> None:
    lex = sil_lift.load(_make_zip(tmp_path / "src.zip", PAIR, wrap="Src"))
    out = tmp_path / "out.zip"
    lex.save_zip(out, wrap_folder="Out")
    names = _names(out)
    assert "Out/test20080407.lift" in names
    assert "Out/test20080407.lift-ranges" in names
    assert list(sil_lift.load(out).iter_problems()) == []


def test_save_zip_flat_carries_extra_files(tmp_path: Path) -> None:
    src = tmp_path / "src.zip"
    with zipfile.ZipFile(src, "w") as archive:
        archive.write(PAIR_DIR / "test20080407.lift", "Proj/test20080407.lift")
        archive.write(PAIR_DIR / "test20080407.lift-ranges", "Proj/test20080407.lift-ranges")
        archive.writestr("Proj/WritingSystems/en.ldml", b"<ldml/>")
    lex = sil_lift.load(src)
    out = tmp_path / "flat.zip"
    lex.save_zip(out, wrap_folder=False)
    names = _names(out)
    assert "test20080407.lift" in names  # flat: no wrapper folder
    assert "WritingSystems/en.ldml" in names  # non-modeled files carried through


def test_save_zip_default_wraps_by_zip_stem(tmp_path: Path) -> None:
    lex = sil_lift.load(_make_zip(tmp_path / "src.zip", PAIR))
    out = tmp_path / "MyExport.zip"
    lex.save_zip(out)  # default wrap_folder=True -> folder named after the zip
    assert "MyExport/test20080407.lift" in _names(out)


def test_save_zip_from_scratch(tmp_path: Path) -> None:
    lex = sil_lift.Lexicon(producer="test")
    entry = sil_lift.Entry(id="e1", guid="dddddddd-dddd-4444-8888-dddddddddddd")
    entry.lexical_unit["en"] = "x"
    lex.entries.append(entry)
    ranges = sil_lift.RangesFile()
    ranges.add_range("grammatical-info").add_element("Noun")
    lex.add_ranges_file(ranges, href="Dict.lift-ranges")

    out = tmp_path / "Dict.zip"
    lex.save_zip(out)  # no source folder to carry; names derive from the zip stem
    names = _names(out)
    assert "Dict/Dict.lift" in names
    assert "Dict/Dict.lift-ranges" in names

    reloaded = sil_lift.load(out)
    assert reloaded.all_ranges()["grammatical-info"].elements[0].id == "Noun"
    assert list(reloaded.iter_problems()) == []
