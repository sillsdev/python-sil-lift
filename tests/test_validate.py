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
    assert problem.guid == "11111111-1111-4444-8888-111111111111"
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


def test_range_parent_tolerates_flex_normalization_asymmetry() -> None:
    # Regression: FLEx writes a grammatical-info range-element id straight from
    # its NFD in-memory string but normalizes the parent attribute to NFC (see
    # PROVENANCE.md), so the two spellings of one name differ within a single
    # element. The parent link is sound; only the encoding differs.
    lexicon = sil_lift.Lexicon()
    ranges = sil_lift.RangesFile()
    # "Compl\u00e9ments" spelled two ways: the id decomposed (e + U+0301),
    # as FLEx writes range-element ids, and the parent composed.
    nfd_id = "Comple\u0301ments"
    nfc_parent = "Compl\u00e9ments"
    range_ = ranges.add_range("grammatical-info")
    range_.add_element(nfd_id)
    range_.add_element("Comple\u0301ment du lieu", parent=nfc_parent)
    lexicon.add_ranges_file(ranges, href="x.lift-ranges")
    entry = sil_lift.Entry(id="e1", guid="bbbbbbbb-1111-4444-8888-bbbbbbbbbbbb")
    entry.lexical_unit["en"] = "e1"
    lexicon.entries.append(entry)
    assert [p for p in lexicon.iter_problems() if p.code == "range-parent"] == []


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


def test_dangling_ranges_href_flags_missing_relative_companion(tmp_path: Path) -> None:
    path = tmp_path / "d.lift"
    path.write_bytes(
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<lift version="0.13">\n'
        b"<header><ranges>\n"
        b'<range id="semantic-domain-ddp4" href="d.lift-ranges"/>\n'
        b"</ranges></header>\n"
        b'<entry id="e1" guid="99999999-9999-4444-8888-999999999999">\n'
        b'<lexical-unit><form lang="en"><text>x</text></form></lexical-unit>\n'
        b"</entry>\n"
        b"</lift>\n"
    )
    assert ("warning", "dangling-ranges-href") in codes(problems_for(path))


def test_dangling_ranges_href_ignores_absolute_flex_href(tmp_path: Path) -> None:
    # FLEx writes header hrefs as dangling file://C:/ URIs resolved by basename;
    # those are the uri-not-rfc case, not a dangling companion.
    path = tmp_path / "d.lift"
    path.write_bytes(
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<lift version="0.13">\n'
        b"<header><ranges>\n"
        b'<range id="grammatical-info" href="file://C:/nope/x.lift-ranges"/>\n'
        b"</ranges></header>\n"
        b'<entry id="e1" guid="aaaaaaaa-aaaa-4444-8888-aaaaaaaaaaaa">\n'
        b'<lexical-unit><form lang="en"><text>x</text></form></lexical-unit>\n'
        b"</entry>\n"
        b"</lift>\n"
    )
    found = codes(problems_for(path))
    assert ("warning", "dangling-ranges-href") not in found
    assert ("warning", "uri-not-rfc") in found


def test_require_ids_flags_missing_guid_and_sense_id() -> None:
    lexicon = sil_lift.Lexicon()
    entry = sil_lift.Entry(id="e1")  # no guid
    entry.lexical_unit["en"] = "x"
    entry.senses.append(sil_lift.Sense())  # no id
    lexicon.entries.append(entry)
    assert not any(p.code == "missing-id" for p in lexicon.iter_problems())
    required = [p for p in lexicon.iter_problems(require_ids=True) if p.code == "missing-id"]
    assert len(required) == 2
    assert all(p.level == "error" for p in required)


def test_undefined_semantic_domain_value_is_flagged() -> None:
    lexicon = sil_lift.Lexicon()
    ranges = sil_lift.RangesFile()
    ranges.add_range("semantic-domain-ddp4").add_element("1.6.1.2")
    lexicon.add_ranges_file(ranges, href="x.lift-ranges")
    entry = sil_lift.Entry(id="e1", guid="bbbbbbbb-bbbb-4444-8888-bbbbbbbbbbbb")
    entry.lexical_unit["en"] = "x"
    sense = sil_lift.Sense(id="s1")
    sense.traits.append(sil_lift.Trait(name="semantic-domain-ddp4", value="9.9.9"))
    entry.senses.append(sense)
    lexicon.entries.append(entry)
    flagged = [p for p in lexicon.iter_problems() if p.code == "undefined-range-value"]
    assert len(flagged) == 1
    assert "9.9.9" in flagged[0].message


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
    # duplicate-guid: FLEx aliases its POS possibility list under both
    # "grammatical-info" and "from-part-of-speech" range ids, reusing the
    # same range-element guids under each (see PROVENANCE.md).
    assert {p.code for p in ranges_errors} == {"schema", "duplicate-guid"}


def test_sango_real_defects_are_found() -> None:
    problems = problems_for(CORPUS_DIR / "large" / "sango" / "sango.lift")
    by_code: dict[str, int] = {}
    for problem in problems:
        by_code[problem.code] = by_code.get(problem.code, 0) + 1
    # One undefined POS value ('prenom') in the real export; NFC-normalization
    # keeps the count at 1. No range-parent finding: the two parent links that
    # differ from their target's spelling are FLEx's NFD ids under an NFC
    # parent (see PROVENANCE.md), not dangling references.
    assert by_code.get("range-parent") is None
    assert by_code.get("undefined-range-value") == 1
    assert by_code.get("schema", 0) > 0  # companion's trait/field extensions
    # 37 real duplicate guids: FLEx aliases its POS list under both
    # "grammatical-info" and "from-part-of-speech" (same range-element guids
    # under each), and similarly for "Publications"/"do-not-publish-in".
    assert by_code.get("duplicate-guid") == 37
    assert all(
        p.file is not None and p.file.suffix == ".lift-ranges"
        for p in problems
        if p.code == "schema"
    )


def test_problems_reflect_in_memory_edits() -> None:
    # Regression: validation must see what save() would write, not the bytes
    # the document was loaded from.
    lexicon = sil_lift.Lexicon.load(NEGATIVE_DIR / "schema-invalid.lift")
    assert any(p.code == "schema" for p in lexicon.iter_problems())
    del lexicon.entries[0]  # removes the schema-invalid entry
    assert list(lexicon.iter_problems()) == []


def test_semantic_addressing_covers_added_entries() -> None:
    # Regression: the entry-line table must align with lexicon.entries even
    # after edits, so problems in appended entries get line addressing.
    lexicon = sil_lift.Lexicon.load(NEGATIVE_DIR / "duplicate-guid.lift")
    extra = sil_lift.Entry(id="three", guid="11111111-1111-4444-8888-111111111111")
    extra.lexical_unit["en"] = "three"
    lexicon.entries.append(extra)
    problems = [p for p in lexicon.iter_problems() if p.code == "duplicate-guid"]
    assert [p.entry_id for p in problems] == ["two", "three"]
    assert all(p.line is not None for p in problems)


def test_dangling_ref_inside_variant_relation() -> None:
    # Regression: relation/@ref nested inside a <variant> must be checked too,
    # not just entry-level and sense-level relations.
    lexicon = sil_lift.Lexicon()
    entry = sil_lift.Entry(id="e1", guid="44444444-4444-4444-8888-444444444444")
    entry.lexical_unit["en"] = "e1"
    variant = sil_lift.Variant()
    variant.relations.append(sil_lift.Relation(type="see", ref="no-such-target"))
    entry.variants.append(variant)
    lexicon.entries.append(entry)
    problems = [p for p in lexicon.iter_problems() if p.code == "dangling-ref"]
    assert len(problems) == 1
    assert "no-such-target" in problems[0].message


def test_duplicate_form_lang_found_in_nested_multitext() -> None:
    # Regression: the check must cover every Multitext, not just lexical-unit,
    # citation, and sense.definition -- a <note>'s forms is a fourth, nested one.
    lexicon = sil_lift.Lexicon()
    entry = sil_lift.Entry(id="e1", guid="55555555-5555-4444-8888-555555555555")
    entry.lexical_unit["en"] = "e1"
    note = sil_lift.Note()
    note.forms.forms.append(sil_lift.Form(lang="en", text=sil_lift.Text(["a"])))
    note.forms.forms.append(sil_lift.Form(lang="en", text=sil_lift.Text(["b"])))
    entry.notes.append(note)
    lexicon.entries.append(entry)
    problems = [p for p in lexicon.iter_problems() if p.code == "duplicate-form-lang"]
    assert any(p.message.startswith("forms has more than one form") for p in problems)


def test_undefined_range_value_found_in_nested_relation_trait() -> None:
    # Regression: a trait nested inside a <relation> (real FLEx pattern: the
    # is-primary/complex-form-type traits under a component-lexeme relation,
    # see PROVENANCE.md) must be checked too, not just entry- and sense-direct
    # traits.
    lexicon = sil_lift.Lexicon()
    ranges = sil_lift.RangesFile()
    ranges.add_range("complex-form-type").add_element("Compound")
    lexicon.add_ranges_file(ranges, href="x.lift-ranges")
    entry = sil_lift.Entry(id="e1", guid="77777777-7777-4444-8888-777777777777")
    entry.lexical_unit["en"] = "e1"
    relation = sil_lift.Relation(type="_component-lexeme", ref="e1")
    relation.traits.append(sil_lift.Trait(name="complex-form-type", value="Idiom"))
    entry.relations.append(relation)
    lexicon.entries.append(entry)
    flagged = [p for p in lexicon.iter_problems() if p.code == "undefined-range-value"]
    assert len(flagged) == 1
    assert "Idiom" in flagged[0].message


def test_undefined_range_value_found_on_reversal_grammatical_info() -> None:
    # Regression: grammatical-info on a <reversal> (and its main chain) must
    # be checked too, not just a sense's own grammatical-info.
    lexicon = sil_lift.Lexicon()
    ranges = sil_lift.RangesFile()
    ranges.add_range("grammatical-info").add_element("Noun")
    lexicon.add_ranges_file(ranges, href="x.lift-ranges")
    entry = sil_lift.Entry(id="e1", guid="aaaaaaaa-1111-4444-8888-aaaaaaaaaaaa")
    entry.lexical_unit["en"] = "e1"
    sense = sil_lift.Sense(id="s1")
    sense.reversals.append(sil_lift.Reversal(grammatical_info=sil_lift.GrammaticalInfo("Verb")))
    entry.senses.append(sense)
    lexicon.entries.append(entry)
    flagged = [p for p in lexicon.iter_problems() if p.code == "undefined-range-value"]
    assert len(flagged) == 1
    assert "Verb" in flagged[0].message


def test_duplicate_guid_across_range_elements() -> None:
    # Regression: a guid reused across range-elements (real FLEx pattern:
    # aliasing one possibility list under two range ids, see PROVENANCE.md)
    # must be caught too, not just duplicate entry guids.
    lexicon = sil_lift.Lexicon()
    ranges = sil_lift.RangesFile()
    shared_guid = "88888888-8888-4444-8888-888888888888"
    ranges.add_range("grammatical-info").add_element("Noun", guid=shared_guid)
    ranges.add_range("from-part-of-speech").add_element("Noun", guid=shared_guid)
    lexicon.add_ranges_file(ranges, href="x.lift-ranges")
    entry = sil_lift.Entry(id="e1", guid="99999999-9999-4444-8888-999999999999")
    entry.lexical_unit["en"] = "e1"
    lexicon.entries.append(entry)
    flagged = [p for p in lexicon.iter_problems() if p.code == "duplicate-guid"]
    assert len(flagged) == 1
    assert shared_guid in flagged[0].message


def test_in_memory_lexicon_validation() -> None:
    lexicon = sil_lift.Lexicon()
    for entry_id in ("a", "b"):
        entry = sil_lift.Entry(id=entry_id, guid="66666666-6666-4444-8888-666666666666")
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
