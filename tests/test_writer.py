import itertools
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest
from lxml import etree

import sil_lift

CORPUS_DIR = Path(__file__).parent / "corpus"

LOADABLE = sorted(
    p for p in CORPUS_DIR.rglob("*.lift") if "0.12" not in p.parts and p.name != "sample.lift"
)


def corpus_id(path: Path) -> str:
    return path.relative_to(CORPUS_DIR).as_posix()


def _normalize(el: etree._Element) -> None:
    """Make interleave-equivalent documents compare equal.

    Outside mixed content: drop ignorable whitespace, then stable-sort children
    by tag — the RNG uses interleave everywhere, so cross-type sibling order is
    not semantically significant, while relative order within one tag (a
    repeated list) is preserved by the stable sort.
    """
    if el.tag in ("text", "span"):
        return  # everything inside mixed content is significant
    if el.text is not None and not el.text.strip():
        el.text = None
    for child in el:
        if child.tail is not None and not child.tail.strip():
            child.tail = None
        if isinstance(child.tag, str):
            _normalize(child)
    el[:] = sorted(el, key=lambda c: c.tag if isinstance(c.tag, str) else "")


def _semantic_bytes(data: bytes) -> bytes:
    root = etree.fromstring(data)
    _normalize(root)
    return etree.tostring(root, method="c14n", with_comments=False)


def _comments(data: bytes) -> list[str]:
    root = etree.fromstring(data)
    return sorted(c.text or "" for c in root.iter() if isinstance(c, etree._Comment))


def _residue_items(extra: sil_lift.Extras) -> list[str]:
    """What residue a node carries, sorted: to_string's order is not a contract."""
    return sorted(extra.to_string().splitlines())


@pytest.mark.parametrize("path", LOADABLE, ids=corpus_id)
def test_unchanged_save_is_byte_identical(path: Path, tmp_path: Path) -> None:
    lexicon = sil_lift.load(path)
    out = tmp_path / "out.lift"
    lexicon.save(out)
    assert out.read_bytes() == path.read_bytes()


@pytest.mark.parametrize("path", LOADABLE, ids=corpus_id)
def test_semantic_roundtrip(path: Path, tmp_path: Path) -> None:
    """Full canonical re-serialization (passthrough disabled) is semantically equal."""
    from sil_lift._writer import canonical_document

    lexicon = sil_lift.load(path)
    canonical = canonical_document(lexicon)
    assert _semantic_bytes(canonical) == _semantic_bytes(path.read_bytes())
    # Comments survive re-serialization (order-insensitively; anchors are clamped).
    assert _comments(canonical) == _comments(path.read_bytes())


def test_touching_one_entry_leaves_other_entry_bytes_verbatim(tmp_path: Path) -> None:
    source = CORPUS_DIR / "flex" / "AllFLExFields" / "AllFLExFields.lift"
    lexicon = sil_lift.load(source)
    second = lexicon.entries[1]
    second.senses[0].glosses[0].text = sil_lift.Text(["B Word (edited)"])
    out = tmp_path / "out.lift"
    lexicon.save(out)
    result = out.read_bytes()
    original = source.read_bytes()

    # Locate the first entry's original bytes; they must appear verbatim.
    from sil_lift._scan import scan

    spans = scan(original)
    assert spans is not None
    entry_spans = [s for s in spans.children if s.tag == "entry"]
    first_bytes = original[entry_spans[0].start : entry_spans[0].end]
    second_bytes = original[entry_spans[1].start : entry_spans[1].end]
    assert first_bytes in result
    assert second_bytes not in result  # the touched entry was re-serialized
    assert b"B Word (edited)" in result

    # Everything before the second entry is untouched.
    assert result[: entry_spans[1].start] == original[: entry_spans[1].start]

    reloaded = sil_lift.load(out)
    assert str(reloaded.entries[1].senses[0].glosses[0].text) == "B Word (edited)"


def test_touched_save_then_unchanged_save_is_stable(tmp_path: Path) -> None:
    source = CORPUS_DIR / "spec-examples" / "0.13" / "full-entry.lift"
    lexicon = sil_lift.load(source)
    lexicon.entries[0].senses[0].definition["en"] = "a grove of trees"
    first_out = tmp_path / "a.lift"
    lexicon.save(first_out)
    reloaded = sil_lift.load(first_out)
    second_out = tmp_path / "b.lift"
    reloaded.save(second_out)
    assert second_out.read_bytes() == first_out.read_bytes()


def test_added_and_removed_entries(tmp_path: Path) -> None:
    source = CORPUS_DIR / "spec-examples" / "0.13" / "subsenses.lift"
    lexicon = sil_lift.load(source)
    new_entry = sil_lift.Entry(id="new_entry")
    new_entry.lexical_unit["en"] = "brand-new"
    lexicon.entries.append(new_entry)
    out = tmp_path / "out.lift"
    lexicon.save(out)
    reloaded = sil_lift.load(out)
    assert [e.id for e in reloaded.entries] == ["opon", "new_entry"]
    assert str(reloaded.entries[1].lexical_unit["en"]) == "brand-new"

    del reloaded.entries[0]
    reloaded.save()
    again = sil_lift.load(out)
    assert [e.id for e in again.entries] == ["new_entry"]


def test_from_scratch_document(tmp_path: Path) -> None:
    lexicon = sil_lift.Lexicon(producer="sil-lift tests")
    entry = sil_lift.Entry(id="hello", guid="00000000-0000-4444-8888-000000000000")
    entry.lexical_unit["en"] = "hello"
    sense = sil_lift.Sense()
    sense.glosses.append(sil_lift.Form("fr", sil_lift.Text(["bonjour"])))
    entry.senses.append(sense)
    lexicon.entries.append(entry)
    out = tmp_path / "new.lift"
    lexicon.save(out)

    reloaded = sil_lift.load(out)
    assert reloaded.producer == "sil-lift tests"
    assert str(reloaded.entries[0].lexical_unit["en"]) == "hello"
    assert reloaded.entries[0].senses[0].glosses[0].lang == "fr"

    # From-scratch output is RNG-valid.
    schema = etree.RelaxNG(
        etree.parse(Path(sil_lift.__file__).parent / "schemas" / "lift-0.13.rng")
    )
    assert schema.validate(etree.parse(out))


def test_save_without_path_raises() -> None:
    with pytest.raises(ValueError, match="path"):
        sil_lift.Lexicon().save()


INJECTED = b"""<?xml version="1.0" encoding="UTF-8"?>
<lift version="0.13" producer="test" x-custom="root-extra">
<!-- leading comment -->
<entry id="one" x-flavor="strawberry">
<lexical-unit><form lang="en"><text>one</text></form></lexical-unit>
<x-unknown a="1"><nested>payload</nested></x-unknown>
<sense id="s1">
<!-- inner comment -->
<gloss lang="en"><text>ONE</text></gloss>
</sense>
</entry>
<entry id="two">
<lexical-unit><form lang="en"><text>two</text></form></lexical-unit>
</entry>
</lift>
"""


def test_out_of_schema_content_survives_touched_reserialization(tmp_path: Path) -> None:
    source = tmp_path / "injected.lift"
    source.write_bytes(INJECTED)
    lexicon = sil_lift.load(source)

    # Unchanged save: byte-identical, trivially lossless.
    out = tmp_path / "roundtrip.lift"
    lexicon.save(out)
    assert out.read_bytes() == INJECTED

    # Touch the entry carrying the residue: everything must survive canonically.
    entry = lexicon.find(id="one")
    assert entry is not None
    entry.senses[0].glosses[0].text = sil_lift.Text(["ONE (edited)"])
    lexicon.save(out)
    result = out.read_bytes()
    assert b'x-flavor="strawberry"' in result
    assert b"<nested>payload</nested>" in result
    assert b"inner comment" in result
    assert b'x-custom="root-extra"' in result
    assert b"leading comment" in result

    reloaded = sil_lift.load(out)
    reloaded_entry = reloaded.find(id="one")
    assert reloaded_entry is not None
    assert reloaded_entry.extra  # unknown attr + element still carried
    assert _semantic_bytes(result) != b""  # well-formed enough to canonicalize


# Residue that is neither an element nor an attribute: a processing instruction,
# stray character data in element-only contexts (both as an element's leading text
# and as a later child's tail), a comment and a PI inside <text>'s mixed content,
# and a second <text> in one <form>.
TEXTUAL_RESIDUE = b"""<?xml version="1.0" encoding="UTF-8"?>
<lift version="0.13">
<entry id="one">stray text<?sil-lift keep me?>
<lexical-unit><form lang="en"><text>on<?inline pi?>e<!-- in mixed --></text>
<text>second</text></form></lexical-unit>
<sense id="s1">
<gloss lang="en"><text>ONE</text></gloss><gloss lang="fr"><text>UN</text></gloss>trailing
</sense>
</entry>
</lift>
"""


def test_textual_residue_survives_touched_reserialization(tmp_path: Path) -> None:
    source = tmp_path / "textual.lift"
    source.write_bytes(TEXTUAL_RESIDUE)
    lexicon = sil_lift.load(source)
    entry = lexicon.entries[0]
    form = entry.lexical_unit.forms[0]
    sense = entry.senses[0]

    assert _residue_items(entry.extra) == ["<?sil-lift keep me?>", "stray text"]
    assert _residue_items(form.extra) == [
        "<!-- in mixed -->",
        "<?inline pi?>",
        "<text>second</text>",
    ]
    assert sense.extra.to_string() == "trailing\n"  # one item: no order to pin

    out = tmp_path / "roundtrip.lift"
    lexicon.save(out)
    assert out.read_bytes() == TEXTUAL_RESIDUE  # untouched: byte-identical

    sense.glosses[0].text = sil_lift.Text(["ONE (edited)"])
    lexicon.save(out)
    result = out.read_bytes()
    for fragment in (
        b"stray text",
        b"<?sil-lift keep me?>",
        b"<?inline pi?>",
        b"<!-- in mixed -->",
        b"<text>second</text>",
        b"trailing",
    ):
        assert fragment in result, fragment

    # Survival is the promise; the sibling it lands next to is not. A recorded
    # position maps onto whatever modelled children the writer finds, so this holds
    # only while the number of children preceding the residue does.
    assert b"</gloss>trailing" in result

    # Text and PI residue is re-read as residue, not silently promoted or lost.
    # (The form's two <text> siblings swap roles on the way back in — the model
    # takes the first, the other becomes residue.)
    reloaded_entry = sil_lift.load(out).entries[0]
    assert reloaded_entry.extra == entry.extra
    assert reloaded_entry.senses[0].extra == sense.extra
    assert _residue_items(reloaded_entry.lexical_unit.forms[0].extra) == [
        "<!-- in mixed -->",
        "<?inline pi?>",
        "<text>one</text>",
    ]


def _ids(items: Sequence[object]) -> list[int]:
    """Compare reported nodes by identity.

    ``Entry`` and ``Range`` are non-frozen dataclasses, so they have generated
    content-based ``__eq__`` — two distinct nodes with equal content compare
    equal. These tests care which object was reported, so they compare identity.
    """
    return [id(item) for item in items]


@pytest.mark.parametrize("path", LOADABLE, ids=corpus_id)
def test_changed_entries_is_empty_for_an_untouched_load(path: Path) -> None:
    assert sil_lift.load(path).changed_entries() == []


def test_changed_entries_reports_the_entry_for_an_edit_at_any_depth() -> None:
    """An entry's digest spans its subtree, so a subsense edit reports the entry."""
    source = CORPUS_DIR / "spec-examples" / "0.13" / "subsenses.lift"
    lexicon = sil_lift.load(source)
    entry = lexicon.entries[0]
    entry.senses[0].subsenses[0].glosses[0].text = sil_lift.Text(["edited"])

    assert _ids(lexicon.changed_entries()) == [id(entry)]


def test_changed_entries_ignores_an_identical_rewrite() -> None:
    """Assigning the value it already had is not a change — the digest is unmoved."""
    source = CORPUS_DIR / "spec-examples" / "0.13" / "subsenses.lift"
    lexicon = sil_lift.load(source)
    gloss = lexicon.entries[0].senses[0].subsenses[0].glosses[0]
    gloss.text = sil_lift.Text([str(gloss.text)])

    assert lexicon.changed_entries() == []


def test_changed_entries_ignores_reordering() -> None:
    """Matches the guarantee on Lexicon.sort: reordering leaves entry bytes alone."""
    lexicon = sil_lift.load(CORPUS_DIR / "misc" / "sample.0.13.lift")
    lexicon.sort()

    assert lexicon.changed_entries() == []


def test_changed_entries_reports_only_the_edited_entry() -> None:
    lexicon = sil_lift.load(CORPUS_DIR / "misc" / "sample.0.13.lift")
    assert len(lexicon.entries) > 1
    target = lexicon.entries[3]
    target.lexical_unit["en"] = "edited"

    assert _ids(lexicon.changed_entries()) == [id(target)]


def test_changed_entries_compares_against_load_not_last_save(tmp_path: Path) -> None:
    """Changed means changed since load, so saving does not clear the report."""
    source = CORPUS_DIR / "spec-examples" / "0.13" / "subsenses.lift"
    lexicon = sil_lift.load(source)
    entry = lexicon.entries[0]
    entry.senses[0].subsenses[0].glosses[0].text = sil_lift.Text(["edited"])
    lexicon.save(tmp_path / "out.lift")

    assert _ids(lexicon.changed_entries()) == [id(entry)]


def test_added_entries_owns_appended_entries_and_changed_entries_does_not() -> None:
    """Each query answers its own question: an appended entry is new, not changed."""
    lexicon = sil_lift.load(CORPUS_DIR / "spec-examples" / "0.13" / "subsenses.lift")
    added = sil_lift.Entry(id="brand-new")
    lexicon.entries.append(added)

    assert _ids(lexicon.added_entries()) == [id(added)]
    assert lexicon.changed_entries() == []
    assert lexicon.removed_entries() == []


def test_removed_entries_returns_the_removed_object_itself() -> None:
    """The parse-time records retain the entry, so a deletion is recoverable."""
    lexicon = sil_lift.load(CORPUS_DIR / "misc" / "sample.0.13.lift")
    victim = lexicon.entries[3]
    del lexicon.entries[3]

    removed = lexicon.removed_entries()
    assert _ids(removed) == [id(victim)]
    assert removed[0] is victim  # intact, not merely named
    assert lexicon.changed_entries() == []
    assert lexicon.added_entries() == []


def test_changed_entries_reports_all_when_the_source_was_not_scannable(tmp_path: Path) -> None:
    """No byte baseline means every entry is reported — and genuinely is rewritten.

    _attach_source declines a source it cannot byte-scan, so a *loaded* document
    can have no source info too, not only a from-scratch lexicon.
    """
    source = CORPUS_DIR / "spec-examples" / "0.13" / "subsenses.lift"
    text = source.read_text(encoding="utf-8").replace('encoding="UTF-8"', 'encoding="UTF-16"')
    utf16 = tmp_path / "utf16.lift"
    utf16.write_bytes(text.encode("utf-16"))

    lexicon = sil_lift.load(utf16)
    assert lexicon.entries  # it loaded fine; only the byte scan was declined
    assert lexicon._source is None
    assert _ids(lexicon.changed_entries()) == _ids(lexicon.entries)

    # Nothing is known to be new or gone, so neither is claimed; the composite
    # says why, and stays truthy because the file will be rewritten in full.
    assert lexicon.added_entries() == []
    assert lexicon.removed_entries() == []
    changes = lexicon.changes()
    assert changes.baseline is False
    assert changes

    # Not a false positive: save() cannot reproduce the source bytes here, so
    # reporting every entry matches what the writer actually does.
    out = tmp_path / "out.lift"
    lexicon.save(out)
    assert out.read_bytes() != utf16.read_bytes()


def _signals(changes: sil_lift.Changes) -> set[str]:
    """Which fields of a Changes actually report something."""
    reported = {
        "entries": bool(changes.entries),
        "added": bool(changes.added),
        "removed": bool(changes.removed),
        "reordered": changes.reordered,
        "header": changes.header,
        "root": changes.root,
        "ranges": any(changes.ranges.values()),
    }
    return {name for name, flagged in reported.items() if flagged}


@pytest.mark.parametrize("path", LOADABLE, ids=corpus_id)
def test_changes_is_falsy_only_when_the_render_reproduces_the_source(path: Path) -> None:
    """The contract that makes changes() a correct write guard.

    The dangerous direction is a falsy result beside differing output, which
    would be a silently wrong "nothing to write".
    """
    from sil_lift._writer import render_document, render_ranges_document

    lexicon = sil_lift.load(path)
    # Stated up front so a future fixture the scanner declines (a UTF-16 file,
    # say) fails saying it has no baseline rather than accusing the guard.
    assert lexicon._source is not None, f"{corpus_id(path)}: corpus fixtures are byte-scannable"
    assert not lexicon.changes()
    assert render_document(lexicon) == path.read_bytes()
    for ranges_file in lexicon.ranges_files.values():
        assert ranges_file.path is not None
        assert ranges_file._source is not None, f"{ranges_file.path.name}: no byte baseline"
        assert not ranges_file.changes()
        assert render_ranges_document(ranges_file) == ranges_file.path.read_bytes()


def _edit_entry(lexicon: sil_lift.Lexicon) -> None:
    lexicon.entries[0].lexical_unit["en"] = "edited"


def _append_entry(lexicon: sil_lift.Lexicon) -> None:
    lexicon.entries.append(sil_lift.Entry(id="appended"))


def _remove_entry(lexicon: sil_lift.Lexicon) -> None:
    del lexicon.entries[0]


def _duplicate_entry(lexicon: sil_lift.Lexicon) -> None:
    """Append an entry the document already has — the object, not a copy."""
    lexicon.entries.append(lexicon.entries[0])


def _reverse_entries(lexicon: sil_lift.Lexicon) -> None:
    lexicon.entries.reverse()


def _edit_header(lexicon: sil_lift.Lexicon) -> None:
    lexicon.header.description["en"] = "edited"


def _change_producer(lexicon: sil_lift.Lexicon) -> None:
    lexicon.producer = "a different producer"


def _add_root_residue(lexicon: sil_lift.Lexicon) -> None:
    lexicon.extra._attrs["x-marker"] = "1"


Mutation = Callable[[sil_lift.Lexicon], None]

CONDITIONS: list[tuple[Mutation, set[str]]] = [
    (_edit_entry, {"entries"}),
    (_append_entry, {"added"}),
    (_duplicate_entry, {"added"}),
    (_remove_entry, {"removed"}),
    (_reverse_entries, {"reordered"}),
    (_edit_header, {"header"}),
    (_change_producer, {"root"}),
    (_add_root_residue, {"root"}),
]

SAMPLE = CORPUS_DIR / "misc" / "sample.0.13.lift"


@pytest.mark.parametrize(
    ("mutate", "expected"),
    CONDITIONS,
    ids=lambda value: value.__name__.lstrip("_") if callable(value) else str(sorted(value)),
)
def test_changes_isolates_each_document_level_condition(
    mutate: Mutation, expected: set[str]
) -> None:
    """Each condition is detected, and reported by that field alone."""
    from sil_lift._writer import render_document

    lexicon = sil_lift.load(SAMPLE)
    mutate(lexicon)

    changes = lexicon.changes()
    assert changes
    assert _signals(changes) == expected
    assert render_document(lexicon) != SAMPLE.read_bytes()


@pytest.mark.parametrize(
    ("first", "second"),
    list(itertools.combinations([mutate for mutate, _ in CONDITIONS], 2)),
    ids=lambda mutate: mutate.__name__.lstrip("_"),
)
def test_changes_tracks_the_render_through_combined_mutations(
    first: Mutation, second: Mutation
) -> None:
    """Conditions in combination still agree with what the writer emits.

    One at a time, a hand-written guard can match the writer by coincidence.
    Pairs cover the interactions — a removal alongside a duplicate, a reorder
    on top of an addition — where a set-based comparison starts cancelling
    itself out.
    """
    from sil_lift._writer import render_document

    lexicon = sil_lift.load(SAMPLE)
    first(lexicon)
    second(lexicon)

    rewritten = render_document(lexicon) != SAMPLE.read_bytes()
    assert bool(lexicon.changes()) == rewritten
    assert rewritten  # every pair really does change the document


def test_a_duplicated_entry_is_added_and_written_twice() -> None:
    """Appending the object itself, which a set difference would swallow."""
    from sil_lift._writer import render_document

    lexicon = sil_lift.load(SAMPLE)
    original = render_document(lexicon)
    lexicon.entries.append(lexicon.entries[0])

    changes = lexicon.changes()
    assert _ids(changes.added) == [id(lexicon.entries[0])]
    assert changes.entries == []  # the content is untouched; there is just more of it
    assert render_document(lexicon).count(b"<entry ") == original.count(b"<entry ") + 1


def test_each_repeat_beyond_the_first_is_its_own_addition() -> None:
    """Occurrences are counted, not collapsed, however many there are."""
    from sil_lift._writer import render_document

    lexicon = sil_lift.load(SAMPLE)
    entry = lexicon.entries[0]
    original = render_document(lexicon)
    lexicon.entries.extend([entry, entry])

    assert _ids(lexicon.changes().added) == [id(entry), id(entry)]
    assert render_document(lexicon).count(b"<entry ") == original.count(b"<entry ") + 2


def test_an_edited_entry_is_reported_once_however_often_it_is_repeated() -> None:
    """changed_entries() answers per entry; the repeat is the addition's business."""
    lexicon = sil_lift.load(SAMPLE)
    entry = lexicon.entries[0]
    lexicon.entries.append(entry)
    entry.lexical_unit["en"] = "edited"

    changes = lexicon.changes()
    assert _ids(changes.entries) == [id(entry)]
    assert _ids(changes.added) == [id(entry)]


def test_dropping_a_repeat_restores_the_source() -> None:
    """The mirror of the addition rule: a repeat removed is a repeat un-added."""
    from sil_lift._writer import render_document

    lexicon = sil_lift.load(SAMPLE)
    lexicon.entries.append(lexicon.entries[0])
    lexicon.entries.pop()

    assert not lexicon.changes()
    assert render_document(lexicon) == SAMPLE.read_bytes()


def test_a_node_is_removed_only_once_no_occurrence_is_left() -> None:
    """Dropping one of two aliased occurrences is a move, not a deletion."""
    lexicon = sil_lift.load(SAMPLE)
    entry = lexicon.entries[0]
    lexicon.entries.append(entry)
    del lexicon.entries[0]  # the original position; the repeat at the end survives

    changes = lexicon.changes()
    assert _signals(changes) == {"reordered"}
    assert changes.removed == []

    del lexicon.entries[-1]  # now nothing of it is left
    assert _ids(lexicon.changes().removed) == [id(entry)]


def test_changes_can_be_truthy_where_the_render_still_reproduces_the_source() -> None:
    """The guarantee is one-way, and this is the harmless direction.

    Root-level residue sends the writer down the canonical path, and for a
    document already in canonical form that path lands back on the source
    bytes. The cost is a redundant write, never a skipped one.
    """
    from sil_lift._extras import _ExtraNode
    from sil_lift._writer import render_document

    path = CORPUS_DIR / "spec-examples" / "0.13" / "minimal.lift"
    lexicon = sil_lift.load(path)
    lexicon.extra._nodes.append(_ExtraNode(kind="text", xml="\n", index=0))

    assert lexicon.changes()
    assert render_document(lexicon) == path.read_bytes()


def test_a_duplicated_range_is_added_and_written_twice() -> None:
    """The same hole on the companion side of the guard."""
    from sil_lift._writer import render_ranges_document

    lexicon = sil_lift.load(CORPUS_DIR / "flex" / "AllFLExFields" / "AllFLExFields.lift")
    ranges_file = next(iter(lexicon.ranges_files.values()))
    original = render_ranges_document(ranges_file)
    ranges_file.ranges.append(ranges_file.ranges[0])

    changes = ranges_file.changes()
    assert changes
    assert _ids(changes.added) == [id(ranges_file.ranges[0])]
    assert _signals(lexicon.changes()) == {"ranges"}
    assert render_ranges_document(ranges_file).count(b"<range ") == original.count(b"<range ") + 1


def test_changes_reports_a_companion_edit_the_lift_itself_does_not_show() -> None:
    """The case an entry-scoped query cannot see: only the companion changed."""
    from sil_lift._writer import render_document

    path = CORPUS_DIR / "flex" / "AllFLExFields" / "AllFLExFields.lift"
    lexicon = sil_lift.load(path)
    assert lexicon.ranges_files
    ranges_file = next(iter(lexicon.ranges_files.values()))
    ranges_file.ranges[0].description["en"] = "edited"

    changes = lexicon.changes()
    assert changes
    assert _signals(changes) == {"ranges"}
    assert lexicon.changed_entries() == []  # the .lift is untouched
    assert render_document(lexicon) == path.read_bytes()
    assert [len(c.ranges) for c in changes.ranges.values()] == [1]


def test_ranges_file_changes_has_no_baseline_when_built_from_scratch() -> None:
    ranges_file = sil_lift.RangesFile()
    ranges_file.add_range("etymology")

    changes = ranges_file.changes()
    assert changes.baseline is False
    assert changes
    assert _ids(changes.ranges) == _ids(ranges_file.ranges)
    assert changes.added == []
    assert changes.removed == []
