"""The text model: Span, Text, Form, Multitext, plus Trait and Annotation.

``<text>`` is mixed content with recursively nestable ``<span>``, so ``Text``
is structured — an ordered list of ``str | Span`` fragments — with
``str(...)`` as the flattening escape hatch. ``Multitext`` is the "one
localized text per language" collection used all over LIFT; ``gloss`` is
form-shaped rather than multitext-shaped, which is why ``Form`` is a public
type of its own.
"""

from __future__ import annotations

from collections.abc import Mapping
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
class Multitext(Mapping[str, Text]):
    """An insertion-ordered collection of forms, keyed by language.

    A ``Mapping[str, Text]`` — ``mt["en"]``, ``"en" in mt``, ``mt.get(...)``,
    ``mt.keys()`` and the other views — plus assignment, which coerces plain
    strings (``mt["en"] = "dog"``), and deletion, which takes every form for
    the language, so ``del mt["en"]`` leaves ``"en" not in mt``.

    ``forms`` is the full truth and holds what no key can reach: a form with
    a ``None`` lang, and a second form for a language already present. Neither
    is yielded by a view or counted by ``len()``; where a language repeats,
    the mapping reads and updates its first form only.

    ``bool(mt)`` asks "is there anything to serialize", so a multitext holding
    only residue or only a lang-less form is truthy while ``len()`` is 0.
    Equality compares ``forms``, stricter than ``Mapping`` equality.
    """

    forms: list[Form] = field(default_factory=list)
    extra: Extras = field(default_factory=Extras)

    def _find(self, lang: str) -> Form | None:
        # A lang-less form is not a key: matching one here would answer
        # __getitem__ and get() for something keys() never reports.
        for form in self.forms:
            if form.lang is not None and form.lang == lang:
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
        if self._find(lang) is None:
            raise KeyError(lang)
        # Every form for the language, so the key is gone afterwards. Sliced in
        # place because callers hold `forms` directly.
        self.forms[:] = [form for form in self.forms if form.lang != lang]

    def __iter__(self) -> Iterator[str]:
        # Snapshot so a caller can delete through the mapping while iterating
        # it; walking forms live would skip the language after each removal.
        # Reads forms rather than a view: the views are built on this method.
        seen: set[str] = set()
        for form in tuple(self.forms):
            if form.lang is not None and form.lang not in seen:
                seen.add(form.lang)
                yield form.lang

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __bool__(self) -> bool:
        return bool(self.forms) or bool(self.extra)

    def __repr__(self) -> str:
        pairs = [(form.lang, str(form.text)) for form in self.forms]
        langs = [lang for lang, _ in pairs]
        # Dict-shaped only while the forms are one per language: a repeated or
        # lang-less form would render as a dict literal that cannot exist and
        # whose keys contradict keys().
        if None not in langs and len(set(langs)) == len(langs):
            inner = ", ".join(f"{lang!r}: {text!r}" for lang, text in pairs)
            return f"Multitext({{{inner}}})"
        inner = ", ".join(f"({lang!r}, {text!r})" for lang, text in pairs)
        return f"Multitext([{inner}])"
