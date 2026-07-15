"""Header-side model: Header, FieldDefinition, Range, RangeElement.

The header ``<field tag=...>`` (a field *definition*) is a structurally
different element from the entry-level ``<field type=...>`` usage variant
(data-model quirk 1) — hence ``FieldDefinition`` here vs ``Field`` in
``_model``. None of these elements are extensible.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._extras import Extras
from ._text import Multitext

__all__ = ["FieldDefinition", "Header", "Range", "RangeElement"]


@dataclass(slots=True, kw_only=True)
class FieldDefinition:
    """A header ``<field tag=...>``: documents a field type used in the document."""

    tag: str
    content: Multitext = field(default_factory=Multitext)
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True, kw_only=True)
class RangeElement:
    """A ``<range-element>``: one value in a range; ``parent`` builds hierarchies."""

    id: str
    parent: str | None = None
    guid: str | None = None
    description: Multitext = field(default_factory=Multitext)
    label: Multitext = field(default_factory=Multitext)
    abbrev: Multitext = field(default_factory=Multitext)
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True, kw_only=True)
class Range:
    """A ``<range>``: a controlled vocabulary, inline and/or via ``href``.

    ``href`` points at an external ``.lift-ranges`` resource; its contents are
    carried unresolved here (resolution/tracking is milestone M3).
    """

    id: str
    href: str | None = None
    guid: str | None = None
    description: Multitext = field(default_factory=Multitext)
    label: Multitext = field(default_factory=Multitext)
    abbrev: Multitext = field(default_factory=Multitext)
    elements: list[RangeElement] = field(default_factory=list)
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True, kw_only=True)
class Header:
    """The optional ``<header>``: description, ranges, field definitions."""

    description: Multitext = field(default_factory=Multitext)
    ranges: list[Range] = field(default_factory=list)
    fields: list[FieldDefinition] = field(default_factory=list)
    extra: Extras = field(default_factory=Extras)

    def __bool__(self) -> bool:
        return bool(self.description or self.ranges or self.fields or self.extra)
