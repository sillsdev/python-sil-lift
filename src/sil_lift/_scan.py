"""Byte-region scanner: locate the exact source bytes of each root child.

The writer emits untouched entries verbatim from their original bytes, which
requires knowing each top-level ``<entry>``'s (and ``<header>``'s) exact byte
region in the source. lxml exposes no byte offsets, so this module walks the
raw bytes with a small state machine that understands tags, quoted attribute
values, comments, CDATA sections, and processing instructions.

"Region" rather than "span" throughout: LIFT has a ``<span>`` element for
inline markup, modelled as :class:`~sil_lift.Span`, and the two would
otherwise collide in the reader and writer — which handle both.

What it exists for is byte identity, not diagnostics — ``docs/en/fidelity.md``
states the guarantee it underpins. Problem reporting needs only the line an
element starts on and takes that from lxml's ``sourceline`` (see
``_validate._line``); a region needs the end offset too, which no parser API
exposes.

It is deliberately conservative: anything unexpected (DOCTYPE, malformed
nesting, non-ASCII-compatible encoding — checked by the caller) returns
``None`` and the writer falls back to canonical serialization, which keeps
the semantic guarantee and waives only byte identity.
"""

from __future__ import annotations

from dataclasses import dataclass

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


def _skip_comment(data: bytes, i: int) -> int | None:
    end = data.find(b"-->", i + 4)
    return None if end < 0 else end + 3


def _skip_pi(data: bytes, i: int) -> int | None:
    end = data.find(b"?>", i + 2)
    return None if end < 0 else end + 2


def _skip_cdata(data: bytes, i: int) -> int | None:
    end = data.find(b"]]>", i + 9)
    return None if end < 0 else end + 3


def _skip_tag(data: bytes, i: int) -> tuple[int, bool] | None:
    """From ``<`` of a start/end tag to just past ``>``; reports self-closing."""
    n = len(data)
    j = i + 1
    quote: int | None = None
    while j < n:
        c = data[j]
        if quote is not None:
            if c == quote:
                quote = None
        elif c in (0x22, 0x27):  # " or '
            quote = c
        elif c == 0x3E:  # >
            return j + 1, data[j - 1] == 0x2F  # preceded by /
        j += 1
    return None


def _tag_name(data: bytes, i: int) -> str:
    j = i + 1
    n = len(data)
    while j < n and data[j] not in b" \t\r\n/>":
        j += 1
    return data[i + 1 : j].decode("utf-8", errors="replace")


def _skip_element(data: bytes, i: int) -> int | None:
    """From ``<`` of a start tag to just past the matching end tag."""
    step = _skip_tag(data, i)
    if step is None:
        return None
    pos, self_closing = step
    if self_closing:
        return pos
    depth = 1
    n = len(data)
    while depth > 0:
        lt = data.find(b"<", pos)
        if lt < 0:
            return None
        if data.startswith(b"<!--", lt):
            nxt = _skip_comment(data, lt)
        elif data.startswith(b"<![CDATA[", lt):
            nxt = _skip_cdata(data, lt)
        elif data.startswith(b"<?", lt):
            nxt = _skip_pi(data, lt)
        elif data.startswith(b"</", lt):
            step = _skip_tag(data, lt)
            if step is None:
                return None
            nxt = step[0]
            depth -= 1
        elif data.startswith(b"<!", lt):
            return None  # DOCTYPE or other markup decl mid-document: bail out
        else:
            step = _skip_tag(data, lt)
            if step is None:
                return None
            nxt, self_closing = step
            if not self_closing:
                depth += 1
        if nxt is None:
            return None
        pos = nxt
        if pos > n:
            return None
    return pos


def scan(data: bytes) -> ScanResult | None:
    """Locate the root open tag and every root child's byte region, or None."""
    n = len(data)
    pos = 0
    # Prolog: BOM, XML declaration, comments, PIs — until the root start tag.
    while True:
        lt = data.find(b"<", pos)
        if lt < 0:
            return None
        if data.startswith(b"<!--", lt):
            nxt = _skip_comment(data, lt)
        elif data.startswith(b"<?", lt):
            nxt = _skip_pi(data, lt)
        elif data.startswith(b"<!", lt):
            return None  # DOCTYPE: no passthrough
        else:
            break
        if nxt is None:
            return None
        pos = nxt
    root_open_start = lt
    step = _skip_tag(data, lt)
    if step is None:
        return None
    root_open_end, self_closing = step
    result = ScanResult(
        root_open_start=root_open_start,
        root_open_end=root_open_end,
        root_self_closing=self_closing,
        children=[],
    )
    if self_closing:
        return result
    pos = root_open_end
    while True:
        lt = data.find(b"<", pos)
        if lt < 0:
            return None  # never saw the root close tag
        if data.startswith(b"<!--", lt):
            nxt = _skip_comment(data, lt)
        elif data.startswith(b"<![CDATA[", lt):
            nxt = _skip_cdata(data, lt)
        elif data.startswith(b"<?", lt):
            nxt = _skip_pi(data, lt)
        elif data.startswith(b"</", lt):
            return result  # root close tag; the trailing bytes are copied as they are
        elif data.startswith(b"<!", lt):
            return None
        else:
            tag = _tag_name(data, lt)
            end = _skip_element(data, lt)
            if end is None or end > n:
                return None
            result.children.append(ChildRegion(tag=tag, start=lt, end=end))
            nxt = end
        if nxt is None:
            return None
        pos = nxt
