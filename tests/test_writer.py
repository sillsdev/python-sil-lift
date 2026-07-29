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


def _ids(entries: list[sil_lift.Entry]) -> list[int]:
    """Compare reported entries by identity.

    ``Entry`` is a non-frozen dataclass, so it has a generated content-based
    ``__eq__`` — two distinct entries with equal content compare equal. These
    tests care which object was reported, so they compare identity.
    """
    return [id(entry) for entry in entries]


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


def test_changed_entries_reports_entries_with_no_parse_time_record() -> None:
    """Appended entries, and every entry of a lexicon that was never loaded."""
    lexicon = sil_lift.load(CORPUS_DIR / "spec-examples" / "0.13" / "subsenses.lift")
    added = sil_lift.Entry(id="brand-new")
    lexicon.entries.append(added)
    assert _ids(lexicon.changed_entries()) == [id(added)]

    scratch = sil_lift.Lexicon(entries=[sil_lift.Entry(id="a"), sil_lift.Entry(id="b")])
    assert _ids(scratch.changed_entries()) == _ids(scratch.entries)


def test_changed_entries_compares_against_load_not_last_save(tmp_path: Path) -> None:
    """Changed means changed since load, so saving does not clear the report."""
    source = CORPUS_DIR / "spec-examples" / "0.13" / "subsenses.lift"
    lexicon = sil_lift.load(source)
    entry = lexicon.entries[0]
    entry.senses[0].subsenses[0].glosses[0].text = sil_lift.Text(["edited"])
    lexicon.save(tmp_path / "out.lift")

    assert _ids(lexicon.changed_entries()) == [id(entry)]


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

    # Not a false positive: save() cannot reproduce the source bytes here, so
    # reporting every entry matches what the writer actually does.
    out = tmp_path / "out.lift"
    lexicon.save(out)
    assert out.read_bytes() != utf16.read_bytes()
