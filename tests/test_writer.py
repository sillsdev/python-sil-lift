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
    """What LIFT residue a node carries, sorted: to_string's order is not a contract."""
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

    scanned = scan(original)
    assert scanned is not None
    entry_regions = [r for r in scanned.children if r.tag == "entry"]
    first_bytes = original[entry_regions[0].start : entry_regions[0].end]
    second_bytes = original[entry_regions[1].start : entry_regions[1].end]
    assert first_bytes in result
    assert second_bytes not in result  # the touched entry was re-serialized
    assert b"B Word (edited)" in result

    # Everything before the second entry is untouched.
    assert result[: entry_regions[1].start] == original[: entry_regions[1].start]

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
