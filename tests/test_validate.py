"""M4 acceptance: every negative fixture caught with correct addressing;
clean corpus validates; C# Validator parity on shared cases (duplicate-guid)."""

from pathlib import Path

import pytest

import sil_lift
from sil_lift import LiftValidationError, Problem

CORPUS_DIR = Path(__file__).parent / "corpus"
NEGATIVE_DIR = CORPUS_DIR / "negative"


def problems_for(path: Path) -> list[Problem]:
    return list(sil_lift.iter_problems(path))


def codes(problems: list[Problem]) -> set[tuple[str, str]]:
    return {(p.level, p.code) for p in problems}


def test_duplicate_guid_is_error_with_addressing() -> None:
    problems = problems_for(NEGATIVE_DIR / "duplicate-guid.lift")
    (problem,) = problems
    assert (problem.level, problem.code) == ("error", "duplicate-guid")
    assert problem.entry_id == "two"
    assert problem.guid == "11111111-1111-1111-1111-111111111111"
    assert problem.line is not None and problem.line > 1


def test_dangling_ref_only_flags_the_broken_one() -> None:
    problems = problems_for(NEGATIVE_DIR / "dangling-ref.lift")
    (problem,) = problems
    assert (problem.level, problem.code) == ("error", "dangling-ref")
    assert problem.entry_id == "one"
    assert "no-such-target" in problem.message


def test_range_parent_integrity() -> None:
    problems = problems_for(NEGATIVE_DIR / "range-parent.lift")
    (problem,) = problems
    assert (problem.level, problem.code) == ("error", "range-parent")
    assert "Nooun" in problem.message


def test_undefined_range_values_are_warnings() -> None:
    problems = problems_for(NEGATIVE_DIR / "undefined-range-value.lift")
    assert codes(problems) == {("warning", "undefined-range-value")}
    assert len(problems) == 2
    assert all(p.entry_id == "one" for p in problems)
    messages = " | ".join(p.message for p in problems)
    assert "Klingon" in messages and "south" in messages


def test_duplicate_form_lang_is_schematron_only_warning() -> None:
    problems = problems_for(NEGATIVE_DIR / "duplicate-form-lang.lift")
    (problem,) = problems
    assert (problem.level, problem.code) == ("warning", "duplicate-form-lang")
    assert problem.entry_id == "one"


def test_schema_violation_is_error_addressed_to_entry() -> None:
    problems = problems_for(NEGATIVE_DIR / "schema-invalid.lift")
    schema_errors = [p for p in problems if p.code == "schema"]
    assert schema_errors
    assert all(p.level == "error" for p in schema_errors)
    assert any(p.entry_id == "broken" for p in schema_errors)
    assert any(p.line is not None for p in schema_errors)


def test_missing_media_folder_fixture() -> None:
    problems = problems_for(NEGATIVE_DIR / "missing-media" / "missing-media.lift")
    assert codes(problems) == {("warning", "missing-media")}
    hrefs = {p.message for p in problems}
    assert any("none.wav" in m for m in hrefs)
    assert any("gone.png" in m for m in hrefs)


def test_flex_uri_quirks_warn_but_never_error() -> None:
    problems = problems_for(NEGATIVE_DIR / "flex-quirks.lift")
    assert problems, "the quirky URIs must be reported"
    assert codes(problems) == {("warning", "uri-not-rfc")}


def test_validate_file_raises_on_first_error() -> None:
    with pytest.raises(LiftValidationError) as info:
        sil_lift.validate_file(NEGATIVE_DIR / "duplicate-guid.lift")
    assert info.value.problem.code == "duplicate-guid"


def test_validate_file_passes_on_warning_only_files() -> None:
    sil_lift.validate_file(NEGATIVE_DIR / "flex-quirks.lift")
    sil_lift.validate_file(NEGATIVE_DIR / "duplicate-form-lang.lift")


CLEAN = [
    "spec-examples/0.13/full-entry.lift",
    "spec-examples/0.13/subsenses.lift",
    "spec-examples/0.13/reversals-hierarchy.lift",
    "spec-examples/0.13/simple.lift",
    "spec-examples/0.13/header.lift",  # its file://C:/ hrefs become warnings
    "ranges/test20080407.lift",
    "folder/Moma/Moma.lift",
    "misc/sample.0.13.lift",
]


@pytest.mark.parametrize("name", CLEAN)
def test_clean_corpus_has_no_errors(name: str) -> None:
    problems = problems_for(CORPUS_DIR / name)
    errors = [p for p in problems if p.level == "error"]
    assert errors == []


def test_test20080407_pair_is_fully_clean() -> None:
    assert problems_for(CORPUS_DIR / "ranges" / "test20080407.lift") == []


def test_flex_lift_is_schema_clean_but_companion_is_not() -> None:
    problems = problems_for(CORPUS_DIR / "flex" / "AllFLExFields" / "AllFLExFields.lift")
    lift_errors = [
        p for p in problems if p.level == "error" and p.file and p.file.suffix == ".lift"
    ]
    ranges_errors = [
        p for p in problems if p.level == "error" and p.file and p.file.suffix == ".lift-ranges"
    ]
    assert lift_errors == []  # href-masking + tag-grouping make the .lift clean
    assert ranges_errors, "FLEx trait/field in range-element (see PROVENANCE.md)"
    assert {p.code for p in ranges_errors} == {"schema"}


def test_sango_real_defects_are_found() -> None:
    problems = problems_for(CORPUS_DIR / "large" / "sango" / "sango.lift")
    by_code: dict[str, int] = {}
    for problem in problems:
        by_code[problem.code] = by_code.get(problem.code, 0) + 1
    # Two genuinely dangling range-element parents + one undefined POS value
    # ('prenom') in the real export; NFC-normalization keeps the count at 1.
    assert by_code.get("range-parent") == 2
    assert by_code.get("undefined-range-value") == 1
    assert by_code.get("schema", 0) > 0  # companion's trait/field extensions
    assert all(
        p.file is not None and p.file.suffix == ".lift-ranges"
        for p in problems
        if p.code == "schema"
    )


def test_in_memory_lexicon_validation() -> None:
    lexicon = sil_lift.Lexicon()
    for entry_id in ("a", "b"):
        entry = sil_lift.Entry(id=entry_id, guid="33333333-3333-3333-3333-333333333333")
        entry.lexical_unit["en"] = entry_id
        lexicon.entries.append(entry)
    problems = list(lexicon.iter_problems())
    assert ("error", "duplicate-guid") in codes(problems)


def test_problem_str_format() -> None:
    problems = problems_for(NEGATIVE_DIR / "duplicate-guid.lift")
    text = str(problems[0])
    assert "error [duplicate-guid]" in text
    assert "duplicate-guid.lift:" in text
    assert "entry two" in text
