"""The demo CLI (decision-document section D): validate / stats / sort / check-media / export.

A LiftTools-style utility exercising every scope pillar end-to-end: validation
(all three layers), streaming reads (stats, export), the canonical sort + write
path (sort), and the folder/media model (check-media). Deliberately stdlib-only.
"""

from __future__ import annotations

import argparse
import csv
import sys
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
    from typing import TextIO

    from ._model import Entry, Sense
    from ._text import Text

__all__ = ["main"]


def _cmd_validate(args: argparse.Namespace) -> int:
    errors = warnings = 0
    for problem in iter_problems(args.path):
        print(problem)
        if problem.level == "error":
            errors += 1
        else:
            warnings += 1
    print(f"{errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


def _iter_senses(entry: Entry) -> list[Sense]:
    senses: list[Sense] = []
    stack = list(entry.senses)
    while stack:
        sense = stack.pop()
        senses.append(sense)
        stack.extend(sense.subsenses)
    return senses


def _cmd_stats(args: argparse.Namespace) -> int:
    entries = senses = examples = media = 0
    langs: set[str] = set()
    traits: Counter[str] = Counter()
    with open_reader(args.path) as reader:
        for entry in reader:
            entries += 1
            langs.update(entry.lexical_unit.keys())
            traits.update(trait.name for trait in entry.traits)
            for pronunciation in entry.pronunciations:
                media += len(pronunciation.media)
            for sense in _iter_senses(entry):
                senses += 1
                examples += len(sense.examples)
                media += len(sense.illustrations)
                langs.update(g.lang for g in sense.glosses if g.lang)
                langs.update(sense.definition.keys())
                traits.update(trait.name for trait in sense.traits)
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
    base = Path(args.path).parent
    for ref in lexicon.media_refs():
        relative = _normalize_href(ref.href)
        if relative is None:  # remote/absolute hrefs can't vouch for local files
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


def _cmd_export(args: argparse.Namespace) -> int:
    if args.langs:
        langs: list[str] = [lang.strip() for lang in args.langs.split(",") if lang.strip()]
    else:
        detected: set[str] = set()
        with open_reader(args.path) as reader:
            for entry in reader:
                for sense in _iter_leaf_senses(entry.senses):
                    detected.update(form.lang for form in sense.glosses if form.lang is not None)
                    detected.update(sense.definition.keys())
        langs = sorted(detected)

    header = ["entry_id", "entry_guid", "sense_id", "lexeme", "pos"]
    for lang in langs:
        header.extend([f"gloss_{lang}", f"definition_{lang}"])

    out_file: TextIO = (
        sys.stdout if args.output is None else args.output.open("w", encoding="utf-8", newline="")
    )
    try:
        writer = csv.writer(out_file, delimiter="\t" if args.tsv else ",")
        writer.writerow(header)
        with open_reader(args.path) as reader:
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
        if args.output is not None:
            out_file.close()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sil-lift",
        description="Utilities for LIFT 0.13 lexicon files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser(
        "validate", help="schema + semantic validation; exit 1 on errors"
    )
    validate.add_argument("path", type=Path, help="a .lift file")
    validate.set_defaults(func=_cmd_validate)

    stats = subparsers.add_parser("stats", help="entry/sense/language counts (streaming)")
    stats.add_argument("path", type=Path, help="a .lift file")
    stats.set_defaults(func=_cmd_stats)

    sort = subparsers.add_parser("sort", help="write a canonically sorted copy")
    sort.add_argument("path", type=Path, help="a .lift file")
    sort.add_argument("-o", "--output", type=Path, default=None, help="default: in place")
    sort.set_defaults(func=_cmd_sort)

    check_media = subparsers.add_parser(
        "check-media", help="report missing and orphaned media files"
    )
    check_media.add_argument("path", type=Path, help="a .lift file")
    check_media.set_defaults(func=_cmd_check_media)

    export = subparsers.add_parser(
        "export", help="flatten senses to CSV/TSV, one row per sense (streaming)"
    )
    export.add_argument("path", type=Path, help="a .lift file")
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
