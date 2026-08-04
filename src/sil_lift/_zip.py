"""Zip-packaged LIFT: read and write a LIFT folder as a ``.zip`` archive.

A LIFT package is just a zipped LIFT folder. Two layouts occur in the wild
(both produced and accepted by FieldWorks and The Combine): the files at the
archive root (``foo.lift`` beside ``WritingSystems/``, ``audio/``, ...), or
nested one level under a single folder (``Foo/foo.lift`` ...). This module
locates the single ``.lift`` member (its parent is the package root), extracts
to a temporary directory, and hands off to the ordinary path-based
reader/writer — so media resolution, companion discovery, and byte-fidelity all
work unchanged.

Streaming reads (:func:`lift_source`) extract that one member and nothing else:
they resolve neither companions nor media, so writing the rest of an
audio-heavy package to disk would cost gigabytes that nothing goes on to read.

The archive *container* is not byte-reproducible (zip carries timestamps,
compression, and ordering); the guarantee is at the file level — the ``.lift``
and ``.lift-ranges`` keep their fidelity contract, and every other packaged
file is carried through verbatim.
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from ._errors import LiftParseError
from ._model import Lexicon

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

__all__ = ["load_zip", "save_zip"]


# Guards against malicious archives. Audio makes real LIFT projects large, so
# the size ceiling is generous; the entry cap stops "millions of tiny files"
# archives that the size cap alone would miss.
_MAX_UNCOMPRESSED_BYTES = 10 * 1024**3  # 10 GiB
_MAX_ENTRIES = 100_000
_EXTRACT_CHUNK = 1 << 20  # 1 MiB


def _size_limit_message(zip_path: Path, member: str | None = None) -> str:
    """The size-cap refusal, for the package as a whole or for one member."""
    limit_gib = _MAX_UNCOMPRESSED_BYTES / 1024**3
    if member is None:
        return f"{zip_path.name}: uncompressed size exceeds the {limit_gib:.0f} GiB limit"
    return f"{zip_path.name}: {member!r} alone exceeds the {limit_gib:.0f} GiB limit"


def _select_lift_member(names: Iterable[str]) -> str:
    """The single ``.lift`` member of an archive listing; its parent is the root.

    Handles both the flat and folder-wrapped layouts, and ignores junk such as
    ``__MACOSX`` and dotfile entries that some zip tools add. One path stored
    twice counts once — some writers append a record rather than replace it,
    and extraction overwrites, so what lands on disk is a single file.

    The suffix match is case-insensitive, so a ``.LIFT`` member resolves the
    same way on every platform rather than only where the filesystem happens to
    case-fold. How such a name then finds its companion is not this layer's
    concern: it is the same question a case-variant ``.lift`` in a plain folder
    raises, and ``Lexicon._resolve_ranges`` is where it is answered.
    """
    lifts = list(
        dict.fromkeys(  # de-duplicate, preserving listing order
            name
            for name in names
            if name.lower().endswith(".lift")
            and not any(
                part == "__MACOSX" or part.startswith(".") for part in PurePosixPath(name).parts
            )
        )
    )
    if not lifts:
        raise LiftParseError("no .lift file found in the archive")
    if len(lifts) > 1:
        found = ", ".join(sorted(PurePosixPath(name).name for name in lifts))
        raise LiftParseError(f"multiple .lift files found in the archive: {found}")
    return lifts[0]


def _safe_extract(zip_path: Path, dest: Path, *, only_lift: bool = False) -> str:
    """Extract ``zip_path`` into ``dest``; returns the ``.lift`` member's name.

    Path-traversal members (``..`` or absolute, resolved against ``dest``) are
    rejected and the entry count is capped, both over the whole listing however
    much of it gets written. Bytes written are capped as they stream, since a
    crafted archive's declared size can lie.

    ``only_lift`` narrows the write to the ``.lift`` itself, which is all a
    streaming read needs. The aggregate declared-size check then has nothing to
    guard and is left to full extraction, so a decompression bomb of a ``.lift``
    is refused only once it has written ``_MAX_UNCOMPRESSED_BYTES`` — the same
    worst-case temp usage as a full extraction, reached by one member instead of
    the whole package.
    """
    dest_root = dest.resolve()
    try:
        with zipfile.ZipFile(zip_path) as archive:
            infos = archive.infolist()
            if len(infos) > _MAX_ENTRIES:
                raise LiftParseError(f"{zip_path.name}: archive has too many entries")
            for info in infos:
                if not (dest / info.filename).resolve().is_relative_to(dest_root):
                    raise LiftParseError(
                        f"{zip_path.name}: unsafe path in archive: {info.filename!r}"
                    )
            member = _select_lift_member(info.filename for info in infos)
            if only_lift:
                infos = [info for info in infos if info.filename == member]
            elif sum(info.file_size for info in infos) > _MAX_UNCOMPRESSED_BYTES:
                raise LiftParseError(_size_limit_message(zip_path))
            written = 0
            for info in infos:
                target = dest / info.filename
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("wb") as sink:
                    while chunk := source.read(_EXTRACT_CHUNK):
                        written += len(chunk)
                        if written > _MAX_UNCOMPRESSED_BYTES:
                            raise LiftParseError(
                                _size_limit_message(zip_path, info.filename if only_lift else None)
                            )
                        sink.write(chunk)
    except zipfile.BadZipFile as exc:
        raise LiftParseError(f"{zip_path.name}: not a valid zip archive: {exc}") from exc
    return member


@contextmanager
def lift_source(path: Path) -> Iterator[Path]:
    """Yield a ``.lift`` path for ``path``, extracting a ``.zip`` to a temp dir.

    A non-zip path is yielded unchanged. From a zip only the ``.lift`` member
    is extracted, for the duration of the ``with`` block — all a streaming
    caller reads, since it resolves neither companions nor media.
    """
    if path.suffix.lower() != ".zip":
        yield path
        return
    with tempfile.TemporaryDirectory(prefix="sil-lift-") as tmp:
        member = _safe_extract(path, Path(tmp), only_lift=True)
        yield Path(tmp) / member


def load_zip(path: Path, *, resolve_ranges: bool = True) -> Lexicon:
    """Load a zip-packaged LIFT folder (see :meth:`Lexicon.load`).

    The extraction directory is kept alive for the returned lexicon's lifetime
    (via :attr:`Lexicon._tempdir`), so media checks and :meth:`Lexicon.save_zip`
    can still reach the packaged files.
    """
    tmp = tempfile.TemporaryDirectory(prefix="sil-lift-")
    try:
        member = _safe_extract(path, Path(tmp.name))
        lexicon = Lexicon.load(Path(tmp.name) / member, resolve_ranges=resolve_ranges)
    except BaseException:
        tmp.cleanup()
        raise
    lexicon._tempdir = tmp
    return lexicon


def _resolve_wrap_folder(wrap_folder: str | bool, dest: Path) -> str | None:
    if isinstance(wrap_folder, str):
        return wrap_folder
    return dest.stem if wrap_folder else None


def save_zip(lexicon: Lexicon, dest: Path, *, wrap_folder: str | bool = True) -> None:
    """Write ``lexicon`` and its folder companions to the zip at ``dest``."""
    from ._writer import render_document, render_ranges_document

    folder = _resolve_wrap_folder(wrap_folder, dest)
    with tempfile.TemporaryDirectory(prefix="sil-lift-") as staging:
        content = Path(staging) / folder if folder else Path(staging)
        content.mkdir(parents=True, exist_ok=True)

        # Carry the whole source package through (media, WritingSystems, ...).
        source_root = lexicon.path.parent if lexicon.path is not None else None
        if source_root is not None and source_root.is_dir():
            shutil.copytree(source_root, content, dirs_exist_ok=True)

        # (Over)write the .lift and its companions with current, rendered bytes.
        lift_name = lexicon.path.name if lexicon.path is not None else f"{folder or 'lexicon'}.lift"
        (content / lift_name).write_bytes(render_document(lexicon))
        for key, ranges_file in lexicon.ranges_files.items():
            name = ranges_file.path.name if ranges_file.path is not None else Path(key).name
            (content / name).write_bytes(render_ranges_document(ranges_file))

        _write_zip(Path(staging), dest)


def _write_zip(root: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(root.rglob("*")):
            if item.is_file():
                archive.write(item, item.relative_to(root).as_posix())
