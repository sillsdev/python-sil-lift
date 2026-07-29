"""Read, write, and validate LIFT (Lexicon Interchange Format) 0.13 lexicons.

The public API is exactly what this module re-exports; underscore-prefixed
modules are implementation details.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._canonical import canonicalize
from ._errors import LiftError, LiftParseError, LiftValidationError
from ._extras import Extras
from ._header import FieldDefinition, Header, Range, RangeElement
from ._model import (
    Changes,
    Entry,
    Etymology,
    Example,
    Field,
    GrammaticalInfo,
    Lexicon,
    MediaRef,
    Note,
    Pronunciation,
    RangesChanges,
    RangesFile,
    Relation,
    Reversal,
    ReversalMain,
    Sense,
    Translation,
    URLRef,
    Variant,
)
from ._stream import LiftReader, LiftWriter, open_reader, open_writer
from ._text import Annotation, Form, Multitext, Span, Text, Trait
from ._validate import Problem, iter_problems, validate_file

if TYPE_CHECKING:
    import os

__version__ = "0.1.0"

__all__ = [
    "Annotation",
    "Changes",
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
    "LiftReader",
    "LiftValidationError",
    "LiftWriter",
    "MediaRef",
    "Multitext",
    "Note",
    "Problem",
    "Pronunciation",
    "Range",
    "RangeElement",
    "RangesChanges",
    "RangesFile",
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
    "canonicalize",
    "iter_problems",
    "load",
    "open_reader",
    "open_writer",
    "validate_file",
]


def load(path: str | os.PathLike[str], *, resolve_ranges: bool = True) -> Lexicon:
    """Parse a ``.lift`` file (LIFT 0.13 only) into a :class:`Lexicon`.

    Companion ``.lift-ranges`` files are located and loaded too unless
    ``resolve_ranges=False``; see :meth:`Lexicon.load`.
    """
    return Lexicon.load(path, resolve_ranges=resolve_ranges)
