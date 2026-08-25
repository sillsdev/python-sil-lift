"""The ``sil-lift`` command line: validate / stats / sort / check-media / export.

A utility in the spirit of LiftTools, exercising every major capability
end-to-end: validation (all three layers), streaming reads (stats, export), the
canonical sort + write path (sort), and the folder/media model (check-media).
Deliberately stdlib-only.

``validate`` is a supported interface for automation: its exit codes and
``--format json`` schema are covered by tests and change only under SemVer.
"""

from __future__ import annotations

import argparse
import codecs
import csv
import io
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

from ._canonical import canonicalize
from ._errors import LiftError
from ._model import Lexicon, _normalize_href
from ._stream import open_reader
from ._validate import iter_problems

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from typing import BinaryIO, TextIO

    from ._model import Entry, Sense
    from ._text import Text
    from ._validate import Problem

__all__ = ["main"]


def _problem_json(problem: Problem) -> dict[str, object]:
    return {
        "level": problem.level,
        "code": problem.code,
        "message": problem.message,
        "file": problem.file.name if problem.file else None,
        "entry_id": problem.entry_id,
        "guid": problem.guid,
        "line": problem.line,
    }


def _collect_problems(args: argparse.Namespace) -> list[Problem]:
    if str(args.path) == "-":
        data = sys.stdin.buffer.read()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_file = Path(tmp) / "stdin.lift"
            tmp_file.write_bytes(data)
            # A piped document has no folder context, so companion .lift-ranges
            # and media can't be resolved; those checks are skipped (path None).
            lexicon = Lexicon.load(tmp_file, resolve_ranges=False)
            lexicon.path = None
            problems = list(lexicon.iter_problems(require_ids=args.require_ids))
    else:
        problems = list(iter_problems(args.path, require_ids=args.require_ids))
    return [
        problem
        for problem in problems
        if not (args.no_check_media and problem.code == "missing-media")
    ]


def _cmd_validate(args: argparse.Namespace) -> int:
    problems = _collect_problems(args)
    errors = sum(1 for problem in problems if problem.level == "error")
    warnings = len(problems) - errors
    failed = bool(errors) or (args.strict and bool(warnings))
    if args.format == "json":
        json.dump(
            {
                "problems": [_problem_json(problem) for problem in problems],
                "summary": {"errors": errors, "warnings": warnings},
            },
            sys.stdout,
            indent=2,
        )
        print()
    else:
        for problem in problems:
            print(problem)
        strict_note = "  (strict: warnings treated as errors)" if args.strict and warnings else ""
        print(f"{errors} error(s), {warnings} warning(s){strict_note}")
    return 1 if failed else 0


def _iter_senses(entry: Entry) -> list[Sense]:
    senses: list[Sense] = []
    stack = list(entry.senses)
    while stack:
        sense = stack.pop()
        senses.append(sense)
        stack.extend(sense.subsenses)
    return senses


def _cmd_stats(args: argparse.Namespace) -> int:
    from ._zip import lift_source

    entries = senses = examples = media = 0
    langs: set[str] = set()
    traits: Counter[str] = Counter()
    with lift_source(args.path) as lift_path, open_reader(lift_path) as reader:
        for entry in reader:
            entries += 1
            langs.update(entry.lexical_unit.keys())
            traits.update(trait.name for trait in entry.traits)
            pronunciations = list(entry.pronunciations)
            for variant in entry.variants:
                pronunciations.extend(variant.pronunciations)
            for pronunciation in pronunciations:
                media += len(pronunciation.media)
            for sense in _iter_senses(entry):
                senses += 1
                examples += len(sense.examples)
                media += len(sense.illustrations)
                langs.update(g.lang for g in sense.glosses if g.lang)
                langs.update(sense.definition.keys())
                traits.update(trait.name for trait in sense.traits)
    if args.format == "json":
        json.dump(
            {
                "entries": entries,
                "senses": senses,
                "examples": examples,
                "media_refs": media,
                "languages": sorted(langs),
                "traits": dict(sorted(traits.items())),
            },
            sys.stdout,
            indent=2,
        )
        print()
    else:
        print(f"entries:   {entries}")
        print(f"senses:    {senses}")
        print(f"examples:  {examples}")
        print(f"media refs: {media}")
        print(f"languages: {', '.join(sorted(langs)) if langs else '(none)'}")
        if traits:
            top = ", ".join(f"{name} ({count})" for name, count in traits.most_common(5))
            print(f"top traits: {top}")
    return 0


def _cmd_sort(args: argparse.Namespace) -> int:
    target = args.output if args.output is not None else args.path
    canonicalize(args.path, target)
    print(f"wrote {target}")
    return 0


def _cmd_check_media(args: argparse.Namespace) -> int:
    lexicon = Lexicon.load(args.path)
    missing = lexicon.missing_media()
    for ref in missing:
        owner = ref.entry_id or ref.entry_guid or "?"
        print(f"missing  {ref.kind:12s} {ref.href!r} (entry {owner})")

    referenced: set[Path] = set()
    base = lexicon.path.parent if lexicon.path is not None else Path(args.path).parent
    for ref in lexicon.media_refs():
        relative = _normalize_href(ref.href)
        if relative is None:  # remote/absolute hrefs can't confirm a local file
            continue
        referenced.add((base / relative).resolve())
        subfolder = "audio" if ref.kind == "media" else "pictures"
        referenced.add((base / subfolder / relative).resolve())
    orphans = [
        file
        for folder in ("audio", "pictures")
        if (base / folder).is_dir()
        for file in sorted((base / folder).rglob("*"))
        if file.is_file() and file.resolve() not in referenced
    ]
    for file in orphans:
        print(f"orphaned {file.relative_to(base)} (no media/illustration references it)")
    if orphans:
        print(
            "note: WeSay-style audio writing systems reference files from form "
            "text, which this check does not follow"
        )
    print(f"{len(missing)} missing, {len(orphans)} orphaned")
    return 1 if missing else 0


def _iter_leaf_senses(senses: Sequence[Sense]) -> Iterator[Sense]:
    """Depth-first leaf senses, document order.

    A sense with subsenses is a LIFT grouping node (e.g. numbered "1a"/"1b"
    under a bare "1") whose own gloss/definition are conventionally empty —
    its subsenses carry the content and get the rows instead.
    """
    for sense in senses:
        if sense.subsenses:
            yield from _iter_leaf_senses(sense.subsenses)
        else:
            yield sense


def _text_or_empty(text: Text | None) -> str:
    return str(text) if text is not None else ""


class _Utf8Sink:
    """A csv sink writing UTF-8 to a byte stream it does not own.

    csv writes CRLF row terminators, and a stdout that translates newlines
    doubles the CR into a blank row between every data row, so a redirected
    export is not the file ``--output`` writes. Going straight to the byte
    layer settles both halves of that. A ``TextIOWrapper`` around the same
    buffer would too, but it owns the buffer until detached, and an error on
    the way out would take stdout down with it.
    """

    def __init__(self, buffer: BinaryIO) -> None:
        self._buffer = buffer

    def write(self, text: str) -> int:
        """Bytes written, not characters; csv discards the count either way."""
        return self._buffer.write(text.encode("utf-8"))


def _cmd_export(args: argparse.Namespace) -> int:
    from ._zip import lift_source

    with lift_source(args.path) as lift_path:
        if args.langs:
            langs: list[str] = [lang.strip() for lang in args.langs.split(",") if lang.strip()]
        else:
            detected: set[str] = set()
            with open_reader(lift_path) as reader:
                for entry in reader:
                    for sense in _iter_leaf_senses(entry.senses):
                        detected.update(g.lang for g in sense.glosses if g.lang is not None)
                        detected.update(sense.definition.keys())
            langs = sorted(detected)

        header = ["entry_id", "entry_guid", "sense_id", "lexeme", "pos"]
        for lang in langs:
            header.extend([f"gloss_{lang}", f"definition_{lang}"])

        out_file: TextIO | None = None
        sink: TextIO | _Utf8Sink
        if args.output is not None:
            out_file = sink = args.output.open("w", encoding="utf-8", newline="")
        elif isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout.flush()  # nothing of its own may sit behind these bytes
            sink = _Utf8Sink(sys.stdout.buffer)
        else:  # a replaced stdout need not have a byte layer to write to
            sink = sys.stdout
        try:
            writer = csv.writer(sink, delimiter="\t" if args.tsv else ",")
            writer.writerow(header)
            with open_reader(lift_path) as reader:
                for entry in reader:
                    forms = entry.lexical_unit.forms
                    lexeme = str(forms[0].text) if forms else ""
                    for sense in _iter_leaf_senses(entry.senses):
                        pos = sense.grammatical_info.value if sense.grammatical_info else ""
                        row = [entry.id or "", entry.guid or "", sense.id or "", lexeme, pos]
                        for lang in langs:
                            row.append(_text_or_empty(sense.gloss(lang)))
                            row.append(_text_or_empty(sense.definition.get(lang)))
                        writer.writerow(row)
        finally:
            if out_file is not None:
                out_file.close()
    return 0


def _force_utf8(stream: TextIO) -> None:
    """Make one of the standard streams write UTF-8, whatever the locale is.

    A stream that is not a console gets the locale encoding — cp1252 on
    Windows, ASCII under a C/POSIX locale — which cannot hold LIFT content, so
    one unrepresentable character killed the command mid-output. ``-o`` has
    always forced UTF-8; this makes a redirect agree with it.

    Only the encoding changes. ``reconfigure`` resets the error handler to
    ``strict`` unless it is passed one, and each stream's own is worth keeping:
    stderr is ``backslashreplace`` so a message always arrives, and stdout is
    ``surrogateescape`` on some platforms, which is what round-trips a filename
    the filesystem encoding could not decode.
    """
    if not isinstance(stream, io.TextIOWrapper):  # a replaced stream may be anything
        return
    if codecs.lookup(stream.encoding).name == "utf-8":
        return
    stream.reconfigure(encoding="utf-8", errors=stream.errors)


def main(argv: Sequence[str] | None = None) -> int:
    _force_utf8(sys.stdout)
    _force_utf8(sys.stderr)
    parser = argparse.ArgumentParser(
        prog="sil-lift",
        description="Utilities for LIFT 0.13 lexicon files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser(
        "validate", help="schema + semantic validation; exit 1 on errors"
    )
    validate.add_argument("path", type=Path, help="a .lift or .zip file, or - for stdin")
    validate.add_argument(
        "--format", choices=("text", "json"), default="text", help="output format (default: text)"
    )
    validate.add_argument(
        "--strict", action="store_true", help="treat warnings as errors (exit 1 on any warning)"
    )
    validate.add_argument(
        "--no-check-media",
        action="store_true",
        help="skip the filesystem media-presence check (suppresses missing-media findings)",
    )
    validate.add_argument(
        "--require-ids",
        action="store_true",
        help="error on entries missing a guid or senses missing an id",
    )
    validate.set_defaults(func=_cmd_validate)

    stats = subparsers.add_parser("stats", help="entry/sense/language counts (streaming)")
    stats.add_argument("path", type=Path, help="a .lift or .zip file")
    stats.add_argument(
        "--format", choices=("text", "json"), default="text", help="output format (default: text)"
    )
    stats.set_defaults(func=_cmd_stats)

    sort = subparsers.add_parser("sort", help="write a canonically sorted copy")
    sort.add_argument("path", type=Path, help="a .lift file")
    sort.add_argument("-o", "--output", type=Path, default=None, help="default: in place")
    sort.set_defaults(func=_cmd_sort)

    check_media = subparsers.add_parser(
        "check-media", help="report missing and orphaned media files"
    )
    check_media.add_argument("path", type=Path, help="a .lift or .zip file")
    check_media.set_defaults(func=_cmd_check_media)

    export = subparsers.add_parser(
        "export", help="flatten senses to CSV/TSV, one row per leaf sense (streaming)"
    )
    export.add_argument("path", type=Path, help="a .lift or .zip file")
    export.add_argument("-o", "--output", type=Path, default=None, help="default: stdout")
    export.add_argument(
        "--langs", default=None, help="comma-separated analysis languages (default: auto-detect)"
    )
    export.add_argument("--tsv", action="store_true", help="tab-delimited output (default: CSV)")
    export.set_defaults(func=_cmd_export)

    args = parser.parse_args(argv)
    try:
        result: int = args.func(args)
    except LiftError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return result


if __name__ == "__main__":
    sys.exit(main())
