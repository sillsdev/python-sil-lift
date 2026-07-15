"""Read, write, and validate LIFT (Lexicon Interchange Format) 0.13 lexicons.

The public API is exactly what this module re-exports; underscore-prefixed
modules are implementation details.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._errors import LiftError, LiftParseError
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
    import os

__version__ = "0.1.0.dev0"

__all__ = [
    "Annotation",
    "Entry",
    "Etymology",
    "Example",
    "Extras",
    "Field",
    "FieldDefinition",
    "Form",
    "GrammaticalInfo",
    "Header",
    "Lexicon",
    "LiftError",
    "LiftParseError",
    "Multitext",
    "Note",
    "Pronunciation",
    "Range",
    "RangeElement",
    "Relation",
    "Reversal",
    "ReversalMain",
    "Sense",
    "Span",
    "Text",
    "Trait",
    "Translation",
    "URLRef",
    "Variant",
    "load",
]


def load(path: str | os.PathLike[str]) -> Lexicon:
    """Parse a ``.lift`` file (LIFT 0.13 only) into a :class:`Lexicon`."""
    return Lexicon.load(path)
