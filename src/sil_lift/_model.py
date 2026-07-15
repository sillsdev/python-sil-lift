"""Entry-side model: Entry, Sense, and everything below them, plus Lexicon.

Shapes follow the LIFT 0.13 RNG inventory exactly. Extensibility is a
three-way split (data-model quirk 4): the eight fully-extensible elements
derive from ``_Extensible``; the usage ``<field>`` gets the field-less variant
``_ExtensibleNoFields`` (no field-in-field recursion); ``GrammaticalInfo`` is
the outlier with bare traits only. Typed attributes that fail to parse
(malformed dates/integers in real-world files) are preserved verbatim in the
node's ``extra`` and the model field stays ``None``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from ._extras import Extras
from ._header import Header
from ._text import Annotation, Form, Multitext, Text, Trait

if TYPE_CHECKING:
    import os

    from ._writer import _SourceInfo

__all__ = [
    "Entry",
    "Etymology",
    "Example",
    "Field",
    "GrammaticalInfo",
    "Lexicon",
    "Note",
    "Pronunciation",
    "Relation",
    "Reversal",
    "ReversalMain",
    "Sense",
    "Translation",
    "URLRef",
    "Variant",
]


@dataclass(slots=True, kw_only=True)
class _ExtensibleNoFields:
    """The extensible bundle minus ``<field>``: dates, annotations, traits, residue."""

    date_created: datetime | date | None = None
    date_modified: datetime | date | None = None
    annotations: list[Annotation] = field(default_factory=list)
    traits: list[Trait] = field(default_factory=list)
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True, kw_only=True)
class _Extensible(_ExtensibleNoFields):
    """The full extensible bundle (entry, sense, note, example, ...)."""

    fields: list[Field] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class Field(_ExtensibleNoFields):
    """An entry-level usage ``<field type=...>`` (extensible, but no nested field)."""

    type: str
    content: Multitext = field(default_factory=Multitext)


@dataclass(slots=True)
class GrammaticalInfo:
    """A ``<grammatical-info value=...>``; carries traits only (quirk 4 outlier)."""

    value: str
    traits: list[Trait] = field(default_factory=list)
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True)
class URLRef:
    """A ``<media>`` or ``<illustration>``: an href with an optional label."""

    href: str
    label: Multitext = field(default_factory=Multitext)
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True, kw_only=True)
class Translation:
    """A ``<translation>`` of an example (not extensible)."""

    type: str | None = None
    forms: Multitext = field(default_factory=Multitext)
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True, kw_only=True)
class Note(_Extensible):
    """A ``<note>``; sibling notes conventionally have distinct types."""

    type: str | None = None
    forms: Multitext = field(default_factory=Multitext)


@dataclass(slots=True, kw_only=True)
class Example(_Extensible):
    """An ``<example>`` under a sense."""

    source: str | None = None
    forms: Multitext = field(default_factory=Multitext)
    translations: list[Translation] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class Relation(_Extensible):
    """A ``<relation type=... ref=...>`` cross-reference to another entry/sense."""

    type: str
    ref: str
    order: int | None = None
    usage: Multitext = field(default_factory=Multitext)


@dataclass(slots=True, kw_only=True)
class Etymology(_Extensible):
    """An ``<etymology type=... source=...>``; glosses are form-shaped (quirk 3)."""

    type: str
    source: str
    forms: Multitext = field(default_factory=Multitext)
    glosses: list[Form] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class ReversalMain:
    """A reversal ``<main>``: the parent node in a reversal-index chain (recursive)."""

    forms: Multitext = field(default_factory=Multitext)
    main: ReversalMain | None = None
    grammatical_info: GrammaticalInfo | None = None
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True, kw_only=True)
class Reversal:
    """A ``<reversal>`` index entry (not extensible)."""

    type: str | None = None
    forms: Multitext = field(default_factory=Multitext)
    main: ReversalMain | None = None
    grammatical_info: GrammaticalInfo | None = None
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True, kw_only=True)
class Pronunciation(_Extensible):
    """A ``<pronunciation>`` with optional ``<media>`` references."""

    forms: Multitext = field(default_factory=Multitext)
    media: list[URLRef] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class Variant(_Extensible):
    """A ``<variant>``: an inline variant form and/or a ``ref`` cross-reference."""

    ref: str | None = None
    forms: Multitext = field(default_factory=Multitext)
    pronunciations: list[Pronunciation] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class Sense(_Extensible):
    """A ``<sense>`` (or ``<subsense>`` — same content model, recursive)."""

    id: str | None = None
    order: int | None = None
    grammatical_info: GrammaticalInfo | None = None
    glosses: list[Form] = field(default_factory=list)
    definition: Multitext = field(default_factory=Multitext)
    relations: list[Relation] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    examples: list[Example] = field(default_factory=list)
    reversals: list[Reversal] = field(default_factory=list)
    illustrations: list[URLRef] = field(default_factory=list)
    subsenses: list[Sense] = field(default_factory=list)

    def gloss(self, lang: str) -> Text | None:
        """The gloss text in ``lang``, or None (first match; quirk-3 helper)."""
        for gloss_form in self.glosses:
            if gloss_form.lang == lang:
                return gloss_form.text
        return None


@dataclass(slots=True, kw_only=True)
class Entry(_Extensible):
    """An ``<entry>``. A set ``date_deleted`` marks a tombstone."""

    id: str | None = None
    guid: str | None = None
    order: int | None = None
    date_deleted: datetime | date | None = None
    lexical_unit: Multitext = field(default_factory=Multitext)
    citation: Multitext = field(default_factory=Multitext)
    pronunciations: list[Pronunciation] = field(default_factory=list)
    variants: list[Variant] = field(default_factory=list)
    senses: list[Sense] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)
    etymologies: list[Etymology] = field(default_factory=list)

    def gloss_langs(self) -> set[str]:
        """Every language that has a gloss in any sense or subsense."""
        langs: set[str] = set()
        stack = list(self.senses)
        while stack:
            sense = stack.pop()
            langs.update(g.lang for g in sense.glosses if g.lang is not None)
            stack.extend(sense.subsenses)
        return langs


class Lexicon:
    """The root handle: a parsed ``.lift`` document (and, from M3, its folder)."""

    __slots__ = ("_source", "entries", "extra", "header", "path", "producer")

    def __init__(
        self,
        *,
        header: Header | None = None,
        entries: list[Entry] | None = None,
        producer: str | None = None,
        path: Path | None = None,
        extra: Extras | None = None,
    ) -> None:
        self.header = header if header is not None else Header()
        self.entries = entries if entries is not None else []
        self.producer = producer
        self.path = path
        self.extra = extra if extra is not None else Extras()
        self._source: _SourceInfo | None = None  # set by the reader (A2 passthrough)

    @classmethod
    def load(cls, path: str | os.PathLike[str]) -> Lexicon:
        """Parse a ``.lift`` file (LIFT 0.13 only) into a full object graph."""
        from ._reader import parse_document

        return parse_document(Path(path))

    def save(self, path: str | os.PathLike[str] | None = None) -> None:
        """Write the ``.lift`` file.

        Untouched entries are emitted byte-identical to the source; modified
        entries are re-serialized canonically with all residue preserved (A2).
        With no ``path``, saves to where the lexicon was loaded from.
        """
        from ._writer import render_document

        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("no target path: pass save(path) or load the lexicon from a file")
        target.write_bytes(render_document(self))
        self.path = target

    def find(self, *, id: str | None = None, guid: str | None = None) -> Entry | None:
        """The first entry matching the given id and/or guid, or None."""
        if id is None and guid is None:
            raise ValueError("find() needs id= and/or guid=")
        for entry in self.entries:
            if (id is None or entry.id == id) and (guid is None or entry.guid == guid):
                return entry
        return None

    def __repr__(self) -> str:
        source = f", path={str(self.path)!r}" if self.path else ""
        return f"Lexicon({len(self.entries)} entries{source})"
