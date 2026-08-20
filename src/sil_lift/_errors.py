"""Exception hierarchy."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._validate import Problem

__all__ = ["LiftError", "LiftParseError", "LiftValidationError", "LiftWriteError"]


class LiftError(Exception):
    """Base class for all sil-lift errors."""


class LiftParseError(LiftError):
    """A document could not be read as LIFT 0.13.

    Raised for non-XML input, a non-LIFT root element, or a LIFT version other
    than 0.13 (sil-lift does not migrate; see the lift-standard repo's XSLTs
    for one-off migration of legacy files).
    """


class LiftWriteError(LiftError):
    """A model holds content that XML cannot represent, so it cannot be written.

    The only such content is a lone surrogate (U+D800-U+DFFF): a Python string
    may hold one, an XML document may not, in any encoding. It cannot come from
    a LIFT file — the parser rejects both spellings, a numeric character
    reference and CESU-8/WTF-8 bytes — so it is always a string assigned
    through the API. Raised by :meth:`Lexicon.save` and by everything else that
    serializes (:meth:`Lexicon.changes`, validation, the streaming writer);
    nothing is written, and the model is left untouched.
    """


class LiftValidationError(LiftError):
    """Raised by the fail-fast validation wrappers on the first error-level
    :class:`~sil_lift.Problem` (warnings never raise)."""

    def __init__(self, problem: Problem) -> None:
        super().__init__(str(problem))
        self.problem = problem
