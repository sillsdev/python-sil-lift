"""Entry-side model: Entry, Sense, and everything below them, plus Lexicon.

Shapes follow the LIFT 0.13 RELAX NG (RNG) inventory exactly. Extensibility is
a three-way split: the eight fully-extensible elements derive from
``_Extensible``; the usage ``<field>`` gets the field-less variant
``_ExtensibleNoFields`` (no field-in-field recursion); ``GrammaticalInfo`` is
the exception, with bare traits only. Typed attributes that fail to parse
(malformed dates/integers in real-world files) are preserved verbatim in the
node's ``extra`` and the model field stays ``None``.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING

from ._extras import Extras
from ._header import Header, Range
from ._text import Annotation, Form, Multitext, Text, Trait

if TYPE_CHECKING:
    import os
    import tempfile
    from collections.abc import Iterator
    from typing import Literal

    from ._validate import Problem
    from ._writer import _RangesSourceInfo, _SourceInfo

__all__ = [
    "Changes",
    "Entry",
    "Etymology",
    "Example",
    "Field",
    "GrammaticalInfo",
    "Lexicon",
    "MediaRef",
    "Note",
    "Pronunciation",
    "RangesChanges",
    "RangesFile",
    "Relation",
    "Reversal",
    "ReversalMain",
    "Sense",
    "Translation",
    "URLRef",
    "Variant",
]


@dataclass(slots=True, kw_only=True)
class _ExtensibleNoFields:
    """The extensible fields minus ``<field>``: dates, annotations, traits, LIFT residue."""

    date_created: datetime | date | None = None
    date_modified: datetime | date | None = None
    annotations: list[Annotation] = field(default_factory=list)
    traits: list[Trait] = field(default_factory=list)
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True, kw_only=True)
class _Extensible(_ExtensibleNoFields):
    """The full set of extensible fields (entry, sense, note, example, ...)."""

    fields: list[Field] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class Field(_ExtensibleNoFields):
    """An entry-level usage ``<field type=...>`` (extensible, but no nested field)."""

    type: str
    content: Multitext = field(default_factory=Multitext)


@dataclass(slots=True)
class GrammaticalInfo:
    """A ``<grammatical-info value=...>``; the extensibility exception — traits only, no fields."""

    value: str
    traits: list[Trait] = field(default_factory=list)
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True)
class URLRef:
    """A ``<media>`` or ``<illustration>``: an href with an optional label."""

    href: str
    label: Multitext = field(default_factory=Multitext)
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True, kw_only=True)
class Translation:
    """A ``<translation>`` of an example (not extensible)."""

    type: str | None = None
    forms: Multitext = field(default_factory=Multitext)
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True, kw_only=True)
class Note(_Extensible):
    """A ``<note>``; sibling notes conventionally have distinct types."""

    type: str | None = None
    forms: Multitext = field(default_factory=Multitext)


@dataclass(slots=True, kw_only=True)
class Example(_Extensible):
    """An ``<example>`` under a sense."""

    source: str | None = None
    forms: Multitext = field(default_factory=Multitext)
    translations: list[Translation] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class Relation(_Extensible):
    """A ``<relation type=... ref=...>`` cross-reference to another entry/sense."""

    type: str
    ref: str
    order: int | None = None
    usage: Multitext = field(default_factory=Multitext)


@dataclass(slots=True, kw_only=True)
class Etymology(_Extensible):
    """An ``<etymology type=... source=...>``; each gloss carries its own lang."""

    type: str
    source: str
    forms: Multitext = field(default_factory=Multitext)
    glosses: list[Form] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class ReversalMain:
    """A reversal ``<main>``: the parent node in a reversal-index chain (recursive)."""

    forms: Multitext = field(default_factory=Multitext)
    main: ReversalMain | None = None
    grammatical_info: GrammaticalInfo | None = None
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True, kw_only=True)
class Reversal:
    """A ``<reversal>`` index entry (not extensible)."""

    type: str | None = None
    forms: Multitext = field(default_factory=Multitext)
    main: ReversalMain | None = None
    grammatical_info: GrammaticalInfo | None = None
    extra: Extras = field(default_factory=Extras)


@dataclass(slots=True, kw_only=True)
class Pronunciation(_Extensible):
    """A ``<pronunciation>`` with optional ``<media>`` references."""

    forms: Multitext = field(default_factory=Multitext)
    media: list[URLRef] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class Variant(_Extensible):
    """A ``<variant>``: an inline variant form and/or a ``ref`` cross-reference."""

    ref: str | None = None
    forms: Multitext = field(default_factory=Multitext)
    pronunciations: list[Pronunciation] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class Sense(_Extensible):
    """A ``<sense>`` (or ``<subsense>`` — same content model, recursive)."""

    id: str | None = None
    order: int | None = None
    grammatical_info: GrammaticalInfo | None = None
    glosses: list[Form] = field(default_factory=list)
    definition: Multitext = field(default_factory=Multitext)
    relations: list[Relation] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    examples: list[Example] = field(default_factory=list)
    reversals: list[Reversal] = field(default_factory=list)
    illustrations: list[URLRef] = field(default_factory=list)
    subsenses: list[Sense] = field(default_factory=list)

    def gloss(self, lang: str) -> Text | None:
        """The gloss text in ``lang``, or None (first match; each ``<gloss>`` has its own lang)."""
        for gloss_form in self.glosses:
            if gloss_form.lang == lang:
                return gloss_form.text
        return None


@dataclass(slots=True, kw_only=True)
class Entry(_Extensible):
    """An ``<entry>``. A set ``date_deleted`` marks it deleted (a tombstone)."""

    id: str | None = None
    guid: str | None = None
    order: int | None = None
    date_deleted: datetime | date | None = None
    lexical_unit: Multitext = field(default_factory=Multitext)
    citation: Multitext = field(default_factory=Multitext)
    pronunciations: list[Pronunciation] = field(default_factory=list)
    variants: list[Variant] = field(default_factory=list)
    senses: list[Sense] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)
    etymologies: list[Etymology] = field(default_factory=list)

    def gloss_langs(self) -> set[str]:
        """Every language that has a gloss in any sense or subsense."""
        langs: set[str] = set()
        stack = list(self.senses)
        while stack:
            sense = stack.pop()
            langs.update(g.lang for g in sense.glosses if g.lang is not None)
            stack.extend(sense.subsenses)
        return langs


@dataclass(slots=True)
class MediaRef:
    """One media reference in the document, with its owner's identity."""

    href: str
    kind: Literal["media", "illustration"]
    entry_id: str | None
    entry_guid: str | None
    sense_id: str | None = None  # set for illustrations (they live on senses)


@dataclass(slots=True)
class RangesChanges:
    """What differs between a companion ``.lift-ranges`` and the file it was read from.

    ``baseline`` is False when no byte snapshot was captured (a companion built
    from scratch, or a source the byte scanner declined to read). Nothing
    can be compared then, so the fields say what :meth:`RangesFile.save` will
    write rather than what differs: ``ranges`` lists everything, while
    ``added``, ``removed``, and ``root`` stay empty or False — nothing is known
    to have been there before. The object is truthy either way: the file will
    be written in full.

    ``ranges`` names each range once, even one aliased into the list twice;
    against a baseline the repeat is reported by ``added``, and without one it
    is not reported at all, though :meth:`RangesFile.save` still writes it.
    ``reordered`` answers only where the same ranges are still present, as on
    :class:`Changes`.
    """

    ranges: list[Range]  # content differs from the source
    added: list[Range]
    removed: list[Range]
    reordered: bool  # same ranges, different order
    root: bool  # root attributes or root-level LIFT residue
    baseline: bool

    def __bool__(self) -> bool:
        return (
            not self.baseline
            or bool(self.ranges or self.added or self.removed)
            or self.reordered
            or self.root
        )


@dataclass(slots=True)
class Changes:
    """Everything that differs between a lexicon and the document it was loaded from.

    Falsy only when :meth:`Lexicon.save` would reproduce the source bytes,
    which makes it the correct guard for skipping an in-place write —
    :meth:`Lexicon.changed_entries` alone is not, since it covers only entry
    content.

    The guarantee is one-way. Every condition that sends the writer down its
    canonical path is reported here, so a falsy result is never a wrong
    "nothing to write"; but that path can land back on the source bytes for a
    document already in canonical form, so a truthy result means the write is
    not provably unnecessary rather than certainly needed.

    ``reordered`` answers only where the same entries are still present. An
    addition or a removal re-serializes the document on its own, so a
    reordering alongside one is not reported separately — enough for the guard,
    short of a full account of what happened.

    ``baseline`` is False when no byte snapshot was captured. Nothing can be
    compared then, so the fields say what :meth:`Lexicon.save` will write
    rather than what differs: ``entries`` lists every entry and ``header`` is
    True if there is a header to emit, while ``added``, ``removed``, and
    ``root`` stay empty or False — nothing is known to have been there before.
    The object is truthy either way.
    """

    entries: list[Entry]  # content differs from the source
    added: list[Entry]
    removed: list[Entry]
    reordered: bool  # same entries, different order
    header: bool
    root: bool  # producer, root attributes, or root-level LIFT residue
    ranges: dict[Path, RangesChanges]  # keyed by companion; ranges live in several files
    baseline: bool

    def __bool__(self) -> bool:
        return (
            not self.baseline
            or bool(self.entries or self.added or self.removed)
            or self.reordered
            or self.header
            or self.root
            or any(self.ranges.values())
        )


class RangesFile:
    """A standalone ``.lift-ranges`` document (root ``<lift-ranges>``)."""

    __slots__ = ("_source", "extra", "path", "ranges")

    def __init__(
        self,
        *,
        ranges: list[Range] | None = None,
        path: Path | None = None,
        extra: Extras | None = None,
    ) -> None:
        self.ranges = ranges if ranges is not None else []
        self.path = path
        self.extra = extra if extra is not None else Extras()
        self._source: _RangesSourceInfo | None = None

    @classmethod
    def load(cls, path: str | os.PathLike[str]) -> RangesFile:
        from ._reader import parse_ranges_document

        return parse_ranges_document(Path(path))

    def save(self, path: str | os.PathLike[str] | None = None) -> None:
        """Write the ``.lift-ranges`` file (byte-identical when unchanged).

        Raises :class:`ValueError` if no target path is available (none was
        passed and the file was not loaded from disk).
        """
        from ._writer import render_ranges_document

        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("no target path: pass save(path) or load the file from disk")
        target.write_bytes(render_ranges_document(self))
        self.path = target

    def find(self, id: str) -> Range | None:
        for range_ in self.ranges:
            if range_.id == id:
                return range_
        return None

    def add_range(self, id: str, *, href: str | None = None, guid: str | None = None) -> Range:
        """Append a new :class:`Range` to this file and return it.

        Populate its values with :meth:`Range.add_element`.
        """
        range_ = Range(id=id, href=href, guid=guid)
        self.ranges.append(range_)
        return range_

    def sort(self) -> None:
        """Sort ranges and their elements into canonical (id) order."""
        from ._canonical import sort_ranges_file

        sort_ranges_file(self)

    def changes(self) -> RangesChanges:
        """Everything that differs between this companion and the file it was read from.

        Falsy only when :meth:`save` would reproduce the source bytes, one-way
        in the same safe direction as :class:`Changes`. Costs one canonical
        serialization pass over the ranges.
        """
        from ._writer import node_diff, range_digest

        source = self._source
        # Keyed by identity: a range aliased into the list twice is one range.
        unique = list({id(range_): range_ for range_ in self.ranges}.values())
        if source is None:
            return RangesChanges(
                ranges=unique,
                added=[],
                removed=[],
                reordered=False,
                root=False,
                baseline=False,
            )
        digests = {id(record.range): record.digest for record in source.range_records}
        added, removed, reordered = node_diff(
            [id(range_) for range_ in self.ranges],
            [id(record.range) for record in source.range_records],
        )
        return RangesChanges(
            ranges=[
                range_
                for range_ in unique
                if (digest := digests.get(id(range_))) is not None
                and range_digest(range_) != digest
            ],
            added=[self.ranges[index] for index in added],
            removed=[source.range_records[index].range for index in removed],
            reordered=reordered,
            root=(
                dict(self.extra._attrs) != source.root_extra_attrs
                or self.extra._nodes != source.root_extra_snapshot._nodes
            ),
            baseline=True,
        )

    def __repr__(self) -> str:
        source = f", path={str(self.path)!r}" if self.path else ""
        return f"RangesFile({len(self.ranges)} ranges{source})"


def _normalize_href(href: str) -> Path | None:
    """A relative filesystem path for an href, or None if it isn't one.

    Real-world hrefs use backslashes and literal spaces (WeSay) or dangling
    absolute ``file://C:/...`` URIs from the exporting machine (FLEx) — for
    the latter, only the basename is meaningful.
    """
    if "://" in href or href.startswith(("http:", "https:", "file:")):
        return None
    normalized = href.replace("\\", "/")
    # Absolute under either OS convention, independent of the host: PurePosixPath
    # catches "/abs", PureWindowsPath catches a drive-letter "C:/..." — each
    # reports the other's form as relative, misjudging hrefs on the opposite host.
    if PurePosixPath(normalized).is_absolute() or PureWindowsPath(normalized).is_absolute():
        return None
    return Path(normalized)


def _fold(text: str) -> str:
    """A filename reduced to what a case-folding filesystem treats as one name.

    ``casefold`` for what ``lower`` gets wrong (the Turkish dotless i), NFC
    because FLEx mixes normalization forms within one export. An approximation
    of NTFS's and APFS's tables, not a general equivalence.
    """
    return unicodedata.normalize("NFC", text).casefold()


def _existing_file(candidate: Path, listings: dict[Path, dict[str, Path]]) -> Path | None:
    """``candidate`` if it is a file, else one whose name folds onto it.

    LIFT folders are written on Windows, where the filesystem folds case, and
    read everywhere: ``Dict.LIFT`` beside ``Dict.lift-ranges`` resolves there
    and, before this fallback, silently did not on a case-sensitive filesystem.

    Only the final component folds — the hrefs this serves are basenames or
    same-folder relatives — and only after the exact name misses, so a
    case-folding filesystem never reaches this. Among names that fold together
    the first in code point order wins: arbitrary, but stable across runs and
    platforms, which directory order is not. ``listings`` caches one directory
    read per folder.
    """
    try:
        if candidate.is_file():
            return candidate
    except OSError:
        pass  # unstattable exact spelling: a case variant of it may still stat
    folder = candidate.parent
    if folder not in listings:
        files: dict[str, Path] = {}
        try:
            # By name, not by Path: PurePath ordering is case-folded on Windows,
            # which would leave the tie-break to directory order there.
            for path in sorted(folder.iterdir(), key=lambda entry: entry.name):
                if path.is_file():
                    files.setdefault(_fold(path.name), path)
        except OSError:
            pass  # unreadable folder: no candidate resolves out of it
        listings[folder] = files
    return listings[folder].get(_fold(candidate.name))


def _same_file(left: Path, right: Path) -> bool:
    """Whether two paths that fold together denote one file.

    ``Path.resolve()`` canonicalizes case on Windows but not on macOS, where
    one file reached under two spellings yields two keys — tracked twice, and
    written twice by :meth:`Lexicon.save`. The fold pre-check keeps the inode
    comparison from conflating distinct files where ``st_ino`` is 0.
    """
    if _fold(str(left)) != _fold(str(right)):
        return False
    try:
        return left.samefile(right)
    except OSError:
        return False


def _same_dir(left: Path, right: Path | None) -> bool:
    """Whether two paths denote the same directory, spelling aside.

    ``Path`` equality is textual, so a relative target and an absolute load
    path compare unequal even when they name one directory; resolving first
    also collapses ``..`` and symlinks.
    """
    if right is None:
        return False
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return left == right


class Lexicon:
    """The root handle: a parsed ``.lift`` document and its folder companions."""

    __slots__ = (
        "_source",
        "_tempdir",
        "entries",
        "extra",
        "header",
        "path",
        "producer",
        "ranges_files",
    )

    def __init__(
        self,
        *,
        header: Header | None = None,
        entries: list[Entry] | None = None,
        producer: str | None = None,
        path: Path | None = None,
        extra: Extras | None = None,
    ) -> None:
        self.header = header if header is not None else Header()
        self.entries = entries if entries is not None else []
        self.producer = producer
        self.path = path
        self.extra = extra if extra is not None else Extras()
        self.ranges_files: dict[Path, RangesFile] = {}
        self._source: _SourceInfo | None = None  # set by the reader
        self._tempdir: tempfile.TemporaryDirectory[str] | None = None  # zip extraction, if any

    @classmethod
    def load(cls, path: str | os.PathLike[str], *, resolve_ranges: bool = True) -> Lexicon:
        """Parse a ``.lift`` file (LIFT 0.13 only) into a full object graph.

        With ``resolve_ranges`` (the default), companion ``.lift-ranges``
        files are loaded and tracked in :attr:`ranges_files`. Several
        candidates are tried and every one that exists is loaded: the
        conventional ``<name>.lift-ranges`` sibling, and for each header
        ``range/@href`` both the href resolved as a path relative to the
        ``.lift`` file and its bare basename in the same directory (FLEx
        hrefs are usually dangling absolute ``file://C:/...`` paths from the
        exporting machine, so the basename is what resolves locally). A
        candidate that no file matches exactly still resolves to a file whose
        name differs only in case or Unicode normalization, so a folder
        authored on Windows loads the same way on a case-sensitive filesystem.
        The ``.lift`` itself is never taken as its own companion.

        A ``.zip`` path is treated as a packaged LIFT folder: it is extracted
        to a temporary directory (kept alive for the returned lexicon's
        lifetime) and the single contained ``.lift`` is loaded.
        """
        source = Path(path)
        if source.suffix.lower() == ".zip":
            from ._zip import load_zip

            return load_zip(source, resolve_ranges=resolve_ranges)
        from ._reader import parse_document

        lexicon = parse_document(source)
        if resolve_ranges:
            lexicon._resolve_ranges()
        return lexicon

    def _resolve_ranges(self) -> None:
        if self.path is None:
            return
        base = self.path.parent
        try:
            own = self.path.resolve()
        except OSError:
            own = self.path
        candidates: list[Path] = []
        # with_name, not with_suffix: they agree on every name that has an
        # extension, but with_suffix rejects "-ranges" outright on a name
        # without one, and nothing upstream requires the document to be named
        # ``.lift`` — parse_document never looks at the extension.
        candidates.append(self.path.with_name(self.path.name + "-ranges"))
        for range_ in self.header.ranges:
            if range_.href is None:
                continue
            relative = _normalize_href(range_.href)
            if relative is not None:
                candidates.append(base / relative)
            basename = range_.href.replace("\\", "/").rpartition("/")[2]
            if basename:
                candidates.append(base / basename)
        listings: dict[Path, dict[str, Path]] = {}
        for candidate in candidates:
            found = _existing_file(candidate, listings)
            if found is None:
                continue
            try:
                resolved = found.resolve()
            except OSError:
                continue
            # Skip a spelling of something already tracked (macOS keeps two
            # keys for one file) and the .lift itself, which a header href
            # naming it in another case now folds onto — RangesFile.load would
            # reject its root and take the whole load down with it.
            if resolved in self.ranges_files or any(
                _same_file(resolved, other) for other in (own, *self.ranges_files)
            ):
                continue
            self.ranges_files[resolved] = RangesFile.load(found)

    def save(self, path: str | os.PathLike[str] | None = None) -> None:
        """Write the ``.lift`` file and every tracked ``.lift-ranges`` companion.

        Untouched entries are emitted byte-identical to the source; modified
        entries are re-serialized canonically with all residue preserved.
        With no ``path``, saves to where the lexicon was loaded from. When
        saving into a different directory, companions are written next to the
        new ``.lift`` file under their original basenames. Saving under a new
        name in the *same* directory leaves companions at their original
        paths (they are shared with the original document, not copied).

        Raises :class:`ValueError` if no target path is available (none was
        passed and the lexicon was not loaded from a file).
        """
        from ._writer import render_document

        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("no target path: pass save(path) or load the lexicon from a file")
        original_dir = self.path.parent if self.path is not None else None
        target.write_bytes(render_document(self))
        self.path = target
        relocating = not _same_dir(target.parent, original_dir)
        for key, ranges_file in self.ranges_files.items():
            if ranges_file.path is None:
                # A from-scratch companion (see add_ranges_file): the dict key
                # is its intended href — write it beside the saved .lift.
                ranges_file.save(target.parent / Path(key).name)
            elif relocating:
                ranges_file.save(target.parent / ranges_file.path.name)
            else:
                ranges_file.save()
        # Keys must keep tracking the companions' current locations.
        self.ranges_files = {
            ranges_file.path.resolve(): ranges_file
            for ranges_file in self.ranges_files.values()
            if ranges_file.path is not None
        }

    def save_zip(self, path: str | os.PathLike[str], *, wrap_folder: str | bool = True) -> None:
        """Write the lexicon and its folder companions as a zip package.

        The ``.lift`` and ``.lift-ranges`` are (re-)serialized with the usual
        fidelity (untouched entries byte-identical); any other files from the
        source package (media, ``WritingSystems/``, ``consent/``, ...) are
        carried through verbatim. ``wrap_folder`` controls the layout: ``True``
        (default) nests everything under a folder named after the zip — the
        convention FieldWorks and The Combine expect on import — ``False``
        writes the files at the archive root, and a string uses that folder
        name. The archive container itself is not byte-reproducible.
        """
        from ._zip import save_zip

        save_zip(self, Path(path), wrap_folder=wrap_folder)

    def sort(self) -> None:
        """Sort into canonical order, in place: entries by (guid, id), header
        ranges/range-elements by id, field definitions by tag.

        Sorting alone does not mark entries as modified — a subsequent
        :meth:`save` still emits untouched entries byte-identically, just in
        the new order. For fully re-serialized diff-ready output use
        :func:`sil_lift.canonicalize`.
        """
        from ._canonical import sort_lexicon

        sort_lexicon(self)

    def changed_entries(self) -> list[Entry]:
        """Entries currently in the lexicon whose content differs from the document as loaded.

        An entry's digest covers its whole subtree, so an edit at any depth —
        a gloss on a nested subsense included — reports the containing entry.
        Assigning a field the value it already had reports nothing, and neither
        does reordering (see :meth:`sort`).

        The comparison is always against the document as loaded, never against
        the most recent :meth:`save`, so an entry stays reported once changed.

        Content changes only. Entries added since loading are reported by
        :meth:`added_entries` and removed ones by :meth:`removed_entries`; for
        everything that makes :meth:`save` differ from the source — including
        the header, the ranges companions, and the root element — use
        :meth:`changes`. An empty result here does not mean the document would
        round-trip byte-identically.

        One report per entry, not per occurrence: an entry aliased into the
        list twice is named once here, so a count of this list is a count of
        entries. Against a baseline the repeat is an addition (see
        :meth:`added_entries`), which accounts for every occurrence exactly
        once; without a baseline, nothing is reported as added, so the repeat
        goes unnamed even though :meth:`save` writes it.

        Every entry is reported when there is no byte baseline to compare
        against — a lexicon built from scratch, and equally one whose source the
        byte scanner declined to read (an encoding that is not ASCII-compatible,
        or a scanner/parser disagreement). Both re-serialize in full on
        :meth:`save`, so those entries genuinely are rewritten.

        Costs one canonical serialization pass over the entries.
        """
        from ._writer import entry_digest

        source = self._source
        # Keyed by identity: an entry aliased into the list twice is one entry.
        entries = list({id(entry): entry for entry in self.entries}.values())
        if source is None:
            return entries
        digests = {id(record.entry): record.digest for record in source.entry_records}
        return [
            entry
            for entry in entries
            if (digest := digests.get(id(entry))) is not None and entry_digest(entry) != digest
        ]

    def _entry_diff(self) -> tuple[list[Entry], list[Entry], bool]:
        """Added entries, removed entries, and whether the survivors were reordered."""
        from ._writer import node_diff

        source = self._source
        if source is None:
            return [], [], False
        added, removed, reordered = node_diff(
            [id(entry) for entry in self.entries],
            [id(record.entry) for record in source.entry_records],
        )
        return (
            [self.entries[index] for index in added],
            [source.entry_records[index].entry for index in removed],
            reordered,
        )

    def added_entries(self) -> list[Entry]:
        """Entries in the lexicon that were not in the loaded document.

        An entry the document already held, appended a second time, counts as
        an addition too: the list gained an occurrence, and :meth:`save` writes
        the entry out twice.

        Empty when there is no byte baseline: nothing is known to be new, since
        nothing is known to have been there before. Needs no serialization.
        """
        return self._entry_diff()[0]

    def removed_entries(self) -> list[Entry]:
        """Entries from the loaded document that are no longer in the lexicon.

        The entry objects survive because the parse-time records hold them, so
        a removed entry is returned intact rather than merely counted.

        The mirror of the addition rule: an entry aliased into the list twice
        is removed only once no occurrence is left. Dropping just one leaves
        the list reordered, or unchanged if what went was the repeat.

        Empty when there is no byte baseline. Needs no serialization.
        """
        return self._entry_diff()[1]

    def _header_changed(self) -> bool:
        from ._writer import header_digest

        source = self._source
        if source is None or source.header_digest is None:
            # No header in the source: only a non-empty one now is a change,
            # matching what render_document emits.
            return bool(self.header)
        return header_digest(self.header) != source.header_digest

    def _root_changed(self) -> bool:
        source = self._source
        if source is None:
            return False
        return (
            self.producer != source.producer
            or dict(self.extra._attrs) != source.root_extra_attrs
            or self.extra._nodes != source.root_extra_snapshot._nodes
        )

    def changes(self) -> Changes:
        """Everything that differs between this lexicon and the document it was loaded from.

        Falsy only when :meth:`save` would reproduce the source bytes, which
        makes it the correct guard for skipping an in-place write::

            if not lex.changes():
                return

        One-way, and in the safe direction — see :class:`Changes`.

        Content only, so it says nothing about the destination: a ``save(path)``
        into another directory writes the document and its companions there
        whatever this reports, and skipping that is a lost copy, not a saved
        one. Never guard :meth:`save_zip` with it — that has no in-place form,
        its archive is never byte-reproducible, and it carries package files
        (media, ``WritingSystems/``, ...) that nothing here inspects.

        The most expensive query here: it serializes the entries, the header,
        and every tracked companion's ranges. When only one part is wanted,
        :meth:`changed_entries`, :meth:`added_entries`, and
        :meth:`removed_entries` answer individually, and the latter two need no
        serialization at all.

        It is not a shortcut around :meth:`save` — it costs more than the save
        it guards. Deciding which source bytes can be reused digests every entry
        again, and nothing is cached between the two calls, so guarding a write
        that turns out to be needed roughly doubles the work. What the guard
        buys is not writing: an unchanged file-modification time, no spurious
        diff, nothing downstream woken up.
        """
        added, removed, reordered = self._entry_diff()
        return Changes(
            entries=self.changed_entries(),
            added=added,
            removed=removed,
            reordered=reordered,
            header=self._header_changed(),
            root=self._root_changed(),
            ranges={path: file.changes() for path, file in self.ranges_files.items()},
            baseline=self._source is not None,
        )

    def iter_problems(self, *, require_ids: bool = False) -> Iterator[Problem]:
        """Validate the in-memory state (schema layers + semantic checks).

        The schema layers need serialized bytes: what :meth:`save` would
        write is validated, so in-memory edits are always visible. For an
        untouched loaded document those are the source bytes (line numbers
        match the file on disk); otherwise serialization is a documented
        cost on large lexicons.

        With ``require_ids``, entries missing a ``guid`` and senses missing an
        ``id`` are reported as ``missing-id`` errors — stricter than LIFT (both
        are optional there), for workflows that re-import by a stable id.
        """
        from ._validate import iter_lexicon_problems

        return iter_lexicon_problems(self, require_ids=require_ids)

    def all_ranges(self) -> dict[str, Range]:
        """Inline and external ranges, merged by id.

        An inline header range that enumerates its own elements wins;
        otherwise the external definition (from any tracked ranges file) is
        used. External ranges never referenced by the header are included too.
        """
        merged: dict[str, Range] = {}
        for ranges_file in self.ranges_files.values():
            for range_ in ranges_file.ranges:
                merged.setdefault(range_.id, range_)
        for range_ in self.header.ranges:
            if range_.elements or range_.id not in merged:
                merged[range_.id] = range_
        return merged

    def add_ranges_file(self, ranges_file: RangesFile | None = None, *, href: str) -> RangesFile:
        """Attach a companion ``.lift-ranges`` document so :meth:`save` writes it.

        For every range already in ``ranges_file`` that the header does not
        list, a ``<range id=... href=...>`` reference is added to the header so
        LIFT consumers can find the companion. ``href`` is the reference as
        written in the header — normally a filename beside the ``.lift`` (e.g.
        ``"mydict.lift-ranges"``); the companion is written next to the saved
        ``.lift`` under that basename. Populate the companion before calling
        (or call again to reference ranges added later).

        Returns the attached (or newly created) :class:`RangesFile`.
        """
        if ranges_file is None:
            ranges_file = RangesFile()
        referenced = {range_.id for range_ in self.header.ranges}
        for range_ in ranges_file.ranges:
            if range_.id not in referenced:
                self.header.ranges.append(Range(id=range_.id, href=href))
                referenced.add(range_.id)
        self.ranges_files[Path(href)] = ranges_file
        return ranges_file

    def media_refs(self) -> Iterator[MediaRef]:
        """Every ``<media>`` and ``<illustration>`` reference, with its owner."""
        for entry in self.entries:
            pronunciations = list(entry.pronunciations)
            for variant in entry.variants:
                pronunciations.extend(variant.pronunciations)
            for pronunciation in pronunciations:
                for media in pronunciation.media:
                    yield MediaRef(media.href, "media", entry.id, entry.guid)
            stack = list(entry.senses)
            while stack:
                sense = stack.pop()
                for illustration in sense.illustrations:
                    yield MediaRef(
                        illustration.href, "illustration", entry.id, entry.guid, sense.id
                    )
                stack.extend(sense.subsenses)

    def missing_media(self) -> list[MediaRef]:
        """Media references whose files don't exist in the LIFT folder layout.

        A relative href is checked as given (backslashes normalized) and under
        the conventional subfolder (``audio/`` for media, ``pictures/`` for
        illustrations). Remote/absolute hrefs can't be checked and are skipped.
        """
        if self.path is None:
            return []
        base = self.path.parent
        subfolder = {"media": "audio", "illustration": "pictures"}
        missing = []
        for ref in self.media_refs():
            relative = _normalize_href(ref.href)
            if relative is None:
                continue
            candidates = [base / relative, base / subfolder[ref.kind] / relative]
            if not any(candidate.is_file() for candidate in candidates):
                missing.append(ref)
        return missing

    def find(self, *, id: str | None = None, guid: str | None = None) -> Entry | None:
        """The first entry matching the given id and/or guid, or None.

        Raises :class:`ValueError` if neither ``id`` nor ``guid`` is given.
        """
        if id is None and guid is None:
            raise ValueError("find() needs id= and/or guid=")
        for entry in self.entries:
            if (id is None or entry.id == id) and (guid is None or entry.guid == guid):
                return entry
        return None

    def __repr__(self) -> str:
        source = f", path={str(self.path)!r}" if self.path else ""
        return f"Lexicon({len(self.entries)} entries{source})"
