"""Where LIFT residue is kept: content the LIFT 0.13 schema does not define.

Every model node carries an ``Extras`` holding whatever the parser found that the
LIFT 0.13 schema does not define: unknown attributes, unknown child elements, XML
comments/processing instructions, and stray text in element-only contexts. The
writer re-emits it so nothing is dropped.

FieldWorks calls this LIFT residue and keeps it much the same way — content that
does not map onto its model is serialized into a ``<lift-residue>`` blob held in
a ``LiftResidue`` field — so that is the name used throughout this package. Take
care with the bare word: in FieldWorks "residue" on its own means the
``import-residue`` field, a user-visible LIFT field recording what a standard
format import could not place, which is a different thing entirely.

The public surface is deliberately tiny — equality, repr, emptiness, to_string()
— so the internal representation stays swappable and no lxml type ever leaks.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["Extras"]


@dataclass(slots=True)
class _ExtraNode:
    kind: str  # "element" | "comment" | "pi" | "text"
    xml: str  # serialized fragment (for "text": the raw character data)
    # Child position in the original parent — a recorded position, not content:
    # the same residue at a slightly different position is still equal.
    index: int = field(compare=False, default=0)


@dataclass(slots=True, repr=False)
class Extras:
    """Out-of-schema content carried losslessly (opaque; see module docstring)."""

    _attrs: dict[str, str] = field(default_factory=dict)
    _nodes: list[_ExtraNode] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self._attrs or self._nodes)

    def __repr__(self) -> str:
        if not self:
            return "Extras()"
        return f"Extras({len(self._attrs)} attrs, {len(self._nodes)} nodes)"

    def to_string(self) -> str:
        """Human-readable dump of the carried content (not a serialization format)."""
        parts = [f"@{name}={value!r}" for name, value in self._attrs.items()]
        parts += [node.xml for node in self._nodes]
        return "\n".join(parts)
