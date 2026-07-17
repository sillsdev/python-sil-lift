"""Validation: schema layers + semantic checks -> a stream of Problems.

Three layers, all explicit-call (never implicit on load/save):

1. RELAX NG against the vendored ``lift-0.13.rng`` — with two deliberate
   deviations from raw libxml2 behavior:

   - ``href`` attributes are masked before validation. libxml2's ``anyURI``
     check rejects the ``file://C:/...`` URIs that FLEx systematically writes
     (the C# validator's engine never enforced anyURI), which would flag
     virtually every real lexicon. Instead, sil-lift runs its own URI
     plausibility check and reports offenders as *warnings* (``uri-not-rfc``).
   - children are grouped by tag before validation. libxml2's interleave
     support rejects legally-interleaved documents once an element type
     appears in more than one run (e.g. ``field, note, field, note`` inside a
     sense — real FLEx output). Grouping same-tag siblings contiguously is
     semantics-preserving here: every content model in the LIFT grammar is
     interleave-based except the root's (header before entries), which is
     left untouched.
2. The project-authored ``lift-ranges-0.13.rng`` over each tracked
   ``.lift-ranges`` companion.
3. Semantic checks the grammar cannot express: duplicate entry GUIDs,
   dangling ``relation/@ref`` and ``variant/@ref``, ``range-element/@parent``
   integrity, undefined range values (grammatical-info and range-keyed
   traits), duplicate form languages (the RNG's Schematron rule, which lxml
   ignores), and missing media files.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from lxml import etree

from ._errors import LiftValidationError
from ._model import Lexicon
from ._text import Multitext

if TYPE_CHECKING:
    import os
    from collections.abc import Iterator

    from ._header import Range
    from ._model import Entry, Sense

__all__ = ["Problem", "iter_problems", "validate_file"]

_SCHEMAS_DIR = Path(__file__).parent / "schemas"


@dataclass(slots=True)
class Problem:
    """One validation finding, addressable to a file/entry/line."""

    level: Literal["error", "warning"]
    code: str  # "schema", "duplicate-guid", "dangling-ref", "range-parent",
    # "undefined-range-value", "duplicate-form-lang", "missing-media", "uri-not-rfc"
    message: str
    file: Path | None = None
    entry_id: str | None = None
    guid: str | None = None
    line: int | None = None

    def __str__(self) -> str:
        where = self.file.name if self.file else "<memory>"
        if self.line is not None:
            where += f":{self.line}"
        entry = f" (entry {self.entry_id or self.guid})" if self.entry_id or self.guid else ""
        return f"{self.level} [{self.code}] {where}{entry}: {self.message}"


def iter_problems(path: str | os.PathLike[str]) -> Iterator[Problem]:
    """All problems in the document and its tracked companions, lazily."""
    return Lexicon.load(path).iter_problems()


def validate_file(path: str | os.PathLike[str]) -> None:
    """Raise :class:`LiftValidationError` on the first error-level problem."""
    for problem in iter_problems(path):
        if problem.level == "error":
            raise LiftValidationError(problem)


def iter_lexicon_problems(lexicon: Lexicon) -> Iterator[Problem]:
    from ._writer import render_document, render_ranges_document

    lift_schema = etree.RelaxNG(etree.parse(_SCHEMAS_DIR / "lift-0.13.rng"))
    ranges_schema = etree.RelaxNG(etree.parse(_SCHEMAS_DIR / "lift-ranges-0.13.rng"))

    # What save() would write, not the loaded bytes: edits must be visible to
    # validation. Untouched loaded documents render byte-identical to their
    # source, so line numbers keep matching the file on disk — and rendered
    # entry order always matches lexicon.entries, keeping the entry_lines
    # table aligned for semantic addressing even after edits or sort().
    data = render_document(lexicon)
    entry_lines, problems = _schema_problems(data, lift_schema, lexicon.path)
    yield from problems
    for ranges_file in lexicon.ranges_files.values():
        rdata = render_ranges_document(ranges_file)
        _, range_problems = _schema_problems(rdata, ranges_schema, ranges_file.path)
        yield from range_problems
    yield from _semantic_problems(lexicon, entry_lines)


# --- schema layer ----------------------------------------------------------------


def _suspicious_uri(value: str) -> str | None:
    """Why a URI would fail RFC parsing, or None. Mirrors the real-world quirks."""
    if " " in value:
        return "contains an unencoded space"
    if "\\" in value:
        return "contains backslashes (not a URI path separator)"
    if value.startswith("file://") and not value.startswith("file:///"):
        rest = value[len("file://") :]
        if rest and rest[0].isalpha() and rest[1:2] == ":":
            return "Windows drive letter used as URI authority (FLEx-style file://C:/)"
    return None


def _line(el: etree._Element) -> int | None:
    line = el.sourceline  # lxml-stubs give this a non-int placeholder type
    return line if isinstance(line, int) else None


def _group_children_by_tag(el: etree._Element, *, is_root: bool) -> None:
    """Stable-sort same-tag siblings together (see module docstring, layer 1).

    The document root keeps its order (its content model is a sequence);
    mixed content (``<text>``/``<span>``) is never touched. sourceline info
    survives the moves, so line addressing stays intact.
    """
    if not isinstance(el.tag, str) or el.tag in ("text", "span"):
        return
    if not is_root and len(el) > 1:
        el[:] = sorted(el, key=lambda c: c.tag if isinstance(c.tag, str) else "￿")
    for child in el:
        _group_children_by_tag(child, is_root=False)


def _schema_problems(
    data: bytes, schema: etree.RelaxNG, file: Path | None
) -> tuple[list[tuple[int | None, str | None, str | None]], list[Problem]]:
    """Validate one document; returns (per-entry line/id/guid table, problems)."""
    problems: list[Problem] = []
    root = etree.fromstring(data)
    _group_children_by_tag(root, is_root=True)
    entry_lines: list[tuple[int | None, str | None, str | None]] = []
    for child in root:
        if isinstance(child.tag, str) and child.tag == "entry":
            entry_lines.append((_line(child), child.get("id"), child.get("guid")))
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        href = el.get("href")
        if href is None:
            continue
        reason = _suspicious_uri(href)
        if reason is not None:
            problems.append(
                Problem(
                    "warning",
                    "uri-not-rfc",
                    f"<{el.tag} href={href!r}>: {reason}",
                    file=file,
                    line=_line(el),
                )
            )
        el.set("href", "masked:uri")  # see module docstring: anyURI is ours to report
    if not schema.validate(root.getroottree()):
        for error in schema.error_log:
            line = error.line if error.line and error.line > 0 else None
            entry_id, guid = _nearest_entry(entry_lines, line)
            problems.append(
                Problem(
                    "error",
                    "schema",
                    error.message,
                    file=file,
                    entry_id=entry_id,
                    guid=guid,
                    line=line,
                )
            )
    return entry_lines, problems


def _nearest_entry(
    entry_lines: list[tuple[int | None, str | None, str | None]], line: int | None
) -> tuple[str | None, str | None]:
    if line is None:
        return None, None
    best: tuple[str | None, str | None] = (None, None)
    for entry_line, entry_id, guid in entry_lines:
        if entry_line is None:
            continue  # parsed entries always carry a sourceline; stay defensive
        if entry_line > line:
            break
        best = (entry_id, guid)
    return best


# --- semantic layer ----------------------------------------------------------------


def _iter_senses(entry: Entry) -> Iterator[Sense]:
    stack = list(entry.senses)
    while stack:
        sense = stack.pop()
        yield sense
        stack.extend(sense.subsenses)


def _iter_multitexts(obj: object) -> Iterator[tuple[str, Multitext]]:
    """Every ``Multitext`` reachable from ``obj``, generic over the model shape.

    Mirrors the RNG's Schematron ``multitext-content`` rule, which fires on
    every ``<form>``-bearing element in the grammar — including forms nested
    inside annotation content (``Annotation.content`` is itself a Multitext,
    reachable from almost any node via ``.annotations``). Walking the
    dataclass tree instead of hand-listing fields keeps this in sync as the
    model grows.
    """
    if isinstance(obj, list):
        for item in obj:
            yield from _iter_multitexts(item)
        return
    if not is_dataclass(obj) or isinstance(obj, type):
        return
    for f in fields(obj):
        value = getattr(obj, f.name)
        if isinstance(value, Multitext):
            yield f.name.replace("_", "-"), value
        yield from _iter_multitexts(value)


def _semantic_problems(
    lexicon: Lexicon,
    entry_lines: list[tuple[int | None, str | None, str | None]],
) -> Iterator[Problem]:
    file = lexicon.path

    def at(index: int) -> int | None:
        return entry_lines[index][0] if index < len(entry_lines) else None

    # Duplicate GUIDs (C# Validator parity case).
    seen_guids: dict[str, int] = {}
    for index, entry in enumerate(lexicon.entries):
        if entry.guid is None:
            continue
        if entry.guid in seen_guids:
            yield Problem(
                "error",
                "duplicate-guid",
                f"guid {entry.guid} already used by entry index {seen_guids[entry.guid]}",
                file=file,
                entry_id=entry.id,
                guid=entry.guid,
                line=at(index),
            )
        else:
            seen_guids[entry.guid] = index

    # Dangling refs: relation/@ref and variant/@ref may target an entry id,
    # an entry guid, or a sense id (FLEx does all three).
    targets: set[str] = set()
    for entry in lexicon.entries:
        targets.update(t for t in (entry.id, entry.guid) if t)
        for sense in _iter_senses(entry):
            if sense.id:
                targets.add(sense.id)
    for index, entry in enumerate(lexicon.entries):
        refs: list[str] = [r.ref for r in entry.relations]
        refs.extend(v.ref for v in entry.variants if v.ref)
        for variant in entry.variants:
            refs.extend(r.ref for r in variant.relations)
        for sense in _iter_senses(entry):
            refs.extend(r.ref for r in sense.relations)
        for ref in refs:
            if ref and ref not in targets:
                yield Problem(
                    "error",
                    "dangling-ref",
                    f"ref {ref!r} matches no entry id/guid or sense id",
                    file=file,
                    entry_id=entry.id,
                    guid=entry.guid,
                    line=at(index),
                )

    # Duplicate form languages (the RNG's Schematron rule; lxml ignores it) —
    # every Multitext under the entry, not just the top-level ones.
    for index, entry in enumerate(lexicon.entries):
        for label, multitext in _iter_multitexts(entry):
            langs = [f.lang for f in multitext.forms if f.lang is not None]
            for lang in sorted({lang for lang in langs if langs.count(lang) > 1}):
                yield Problem(
                    "warning",
                    "duplicate-form-lang",
                    f"{label} has more than one form with lang {lang!r}",
                    file=file,
                    entry_id=entry.id,
                    guid=entry.guid,
                    line=at(index),
                )

    # Range integrity over the merged view (inline + companions).
    all_ranges = lexicon.all_ranges()
    for range_ in all_ranges.values():
        element_ids = {element.id for element in range_.elements}
        for element in range_.elements:
            if element.parent and element.parent not in element_ids:
                yield Problem(
                    "error",
                    "range-parent",
                    f"range {range_.id!r}: range-element {element.id!r} has "
                    f"parent {element.parent!r} which is not a sibling id",
                    file=file,
                )

    # Undefined range values: grammatical-info against the grammatical-info
    # range; traits whose name matches a known range. Only ranges that
    # actually enumerate elements can vouch for values; empty values skipped
    # (FLEx writes them). Comparison is NFC-normalized: FLEx writes the .lift
    # in NFC but the companion .lift-ranges in NFD within the same export.
    def nfc(value: str) -> str:
        return unicodedata.normalize("NFC", value)

    def defined(range_id: str) -> set[str] | None:
        range_: Range | None = all_ranges.get(range_id)
        if range_ is None or not range_.elements:
            return None
        return {nfc(element.id) for element in range_.elements}

    grammatical_values = defined("grammatical-info")
    for index, entry in enumerate(lexicon.entries):
        checks: list[tuple[str, str, set[str]]] = []  # (label, value, allowed)
        for sense in _iter_senses(entry):
            info = sense.grammatical_info
            if info is not None and info.value and grammatical_values is not None:
                checks.append(("grammatical-info", info.value, grammatical_values))
            for trait in sense.traits:
                allowed = defined(trait.name)
                if allowed is not None and trait.value:
                    checks.append((f"trait {trait.name!r}", trait.value, allowed))
        for trait in entry.traits:
            allowed = defined(trait.name)
            if allowed is not None and trait.value:
                checks.append((f"trait {trait.name!r}", trait.value, allowed))
        for label, value, allowed in checks:
            if nfc(value) not in allowed:
                yield Problem(
                    "warning",
                    "undefined-range-value",
                    f"{label} value {value!r} is not defined in the range",
                    file=file,
                    entry_id=entry.id,
                    guid=entry.guid,
                    line=at(index),
                )

    # Missing media files.
    for media_ref in lexicon.missing_media():
        yield Problem(
            "warning",
            "missing-media",
            f"{media_ref.kind} file not found: {media_ref.href!r}",
            file=file,
            entry_id=media_ref.entry_id,
            guid=media_ref.entry_guid,
        )
