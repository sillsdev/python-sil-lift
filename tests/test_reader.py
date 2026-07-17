from datetime import UTC, date, datetime
from pathlib import Path

import pytest

import sil_lift
from sil_lift import LiftParseError, Span

CORPUS_DIR = Path(__file__).parent / "corpus"

LOADABLE = sorted(
    p
    for p in CORPUS_DIR.rglob("*.lift")
    if "0.12" not in p.parts and p.name != "sample.lift"  # 0.12 originals: see guard tests
)
V012_FILES = [
    *sorted((CORPUS_DIR / "spec-examples" / "0.12").glob("*.lift")),
    CORPUS_DIR / "misc" / "sample.lift",
]


def corpus_id(path: Path) -> str:
    return path.relative_to(CORPUS_DIR).as_posix()


@pytest.mark.parametrize("path", LOADABLE, ids=corpus_id)
def test_loads(path: Path) -> None:
    lexicon = sil_lift.load(path)
    assert lexicon.path == path
    for entry in lexicon.entries:
        assert entry.lexical_unit is not None


def test_minimal_loads_empty() -> None:
    lexicon = sil_lift.load(CORPUS_DIR / "spec-examples" / "0.13" / "minimal.lift")
    assert lexicon.entries == []
    assert not lexicon.header


@pytest.mark.parametrize("path", V012_FILES, ids=corpus_id)
def test_version_guard_names_the_version(path: Path) -> None:
    with pytest.raises(LiftParseError, match=r"0\.12"):
        sil_lift.load(path)


def test_not_xml() -> None:
    with pytest.raises(LiftParseError, match="not well-formed"):
        sil_lift.load(CORPUS_DIR / "PROVENANCE.md")


def test_full_entry_spot_check() -> None:
    lexicon = sil_lift.load(CORPUS_DIR / "spec-examples" / "0.13" / "full-entry.lift")
    assert len(lexicon.entries) == 1
    entry = lexicon.entries[0]
    assert entry.id == "abat"
    assert entry.date_modified == date(1990, 2, 26)
    assert str(entry.lexical_unit["zxx-Latn"]) == "abat"

    (variant,) = entry.variants
    assert variant.traits[0].name == "paradigm"
    assert variant.traits[0].value == "singular"
    assert str(variant.forms["zxx-Latn"]) == "abatke"

    (sense,) = entry.senses
    assert sense.id == "abat_"
    assert sense.grammatical_info is not None
    assert sense.grammatical_info.value == "n"
    assert entry.gloss_langs() == {"en", "id"}
    assert str(sense.gloss("en") or "") == "grove"
    assert str(sense.gloss("id") or "") == "dusun"

    first, second = sense.examples
    assert first.source == "d2.077.03"
    (translation,) = first.translations
    assert str(translation.forms["id"]) == "Saya pergi menyiangi dusun kelapa."
    assert second.source == "d4.079.16"

    (note,) = sense.notes
    assert note.type == "encyclopedic"
    text = note.forms["en"]
    spans = [f for f in text.fragments if isinstance(f, Span)]
    assert len(spans) == 1
    assert spans[0].class_ == "emphasis"
    assert str(spans[0]) == "not"
    assert "not limited" in " ".join(str(text).split())

    # The top-of-file MDF comment is residue on the lexicon, not lost.
    assert lexicon.extra


def test_subsenses_spot_check() -> None:
    lexicon = sil_lift.load(CORPUS_DIR / "spec-examples" / "0.13" / "subsenses.lift")
    entry = lexicon.find(id="opon")
    assert entry is not None
    sense_1, sense_2 = entry.senses
    assert sense_1.order == 1
    assert [s.id for s in sense_1.subsenses] == ["opon_1a", "opon_1b"]
    assert str(sense_1.subsenses[0].gloss("en") or "") == "grand kin"
    assert sense_2.subsenses == []
    assert str(sense_2.gloss("en") or "") == "master"


def test_reversal_main_chain() -> None:
    lexicon = sil_lift.load(CORPUS_DIR / "spec-examples" / "0.13" / "reversals-hierarchy.lift")
    (entry,) = lexicon.entries
    (sense,) = entry.senses
    (reversal,) = sense.reversals
    assert reversal.type == "eng"
    assert str(reversal.forms["en"]) == "mushroom"
    assert reversal.main is not None
    assert str(reversal.main.forms["en"]) == "vegetable"
    assert reversal.main.main is None


def test_all_flex_fields_spot_check() -> None:
    lexicon = sil_lift.load(CORPUS_DIR / "flex" / "AllFLExFields" / "AllFLExFields.lift")
    assert lexicon.producer == "SIL.FLEx 8.0.9.41689"

    header = lexicon.header
    assert len(header.ranges) == 22
    assert header.ranges[0].id == "dialect"
    assert header.ranges[0].href is not None
    assert header.ranges[0].href.startswith("file://C:/")
    assert [f.tag for f in header.fields] == [
        "cv-pattern",
        "tone",
        "comment",
        "import-residue",
        "literal-meaning",
        "summary-definition",
        "scientific-name",
    ]
    # The two comments inside <ranges> are carried as header residue.
    assert header.extra

    entry = lexicon.find(guid="0a18bb95-0eb2-422e-bf7e-c1fd90274670")
    assert entry is not None
    assert entry.id == "คาม_0a18bb95-0eb2-422e-bf7e-c1fd90274670"
    assert entry.date_created == datetime(2014, 9, 25, 9, 13, 41, tzinfo=UTC)
    assert str(entry.lexical_unit["th"]) == "คาม"
    assert str(entry.citation["th"]) == "คาม"
    assert entry.traits[0].name == "morph-type"
    assert {f.type for f in entry.fields} == {
        "literal-meaning",
        "summary-definition",
        "import-residue",
    }
    assert {n.type for n in entry.notes} == {"bibliography", None, "restrictions"}

    (etymology,) = entry.etymologies
    assert etymology.type == "proto"
    assert etymology.source == "A Etymology Source"
    assert [f.lang for f in etymology.forms.forms] == ["th", "en"]
    assert etymology.glosses[0].lang == "en"
    assert etymology.fields[0].type == "comment"

    (relation,) = entry.relations
    assert relation.type == "_component-lexeme"
    assert relation.order == 0
    assert relation.fields[0].type == "summary"

    (pronunciation,) = entry.pronunciations
    assert pronunciation.media[0].href == "Kalimba.mp3"
    assert {f.type for f in pronunciation.fields} == {"cv-pattern", "tone"}

    (sense,) = entry.senses
    assert sense.grammatical_info is not None
    assert sense.grammatical_info.value == "Noun"
    hyperlink_note = next(n for n in sense.notes if n.type == "encyclopedic")
    (span,) = [f for f in hyperlink_note.forms["en"].fragments if isinstance(f, Span)]
    assert span.href == "http://angular.github.io/"
    assert span.class_ == "Hyperlink"
    (illustration,) = sense.illustrations
    assert illustration.href == "Desert.jpg"
    assert illustration.label.keys() == ["th", "en", "fr"]

    other = lexicon.find(id="คาม ๒_dc4106ac-13fd-4ae0-a32b-b737f413d515")
    assert other is not None
    assert len(other.relations) == 2


def test_sango_loads_and_is_big() -> None:
    lexicon = sil_lift.load(CORPUS_DIR / "large" / "sango" / "sango.lift")
    assert len(lexicon.entries) == 3507
    assert lexicon.producer == "SIL.FLEx 9.1.15.658"


def test_multitext_mapping_behavior() -> None:
    lexicon = sil_lift.load(CORPUS_DIR / "spec-examples" / "0.13" / "full-entry.lift")
    lexical_unit = lexicon.entries[0].lexical_unit
    assert "zxx-Latn" in lexical_unit
    assert list(lexical_unit) == ["zxx-Latn"]
    assert lexical_unit.get("nope") is None
    with pytest.raises(KeyError):
        lexical_unit["nope"]
    lexical_unit["en"] = "grove-tree"
    assert str(lexical_unit["en"]) == "grove-tree"
    del lexical_unit["en"]
    assert "en" not in lexical_unit


def test_find_requires_criteria() -> None:
    lexicon = sil_lift.load(CORPUS_DIR / "spec-examples" / "0.13" / "full-entry.lift")
    with pytest.raises(ValueError, match="find"):
        lexicon.find()
    assert lexicon.find(id="no-such-entry") is None


def test_schema_invalid_content_is_carried_not_dropped() -> None:
    """dialects.lift has <form> without lang inside <etymology> (see PROVENANCE.md)."""
    lexicon = sil_lift.load(CORPUS_DIR / "spec-examples" / "0.13" / "dialects.lift")
    lang_less = [
        form
        for entry in lexicon.entries
        for etymology in entry.etymologies
        for form in etymology.forms.forms
        if form.lang is None
    ]
    assert lang_less, "expected the schema-invalid lang-less etymology form to load"
    assert str(lang_less[0].text)  # its text content survives
