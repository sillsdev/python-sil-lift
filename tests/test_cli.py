import csv
import io
import json
import shutil
from pathlib import Path

import pytest

from sil_lift._cli import main

CORPUS_DIR = Path(__file__).parent / "corpus"


def test_validate_clean_file(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", str(CORPUS_DIR / "ranges" / "test20080407.lift")]) == 0
    out = capsys.readouterr().out
    assert "0 error(s), 0 warning(s)" in out


def test_validate_reports_errors_and_exits_1(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", str(CORPUS_DIR / "negative" / "duplicate-guid.lift")]) == 1
    out = capsys.readouterr().out
    assert "duplicate-guid" in out
    assert "1 error(s)" in out


def test_validate_warnings_only_exits_0(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", str(CORPUS_DIR / "negative" / "flex-quirks.lift")]) == 0
    assert "uri-not-rfc" in capsys.readouterr().out


def test_validate_json_reports_findings(capsys: pytest.CaptureFixture[str]) -> None:
    path = CORPUS_DIR / "negative" / "duplicate-guid.lift"
    assert main(["validate", str(path), "--format", "json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["errors"] >= 1
    assert any(problem["code"] == "duplicate-guid" for problem in payload["problems"])


def test_validate_json_clean_file(capsys: pytest.CaptureFixture[str]) -> None:
    path = CORPUS_DIR / "ranges" / "test20080407.lift"
    assert main(["validate", str(path), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"problems": [], "summary": {"errors": 0, "warnings": 0}}


def test_validate_strict_treats_warnings_as_errors(capsys: pytest.CaptureFixture[str]) -> None:
    path = CORPUS_DIR / "negative" / "flex-quirks.lift"
    assert main(["validate", str(path)]) == 0  # warnings alone pass by default
    assert main(["validate", str(path), "--strict"]) == 1
    assert "strict: warnings treated as errors" in capsys.readouterr().out


def test_validate_no_check_media(capsys: pytest.CaptureFixture[str]) -> None:
    path = CORPUS_DIR / "negative" / "missing-media" / "missing-media.lift"
    assert main(["validate", str(path)]) == 0
    assert "[missing-media]" in capsys.readouterr().out
    assert main(["validate", str(path), "--no-check-media"]) == 0
    assert "[missing-media]" not in capsys.readouterr().out


def test_validate_require_ids(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "noid.lift"
    path.write_bytes(
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<lift version="0.13">\n'
        b'<entry id="e1">\n'  # no guid
        b'<lexical-unit><form lang="en"><text>x</text></form></lexical-unit>\n'
        b"</entry>\n"
        b"</lift>\n"
    )
    assert main(["validate", str(path)]) == 0  # ids are optional by default
    assert main(["validate", str(path), "--require-ids"]) == 1
    assert "missing-id" in capsys.readouterr().out


def test_validate_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<lift version="0.13"><entry id="e1" guid="cccccccc-cccc-4444-8888-cccccccccccc">'
        b'<lexical-unit><form lang="en"><text>x</text></form></lexical-unit></entry></lift>\n'
    )

    class _Stdin:
        buffer = io.BytesIO(doc)

    monkeypatch.setattr("sys.stdin", _Stdin())
    assert main(["validate", "-", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"problems": [], "summary": {"errors": 0, "warnings": 0}}


def test_stats_json(capsys: pytest.CaptureFixture[str]) -> None:
    path = CORPUS_DIR / "spec-examples" / "0.13" / "full-entry.lift"
    assert main(["stats", str(path), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["entries"] == 1
    assert payload["senses"] >= 1
    assert isinstance(payload["languages"], list)


def test_filename_with_space(capsys: pytest.CaptureFixture[str]) -> None:
    path = CORPUS_DIR / "spec-examples" / "0.13" / "fields any order.lift"
    assert main(["stats", str(path)]) == 0
    assert "entries:   1" in capsys.readouterr().out


def test_stats_streaming_on_sango(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["stats", str(CORPUS_DIR / "large" / "sango" / "sango.lift")]) == 0
    out = capsys.readouterr().out
    assert "entries:   3507" in out
    assert "sg" in out  # a language present in the data


def test_stats_counts_variant_media(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Regression: media inside a <variant>'s <pronunciation> must count too,
    # matching media_refs()/check-media rather than just top-level pronunciations.
    path = tmp_path / "variant-media.lift"
    path.write_bytes(
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<lift version="0.13">\n'
        b'<entry id="e1">\n'
        b'<lexical-unit><form lang="en"><text>x</text></form></lexical-unit>\n'
        b"<variant>\n"
        b'<pronunciation><media href="one.wav"/></pronunciation>\n'
        b"</variant>\n"
        b"</entry>\n"
        b"</lift>\n"
    )
    assert main(["stats", str(path)]) == 0
    assert "media refs: 1" in capsys.readouterr().out


def test_sort_writes_canonical_copy(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = CORPUS_DIR / "spec-examples" / "0.13" / "subsenses.lift"
    out = tmp_path / "sorted.lift"
    assert main(["sort", str(source), "-o", str(out)]) == 0
    assert out.is_file()
    again = tmp_path / "sorted-again.lift"
    assert main(["sort", str(out), "-o", str(again)]) == 0
    assert again.read_bytes() == out.read_bytes()  # idempotent


def test_sort_in_place(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "file.lift"
    shutil.copy(CORPUS_DIR / "spec-examples" / "0.13" / "full-entry.lift", target)
    before = target.read_bytes()
    assert main(["sort", str(target)]) == 0
    assert target.read_bytes() != before  # canonical layout replaces original


def test_check_media_on_moma(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check-media", str(CORPUS_DIR / "folder" / "Moma" / "Moma.lift")]) == 0
    out = capsys.readouterr().out
    assert "0 missing" in out
    # The wav files are referenced via audio writing systems, not <media>:
    assert "orphaned" in out


def test_check_media_flags_missing(capsys: pytest.CaptureFixture[str]) -> None:
    path = CORPUS_DIR / "negative" / "missing-media" / "missing-media.lift"
    assert main(["check-media", str(path)]) == 1
    out = capsys.readouterr().out
    assert "none.wav" in out and "gone.png" in out


def test_check_media_absolute_href_does_not_mark_local_file_referenced(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # An absolute href (FLEx-style dangling path) must not mark a folder file
    # as referenced — mirrors missing_media(), which skips non-relative hrefs.
    audio = tmp_path / "audio"
    audio.mkdir()
    wav = audio / "one.wav"
    wav.write_bytes(b"")
    href = str(wav).replace("\\", "/")
    (tmp_path / "abs.lift").write_bytes(
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<lift version="0.13">\n'
        b'<entry id="e1">\n'
        b'<lexical-unit><form lang="en"><text>x</text></form></lexical-unit>\n'
        b'<pronunciation><media href="' + href.encode() + b'"/></pronunciation>\n'
        b"</entry>\n"
        b"</lift>\n"
    )
    assert main(["check-media", str(tmp_path / "abs.lift")]) == 0
    out = capsys.readouterr().out
    assert "orphaned" in out and "one.wav" in out


def test_bad_input_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", str(CORPUS_DIR / "PROVENANCE.md")]) == 2
    assert "error:" in capsys.readouterr().err


def test_export_auto_detects_langs(tmp_path: Path) -> None:
    source = CORPUS_DIR / "spec-examples" / "0.13" / "full-entry.lift"
    out = tmp_path / "out.csv"
    assert main(["export", str(source), "-o", str(out)]) == 0
    header, *data = csv.reader(out.open(encoding="utf-8", newline=""))
    assert header == [
        "entry_id",
        "entry_guid",
        "sense_id",
        "lexeme",
        "pos",
        "gloss_en",
        "definition_en",
        "gloss_id",
        "definition_id",
    ]
    assert len(data) == 1
    row = dict(zip(header, data[0], strict=True))
    assert row["entry_id"] == "abat"
    assert row["pos"] == "n"
    assert row["gloss_en"] == "grove"
    assert row["gloss_id"] == "dusun"


def test_export_flattens_subsenses(tmp_path: Path) -> None:
    source = CORPUS_DIR / "spec-examples" / "0.13" / "subsenses.lift"
    out = tmp_path / "out.csv"
    assert main(["export", str(source), "-o", str(out)]) == 0
    header, *data = csv.reader(out.open(encoding="utf-8", newline=""))
    assert len(data) == 3
    sense_ids = [row[header.index("sense_id")] for row in data]
    assert sense_ids == ["opon_1a", "opon_1b", "opon_2"]


def test_export_langs_option_restricts_and_orders(tmp_path: Path) -> None:
    source = CORPUS_DIR / "spec-examples" / "0.13" / "full-entry.lift"

    reordered = tmp_path / "reordered.csv"
    assert main(["export", str(source), "-o", str(reordered), "--langs", "id,en"]) == 0
    header = next(csv.reader(reordered.open(encoding="utf-8", newline="")))
    assert header == [
        "entry_id",
        "entry_guid",
        "sense_id",
        "lexeme",
        "pos",
        "gloss_id",
        "definition_id",
        "gloss_en",
        "definition_en",
    ]

    restricted = tmp_path / "restricted.csv"
    assert main(["export", str(source), "-o", str(restricted), "--langs", "en"]) == 0
    header = next(csv.reader(restricted.open(encoding="utf-8", newline="")))
    assert header == [
        "entry_id",
        "entry_guid",
        "sense_id",
        "lexeme",
        "pos",
        "gloss_en",
        "definition_en",
    ]


def test_export_tsv(tmp_path: Path) -> None:
    source = CORPUS_DIR / "spec-examples" / "0.13" / "full-entry.lift"
    out = tmp_path / "out.tsv"
    assert main(["export", str(source), "-o", str(out), "--tsv", "--langs", "en"]) == 0
    first_line = out.read_text(encoding="utf-8").splitlines()[0]
    assert first_line == "entry_id\tentry_guid\tsense_id\tlexeme\tpos\tgloss_en\tdefinition_en"


def test_export_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    source = CORPUS_DIR / "spec-examples" / "0.13" / "full-entry.lift"
    assert main(["export", str(source), "--langs", "en"]) == 0
    out = capsys.readouterr().out
    assert "entry_id" in out
    assert "abat" in out


def test_export_filename_with_space(tmp_path: Path) -> None:
    path = CORPUS_DIR / "spec-examples" / "0.13" / "fields any order.lift"
    out = tmp_path / "out.csv"
    assert main(["export", str(path), "-o", str(out)]) == 0
    assert out.is_file()
