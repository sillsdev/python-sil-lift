"""Exception hierarchy."""

from __future__ import annotations

__all__ = ["LiftError", "LiftParseError", "LiftWriteError"]


class LiftError(Exception):
    """Base class for all sil-lift errors."""


class LiftParseError(LiftError):
    """A document could not be read as LIFT 0.13.

    Raised for non-XML input, a non-LIFT root element, or a LIFT version other
    than 0.13 (sil-lift does not migrate; see the lift-standard repo's XSLTs
    for one-off migration of legacy files).
    """


class LiftWriteError(LiftError):
    """An in-memory document holds content that XML cannot represent, so it cannot be written."""
