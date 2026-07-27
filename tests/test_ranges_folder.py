import shutil
from pathlib import Path

import pytest
from lxml import etree

import sil_lift
from sil_lift import LiftParseError, RangesFile, Text
from sil_lift._model import _normalize_href

CORPUS_DIR = Path(__file__).parent / "corpus"
PAIR_DIR = CORPUS_DIR / "ranges"
SANGO_DIR = CORPUS_DIR / "large" / "sango"


def _copy_pair(src_dir: Path, stem: str, dst: Path) -> Path:
    for suffix in (".lift", ".lift-ranges"):
        shutil.copy(src_dir / f"{stem}{suffix}", dst / f"{stem}{suffix}")
    return dst / f"{stem}.lift"


def test_build_lexicon_and_ranges_from_scratch(tmp_path: Path) -> None:
    lexicon = sil_lift.Lexicon(producer="test")
    entry = sil_lift.Entry(id="e1", guid="77777777-7777-4444-8888-777777777777")
    entry.lexical_unit["seh"] = "kanga"
    sense = sil_lift.Sense(id="s1")
    sense.glosses.append(sil_lift.Form(lang="en", text=Text(["chicken"])))
    sense.traits.append(sil_lift.Trait(name="semantic-domain-ddp4", value="1.6.1.2"))
    entry.senses.append(sense)
    lexicon.entries.append(entry)

    ranges = RangesFile()
    domain = ranges.add_range("semantic-domain-ddp4")
    domain.add_element("1.6.1.2").label["en"] = "Bird"
    lexicon.add_ranges_file(ranges, href="dict.lift-ranges")

    lexicon.save(tmp_path / "dict.lift")
    assert (tmp_path / "dict.lift").is_file()
    assert (tmp_path / "dict.lift-ranges").is_file()
    # add_ranges_file registered the companion in the header.
    assert any(
        r.id == "semantic-domain-ddp4" and r.href == "dict.lift-ranges"
        for r in lexicon.header.ranges
    )

    reloaded = sil_lift.load(tmp_path / "dict.lift")
    assert [r.id for rf in reloaded.ranges_files.values() for r in rf.ranges] == [
        "semantic-domain-ddp4"
    ]
    assert list(reloaded.iter_problems()) == []  # trait value is defined; href resolves


def test_sibling_ranges_file_is_discovered_and_tracked() -> None:
    lexicon = sil_lift.load(PAIR_DIR / "test20080407.lift")
    assert len(lexicon.ranges_files) == 1
    (ranges_file,) = lexicon.ranges_files.values()
    assert ranges_file.path is not None
    assert ranges_file.path.name == "test20080407.lift-ranges"
    assert [r.id for r in ranges_file.ranges] == ["grammatical-info"]
    assert [e.id for e in ranges_file.ranges[0].elements] == ["Adverb", "Noun", "Verb"]


def test_resolve_ranges_false_tracks_nothing() -> None:
    lexicon = sil_lift.load(PAIR_DIR / "test20080407.lift", resolve_ranges=False)
    assert lexicon.ranges_files == {}


def test_pair_roundtrips_byte_identically(tmp_path: Path) -> None:
    lift_path = _copy_pair(PAIR_DIR, "test20080407", tmp_path)
    lexicon = sil_lift.load(lift_path)
    lexicon.save()
    for suffix in (".lift", ".lift-ranges"):
        name = f"test20080407{suffix}"
        assert (tmp_path / name).read_bytes() == (PAIR_DIR / name).read_bytes(), name


def test_save_to_new_directory_carries_companions(tmp_path: Path) -> None:
    lexicon = sil_lift.load(PAIR_DIR / "test20080407.lift")
    target_dir = tmp_path / "elsewhere"
    target_dir.mkdir()
    lexicon.save(target_dir / "test20080407.lift")
    assert (target_dir / "test20080407.lift").read_bytes() == (
        PAIR_DIR / "test20080407.lift"
    ).read_bytes()
    assert (target_dir / "test20080407.lift-ranges").read_bytes() == (
        PAIR_DIR / "test20080407.lift-ranges"
    ).read_bytes()
    # The tracking dict must be re-keyed to the companions' new locations.
    assert set(lexicon.ranges_files) == {(target_dir / "test20080407.lift-ranges").resolve()}


def test_save_to_the_same_directory_spelled_differently_keeps_companions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A relative target naming the load directory is not a relocation.

    The companion lives in a subfolder, so a spurious relocation would fork it:
    the edit would land beside the .lift while the header href still points at
    the now-stale original.
    """
    subfolder = tmp_path / "sub"
    subfolder.mkdir()
    (tmp_path / "dict.lift").write_bytes(
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<lift version="0.13"><header><ranges>'
        b'<range id="grammatical-info" href="sub/shared.lift-ranges"/>'
        b"</ranges></header></lift>\n"
    )
    shutil.copy(PAIR_DIR / "test20080407.lift-ranges", subfolder / "shared.lift-ranges")

    lexicon = sil_lift.load(tmp_path / "dict.lift")
    (ranges_file,) = lexicon.ranges_files.values()
    ranges_file.ranges[0].elements[0].label["en"] = Text(["edited"])
    monkeypatch.chdir(tmp_path)
    lexicon.save("dict.lift")

    assert not (tmp_path / "shared.lift-ranges").exists()
    assert b"edited" in (subfolder / "shared.lift-ranges").read_bytes()
    assert set(lexicon.ranges_files) == {(subfolder / "shared.lift-ranges").resolve()}


def test_ranges_edit_saves_back_to_the_right_file(tmp_path: Path) -> None:
    lift_path = _copy_pair(SANGO_DIR, "sango", tmp_path)
    lexicon = sil_lift.load(lift_path)
    (ranges_file,) = lexicon.ranges_files.values()
    assert len(ranges_file.ranges) == 16

    target = ranges_file.find("etymology")
    assert target is not None
    target.elements[0].label["en"] = Text(["borrowed (edited)"])
    lexicon.save()

    # The .lift itself is untouched -> byte-identical.
    assert (tmp_path / "sango.lift").read_bytes() == (SANGO_DIR / "sango.lift").read_bytes()
    # The ranges file changed, but every untouched range kept its exact bytes.
    original = (SANGO_DIR / "sango.lift-ranges").read_bytes()
    result = (tmp_path / "sango.lift-ranges").read_bytes()
    assert result != original
    from sil_lift._scan import scan

    spans = scan(original)
    assert spans is not None
    range_spans = [s for s in spans.children if s.tag == "range"]
    assert len(range_spans) == 16
    for span in range_spans[1:]:  # etymology is the first range in the file
        assert original[span.start : span.end] in result

    reloaded = RangesFile.load(tmp_path / "sango.lift-ranges")
    edited = reloaded.find("etymology")
    assert edited is not None
    assert str(edited.elements[0].label["en"]) == "borrowed (edited)"


def test_all_ranges_merges_inline_and_external() -> None:
    lexicon = sil_lift.load(PAIR_DIR / "test20080407.lift")
    merged = lexicon.all_ranges()
    # External definition (only in the .lift-ranges file):
    assert [e.id for e in merged["grammatical-info"].elements] == ["Adverb", "Noun", "Verb"]
    # Inline definitions in the header keep winning:
    inline_ids = {r.id for r in lexicon.header.ranges if r.elements}
    for range_id in inline_ids:
        assert merged[range_id] is next(r for r in lexicon.header.ranges if r.id == range_id)


def test_all_ranges_resolves_flex_href_basenames() -> None:
    lexicon = sil_lift.load(CORPUS_DIR / "flex" / "AllFLExFields" / "AllFLExFields.lift")
    # Every header range is href-only (dangling file://C:/ URI); resolution
    # falls back to the basename sibling.
    assert len(lexicon.ranges_files) == 1
    merged = lexicon.all_ranges()
    grammatical = merged["grammatical-info"]
    assert grammatical.elements, "external definition should supply the elements"
    assert any(e.id == "Noun" for e in grammatical.elements)


def test_flex_range_element_extensions_are_carried() -> None:
    """FLEx writes trait/field inside range-element (out of schema, see PROVENANCE)."""
    ranges_file = RangesFile.load(SANGO_DIR / "sango.lift-ranges")
    with_residue = [
        element for range_ in ranges_file.ranges for element in range_.elements if element.extra
    ]
    assert with_residue, "expected FLEx trait/field extensions to land in Extras"


def test_ranges_file_version_guard() -> None:
    with pytest.raises(LiftParseError, match="lift-ranges"):
        RangesFile.load(PAIR_DIR / "test20080407.lift")  # a .lift is not a ranges doc


def test_ranges_schema_is_loadable_and_spec_faithful() -> None:
    schema_path = Path(sil_lift.__file__).parent / "schemas" / "lift-ranges-0.13.rng"
    schema = etree.RelaxNG(etree.parse(schema_path))
    assert schema.validate(etree.parse(PAIR_DIR / "test20080407.lift-ranges"))
    # FLEx files carry out-of-schema extensions (documented in PROVENANCE.md).
    assert not schema.validate(etree.parse(SANGO_DIR / "sango.lift-ranges"))
    assert not schema.validate(
        etree.parse(CORPUS_DIR / "flex" / "AllFLExFields" / "AllFLExFields.lift-ranges")
    )


def test_media_refs_and_missing_media_on_moma_folder() -> None:
    lexicon = sil_lift.load(CORPUS_DIR / "folder" / "Moma" / "Moma.lift")
    refs = list(lexicon.media_refs())
    assert {r.href for r in refs} == {"pictures\\cultural law.png", "pictures\\sdd.png"}
    assert all(r.kind == "illustration" for r in refs)
    assert all(r.entry_id for r in refs)
    assert lexicon.missing_media() == []


def test_missing_media_on_all_flex_fields() -> None:
    # The corpus deliberately omits the upstream filler media (PROVENANCE.md),
    # so these references must be reported missing.
    lexicon = sil_lift.load(CORPUS_DIR / "flex" / "AllFLExFields" / "AllFLExFields.lift")
    missing = {(r.kind, r.href) for r in lexicon.missing_media()}
    assert ("media", "Kalimba.mp3") in missing
    assert ("illustration", "Desert.jpg") in missing


def test_missing_media_flags_broken_ref(tmp_path: Path) -> None:
    src = CORPUS_DIR / "folder" / "Moma"
    shutil.copytree(src, tmp_path / "Moma")
    lexicon = sil_lift.load(tmp_path / "Moma" / "Moma.lift")
    (tmp_path / "Moma" / "pictures" / "sdd.png").unlink()
    missing = lexicon.missing_media()
    assert [r.href for r in missing] == ["pictures\\sdd.png"]


@pytest.mark.parametrize(
    ("href", "expected"),
    [
        ("audio/one.wav", Path("audio/one.wav")),
        ("pictures\\cultural law.png", Path("pictures/cultural law.png")),
        ("C:/dir/pic.png", None),
        ("C:\\dir\\pic.png", None),
        ("/abs/pic.png", None),
        ("//server/share/pic.png", None),
        ("file://C:/x.png", None),
        ("http://example.com/x.png", None),
    ],
)
def test_normalize_href(href: str, expected: Path | None) -> None:
    # WeSay backslash+space stays relative; every absolute form (drive-letter,
    # POSIX, UNC, file://, remote) is refused regardless of host.
    assert _normalize_href(href) == expected
