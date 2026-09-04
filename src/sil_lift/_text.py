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
    """An insertion-ordered collection of forms, one per language.

    A ``Mapping[str, Text]`` keyed by language — ``mt["en"]``, ``"en" in mt``,
    ``mt.get(...)``, ``mt.keys()`` and the other views — plus the two mutators
    LIFT editing needs: assignment coercing plain strings (``mt["en"] = "dog"``)
    and deletion. The rest of ``MutableMapping`` is deliberately not inherited;
    ``clear`` and ``popitem`` have no clear meaning for a form list that can
    also hold forms no key reaches.

    The ``forms`` list is the full truth, and holds what no mapping can
    represent: a form with a ``None`` lang, and a second form for a language
    already present. Both are schema-invalid — the LIFT 0.13 spec's own example
    documents carry a lang-less form, and a repeated language is what validation
    reports as ``duplicate-form-lang``, read off ``forms`` rather than off the
    mapping. Neither is reachable by key, yielded by a view, or counted by
    ``len()``.

    Where a language is repeated, the mapping is its first form: that is the one
    ``mt["en"]`` reads and the one assignment updates, leaving any later form for
    the language alone, since a ``Form`` carries annotations and residue the
    mapping cannot show a caller. Deletion takes every form for the language, so
    ``del mt["en"]`` leaves ``"en" not in mt``.

    Two further deviations from ``Mapping``, both serving the fidelity contract.
    ``bool(mt)`` asks "is there anything to serialize" rather than
    ``len(mt) != 0``, so a multitext holding only residue or only a lang-less
    form is truthy while empty. Equality is the dataclass's: form lists must
    match exactly, which is stricter than ``Mapping`` equality, where a form no
    key reaches would not count.
    """

    forms: list[Form] = field(default_factory=list)
    extra: Extras = field(default_factory=Extras)

    def _find(self, lang: str) -> Form | None:
        # A None lang is not a key. Matching one would answer __getitem__ and
        # __contains__ for a form that no view yields and len() does not count.
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

    # Both read forms directly rather than through keys(): the inherited views
    # are built on these two, so consulting a view here would not terminate.
    def __iter__(self) -> Iterator[str]:
        # One key per language — the form __getitem__ answers with — so the
        # views, len() and dict(self) agree whatever forms holds. The snapshot
        # lets a caller delete through the mapping while iterating it; walking
        # forms live would skip the language after each removal.
        seen: set[str] = set()
        for form in tuple(self.forms):
            if form.lang is not None and form.lang not in seen:
                seen.add(form.lang)
                yield form.lang

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __bool__(self) -> bool:
        # Not derived from len(): emptiness here means "nothing to serialize",
        # which residue and a lang-less form each defeat on their own.
        return bool(self.forms) or bool(self.extra)

    def __repr__(self) -> str:
        pairs = [(form.lang, str(form.text)) for form in self.forms]
        langs = [lang for lang, _ in pairs]
        # Dict-shaped only while the forms are one per language: a repeated or
        # lang-less form would render as a dict literal that cannot exist and
        # whose keys contradict keys(). Falling back to pairs keeps every form
        # visible, and the shape is the signal that forms holds more than the
        # mapping reaches.
        if None not in langs and len(set(langs)) == len(langs):
            inner = ", ".join(f"{lang!r}: {text!r}" for lang, text in pairs)
            return f"Multitext({{{inner}}})"
        inner = ", ".join(f"({lang!r}, {text!r})" for lang, text in pairs)
        return f"Multitext([{inner}])"
