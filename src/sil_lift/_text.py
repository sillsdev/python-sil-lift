"""The text model: Span, Text, Form, Multitext, plus Trait and Annotation.

``<text>`` is mixed content with recursively nestable ``<span>``, so ``Text``
is structured — an ordered list of ``str | Span`` fragments — with
``str(...)`` as the flattening escape hatch. ``Multitext`` is the "one
localized text per language" collection used all over LIFT; ``gloss`` is
form-shaped rather than multitext-shaped, which is why ``Form`` is a public
type of its own.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING

from ._extras import Extras

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = ["Annotation", "Form", "Multitext", "Span", "Text", "Trait"]


@dataclass(slots=True)
class Span:
    """An inline markup run inside a ``<text>``; nests recursively."""

    content: list[str | Span] = field(default_factory=list)
    lang: str | None = None  # None inherits the enclosing form's language
    href: str | None = None
    class_: str | None = None  # the XML attribute is named 'class'
    extra: Extras = field(default_factory=Extras)

    def __str__(self) -> str:
        return "".join(str(fragment) for fragment in self.content)


@dataclass(slots=True)
class Text:
    """Mixed content of a ``<text>``: ordered ``str`` and ``Span`` fragments."""

    fragments: list[str | Span] = field(default_factory=list)

    def __str__(self) -> str:
        """Plain-text flattening; span markup is stripped, span text kept."""
        return "".join(str(fragment) for fragment in self.fragments)


@dataclass(slots=True)
class Trait:
    """A ``<trait>``: a name/value pair, typically keyed to a range."""

    name: str
    value: str
    annotations: list[Annotation] = field(default_factory=list)
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True)
class Annotation:
    """An ``<annotation>``: reviewer/editorial metadata on a node."""

    name: str
    value: str | None = None
    who: str | None = None
    when: datetime | date | None = None
    content: Multitext = field(default_factory=lambda: Multitext())
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True)
class Form:
    """A single-language text unit: ``<form lang=...><text/></form>``, also ``<gloss>``.

    ``lang`` is required by the schema; it is ``None`` only when reading
    schema-invalid real-world files (which sil-lift loads rather than rejects).
    """

    lang: str | None
    text: Text = field(default_factory=Text)
    annotations: list[Annotation] = field(default_factory=list)
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True, repr=False)
class Multitext:
    """An insertion-ordered collection of forms, one per language.

    Behaves like a ``Mapping[str, Text]`` keyed by language (``mt["en"]``),
    with assignment coercing plain strings (``mt["en"] = "dog"``). The
    underlying ``forms`` list is the full truth — forms with a ``None`` lang
    (schema-invalid input) are reachable there but not via mapping keys.
    """

    forms: list[Form] = field(default_factory=list)
    extra: Extras = field(default_factory=Extras)

    def _find(self, lang: str) -> Form | None:
        for form in self.forms:
            if form.lang == lang:
                return form
        return None

    def __getitem__(self, lang: str) -> Text:
        form = self._find(lang)
        if form is None:
            raise KeyError(lang)
        return form.text

    def __setitem__(self, lang: str, value: Text | str) -> None:
        text = Text([value]) if isinstance(value, str) else value
        form = self._find(lang)
        if form is None:
            self.forms.append(Form(lang, text))
        else:
            form.text = text

    def __delitem__(self, lang: str) -> None:
        form = self._find(lang)
        if form is None:
            raise KeyError(lang)
        self.forms.remove(form)

    def get(self, lang: str, default: Text | None = None) -> Text | None:
        form = self._find(lang)
        return default if form is None else form.text

    def __contains__(self, lang: object) -> bool:
        return isinstance(lang, str) and self._find(lang) is not None

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())

    def __len__(self) -> int:
        return len(self.forms)

    def __bool__(self) -> bool:
        return bool(self.forms) or bool(self.extra)

    def keys(self) -> list[str]:
        return [form.lang for form in self.forms if form.lang is not None]

    def values(self) -> list[Text]:
        return [form.text for form in self.forms if form.lang is not None]

    def items(self) -> list[tuple[str, Text]]:
        return [(form.lang, form.text) for form in self.forms if form.lang is not None]

    def __repr__(self) -> str:
        inner = ", ".join(f"{form.lang!r}: {str(form.text)!r}" for form in self.forms)
        return f"Multitext({{{inner}}})"
