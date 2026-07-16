"""M5 acceptance: idempotent, deterministic, LiftSorter-rule-faithful sort;
canonicalized output stays RNG-valid and semantically equal to its input."""

from pathlib import Path

import pytest
from lxml import etree

import sil_lift
from sil_lift import canonicalize
from test_writer import _semantic_bytes

CORPUS_DIR = Path(__file__).parent / "corpus"

# header.lift is excluded: raw-RNG-invalid per PROVENANCE.md (file://C:/ hrefs).
RNG_VALID = [
    "spec-examples/0.13/full-entry.lift",
    "spec-examples/0.13/subsenses.lift",
    "spec-examples/0.13/reversals.lift",
    "spec-examples/0.13/hugal-mdf.lift",
    "ranges/test20080407.lift",
    "folder/Moma/Moma.lift",
]

UNSORTED = b"""<?xml version="1.0" encoding="UTF-8"?>
<lift version="0.13">
<header>
<fields>
<field tag="zeta"><form lang="en"><text>z</text></form></field>
<field tag="alpha"><form lang="en"><text>a</text></form></field>
</fields>
<ranges>
<range id="zoo"><range-element id="b"/><range-element id="A"/></range>
<range id="Alpha"/>
</ranges>
</header>
<entry id="mid" guid="BBBBBBBB-0000-0000-0000-000000000000">
<lexical-unit><form lang="en"><text>mid</text></form></lexical-unit>
</entry>
<entry id="last" guid="cccccccc-0000-0000-0000-000000000000">
<lexical-unit><form lang="en"><text>last</text></form></lexical-unit>
</entry>
<entry id="first" guid="aaaaaaaa-0000-0000-0000-000000000000">
<lexical-unit><form lang="en"><text>first</text></form></lexical-unit>
</entry>
<entry id="no-guid">
<lexical-unit><form lang="en"><text>guidless</text></form></lexical-unit>
</entry>
</lift>
"""


def test_sort_mirrors_liftsorter_rules(tmp_path: Path) -> None:
    source = tmp_path / "unsorted.lift"
    source.write_bytes(UNSORTED)
    lexicon = sil_lift.load(source)
    lexicon.sort()
    # Entries by casefolded guid (guidless first: empty key), LiftSorter-style.
    assert [e.id for e in lexicon.entries] == ["no-guid", "first", "mid", "last"]
    # Header ranges by casefolded id; range-elements by casefolded id.
    assert [r.id for r in lexicon.header.ranges] == ["Alpha", "zoo"]
    assert [e.id for e in lexicon.header.ranges[1].elements] == ["A", "b"]
    # Header field definitions by tag.
    assert [f.tag for f in lexicon.header.fields] == ["alpha", "zeta"]


def test_sort_is_idempotent(tmp_path: Path) -> None:
    source = tmp_path / "unsorted.lift"
    source.write_bytes(UNSORTED)
    lexicon = sil_lift.load(source)
    lexicon.sort()
    once = [e.id for e in lexicon.entries]
    lexicon.sort()
    assert [e.id for e in lexicon.entries] == once


def test_sort_then_save_keeps_untouched_entries_verbatim(tmp_path: Path) -> None:
    source = tmp_path / "unsorted.lift"
    source.write_bytes(UNSORTED)
    lexicon = sil_lift.load(source)
    lexicon.sort()
    out = tmp_path / "sorted.lift"
    lexicon.save(out)
    result = out.read_bytes()

    from sil_lift._scan import scan

    spans = scan(UNSORTED)
    assert spans is not None
    for span in (s for s in spans.children if s.tag == "entry"):
        assert UNSORTED[span.start : span.end] in result  # bytes moved, not rewritten
    reloaded = sil_lift.load(out)
    assert [e.id for e in reloaded.entries] == ["no-guid", "first", "mid", "last"]


def test_canonicalize_is_deterministic_and_idempotent(tmp_path: Path) -> None:
    source = tmp_path / "unsorted.lift"
    source.write_bytes(UNSORTED)
    first = tmp_path / "c1.lift"
    second = tmp_path / "c2.lift"
    canonicalize(source, first)
    canonicalize(source, second)
    assert first.read_bytes() == second.read_bytes()  # deterministic across runs
    third = tmp_path / "c3.lift"
    canonicalize(first, third)
    assert third.read_bytes() == first.read_bytes()  # sort . sort = sort


def _entries_sorted(data: bytes) -> bytes:
    """Comparer aid: normalize exactly the orderings canonicalize changes —
    entries by (guid, id), ranges/range-elements by id, field defs by tag
    (all unordered/id-keyed collections per the LIFT spec)."""
    root = etree.fromstring(data)
    entries = [e for e in root if isinstance(e.tag, str) and e.tag == "entry"]
    for entry in entries:
        root.remove(entry)
    for entry in sorted(
        entries, key=lambda e: ((e.get("guid") or "").casefold(), (e.get("id") or "").casefold())
    ):
        root.append(entry)
    for parent_tag, child_tag, key in [
        ("ranges", "range", "id"),
        ("range", "range-element", "id"),
        ("fields", "field", "tag"),
    ]:
        for parent in list(root.iter(parent_tag)):
            children = [c for c in parent if isinstance(c.tag, str) and c.tag == child_tag]
            for child in children:
                parent.remove(child)
            for child in sorted(children, key=lambda c: (c.get(key) or "").casefold()):
                parent.append(child)
    return etree.tostring(root)


@pytest.mark.parametrize("name", RNG_VALID)
def test_canonicalized_output_is_rng_valid_and_semantically_equal(
    name: str, tmp_path: Path
) -> None:
    source = CORPUS_DIR / name
    out = tmp_path / "canonical.lift"
    canonicalize(source, out)
    schema = etree.RelaxNG(
        etree.parse(Path(sil_lift.__file__).parent / "schemas" / "lift-0.13.rng")
    )
    assert schema.validate(etree.parse(out))
    assert _semantic_bytes(_entries_sorted(out.read_bytes())) == _semantic_bytes(
        _entries_sorted(source.read_bytes())
    )


def test_canonicalize_never_touches_text_whitespace(tmp_path: Path) -> None:
    source = CORPUS_DIR / "spec-examples" / "0.13" / "subsenses.lift"
    out = tmp_path / "canonical.lift"
    canonicalize(source, out)
    reloaded = sil_lift.load(out)
    original = sil_lift.load(source)
    for a, b in zip(reloaded.entries, original.entries, strict=True):
        for sense_a, sense_b in zip(a.senses, b.senses, strict=True):
            assert str(sense_a.definition.get("en") or "") == str(
                sense_b.definition.get("en") or ""
            )


def test_ranges_file_sort(tmp_path: Path) -> None:
    import shutil

    shutil.copy(CORPUS_DIR / "ranges" / "test20080407.lift-ranges", tmp_path / "r.lift-ranges")
    ranges_file = sil_lift.RangesFile.load(tmp_path / "r.lift-ranges")
    ranges_file.ranges[0].elements.reverse()
    ranges_file.sort()
    assert [e.id for e in ranges_file.ranges[0].elements] == ["Adverb", "Noun", "Verb"]
