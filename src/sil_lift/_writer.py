"""Canonical serializer + byte reuse.

Two paths out of a :class:`~sil_lift._model.Lexicon`:

- **Canonical serialization** (``canonical_document``): deterministic,
  documented shape — UTF-8, LF, 2-space indent, fixed child grouping and
  attribute order per element, LIFT residue from ``Extras`` re-emitted at
  (clamped) original positions.

- **Byte reuse** (``render_document`` when the lexicon came from a file): the
  bytes between and around the top-level child regions are copied verbatim
  from the source; an entry/header whose model still serializes to its
  parse-time snapshot is emitted from its original bytes; only touched nodes
  are re-serialized canonically. A fully-unchanged document therefore
  reassembles byte-identically.

Snapshots are sha256 digests of canonical bytes, taken at parse time.

Both paths refuse content XML cannot represent: see :func:`_guarded`.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from lxml import etree

from ._errors import LiftWriteError
from ._extras import Extras
from ._header import FieldDefinition, Header, Range, RangeElement
from ._model import (
    Entry,
    Etymology,
    Example,
    Field,
    GrammaticalInfo,
    Lexicon,
    Note,
    Pronunciation,
    RangesFile,
    Relation,
    Reversal,
    ReversalMain,
    Sense,
    Translation,
    URLRef,
    Variant,
)
from ._text import Annotation, Form, Multitext, Span, Text, Trait

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from datetime import date, datetime

    from ._extras import _ExtraNode
    from ._scan import ChildRegion

__all__ = [
    "canonical_document",
    "canonical_ranges_document",
    "entry_digest",
    "header_digest",
    "node_diff",
    "range_digest",
    "render_document",
    "render_ranges_document",
]

_FRAGMENT_PARSER = etree.XMLParser(resolve_entities=False, no_network=True)


def _guarded(what: str, build: Callable[[], bytes]) -> bytes:
    """Serialize one node, turning unrepresentable content into a LIFT error.

    A Python string may hold a lone surrogate; XML may not, in any encoding.
    lxml reports it as a bare ``UnicodeEncodeError`` from wherever the text or
    attribute was set — deep inside the builders below, naming no node. Every
    entry point that builds and serializes a node passes through here so the
    failure arrives as a :class:`~sil_lift.LiftWriteError` that says which node
    and which codepoint. Nothing else in a ``str`` is unencodable as UTF-8, so
    anything else is re-raised untouched rather than mislabelled.
    """
    try:
        return build()
    except UnicodeEncodeError as exc:
        char = exc.object[exc.start]
        if not 0xD800 <= ord(char) <= 0xDFFF:
            raise
        raise LiftWriteError(
            f"{what}: U+{ord(char):04X} is a lone surrogate, which XML cannot "
            f"represent in any encoding (in {exc.object!r})"
        ) from exc


def _entry_label(entry: Entry) -> str:
    name = entry.id or entry.guid
    return f"entry {name!r}" if name else "entry (no id or guid)"


# --- byte-reuse state (created by the reader, consumed here) ---------------------


@dataclass(slots=True)
class _EntryRecord:
    entry: Entry  # strong ref: keeps id() stable for the identity check
    digest: bytes


@dataclass(slots=True)
class _SourceInfo:
    data: bytes
    root_open_start: int
    root_open_end: int
    root_self_closing: bool
    children: list[ChildRegion]  # all root children, document order
    entry_records: list[_EntryRecord]  # parallel to the "entry" regions in children
    header_digest: bytes | None  # set iff a <header> element existed in the source
    producer: str | None
    root_extra_attrs: dict[str, str]
    root_extra_snapshot: Extras


@dataclass(slots=True)
class _RangeRecord:
    range: Range
    digest: bytes


@dataclass(slots=True)
class _RangesSourceInfo:
    data: bytes
    root_open_start: int
    root_open_end: int
    root_self_closing: bool
    children: list[ChildRegion]
    range_records: list[_RangeRecord]  # parallel to the "range" regions in children
    root_extra_attrs: dict[str, str]
    root_extra_snapshot: Extras


def entry_digest(entry: Entry) -> bytes:
    return hashlib.sha256(canonical_entry_bytes(entry)).digest()


def header_digest(header: Header) -> bytes:
    return hashlib.sha256(canonical_header_bytes(header)).digest()


def range_digest(range_: Range) -> bytes:
    return hashlib.sha256(canonical_range_bytes(range_)).digest()


# --- canonical building blocks ---------------------------------------------------


def _fmt_date(value: datetime | date) -> str:
    text = value.isoformat()
    return text[:-6] + "Z" if text.endswith("+00:00") else text


def _fmt_opt_date(value: datetime | date | None) -> str | None:
    return None if value is None else _fmt_date(value)


def _fmt_opt_int(value: int | None) -> str | None:
    return None if value is None else str(value)


def _element(tag: str, attrs: Iterable[tuple[str, str | None]], extra: Extras) -> etree._Element:
    el = etree.Element(tag)
    for name, value in attrs:
        if value is not None:
            el.set(name, value)
    for name, value in extra._attrs.items():
        if el.get(name) is None:  # a model field always wins over stale residue
            el.set(name, value)
    return el


def _merge_extra_attrs(el: etree._Element, extra: Extras) -> None:
    for name, value in extra._attrs.items():
        if el.get(name) is None:
            el.set(name, value)


def _fragment(node: _ExtraNode) -> etree._Element:
    if node.kind == "comment":
        return etree.Comment(node.xml[4:-3])
    if node.kind == "pi":
        inner = node.xml[2:-2]
        target, _, data = inner.partition(" ")
        return etree.ProcessingInstruction(target, data)
    return etree.fromstring(node.xml, parser=_FRAGMENT_PARSER)


def _append_text(el: etree._Element, position: int, text: str) -> None:
    if position <= 0 or len(el) == 0:
        el.text = (el.text or "") + text
    else:
        prev = el[min(position, len(el)) - 1]
        prev.tail = (prev.tail or "") + text


def _apply_extra_nodes(el: etree._Element, extra: Extras) -> None:
    """Re-insert residue nodes at their recorded positions, clamped to fit."""
    for node in sorted(extra._nodes, key=lambda n: n.index):
        if node.kind == "text":
            _append_text(el, node.index, node.xml)
        else:
            el.insert(min(node.index, len(el)), _fragment(node))


def _append_fragments(el: etree._Element, fragments: list[str | Span]) -> None:
    for fragment in fragments:
        if isinstance(fragment, str):
            if not fragment:
                continue  # "" would force <text></text> instead of <text/>
            if len(el) == 0:
                el.text = (el.text or "") + fragment
            else:
                el[-1].tail = (el[-1].tail or "") + fragment
        else:
            el.append(_span_el(fragment))


def _span_el(span: Span) -> etree._Element:
    el = _element(
        "span",
        [("lang", span.lang), ("href", span.href), ("class", span.class_)],
        span.extra,
    )
    _append_fragments(el, span.content)
    _apply_extra_nodes(el, span.extra)
    return el


def _text_el(text: Text) -> etree._Element:
    el = etree.Element("text")
    _append_fragments(el, text.fragments)
    return el


def _form_el(tag: str, form: Form) -> etree._Element:
    el = _element(tag, [("lang", form.lang)], form.extra)
    el.append(_text_el(form.text))
    for annotation in form.annotations:
        el.append(_annotation_el(annotation))
    _apply_extra_nodes(el, form.extra)
    return el


def _append_forms(el: etree._Element, multitext: Multitext) -> None:
    for form in multitext.forms:
        el.append(_form_el("form", form))


def _multitext_el(tag: str, multitext: Multitext) -> etree._Element:
    el = _element(tag, [], multitext.extra)
    _append_forms(el, multitext)
    _apply_extra_nodes(el, multitext.extra)
    return el


def _annotation_el(annotation: Annotation) -> etree._Element:
    el = _element(
        "annotation",
        [
            ("name", annotation.name),
            ("value", annotation.value),
            ("who", annotation.who),
            ("when", _fmt_opt_date(annotation.when)),
        ],
        annotation.extra,
    )
    _append_forms(el, annotation.content)
    _merge_extra_attrs(el, annotation.content.extra)
    _apply_extra_nodes(el, annotation.content.extra)
    _apply_extra_nodes(el, annotation.extra)
    return el


def _trait_el(trait: Trait) -> etree._Element:
    el = _element("trait", [("name", trait.name), ("value", trait.value)], trait.extra)
    for annotation in trait.annotations:
        el.append(_annotation_el(annotation))
    _apply_extra_nodes(el, trait.extra)
    return el


def _field_el(field: Field) -> etree._Element:
    el = _element(
        "field",
        [
            ("type", field.type),
            ("dateCreated", _fmt_opt_date(field.date_created)),
            ("dateModified", _fmt_opt_date(field.date_modified)),
        ],
        field.extra,
    )
    _append_forms(el, field.content)
    for annotation in field.annotations:
        el.append(_annotation_el(annotation))
    for trait in field.traits:
        el.append(_trait_el(trait))
    _merge_extra_attrs(el, field.content.extra)
    _apply_extra_nodes(el, field.content.extra)
    _apply_extra_nodes(el, field.extra)
    return el


def _append_extensible(
    el: etree._Element,
    annotations: list[Annotation],
    traits: list[Trait],
    fields: list[Field] | None,
) -> None:
    for annotation in annotations:
        el.append(_annotation_el(annotation))
    for trait in traits:
        el.append(_trait_el(trait))
    if fields is not None:
        for field in fields:
            el.append(_field_el(field))


def _grammatical_info_el(info: GrammaticalInfo) -> etree._Element:
    el = _element("grammatical-info", [("value", info.value)], info.extra)
    for trait in info.traits:
        el.append(_trait_el(trait))
    _apply_extra_nodes(el, info.extra)
    return el


def _url_ref_el(tag: str, ref: URLRef) -> etree._Element:
    el = _element(tag, [("href", ref.href)], ref.extra)
    if ref.label:
        el.append(_multitext_el("label", ref.label))
    _apply_extra_nodes(el, ref.extra)
    return el


def _translation_el(translation: Translation) -> etree._Element:
    el = _element("translation", [("type", translation.type)], translation.extra)
    _append_forms(el, translation.forms)
    _merge_extra_attrs(el, translation.forms.extra)
    _apply_extra_nodes(el, translation.forms.extra)
    _apply_extra_nodes(el, translation.extra)
    return el


def _note_el(note: Note) -> etree._Element:
    el = _element(
        "note",
        [
            ("type", note.type),
            ("dateCreated", _fmt_opt_date(note.date_created)),
            ("dateModified", _fmt_opt_date(note.date_modified)),
        ],
        note.extra,
    )
    _append_forms(el, note.forms)
    _append_extensible(el, note.annotations, note.traits, note.fields)
    _merge_extra_attrs(el, note.forms.extra)
    _apply_extra_nodes(el, note.forms.extra)
    _apply_extra_nodes(el, note.extra)
    return el


def _example_el(example: Example) -> etree._Element:
    el = _element(
        "example",
        [
            ("source", example.source),
            ("dateCreated", _fmt_opt_date(example.date_created)),
            ("dateModified", _fmt_opt_date(example.date_modified)),
        ],
        example.extra,
    )
    _append_forms(el, example.forms)
    for translation in example.translations:
        el.append(_translation_el(translation))
    for note in example.notes:
        el.append(_note_el(note))
    _append_extensible(el, example.annotations, example.traits, example.fields)
    _merge_extra_attrs(el, example.forms.extra)
    _apply_extra_nodes(el, example.forms.extra)
    _apply_extra_nodes(el, example.extra)
    return el


def _relation_el(relation: Relation) -> etree._Element:
    el = _element(
        "relation",
        [
            ("type", relation.type),
            ("ref", relation.ref),
            ("order", _fmt_opt_int(relation.order)),
            ("dateCreated", _fmt_opt_date(relation.date_created)),
            ("dateModified", _fmt_opt_date(relation.date_modified)),
        ],
        relation.extra,
    )
    if relation.usage:
        el.append(_multitext_el("usage", relation.usage))
    _append_extensible(el, relation.annotations, relation.traits, relation.fields)
    _apply_extra_nodes(el, relation.extra)
    return el


def _etymology_el(etymology: Etymology) -> etree._Element:
    el = _element(
        "etymology",
        [
            ("type", etymology.type),
            ("source", etymology.source),
            ("dateCreated", _fmt_opt_date(etymology.date_created)),
            ("dateModified", _fmt_opt_date(etymology.date_modified)),
        ],
        etymology.extra,
    )
    _append_forms(el, etymology.forms)
    for gloss in etymology.glosses:
        el.append(_form_el("gloss", gloss))
    _append_extensible(el, etymology.annotations, etymology.traits, etymology.fields)
    _merge_extra_attrs(el, etymology.forms.extra)
    _apply_extra_nodes(el, etymology.forms.extra)
    _apply_extra_nodes(el, etymology.extra)
    return el


def _reversal_main_el(main: ReversalMain) -> etree._Element:
    el = _element("main", [], main.extra)
    _append_forms(el, main.forms)
    if main.main is not None:
        el.append(_reversal_main_el(main.main))
    if main.grammatical_info is not None:
        el.append(_grammatical_info_el(main.grammatical_info))
    _merge_extra_attrs(el, main.forms.extra)
    _apply_extra_nodes(el, main.forms.extra)
    _apply_extra_nodes(el, main.extra)
    return el


def _reversal_el(reversal: Reversal) -> etree._Element:
    el = _element("reversal", [("type", reversal.type)], reversal.extra)
    _append_forms(el, reversal.forms)
    if reversal.main is not None:
        el.append(_reversal_main_el(reversal.main))
    if reversal.grammatical_info is not None:
        el.append(_grammatical_info_el(reversal.grammatical_info))
    _merge_extra_attrs(el, reversal.forms.extra)
    _apply_extra_nodes(el, reversal.forms.extra)
    _apply_extra_nodes(el, reversal.extra)
    return el


def _pronunciation_el(pronunciation: Pronunciation) -> etree._Element:
    el = _element(
        "pronunciation",
        [
            ("dateCreated", _fmt_opt_date(pronunciation.date_created)),
            ("dateModified", _fmt_opt_date(pronunciation.date_modified)),
        ],
        pronunciation.extra,
    )
    _append_forms(el, pronunciation.forms)
    for media in pronunciation.media:
        el.append(_url_ref_el("media", media))
    _append_extensible(el, pronunciation.annotations, pronunciation.traits, pronunciation.fields)
    _merge_extra_attrs(el, pronunciation.forms.extra)
    _apply_extra_nodes(el, pronunciation.forms.extra)
    _apply_extra_nodes(el, pronunciation.extra)
    return el


def _variant_el(variant: Variant) -> etree._Element:
    el = _element(
        "variant",
        [
            ("ref", variant.ref),
            ("dateCreated", _fmt_opt_date(variant.date_created)),
            ("dateModified", _fmt_opt_date(variant.date_modified)),
        ],
        variant.extra,
    )
    _append_forms(el, variant.forms)
    for pronunciation in variant.pronunciations:
        el.append(_pronunciation_el(pronunciation))
    for relation in variant.relations:
        el.append(_relation_el(relation))
    _append_extensible(el, variant.annotations, variant.traits, variant.fields)
    _merge_extra_attrs(el, variant.forms.extra)
    _apply_extra_nodes(el, variant.forms.extra)
    _apply_extra_nodes(el, variant.extra)
    return el


def _sense_el(sense: Sense, tag: str = "sense") -> etree._Element:
    el = _element(
        tag,
        [
            ("id", sense.id),
            ("order", _fmt_opt_int(sense.order)),
            ("dateCreated", _fmt_opt_date(sense.date_created)),
            ("dateModified", _fmt_opt_date(sense.date_modified)),
        ],
        sense.extra,
    )
    if sense.grammatical_info is not None:
        el.append(_grammatical_info_el(sense.grammatical_info))
    for gloss in sense.glosses:
        el.append(_form_el("gloss", gloss))
    if sense.definition:
        el.append(_multitext_el("definition", sense.definition))
    for relation in sense.relations:
        el.append(_relation_el(relation))
    for note in sense.notes:
        el.append(_note_el(note))
    for example in sense.examples:
        el.append(_example_el(example))
    for reversal in sense.reversals:
        el.append(_reversal_el(reversal))
    for illustration in sense.illustrations:
        el.append(_url_ref_el("illustration", illustration))
    for subsense in sense.subsenses:
        el.append(_sense_el(subsense, "subsense"))
    _append_extensible(el, sense.annotations, sense.traits, sense.fields)
    _apply_extra_nodes(el, sense.extra)
    return el


def _entry_el(entry: Entry) -> etree._Element:
    el = _element(
        "entry",
        [
            ("id", entry.id),
            ("guid", entry.guid),
            ("order", _fmt_opt_int(entry.order)),
            ("dateCreated", _fmt_opt_date(entry.date_created)),
            ("dateModified", _fmt_opt_date(entry.date_modified)),
            ("dateDeleted", _fmt_opt_date(entry.date_deleted)),
        ],
        entry.extra,
    )
    if entry.lexical_unit:
        el.append(_multitext_el("lexical-unit", entry.lexical_unit))
    if entry.citation:
        el.append(_multitext_el("citation", entry.citation))
    for pronunciation in entry.pronunciations:
        el.append(_pronunciation_el(pronunciation))
    for variant in entry.variants:
        el.append(_variant_el(variant))
    for sense in entry.senses:
        el.append(_sense_el(sense))
    for note in entry.notes:
        el.append(_note_el(note))
    for relation in entry.relations:
        el.append(_relation_el(relation))
    for etymology in entry.etymologies:
        el.append(_etymology_el(etymology))
    _append_extensible(el, entry.annotations, entry.traits, entry.fields)
    _apply_extra_nodes(el, entry.extra)
    return el


def _field_definition_el(definition: FieldDefinition) -> etree._Element:
    el = _element("field", [("tag", definition.tag)], definition.extra)
    _append_forms(el, definition.content)
    _merge_extra_attrs(el, definition.content.extra)
    _apply_extra_nodes(el, definition.content.extra)
    _apply_extra_nodes(el, definition.extra)
    return el


def _range_element_el(element: RangeElement) -> etree._Element:
    el = _element(
        "range-element",
        [("id", element.id), ("parent", element.parent), ("guid", element.guid)],
        element.extra,
    )
    if element.description:
        el.append(_multitext_el("description", element.description))
    if element.label:
        el.append(_multitext_el("label", element.label))
    if element.abbrev:
        el.append(_multitext_el("abbrev", element.abbrev))
    _apply_extra_nodes(el, element.extra)
    return el


def _range_el(range_: Range) -> etree._Element:
    el = _element(
        "range",
        [("id", range_.id), ("href", range_.href), ("guid", range_.guid)],
        range_.extra,
    )
    if range_.description:
        el.append(_multitext_el("description", range_.description))
    if range_.label:
        el.append(_multitext_el("label", range_.label))
    if range_.abbrev:
        el.append(_multitext_el("abbrev", range_.abbrev))
    for element in range_.elements:
        el.append(_range_element_el(element))
    _apply_extra_nodes(el, range_.extra)
    return el


def _header_el(header: Header) -> etree._Element:
    el = _element("header", [], header.extra)
    if header.description:
        el.append(_multitext_el("description", header.description))
    if header.ranges or header.ranges_extra:
        ranges_el = _element("ranges", [], header.ranges_extra)
        el.append(ranges_el)
        for range_ in header.ranges:
            ranges_el.append(_range_el(range_))
        _apply_extra_nodes(ranges_el, header.ranges_extra)
    if header.fields or header.fields_extra:
        fields_el = _element("fields", [], header.fields_extra)
        el.append(fields_el)
        for definition in header.fields:
            fields_el.append(_field_definition_el(definition))
        _apply_extra_nodes(fields_el, header.fields_extra)
    _apply_extra_nodes(el, header.extra)
    return el


def _indent(el: etree._Element, level: int = 0) -> None:
    """2-space indentation that never touches mixed content.

    lxml's pretty_print injects whitespace inside a ``<text>`` whose content
    starts with a span — corrupting lexical data. This indenter stops at
    ``<text>``/``<span>`` and at any element that already has non-whitespace
    text of its own (e.g. residue fragments).
    """
    if not isinstance(el.tag, str) or el.tag in ("text", "span") or len(el) == 0:
        return
    if el.text is not None and el.text.strip():
        return
    child_indent = "\n" + "  " * (level + 1)
    el.text = child_indent
    for position, child in enumerate(el):
        if child.tail is None or not child.tail.strip():
            child.tail = child_indent if position < len(el) - 1 else "\n" + "  " * level
        _indent(child, level + 1)


def _node_bytes(el: etree._Element) -> bytes:
    _indent(el)
    return etree.tostring(el, encoding="unicode").encode("utf-8") + b"\n"


def canonical_entry_bytes(entry: Entry) -> bytes:
    return _guarded(_entry_label(entry), lambda: _node_bytes(_entry_el(entry)))


def canonical_header_bytes(header: Header) -> bytes:
    return _guarded("header", lambda: _node_bytes(_header_el(header)))


def canonical_range_bytes(range_: Range) -> bytes:
    return _guarded(f"range {range_.id!r}", lambda: _node_bytes(_range_el(range_)))


# --- document rendering ------------------------------------------------------------


def _root_open_bytes(lexicon: Lexicon) -> bytes:
    def build() -> bytes:
        el = _element(
            "lift",
            [("version", "0.13"), ("producer", lexicon.producer)],
            lexicon.extra,
        )
        serialized = etree.tostring(el, encoding="unicode").encode("utf-8")
        return serialized[:-2] + b">"  # "<lift .../>" -> "<lift ...>"

    return _guarded("<lift> root", build)


def canonical_document(
    lexicon: Lexicon,
    entry_bytes: Callable[[Entry], bytes] = canonical_entry_bytes,
    header_bytes: Callable[[Header], bytes] = canonical_header_bytes,
) -> bytes:
    """Serialize the whole document canonically (residue re-emitted from Extras)."""
    chunks: list[bytes] = []
    if lexicon.header:
        chunks.append(header_bytes(lexicon.header))
    for entry in lexicon.entries:
        chunks.append(entry_bytes(entry))
    for node in sorted(lexicon.extra._nodes, key=lambda n: n.index):
        if node.kind == "text":
            continue  # character data at root level is not representable
        position = min(node.index, len(chunks))
        chunks.insert(position, _guarded("root-level residue", node.xml.encode) + b"\n")
    parts = [b'<?xml version="1.0" encoding="UTF-8"?>\n', _root_open_bytes(lexicon), b"\n"]
    # Each chunk's trailing newline is the inter-chunk separator. Byte-reused
    # (untouched) regions end at ">", so append the newline they lack — without
    # it the chunk would run straight into its neighbor.
    parts.extend(chunk if chunk.endswith(b"\n") else chunk + b"\n" for chunk in chunks)
    parts.append(b"</lift>\n")
    return b"".join(parts)


def _fit_between_regions(chunk: bytes) -> bytes:
    """Trim a re-serialized node so it fits between the reused source bytes.

    In :func:`canonical_document` a node's chunk ends with a newline that *is*
    the separator between chunks. On the byte-reuse path the surrounding source
    bytes already supply those separators, so a re-serialized (touched) node's
    trailing newline would double up into a blank line. Regions reused verbatim
    end at ``>`` and are unaffected.
    """
    return chunk[:-1] if chunk.endswith(b"\n") else chunk


def node_diff(current: list[int], original: list[int]) -> tuple[list[int], list[int], bool]:
    """Positions added, positions removed, and whether the survivors moved.

    Node identities, in document order. ``original`` holds one identity per
    parsed node, all distinct; ``current`` may repeat one, since appending a
    node the document already has aliases the object rather than copying it.
    An occurrence beyond the recorded one is therefore an addition — comparing
    the two lists as sets would miss it, and the document would still be
    written with the node twice. The mirror holds on the other side: a recorded
    node counts as removed only once no occurrence of it is left, so dropping
    one of two aliased occurrences leaves the list reordered, or unchanged if
    the occurrence dropped was the repeat.

    This is what ``Lexicon.changes`` and ``RangesFile.changes`` report as
    ``added`` / ``removed`` / ``reordered``, and what :func:`_nodes_aligned`
    reduces to a yes/no, so the guard cannot fall out of step with the writer.
    """
    known = Counter(original)
    seen: Counter[int] = Counter()
    added: list[int] = []
    for index, identity in enumerate(current):
        seen[identity] += 1
        if seen[identity] > known[identity]:
            added.append(index)
    removed = [index for index, identity in enumerate(original) if not seen[identity]]
    return added, removed, not added and not removed and current != original


def _nodes_aligned(current: list[int], original: list[int]) -> bool:
    """Whether the nodes still match the source's regions one-for-one, in order.

    Byte reuse pairs the *i*th source region with the *i*th node, so an
    addition, a removal, a reordering, or the same object repeated all send the
    document down the canonical path instead — exactly the cases
    :func:`node_diff` enumerates, which is how the change guard stays in step
    with the writer.
    """
    return not any(node_diff(current, original))


def _root_unchanged(lexicon: Lexicon, source: _SourceInfo) -> bool:
    return (
        lexicon.producer == source.producer
        and dict(lexicon.extra._attrs) == source.root_extra_attrs
    )


def _header_bytes_fn(source: _SourceInfo) -> Callable[[Header], bytes]:
    def fn(header: Header) -> bytes:
        current = _node_bytes(_header_el(header))
        if (
            source.header_digest is not None
            and hashlib.sha256(current).digest() == source.header_digest
        ):
            for region in source.children:
                if region.tag == "header":
                    return source.data[region.start : region.end]
        return current

    return fn


def _entry_bytes_fn(source: _SourceInfo) -> Callable[[Entry], bytes]:
    regions = [region for region in source.children if region.tag == "entry"]
    by_identity = {
        id(record.entry): (record, region)
        for record, region in zip(source.entry_records, regions, strict=True)
    }

    def fn(entry: Entry) -> bytes:
        found = by_identity.get(id(entry))
        if found is not None:
            record, region = found
            if entry_digest(entry) == record.digest:
                return source.data[region.start : region.end]
        return canonical_entry_bytes(entry)

    return fn


def render_document(lexicon: Lexicon) -> bytes:
    """Render with the strongest fidelity available (see module docstring)."""
    source = lexicon._source
    if source is None:
        return canonical_document(lexicon)

    entry_fn = _entry_bytes_fn(source)
    header_fn = _header_bytes_fn(source)

    # Root-level residue edits invalidate the bytes between regions (comments
    # etc. live in both places); fall back to canonical with per-node byte reuse.
    if lexicon.extra._nodes != source.root_extra_snapshot._nodes:
        return canonical_document(lexicon, entry_fn, header_fn)

    if source.root_self_closing:
        if not lexicon.entries and not lexicon.header and _root_unchanged(lexicon, source):
            return source.data
        return canonical_document(lexicon, entry_fn, header_fn)

    if not _nodes_aligned(
        [id(entry) for entry in lexicon.entries],
        [id(record.entry) for record in source.entry_records],
    ):
        return canonical_document(lexicon, entry_fn, header_fn)

    data = source.data
    parts = [data[: source.root_open_start]]
    if _root_unchanged(lexicon, source):
        parts.append(data[source.root_open_start : source.root_open_end])
    else:
        parts.append(_root_open_bytes(lexicon))
    position = source.root_open_end

    had_header = any(region.tag == "header" for region in source.children)
    if not had_header and lexicon.header:
        parts.append(b"\n" + _fit_between_regions(header_fn(lexicon.header)))

    entry_index = 0
    for region in source.children:
        parts.append(data[position : region.start])
        if region.tag == "header":
            # Unconditional (even for a now-empty Header): the digest check
            # inside header_fn restores the original bytes when unchanged.
            parts.append(_fit_between_regions(header_fn(lexicon.header)))
        elif region.tag == "entry":
            parts.append(_fit_between_regions(entry_fn(lexicon.entries[entry_index])))
            entry_index += 1
        else:
            parts.append(data[region.start : region.end])
        position = region.end
    parts.append(data[position:])
    return b"".join(parts)


# --- .lift-ranges documents ----------------------------------------------------------


def _ranges_root_open_bytes(ranges_file: RangesFile) -> bytes:
    def build() -> bytes:
        root = _element("lift-ranges", [], ranges_file.extra)
        serialized = etree.tostring(root, encoding="unicode").encode("utf-8")
        return serialized[:-2] + b">"  # "<lift-ranges .../>" -> "<lift-ranges ...>"

    return _guarded("<lift-ranges> root", build)


def canonical_ranges_document(
    ranges_file: RangesFile,
    range_bytes: Callable[[Range], bytes] | None = None,
) -> bytes:
    if range_bytes is None:
        range_bytes = canonical_range_bytes
    chunks = [range_bytes(range_) for range_ in ranges_file.ranges]
    for node in sorted(ranges_file.extra._nodes, key=lambda n: n.index):
        if node.kind == "text":
            continue
        fragment = _guarded("root-level residue", node.xml.encode)
        chunks.insert(min(node.index, len(chunks)), fragment + b"\n")
    parts = [
        b'<?xml version="1.0" encoding="UTF-8"?>\n',
        _ranges_root_open_bytes(ranges_file),
        b"\n",
    ]
    # See canonical_document: reused regions need the newline they lack, or the
    # chunk runs into its neighbor.
    parts.extend(chunk if chunk.endswith(b"\n") else chunk + b"\n" for chunk in chunks)
    parts.append(b"</lift-ranges>\n")
    return b"".join(parts)


def _range_bytes_fn(source: _RangesSourceInfo) -> Callable[[Range], bytes]:
    regions = [region for region in source.children if region.tag == "range"]
    by_identity = {
        id(record.range): (record, region)
        for record, region in zip(source.range_records, regions, strict=True)
    }

    def fn(range_: Range) -> bytes:
        found = by_identity.get(id(range_))
        if found is not None:
            record, region = found
            if range_digest(range_) == record.digest:
                return source.data[region.start : region.end]
        return canonical_range_bytes(range_)

    return fn


def render_ranges_document(ranges_file: RangesFile) -> bytes:
    source = ranges_file._source
    if source is None:
        return canonical_ranges_document(ranges_file)

    range_fn = _range_bytes_fn(source)
    root_unchanged = dict(ranges_file.extra._attrs) == source.root_extra_attrs

    if ranges_file.extra._nodes != source.root_extra_snapshot._nodes:
        return canonical_ranges_document(ranges_file, range_fn)
    if source.root_self_closing:
        if not ranges_file.ranges and root_unchanged:
            return source.data
        return canonical_ranges_document(ranges_file, range_fn)

    if not _nodes_aligned(
        [id(range_) for range_ in ranges_file.ranges],
        [id(record.range) for record in source.range_records],
    ):
        return canonical_ranges_document(ranges_file, range_fn)

    data = source.data
    parts = [data[: source.root_open_start]]
    if root_unchanged:
        parts.append(data[source.root_open_start : source.root_open_end])
    else:
        parts.append(_ranges_root_open_bytes(ranges_file))
    position = source.root_open_end
    range_index = 0
    for region in source.children:
        parts.append(data[position : region.start])
        if region.tag == "range":
            parts.append(_fit_between_regions(range_fn(ranges_file.ranges[range_index])))
            range_index += 1
        else:
            parts.append(data[region.start : region.end])
        position = region.end
    parts.append(data[position:])
    return b"".join(parts)
