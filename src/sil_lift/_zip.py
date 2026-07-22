"""Zip-packaged LIFT: read and write a LIFT folder as a ``.zip`` archive.

A LIFT package is just a zipped LIFT folder. Two layouts occur in the wild
(both produced and accepted by FieldWorks and The Combine): the files at the
archive root (``foo.lift`` beside ``WritingSystems/``, ``audio/``, ...), or
nested one level under a single folder (``Foo/foo.lift`` ...). This module
extracts to a temporary directory, locates the single ``.lift`` (its parent is
the package root), and hands off to the ordinary path-based reader/writer — so
media resolution, companion discovery, and byte-fidelity all work unchanged.

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
from pathlib import Path
from typing import TYPE_CHECKING

from ._errors import LiftParseError
from ._model import Lexicon

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = ["load_zip", "save_zip"]


# Guards against malicious archives. Audio makes real LIFT projects large, so
# the size ceiling is generous; the entry cap stops "millions of tiny files"
# archives that the size cap alone would miss.
_MAX_UNCOMPRESSED_BYTES = 10 * 1024**3  # 10 GiB
_MAX_ENTRIES = 100_000
_EXTRACT_CHUNK = 1 << 20  # 1 MiB


def _size_limit_message(zip_path: Path) -> str:
    limit_gib = _MAX_UNCOMPRESSED_BYTES / 1024**3
    return f"{zip_path.name}: uncompressed size exceeds the {limit_gib:.0f} GiB limit"


def _safe_extract(zip_path: Path, dest: Path) -> None:
    """Extract ``zip_path`` into ``dest``, defending against malicious archives.

    Path-traversal members (``..`` or absolute, resolved against ``dest``) are
    rejected, the entry count is capped, and the total uncompressed size is
    capped at ``_MAX_UNCOMPRESSED_BYTES`` — checked against the declared sizes
    up front, then again while streaming each member to disk, since a crafted
    archive's declared size can lie.
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
            if sum(info.file_size for info in infos) > _MAX_UNCOMPRESSED_BYTES:
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
                            raise LiftParseError(_size_limit_message(zip_path))
                        sink.write(chunk)
    except zipfile.BadZipFile as exc:
        raise LiftParseError(f"{zip_path.name}: not a valid zip archive: {exc}") from exc


def _find_lift_root(tree: Path) -> Path:
    """The single ``.lift`` file in an extracted tree; its parent is the root.

    Handles both the flat and folder-wrapped layouts, and ignores junk such as
    ``__MACOSX`` and dotfile entries that some zip tools add.
    """
    lifts = [
        p
        for p in tree.rglob("*.lift")
        if p.is_file()
        and not any(
            part == "__MACOSX" or part.startswith(".") for part in p.relative_to(tree).parts
        )
    ]
    if not lifts:
        raise LiftParseError("no .lift file found in the archive")
    if len(lifts) > 1:
        names = ", ".join(sorted(p.name for p in lifts))
        raise LiftParseError(f"multiple .lift files found in the archive: {names}")
    return lifts[0]


@contextmanager
def lift_source(path: Path) -> Iterator[Path]:
    """Yield a ``.lift`` path for ``path``, extracting a ``.zip`` to a temp dir.

    A non-zip path is yielded unchanged. A zip is extracted for the duration of
    the ``with`` block, then removed — for streaming callers that only read.
    """
    if path.suffix.lower() != ".zip":
        yield path
        return
    with tempfile.TemporaryDirectory(prefix="sil-lift-") as tmp:
        _safe_extract(path, Path(tmp))
        yield _find_lift_root(Path(tmp))


def load_zip(path: Path, *, resolve_ranges: bool = True) -> Lexicon:
    """Load a zip-packaged LIFT folder (see :meth:`Lexicon.load`).

    The extraction directory is kept alive for the returned lexicon's lifetime
    (via :attr:`Lexicon._tempdir`), so media checks and :meth:`Lexicon.save_zip`
    can still reach the packaged files.
    """
    tmp = tempfile.TemporaryDirectory(prefix="sil-lift-")
    try:
        _safe_extract(path, Path(tmp.name))
        lift_path = _find_lift_root(Path(tmp.name))
        lexicon = Lexicon.load(lift_path, resolve_ranges=resolve_ranges)
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
