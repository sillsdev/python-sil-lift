"""Full-document parser: lxml tree -> model graph.

Parsing never rejects schema-invalid-but-well-formed LIFT 0.13: anything the
model does not define lands verbatim in the nearest node's ``Extras`` (unknown
attributes/elements, comments, PIs, stray text, malformed typed attributes).
The only refusals are non-XML input, a non-``<lift>`` root, and a version
other than 0.13.

Interleave everywhere (data-model quirk 2) means child order is never assumed:
every parser dispatches children by tag, whatever their order.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from lxml import etree

from ._errors import LiftParseError
from ._extras import Extras, _ExtraNode
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
    from collections.abc import Callable, Collection, Mapping
    from pathlib import Path

    Handler = Callable[[etree._Element], None]

SUPPORTED_VERSION = "0.13"

_PARSER = etree.XMLParser(resolve_entities=False, no_network=True)


def parse_document(path: Path) -> Lexicon:
    try:
        tree = etree.parse(path, parser=_PARSER)
    except etree.XMLSyntaxError as exc:
        raise LiftParseError(f"{path}: not well-formed XML: {exc}") from exc
    return parse_root(tree.getroot(), path=path)


def parse_root(root: etree._Element, *, path: Path | None = None) -> Lexicon:
    if root.tag != "lift":
        raise LiftParseError(f"root element is <{root.tag}>, expected <lift>")
    version = root.get("version")
    if version != SUPPORTED_VERSION:
        raise LiftParseError(
            f"unsupported LIFT version {version!r}: sil-lift reads LIFT 0.13 only "
            "(one-off migration XSLTs are available in sillsdev/lift-standard)"
        )
    lexicon = Lexicon(path=path)
    attrs = _split_attrs(root, ("version", "producer"), lexicon.extra)
    lexicon.producer = attrs.get("producer")

    def handle_header(el: etree._Element) -> None:
        if lexicon.header:
            _push_node(lexicon.extra, el)  # duplicate <header> is out-of-schema
        else:
            lexicon.header = _parse_header(el)

    _walk(
        root,
        lexicon.extra,
        {
            "header": handle_header,
            "entry": lambda el: lexicon.entries.append(_parse_entry(el)),
        },
    )
    return lexicon


# --- residue plumbing ---------------------------------------------------------


def _push_node(extra: Extras, el: etree._Element, index: int | None = None) -> None:
    if isinstance(el, etree._Comment):
        kind = "comment"
    elif isinstance(el, etree._ProcessingInstruction):
        kind = "pi"
    else:
        kind = "element"
    parent = el.getparent()
    if index is None:
        index = parent.index(el) if parent is not None else 0
    xml = etree.tostring(el, encoding="unicode", with_tail=False)
    extra._nodes.append(_ExtraNode(kind=kind, xml=xml, index=index))


def _split_attrs(el: etree._Element, known: Collection[str], extra: Extras) -> dict[str, str]:
    found: dict[str, str] = {}
    for raw_name, raw_value in el.attrib.items():
        name = raw_name if isinstance(raw_name, str) else raw_name.decode()
        value = raw_value if isinstance(raw_value, str) else raw_value.decode()
        if name in known:
            found[name] = value
        else:
            extra._attrs[name] = value
    return found


def _walk(el: etree._Element, extra: Extras, handlers: Mapping[str, Handler]) -> None:
    """Dispatch children by tag; everything unhandled becomes residue."""
    if el.text and el.text.strip():
        extra._nodes.append(_ExtraNode(kind="text", xml=el.text, index=0))
    for index, child in enumerate(el):
        tag = child.tag
        if isinstance(tag, str) and tag in handlers:
            handlers[tag](child)
        else:
            _push_node(extra, child, index)
        if child.tail and child.tail.strip():
            extra._nodes.append(_ExtraNode(kind="text", xml=child.tail, index=index))


# --- typed attributes (malformed values become residue, field stays None) ------


def _take_date(attrs: dict[str, str], key: str, extra: Extras) -> datetime | date | None:
    raw = attrs.get(key)
    if raw is None:
        return None
    value = raw.strip()
    try:
        if "T" in value:
            return datetime.fromisoformat(value)
        return date.fromisoformat(value)
    except ValueError:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            extra._attrs[key] = raw
            return None


def _take_int(attrs: dict[str, str], key: str, extra: Extras) -> int | None:
    raw = attrs.get(key)
    if raw is None:
        return None
    try:
        return int(raw.strip())
    except ValueError:
        extra._attrs[key] = raw
        return None


# --- text model -----------------------------------------------------------------


def _parse_mixed(el: etree._Element, host_extra: Extras) -> list[str | Span]:
    """Mixed content of <text>/<span>: text and nested spans, in order.

    Comments/PIs/unknown elements inside mixed content are hoisted to the
    nearest host node's residue (position within the run is not preserved —
    untouched-entry passthrough covers exact bytes).
    """
    fragments: list[str | Span] = []
    if el.text:
        fragments.append(el.text)
    for index, child in enumerate(el):
        if child.tag == "span":
            fragments.append(_parse_span(child))
        else:
            _push_node(host_extra, child, index)
        if child.tail:
            fragments.append(child.tail)
    return fragments


def _parse_span(el: etree._Element) -> Span:
    span = Span()
    attrs = _split_attrs(el, ("lang", "href", "class"), span.extra)
    span.lang = attrs.get("lang")
    span.href = attrs.get("href")
    span.class_ = attrs.get("class")
    span.content = _parse_mixed(el, span.extra)
    return span


def _parse_form(el: etree._Element) -> Form:
    """A <form> or (form-shaped, quirk 3) <gloss>."""
    form = Form(None)
    attrs = _split_attrs(el, ("lang",), form.extra)
    form.lang = attrs.get("lang")
    texts: list[Text] = []

    def handle_text(child: etree._Element) -> None:
        if texts:  # more than one <text> is out-of-schema
            _push_node(form.extra, child)
        else:
            texts.append(Text(_parse_mixed(child, form.extra)))

    _walk(
        el,
        form.extra,
        {
            "text": handle_text,
            "annotation": lambda c: form.annotations.append(_parse_annotation(c)),
        },
    )
    if texts:
        form.text = texts[0]
    return form


def _parse_multitext(el: etree._Element) -> Multitext:
    """An element whose entire content model is multitext (definition, label, ...)."""
    multitext = Multitext()
    _split_attrs(el, (), multitext.extra)
    _walk(el, multitext.extra, {"form": lambda c: multitext.forms.append(_parse_form(c))})
    return multitext


def _parse_annotation(el: etree._Element) -> Annotation:
    annotation = Annotation("")
    attrs = _split_attrs(el, ("name", "value", "who", "when"), annotation.extra)
    annotation.name = attrs.get("name", "")
    annotation.value = attrs.get("value")
    annotation.who = attrs.get("who")
    annotation.when = _take_date(attrs, "when", annotation.extra)
    _walk(
        el,
        annotation.extra,
        {"form": lambda c: annotation.content.forms.append(_parse_form(c))},
    )
    return annotation


def _parse_trait(el: etree._Element) -> Trait:
    trait = Trait("", "")
    attrs = _split_attrs(el, ("name", "value"), trait.extra)
    trait.name = attrs.get("name", "")
    trait.value = attrs.get("value", "")
    _walk(
        el,
        trait.extra,
        {"annotation": lambda c: trait.annotations.append(_parse_annotation(c))},
    )
    return trait


# --- extensible plumbing ----------------------------------------------------------


def _extensible_handlers(
    annotations: list[Annotation],
    traits: list[Trait],
    fields: list[Field] | None,
) -> dict[str, Handler]:
    handlers: dict[str, Handler] = {
        "annotation": lambda c: annotations.append(_parse_annotation(c)),
        "trait": lambda c: traits.append(_parse_trait(c)),
    }
    if fields is not None:
        handlers["field"] = lambda c: fields.append(_parse_field(c))
    return handlers


def _parse_field(el: etree._Element) -> Field:
    field = Field(type="")
    attrs = _split_attrs(el, ("type", "dateCreated", "dateModified"), field.extra)
    field.type = attrs.get("type", "")
    field.date_created = _take_date(attrs, "dateCreated", field.extra)
    field.date_modified = _take_date(attrs, "dateModified", field.extra)
    handlers = _extensible_handlers(field.annotations, field.traits, None)
    handlers["form"] = lambda c: field.content.forms.append(_parse_form(c))
    _walk(el, field.extra, handlers)
    return field


# --- entry-side elements -----------------------------------------------------------


def _parse_url_ref(el: etree._Element) -> URLRef:
    ref = URLRef("")
    attrs = _split_attrs(el, ("href",), ref.extra)
    ref.href = attrs.get("href", "")
    _walk(el, ref.extra, {"label": lambda c: _set_multitext(ref, "label", c)})
    return ref


def _set_multitext(obj: object, attr: str, el: etree._Element) -> None:
    setattr(obj, attr, _parse_multitext(el))


def _parse_grammatical_info(el: etree._Element) -> GrammaticalInfo:
    info = GrammaticalInfo("")
    attrs = _split_attrs(el, ("value",), info.extra)
    info.value = attrs.get("value", "")
    _walk(el, info.extra, {"trait": lambda c: info.traits.append(_parse_trait(c))})
    return info


def _parse_translation(el: etree._Element) -> Translation:
    translation = Translation()
    attrs = _split_attrs(el, ("type",), translation.extra)
    translation.type = attrs.get("type")
    _walk(
        el,
        translation.extra,
        {"form": lambda c: translation.forms.forms.append(_parse_form(c))},
    )
    return translation


def _parse_note(el: etree._Element) -> Note:
    note = Note()
    attrs = _split_attrs(el, ("type", "dateCreated", "dateModified"), note.extra)
    note.type = attrs.get("type")
    note.date_created = _take_date(attrs, "dateCreated", note.extra)
    note.date_modified = _take_date(attrs, "dateModified", note.extra)
    handlers = _extensible_handlers(note.annotations, note.traits, note.fields)
    handlers["form"] = lambda c: note.forms.forms.append(_parse_form(c))
    _walk(el, note.extra, handlers)
    return note


def _parse_example(el: etree._Element) -> Example:
    example = Example()
    attrs = _split_attrs(el, ("source", "dateCreated", "dateModified"), example.extra)
    example.source = attrs.get("source")
    example.date_created = _take_date(attrs, "dateCreated", example.extra)
    example.date_modified = _take_date(attrs, "dateModified", example.extra)
    handlers = _extensible_handlers(example.annotations, example.traits, example.fields)
    handlers["form"] = lambda c: example.forms.forms.append(_parse_form(c))
    handlers["translation"] = lambda c: example.translations.append(_parse_translation(c))
    handlers["note"] = lambda c: example.notes.append(_parse_note(c))
    _walk(el, example.extra, handlers)
    return example


def _parse_relation(el: etree._Element) -> Relation:
    relation = Relation(type="", ref="")
    attrs = _split_attrs(
        el, ("type", "ref", "order", "dateCreated", "dateModified"), relation.extra
    )
    relation.type = attrs.get("type", "")
    relation.ref = attrs.get("ref", "")
    relation.order = _take_int(attrs, "order", relation.extra)
    relation.date_created = _take_date(attrs, "dateCreated", relation.extra)
    relation.date_modified = _take_date(attrs, "dateModified", relation.extra)
    handlers = _extensible_handlers(relation.annotations, relation.traits, relation.fields)
    handlers["usage"] = lambda c: _set_multitext(relation, "usage", c)
    _walk(el, relation.extra, handlers)
    return relation


def _parse_etymology(el: etree._Element) -> Etymology:
    etymology = Etymology(type="", source="")
    attrs = _split_attrs(el, ("type", "source", "dateCreated", "dateModified"), etymology.extra)
    etymology.type = attrs.get("type", "")
    etymology.source = attrs.get("source", "")
    etymology.date_created = _take_date(attrs, "dateCreated", etymology.extra)
    etymology.date_modified = _take_date(attrs, "dateModified", etymology.extra)
    handlers = _extensible_handlers(etymology.annotations, etymology.traits, etymology.fields)
    handlers["form"] = lambda c: etymology.forms.forms.append(_parse_form(c))
    handlers["gloss"] = lambda c: etymology.glosses.append(_parse_form(c))
    _walk(el, etymology.extra, handlers)
    return etymology


def _parse_reversal_main(el: etree._Element) -> ReversalMain:
    main = ReversalMain()
    _split_attrs(el, (), main.extra)
    _walk(
        el,
        main.extra,
        {
            "form": lambda c: main.forms.forms.append(_parse_form(c)),
            "main": lambda c: setattr(main, "main", _parse_reversal_main(c)),
            "grammatical-info": lambda c: setattr(
                main, "grammatical_info", _parse_grammatical_info(c)
            ),
        },
    )
    return main


def _parse_reversal(el: etree._Element) -> Reversal:
    reversal = Reversal()
    attrs = _split_attrs(el, ("type",), reversal.extra)
    reversal.type = attrs.get("type")
    _walk(
        el,
        reversal.extra,
        {
            "form": lambda c: reversal.forms.forms.append(_parse_form(c)),
            "main": lambda c: setattr(reversal, "main", _parse_reversal_main(c)),
            "grammatical-info": lambda c: setattr(
                reversal, "grammatical_info", _parse_grammatical_info(c)
            ),
        },
    )
    return reversal


def _parse_pronunciation(el: etree._Element) -> Pronunciation:
    pronunciation = Pronunciation()
    attrs = _split_attrs(el, ("dateCreated", "dateModified"), pronunciation.extra)
    pronunciation.date_created = _take_date(attrs, "dateCreated", pronunciation.extra)
    pronunciation.date_modified = _take_date(attrs, "dateModified", pronunciation.extra)
    handlers = _extensible_handlers(
        pronunciation.annotations, pronunciation.traits, pronunciation.fields
    )
    handlers["form"] = lambda c: pronunciation.forms.forms.append(_parse_form(c))
    handlers["media"] = lambda c: pronunciation.media.append(_parse_url_ref(c))
    _walk(el, pronunciation.extra, handlers)
    return pronunciation


def _parse_variant(el: etree._Element) -> Variant:
    variant = Variant()
    attrs = _split_attrs(el, ("ref", "dateCreated", "dateModified"), variant.extra)
    variant.ref = attrs.get("ref")
    variant.date_created = _take_date(attrs, "dateCreated", variant.extra)
    variant.date_modified = _take_date(attrs, "dateModified", variant.extra)
    handlers = _extensible_handlers(variant.annotations, variant.traits, variant.fields)
    handlers["form"] = lambda c: variant.forms.forms.append(_parse_form(c))
    handlers["pronunciation"] = lambda c: variant.pronunciations.append(_parse_pronunciation(c))
    handlers["relation"] = lambda c: variant.relations.append(_parse_relation(c))
    _walk(el, variant.extra, handlers)
    return variant


def _parse_sense(el: etree._Element) -> Sense:
    sense = Sense()
    attrs = _split_attrs(el, ("id", "order", "dateCreated", "dateModified"), sense.extra)
    sense.id = attrs.get("id")
    sense.order = _take_int(attrs, "order", sense.extra)
    sense.date_created = _take_date(attrs, "dateCreated", sense.extra)
    sense.date_modified = _take_date(attrs, "dateModified", sense.extra)
    handlers = _extensible_handlers(sense.annotations, sense.traits, sense.fields)
    handlers.update(
        {
            "grammatical-info": lambda c: setattr(
                sense, "grammatical_info", _parse_grammatical_info(c)
            ),
            "gloss": lambda c: sense.glosses.append(_parse_form(c)),
            "definition": lambda c: _set_multitext(sense, "definition", c),
            "relation": lambda c: sense.relations.append(_parse_relation(c)),
            "note": lambda c: sense.notes.append(_parse_note(c)),
            "example": lambda c: sense.examples.append(_parse_example(c)),
            "reversal": lambda c: sense.reversals.append(_parse_reversal(c)),
            "illustration": lambda c: sense.illustrations.append(_parse_url_ref(c)),
            "subsense": lambda c: sense.subsenses.append(_parse_sense(c)),
        }
    )
    _walk(el, sense.extra, handlers)
    return sense


def _parse_entry(el: etree._Element) -> Entry:
    entry = Entry()
    attrs = _split_attrs(
        el,
        ("id", "guid", "order", "dateCreated", "dateModified", "dateDeleted"),
        entry.extra,
    )
    entry.id = attrs.get("id")
    entry.guid = attrs.get("guid")
    entry.order = _take_int(attrs, "order", entry.extra)
    entry.date_created = _take_date(attrs, "dateCreated", entry.extra)
    entry.date_modified = _take_date(attrs, "dateModified", entry.extra)
    entry.date_deleted = _take_date(attrs, "dateDeleted", entry.extra)
    handlers = _extensible_handlers(entry.annotations, entry.traits, entry.fields)
    handlers.update(
        {
            "lexical-unit": lambda c: _set_multitext(entry, "lexical_unit", c),
            "citation": lambda c: _set_multitext(entry, "citation", c),
            "pronunciation": lambda c: entry.pronunciations.append(_parse_pronunciation(c)),
            "variant": lambda c: entry.variants.append(_parse_variant(c)),
            "sense": lambda c: entry.senses.append(_parse_sense(c)),
            "note": lambda c: entry.notes.append(_parse_note(c)),
            "relation": lambda c: entry.relations.append(_parse_relation(c)),
            "etymology": lambda c: entry.etymologies.append(_parse_etymology(c)),
        }
    )
    _walk(el, entry.extra, handlers)
    return entry


# --- header side -------------------------------------------------------------------


def _parse_field_definition(el: etree._Element) -> FieldDefinition:
    definition = FieldDefinition(tag="")
    attrs = _split_attrs(el, ("tag",), definition.extra)
    definition.tag = attrs.get("tag", "")
    _walk(
        el,
        definition.extra,
        {"form": lambda c: definition.content.forms.append(_parse_form(c))},
    )
    return definition


def _parse_range_element(el: etree._Element) -> RangeElement:
    element = RangeElement(id="")
    attrs = _split_attrs(el, ("id", "parent", "guid"), element.extra)
    element.id = attrs.get("id", "")
    element.parent = attrs.get("parent")
    element.guid = attrs.get("guid")
    _walk(
        el,
        element.extra,
        {
            "description": lambda c: _set_multitext(element, "description", c),
            "label": lambda c: _set_multitext(element, "label", c),
            "abbrev": lambda c: _set_multitext(element, "abbrev", c),
        },
    )
    return element


def _parse_range(el: etree._Element) -> Range:
    range_ = Range(id="")
    attrs = _split_attrs(el, ("id", "href", "guid"), range_.extra)
    range_.id = attrs.get("id", "")
    range_.href = attrs.get("href")  # carried unresolved (M3)
    range_.guid = attrs.get("guid")
    _walk(
        el,
        range_.extra,
        {
            "description": lambda c: _set_multitext(range_, "description", c),
            "label": lambda c: _set_multitext(range_, "label", c),
            "abbrev": lambda c: _set_multitext(range_, "abbrev", c),
            "range-element": lambda c: range_.elements.append(_parse_range_element(c)),
        },
    )
    return range_


def _parse_header(el: etree._Element) -> Header:
    header = Header()
    _split_attrs(el, (), header.extra)

    def handle_ranges(ranges_el: etree._Element) -> None:
        _split_attrs(ranges_el, (), header.extra)
        _walk(
            ranges_el,
            header.extra,
            {"range": lambda c: header.ranges.append(_parse_range(c))},
        )

    def handle_fields(fields_el: etree._Element) -> None:
        _split_attrs(fields_el, (), header.extra)
        _walk(
            fields_el,
            header.extra,
            {"field": lambda c: header.fields.append(_parse_field_definition(c))},
        )

    _walk(
        el,
        header.extra,
        {
            "description": lambda c: _set_multitext(header, "description", c),
            "ranges": handle_ranges,
            "fields": handle_fields,
        },
    )
    return header
