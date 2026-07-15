"""Property-based round-trip suite (corpus plan §C.9).

Two properties over generated LIFT documents:

1. **Serialize/parse fixpoint**: canonical bytes survive a parse→serialize
   cycle unchanged.
2. **Passthrough**: an on-disk document saved with no edits is byte-identical;
   with one entry touched, every untouched entry's bytes appear verbatim.
"""

import tempfile
from datetime import UTC, date, datetime
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st
from lxml import etree

import sil_lift
from sil_lift import Entry, Form, Lexicon, Multitext, Note, Sense, Span, Text, Trait
from sil_lift._reader import parse_root
from sil_lift._scan import scan
from sil_lift._writer import canonical_document

# XML 1.0 valid characters, minus surrogates (codec="utf-8") and the two
# non-characters; \r is excluded (parsers normalize it), \t and \n are added
# back via explicit alternatives where allowed.
_CHARS = st.characters(min_codepoint=0x20, codec="utf-8", exclude_characters="￾￿")
_TEXT = st.text(alphabet=st.one_of(_CHARS, st.sampled_from("\t\n")), max_size=30)
# Attribute values: XML parsers normalize \t\n in attributes to spaces, so keep
# tokens to characters that round-trip verbatim.
_TOKEN = st.text(alphabet=_CHARS, min_size=1, max_size=15)
_LANG = st.sampled_from(["en", "fr", "th", "sg", "es", "qaa-x-test"])

_WHEN = st.one_of(
    st.none(),
    st.dates(min_value=date(1900, 1, 1), max_value=date(2100, 1, 1)),
    st.datetimes(
        min_value=datetime(1900, 1, 1),
        max_value=datetime(2100, 1, 1),
        timezones=st.one_of(st.none(), st.just(UTC)),
    ),
)


@st.composite
def _spans(draw: st.DrawFn) -> Span:
    return Span(
        content=[draw(_TEXT)],
        lang=draw(st.none() | _LANG),
        href=draw(st.none() | _TOKEN),
        class_=draw(st.none() | _TOKEN),
    )


@st.composite
def _texts(draw: st.DrawFn) -> Text:
    return Text(draw(st.lists(st.one_of(_TEXT, _spans()), max_size=3)))


@st.composite
def _multitexts(draw: st.DrawFn) -> Multitext:
    langs = draw(st.lists(_LANG, unique=True, max_size=3))
    return Multitext([Form(lang, draw(_texts())) for lang in langs])


@st.composite
def _traits(draw: st.DrawFn) -> Trait:
    return Trait(draw(_TOKEN), draw(_TOKEN))


@st.composite
def _notes(draw: st.DrawFn) -> Note:
    return Note(type=draw(st.none() | _TOKEN), forms=draw(_multitexts()))


@st.composite
def _senses(draw: st.DrawFn) -> Sense:
    sense = Sense(
        id=draw(st.none() | _TOKEN),
        order=draw(st.none() | st.integers(min_value=0, max_value=99)),
        definition=draw(_multitexts()),
        date_created=draw(_WHEN),
    )
    for lang in draw(st.lists(_LANG, unique=True, max_size=2)):
        sense.glosses.append(Form(lang, draw(_texts())))
    sense.notes.extend(draw(st.lists(_notes(), max_size=2)))
    sense.traits.extend(draw(st.lists(_traits(), max_size=2)))
    if draw(st.booleans()):
        sense.grammatical_info = sil_lift.GrammaticalInfo(draw(_TOKEN))
    return sense


@st.composite
def _entries(draw: st.DrawFn) -> Entry:
    entry = Entry(
        id=draw(st.none() | _TOKEN),
        guid=draw(st.none() | st.uuids().map(str)),
        lexical_unit=draw(_multitexts()),
        date_modified=draw(_WHEN),
    )
    entry.senses.extend(draw(st.lists(_senses(), max_size=3)))
    entry.traits.extend(draw(st.lists(_traits(), max_size=2)))
    if draw(st.booleans()):
        entry.relations.append(sil_lift.Relation(type=draw(_TOKEN), ref=draw(_TOKEN)))
    return entry


@st.composite
def _lexicons(draw: st.DrawFn) -> Lexicon:
    return Lexicon(
        producer=draw(st.none() | _TOKEN),
        entries=draw(st.lists(_entries(), max_size=4)),
    )


@given(_lexicons())
def test_serialize_parse_fixpoint(lexicon: Lexicon) -> None:
    first = canonical_document(lexicon)
    reparsed = parse_root(etree.fromstring(first))
    assert canonical_document(reparsed) == first


@settings(max_examples=25, deadline=None)
@given(_lexicons())
def test_passthrough_unchanged_save_is_byte_identical(lexicon: Lexicon) -> None:
    data = canonical_document(lexicon)
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "generated.lift"
        source.write_bytes(data)
        loaded = sil_lift.load(source)
        out = Path(tmp) / "out.lift"
        loaded.save(out)
        assert out.read_bytes() == data


@settings(max_examples=25, deadline=None)
@given(_lexicons())
def test_untouched_entries_stay_byte_identical_under_edit(lexicon: Lexicon) -> None:
    data = canonical_document(lexicon)
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "generated.lift"
        source.write_bytes(data)
        loaded = sil_lift.load(source)
        if not loaded.entries:
            return
        loaded.entries[0].lexical_unit["qaa-x-touch"] = "touched"
        out = Path(tmp) / "out.lift"
        loaded.save(out)
        result = out.read_bytes()

        spans = scan(data)
        assert spans is not None
        entry_spans = [s for s in spans.children if s.tag == "entry"]
        for span in entry_spans[1:]:  # every untouched entry survives verbatim
            assert data[span.start : span.end] in result

        reloaded = sil_lift.load(out)
        assert str(reloaded.entries[0].lexical_unit["qaa-x-touch"]) == "touched"
