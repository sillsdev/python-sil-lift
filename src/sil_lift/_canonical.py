"""Canonical sort: a native implementation based on LiftSorter's rules.

The C# oracle — the reference implementation this sort is checked against
(libpalaso ``SIL.Lift/LiftSorter.cs`` @ 4840de8) — sorts entries by
case-insensitive guid, orders header children description → ranges → fields,
sorts ranges/range-elements by id and header field definitions by tag, keeps
senses in file order, and never re-indents ``text``/``span``. sil-lift mirrors
those rules, with two deliberately stricter than LiftSorter's and one looser:

- entries sort by (guid, id), both case-folded — files whose entries lack
  guids still sort deterministically (LiftSorter assumes a guid);
- output is byte-deterministic across runs and platforms (no locale-dependent
  collation: plain casefolded-codepoint ordering);
- within-type sibling lists other than the above (notes, relations, forms,
  ...) keep their document order — the canonical writer already groups them
  by type deterministically, and reordering them adds diff noise without
  determinism gains.

The reference ``canonicalizeLift.xsl`` is deliberately NOT used: it
whitespace-normalizes all text nodes (destructive to lexical data) and its
generated ids are session-specific.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ._model import Lexicon

if TYPE_CHECKING:
    import os

    from ._header import Header, Range
    from ._model import Entry, RangesFile

__all__ = ["canonicalize"]


def entry_sort_key(entry: Entry) -> tuple[str, str]:
    return ((entry.guid or "").casefold(), (entry.id or "").casefold())


def _sort_range(range_: Range) -> None:
    range_.elements.sort(key=lambda element: element.id.casefold())


def sort_header(header: Header) -> None:
    header.ranges.sort(key=lambda range_: range_.id.casefold())
    for range_ in header.ranges:
        _sort_range(range_)
    header.fields.sort(key=lambda definition: definition.tag.casefold())


def sort_lexicon(lexicon: Lexicon) -> None:
    lexicon.entries.sort(key=entry_sort_key)
    sort_header(lexicon.header)


def sort_ranges_file(ranges_file: RangesFile) -> None:
    ranges_file.ranges.sort(key=lambda range_: range_.id.casefold())
    for range_ in ranges_file.ranges:
        _sort_range(range_)


def canonicalize(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
    """Write a fully canonical copy of a ``.lift`` file: sorted entries and
    ranges, documented child grouping and attribute order, 2-space layout.

    Unlike :meth:`Lexicon.save`, the output is *entirely* re-serialized (no
    byte-preserving passthrough) — that is the point: two canonicalized files
    diff cleanly. Text content is never whitespace-normalized. The whole
    document is held in memory (sorting requires it; the C# oracle buffers too).

    No timestamp is generated either: sorting and reformatting change no entry's
    content, so nothing here is a modification to stamp. The output is a pure
    function of the input.

    Only the ``.lift`` file is written: companion ``.lift-ranges`` files are
    neither read nor rewritten (the source is loaded with
    ``resolve_ranges=False``). Sort a ranges file separately via
    :meth:`RangesFile.sort` + :meth:`RangesFile.save`. This differs from
    :meth:`Lexicon.save`, which writes every tracked companion.
    """
    from ._writer import canonical_document

    lexicon = Lexicon.load(src, resolve_ranges=False)
    sort_lexicon(lexicon)
    Path(dst).write_bytes(canonical_document(lexicon))
