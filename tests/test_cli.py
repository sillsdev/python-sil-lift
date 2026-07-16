"""M7 acceptance: the CLI works against the corpus, including the
filename-with-space fixture."""

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


def test_filename_with_space(capsys: pytest.CaptureFixture[str]) -> None:
    path = CORPUS_DIR / "spec-examples" / "0.13" / "fields any order.lift"
    assert main(["stats", str(path)]) == 0
    assert "entries:   1" in capsys.readouterr().out


def test_stats_streaming_on_sango(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["stats", str(CORPUS_DIR / "large" / "sango" / "sango.lift")]) == 0
    out = capsys.readouterr().out
    assert "entries:   3507" in out
    assert "sg" in out  # a language present in the data


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


def test_bad_input_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", str(CORPUS_DIR / "PROVENANCE.md")]) == 2
    assert "error:" in capsys.readouterr().err
