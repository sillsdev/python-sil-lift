"""Byte-region scanner: locate the exact source bytes of each root child.

The writer emits untouched entries verbatim from their original bytes, which
requires knowing each top-level ``<entry>``'s (and ``<header>``'s) exact byte
region in the source. lxml exposes no byte offsets, but the stdlib's expat
binding does: ``CurrentByteIndex`` reports where the current event's markup
begins, which is a region's start at the element's start event and — bar the
empty-element wrinkle noted below — its end at the matching end event.

"Region" rather than "span" throughout: LIFT has a ``<span>`` element for
inline markup, modelled as :class:`~sil_lift.Span`, and the two would
otherwise collide in the reader and writer — which handle both.

What it exists for is byte identity, not diagnostics — ``docs/en/fidelity.md``
states the guarantee it underpins. Problem reporting needs only the line an
element starts on and takes that from lxml's ``sourceline`` (see
``_validate._line``); a region needs the end offset too, which no tree API
exposes.

It is deliberately conservative: anything unexpected (DOCTYPE, malformed
markup, non-ASCII-compatible encoding — checked by the caller) returns ``None``
and the writer falls back to canonical serialization, which keeps the semantic
guarantee and waives only byte identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from xml.parsers import expat

__all__ = ["ChildRegion", "ScanResult", "scan"]


@dataclass(slots=True)
class ChildRegion:
    tag: str  # "header", "entry", or any other root-child tag
    start: int
    end: int  # exclusive


@dataclass(slots=True)
class ScanResult:
    root_open_start: int
    root_open_end: int  # exclusive; end of the <lift ...> open tag
    root_self_closing: bool
    children: list[ChildRegion]  # document order; empty for a self-closing root


class _Unscannable(Exception):
    """Raised inside a handler to abandon the scan; ``scan`` returns None."""


def _tag_end(data: bytes, start: int) -> int:
    """Just past the ``>`` of the start tag beginning at ``start``.

    An attribute value may hold a ``>``, so this tracks quoting rather than
    searching for the delimiter. End tags take no attributes and so need no
    such care.
    """
    quote: int | None = None
    for index in range(start + 1, len(data)):
        char = data[index]
        if quote is not None:
            if char == quote:
                quote = None
        elif char in (0x22, 0x27):  # " or '
            quote = char
        elif char == 0x3E:  # >
            return index + 1
    raise _Unscannable  # unterminated start tag: expat would have refused it too


def scan(data: bytes) -> ScanResult | None:
    """Locate the root open tag and every root child's byte region, or None."""
    parser = expat.ParserCreate()
    # A DTD is refused outright below, so its parameter entities are never
    # fetched or expanded either.
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)

    depth = 0
    # Only the root and its children have regions to report; deeper elements
    # just move the depth counter, which is what keeps a nested <entry> from
    # being mistaken for a root child.
    open_tags: dict[int, tuple[str, int, int]] = {}
    children: list[ChildRegion] = []
    root: tuple[int, int] | None = None
    root_self_closing = False

    def refuse(*_args: object) -> None:
        raise _Unscannable

    def start_element(name: str, _attrs: dict[str, str]) -> None:
        nonlocal depth, root
        depth += 1
        if depth > 2:
            return
        start = parser.CurrentByteIndex
        open_tags[depth] = (name, start, _tag_end(data, start))
        if depth == 1:
            root = (start, open_tags[1][2])

    def end_element(_name: str) -> None:
        nonlocal depth, root_self_closing
        if depth <= 2:
            tag, start, open_end = open_tags[depth]
            # An empty element's end event reports the offset just past the
            # whole element; every other element's reports the "<" of its end
            # tag. Which of the two this is was settled by the start tag, in
            # the "/" before its ">" — not by the end event, whose two cases
            # are not distinguishable from the offset alone.
            self_closing = data[open_end - 2] == 0x2F  # /
            if self_closing:
                end = open_end
            else:
                end = data.find(b">", parser.CurrentByteIndex) + 1
                if end <= 0:
                    raise _Unscannable
            if depth == 1:
                root_self_closing = self_closing
            else:
                children.append(ChildRegion(tag=tag, start=start, end=end))
        depth -= 1

    # A DTD may define entities whose expansion the offsets above would not
    # describe, so a document carrying one is not scanned at all.
    parser.StartDoctypeDeclHandler = refuse
    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element
    try:
        parser.Parse(data, True)
    except (_Unscannable, expat.ExpatError):
        return None
    if root is None:
        return None  # no root element: nothing to reuse bytes from
    return ScanResult(
        root_open_start=root[0],
        root_open_end=root[1],
        root_self_closing=root_self_closing,
        children=children,
    )
