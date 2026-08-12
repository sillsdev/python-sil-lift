"""Streaming read/write: same Entry types, one entry in memory at a time.

The reader wraps ``lxml.etree.iterparse`` with all ``clear()``/preceding-sibling
bookkeeping internal; the writer emits the same bytes ``canonical_document``
would produce for the same content, one entry chunk at a time (each entry's
subtree is built normally, serialized, and flushed — the byte layout is shared
with the canonical serializer by construction, so full and streaming output
never drift apart).

Streaming mode reuses no source bytes: output is always canonical. Root-level
LIFT residue (comments between entries) is not carried either — entries and the
header are.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from lxml import etree

from ._errors import LiftParseError
from ._header import Header, Range
from ._reader import SUPPORTED_VERSION, _parse_entry, _parse_header

if TYPE_CHECKING:
    import os
    from collections.abc import Iterator
    from types import TracebackType

    from ._model import Entry, RangesFile

__all__ = ["LiftReader", "LiftWriter", "open_reader", "open_writer"]


class LiftReader:
    """Lazy entry iterator over a ``.lift`` file; the header is parsed eagerly.

    Use as a context manager. The version guard runs at open time; the header
    (which precedes entries in a conforming file) is available immediately as
    :attr:`header`.
    """

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.header = Header()
        self.producer: str | None = None
        self._header_seen = False
        self._first_entry: Entry | None = None
        self._file = open(path, "rb")  # noqa: SIM115 - lifetime managed by close()
        try:
            self._events = etree.iterparse(
                self._file,
                events=("start", "end"),
                resolve_entities=False,
                no_network=True,
            )
            self._root = self._read_header(path)
        except Exception:
            self._file.close()
            raise

    def _read_header(self, path: str | os.PathLike[str]) -> etree._Element:
        """Pump events until the header (or first entry) has been read."""
        root: etree._Element | None = None
        try:
            for event, el in self._events:
                if event == "start":
                    if root is None:
                        root = el
                        if el.tag != "lift":
                            raise LiftParseError(
                                f"{path}: root element is <{el.tag}>, expected <lift>"
                            )
                        version = el.get("version")
                        if version != SUPPORTED_VERSION:
                            raise LiftParseError(
                                f"unsupported LIFT version {version!r}: sil-lift reads "
                                "LIFT 0.13 only (one-off migration XSLTs are available "
                                "in sillsdev/lift-standard)"
                            )
                        self.producer = el.get("producer")
                    continue
                if root is None or el.getparent() is not root:
                    continue
                if el.tag == "header" and not self._header_seen:
                    self._header_seen = True
                    self.header = _parse_header(el)
                    self._cleanup(el)
                    return root
                if el.tag == "entry":
                    self._first_entry = _parse_entry(el)
                    self._cleanup(el)
                    return root
        except etree.XMLSyntaxError as exc:
            raise LiftParseError(f"{path}: not well-formed XML: {exc}") from exc
        if root is None:
            raise LiftParseError(f"{path}: not well-formed XML: no root element")
        return root  # empty document: no header, no entries

    @staticmethod
    def _cleanup(el: etree._Element) -> None:
        el.clear()
        parent = el.getparent()
        if parent is not None:
            while el.getprevious() is not None:
                del parent[0]

    def __iter__(self) -> Iterator[Entry]:
        if self._first_entry is not None:
            entry, self._first_entry = self._first_entry, None
            yield entry
        try:
            for event, el in self._events:
                if event != "end" or el.getparent() is not self._root:
                    continue
                if el.tag == "entry":
                    entry = _parse_entry(el)
                    self._cleanup(el)
                    yield entry
                elif el.tag == "header" and not self._header_seen:
                    self._header_seen = True  # out-of-spec late header: still read
                    self.header = _parse_header(el)
                    self._cleanup(el)
        except etree.XMLSyntaxError as exc:
            raise LiftParseError(f"not well-formed XML: {exc}") from exc

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> LiftReader:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class LiftWriter:
    """Streaming writer: header up front, then one canonical chunk per entry.

    Use as a context manager; the closing ``</lift>`` is written only on a
    clean exit (an exception leaves an unterminated file, deliberately — a
    half-written lexicon must not look complete).
    """

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        header: Header | None = None,
        producer: str | None = None,
        ranges: RangesFile | None = None,
    ) -> None:
        from ._model import Lexicon
        from ._writer import _root_open_bytes, canonical_header_bytes

        self._ranges = ranges
        self._ranges_path: Path | None = None
        if ranges is not None:
            companion = Path(path).with_name(Path(path).name + "-ranges")
            self._ranges_path = companion
            # The references describe *this* document, so they go on a copy: a
            # caller-supplied header (typically reader.header) is often still in
            # use for the source lexicon, which has no such companion beside it.
            header = replace(header, ranges=list(header.ranges)) if header is not None else Header()
            referenced = {range_.id for range_ in header.ranges}
            for range_ in ranges.ranges:
                if range_.id not in referenced:
                    header.ranges.append(Range(id=range_.id, href=companion.name))
                    referenced.add(range_.id)
        self._file = open(path, "wb")  # noqa: SIM115 - lifetime managed by close()
        self._closed = False
        prototype = Lexicon(producer=producer)
        self._file.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        self._file.write(_root_open_bytes(prototype) + b"\n")
        if header is not None and header:
            self._file.write(canonical_header_bytes(header))

    def write(self, entry: Entry) -> None:
        from ._writer import canonical_entry_bytes

        self._file.write(canonical_entry_bytes(entry))

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._file.write(b"</lift>\n")
            self._file.close()
            if self._ranges is not None and self._ranges_path is not None:
                self._ranges.save(self._ranges_path)

    def __enter__(self) -> LiftWriter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self._closed = True  # leave the file visibly unterminated
            self._file.close()
        else:
            self.close()


def open_reader(path: str | os.PathLike[str]) -> LiftReader:
    """Open a ``.lift`` file for streaming reads (bounded memory)."""
    return LiftReader(path)


def open_writer(
    path: str | os.PathLike[str],
    *,
    header: Header | None = None,
    producer: str | None = None,
    ranges: RangesFile | None = None,
) -> LiftWriter:
    """Open a ``.lift`` file for streaming writes (bounded memory).

    If ``ranges`` is given, its companion ``.lift-ranges`` is written beside
    ``path`` on clean close, and matching ``<range href>`` references are added
    to ``header`` (created if absent) so the document points to the companion.
    """
    return LiftWriter(path, header=header, producer=producer, ranges=ranges)
