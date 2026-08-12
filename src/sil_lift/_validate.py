"""Validation: schema layers + semantic checks -> a stream of Problems.

Three layers, all explicit-call (never implicit on load/save):

1. RELAX NG against the vendored ``lift-0.13.rng`` — with two deliberate
   deviations from raw libxml2 behavior:

   - ``href`` attributes are masked before validation. libxml2's ``anyURI``
     check rejects the ``file://C:/...`` URIs that FieldWorks (FLEx)
     systematically writes (the C# validator's engine never enforced anyURI),
     which would flag virtually every real lexicon. Instead, sil-lift runs its
     own URI plausibility check and reports offenders as *warnings*
     (``uri-not-rfc``).
   - children are grouped by tag before validation. libxml2's interleave
     support rejects legally-interleaved documents once an element type
     appears in more than one run (e.g. ``field, note, field, note`` inside a
     sense — real FLEx output). Grouping same-tag siblings contiguously is
     semantics-preserving here: every content model in the LIFT grammar is
     interleave-based except the root's (header before entries), which is
     left untouched.
2. The vendored ``lift-ranges-0.13.rng`` over each tracked ``.lift-ranges``
   companion.
3. Semantic checks the grammar cannot express: duplicate GUIDs (entries, and
   ranges/range-elements within their own document), dangling ``relation/@ref``
   and ``variant/@ref``, ``range-element/@parent`` integrity, undefined range
   values (every grammatical-info and range-keyed trait anywhere in the entry,
   however deeply nested), duplicate form languages (the RNG's Schematron
   rule, which lxml ignores), missing media files, header ``range/@href``
   references that resolve to no companion, and — opt-in — entries/senses
   missing a stable id.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from lxml import etree

from ._errors import LiftValidationError
from ._model import GrammaticalInfo, Lexicon, _normalize_href
from ._text import Multitext, Trait

if TYPE_CHECKING:
    import os
    from collections.abc import Iterator

    from ._header import Range
    from ._model import Entry, Sense

__all__ = ["Problem", "iter_problems", "validate_file"]

_SCHEMAS_DIR = Path(__file__).parent / "schemas"
_PARSER = etree.XMLParser(resolve_entities=False, no_network=True)


@dataclass(slots=True)
class Problem:
    """One validation finding, addressable to a file/entry/line."""

    level: Literal["error", "warning"]
    code: str  # "schema", "duplicate-guid", "dangling-ref", "range-parent",
    # "undefined-range-value", "normalization-mismatch", "duplicate-form-lang",
    # "missing-media", "uri-not-rfc", "dangling-ranges-href", "missing-id"
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


def iter_problems(path: str | os.PathLike[str], *, require_ids: bool = False) -> Iterator[Problem]:
    """All problems in the document and its tracked companions, lazily.

    With ``require_ids``, also report entries/senses missing a stable id
    (``missing-id`` errors); see :meth:`Lexicon.iter_problems`.
    """
    return Lexicon.load(path).iter_problems(require_ids=require_ids)


def validate_file(path: str | os.PathLike[str]) -> None:
    """Raise :class:`LiftValidationError` on the first error-level problem."""
    for problem in iter_problems(path):
        if problem.level == "error":
            raise LiftValidationError(problem)


def iter_lexicon_problems(lexicon: Lexicon, *, require_ids: bool = False) -> Iterator[Problem]:
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
    yield from _semantic_problems(lexicon, entry_lines, require_ids=require_ids)


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
    root = etree.fromstring(data, parser=_PARSER)
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


def _iter_traits(obj: object) -> Iterator[Trait]:
    """Every ``Trait`` reachable from ``obj``, generic over the model shape.

    Traits are not just entry/sense-direct: real FLEx exports nest them inside
    ``<relation>`` (``is-primary``, ``complex-form-type``), ``<variant>``
    (``morph-type``), ``<pronunciation>``, and other extensible elements —
    walking the dataclass tree (mirrors ``_iter_multitexts``) catches all of
    them instead of only the two levels a hand-written traversal would name.
    """
    if isinstance(obj, Trait):
        yield obj
        return
    if isinstance(obj, list):
        for item in obj:
            yield from _iter_traits(item)
        return
    if not is_dataclass(obj) or isinstance(obj, type):
        return
    for f in fields(obj):
        yield from _iter_traits(getattr(obj, f.name))


def _iter_grammatical_infos(obj: object) -> Iterator[GrammaticalInfo]:
    """Every ``GrammaticalInfo`` reachable from ``obj`` (sense, reversal, and
    reversal ``main`` chains all carry one)."""
    if isinstance(obj, GrammaticalInfo):
        yield obj
        return
    if isinstance(obj, list):
        for item in obj:
            yield from _iter_grammatical_infos(item)
        return
    if not is_dataclass(obj) or isinstance(obj, type):
        return
    for f in fields(obj):
        yield from _iter_grammatical_infos(getattr(obj, f.name))


def _semantic_problems(
    lexicon: Lexicon,
    entry_lines: list[tuple[int | None, str | None, str | None]],
    *,
    require_ids: bool = False,
) -> Iterator[Problem]:
    file = lexicon.path

    def at(index: int) -> int | None:
        return entry_lines[index][0] if index < len(entry_lines) else None

    # Missing stable ids (opt-in): a guid on every entry, an id on every sense.
    # Both are optional in LIFT; required only by workflows that re-import by id.
    if require_ids:
        for index, entry in enumerate(lexicon.entries):
            if entry.guid is None:
                yield Problem(
                    "error",
                    "missing-id",
                    "entry has no guid (needed for re-import by a stable id)",
                    file=file,
                    entry_id=entry.id,
                    line=at(index),
                )
            for sense in _iter_senses(entry):
                if sense.id is None:
                    yield Problem(
                        "error",
                        "missing-id",
                        "sense has no id (needed for re-import by a stable id)",
                        file=file,
                        entry_id=entry.id,
                        guid=entry.guid,
                        line=at(index),
                    )

    # Duplicate GUIDs (C# Validator parity case): Validator.GetDuplicateGuidErrors
    # scans every element's guid attribute in the document being validated, not
    # just entries -- the RNG also allows one on <range> and <range-element>.
    # Scope is per rendered document, matching that per-file scan: the .lift
    # (entries plus any inline header ranges/range-elements) is one scope, and
    # each .lift-ranges companion (its own ranges/range-elements) is another.
    def _range_guids(
        ranges: list[Range],
    ) -> Iterator[tuple[str, str, str | None, int | None]]:
        for range_ in ranges:
            if range_.guid is not None:
                yield f"range {range_.id!r}", range_.guid, None, None
            for element in range_.elements:
                if element.guid is not None:
                    yield (
                        f"range-element {element.id!r} (range {range_.id!r})",
                        element.guid,
                        None,
                        None,
                    )

    def _duplicate_guid_problems(
        pairs: Iterator[tuple[str, str, str | None, int | None]], doc_file: Path | None
    ) -> Iterator[Problem]:
        first_seen: dict[str, str] = {}
        for label, guid, entry_id, line in pairs:
            if guid in first_seen:
                yield Problem(
                    "error",
                    "duplicate-guid",
                    f"guid {guid} already used by {first_seen[guid]}",
                    file=doc_file,
                    entry_id=entry_id,
                    guid=guid,
                    line=line,
                )
            else:
                first_seen[guid] = label

    def _entry_guids() -> Iterator[tuple[str, str, str | None, int | None]]:
        for index, entry in enumerate(lexicon.entries):
            if entry.guid is not None:
                label = f"entry {entry.id!r}" if entry.id else f"entry #{index}"
                yield label, entry.guid, entry.id, at(index)

    def _main_doc_guids() -> Iterator[tuple[str, str, str | None, int | None]]:
        yield from _entry_guids()
        yield from _range_guids(lexicon.header.ranges)

    yield from _duplicate_guid_problems(_main_doc_guids(), file)
    for ranges_file in lexicon.ranges_files.values():
        yield from _duplicate_guid_problems(_range_guids(ranges_file.ranges), ranges_file.path)

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

    # Comparisons of a range value or a parent link against a range-element id
    # are NFC-normalized. FLEx normalizes strings to NFC on export, but a few
    # writes bypass its normalizing helper and emit the NFD it holds in memory
    # -- among them the grammatical-info and lexical-relation range-element
    # ids, whose labels and own parent attribute are normalized. So an id can
    # be NFD while the .lift value and the parent pointing at it are NFC.
    def nfc(value: str) -> str:
        return unicodedata.normalize("NFC", value)

    # Every name that resolved only because of that normalization, keyed by the
    # range-element it resolved to: (range id, id as written) -> a differing
    # reference. Reported once per element however many references differ --
    # in a real 3507-entry export that is 6 findings rather than 82.
    mismatched: dict[tuple[str, str], str] = {}

    # Range integrity over the merged view (inline + companions).
    all_ranges = lexicon.all_ranges()
    for range_ in all_ranges.values():
        element_ids: dict[str, str] = {}  # NFC id -> id as written
        for element in range_.elements:
            element_ids.setdefault(nfc(element.id), element.id)
        for element in range_.elements:
            if not element.parent:
                continue
            target = element_ids.get(nfc(element.parent))
            if target is None:
                yield Problem(
                    "error",
                    "range-parent",
                    f"range {range_.id!r}: range-element {element.id!r} has "
                    f"parent {element.parent!r} which is not a sibling id",
                    file=file,
                )
            elif target != element.parent:
                mismatched.setdefault((range_.id, target), element.parent)

    # Header <range href> references (relative) that resolve to no companion.
    # Absolute/file:// hrefs are ones FLEx writes knowing they will not resolve
    # (they are resolved by basename when the companion is in the same folder)
    # and are not checked here; this catches an exporter that writes a relative
    # href but not the file.
    if lexicon.path is not None:
        base = lexicon.path.parent
        for range_ in lexicon.header.ranges:
            if not range_.href or range_.elements:
                continue
            relative = _normalize_href(range_.href)
            if relative is None:
                continue
            resolved = all_ranges.get(range_.id)
            if resolved is not None and resolved.elements:
                continue  # supplied by a sibling companion instead
            if not (base / relative).is_file():
                yield Problem(
                    "warning",
                    "dangling-ranges-href",
                    f"header range {range_.id!r} references {range_.href!r} "
                    "but no companion file was found",
                    file=lexicon.path,
                )

    # Undefined range values: every grammatical-info (sense, reversal, and
    # reversal main chains) against the grammatical-info range; every trait
    # anywhere in the entry whose name matches a known range — not just entry-
    # and sense-direct ones, since real FLEx exports nest traits like
    # is-primary/complex-form-type inside <relation> and morph-type inside
    # <variant> (_iter_traits/_iter_grammatical_infos walk the whole entry).
    # Only ranges that actually enumerate elements can confirm a value; empty
    # values skipped (FLEx writes them).
    def defined(range_id: str) -> dict[str, str] | None:
        range_: Range | None = all_ranges.get(range_id)
        if range_ is None or not range_.elements:
            return None
        ids: dict[str, str] = {}  # NFC id -> id as written
        for element in range_.elements:
            ids.setdefault(nfc(element.id), element.id)
        return ids

    grammatical_values = defined("grammatical-info")
    for index, entry in enumerate(lexicon.entries):
        # (label, range id, value, allowed ids)
        checks: list[tuple[str, str, str, dict[str, str]]] = []
        for info in _iter_grammatical_infos(entry):
            if info.value and grammatical_values is not None:
                checks.append(
                    ("grammatical-info", "grammatical-info", info.value, grammatical_values)
                )
        for trait in _iter_traits(entry):
            allowed = defined(trait.name)
            if allowed is not None and trait.value:
                checks.append((f"trait {trait.name!r}", trait.name, trait.value, allowed))
        for label, range_id, value, allowed in checks:
            target = allowed.get(nfc(value))
            if target is None:
                yield Problem(
                    "warning",
                    "undefined-range-value",
                    f"{label} value {value!r} is not defined in the range",
                    file=file,
                    entry_id=entry.id,
                    guid=entry.guid,
                    line=at(index),
                )
            elif target != value:
                mismatched.setdefault((range_id, target), value)

    # The two spellings render identically, so name them by code point rather
    # than with the !r other messages use; the file each id lives in is the
    # companion that defines it, not necessarily the document being validated.
    ranges_paths = {
        range_.id: ranges_file.path
        for ranges_file in lexicon.ranges_files.values()
        for range_ in ranges_file.ranges
        if all_ranges.get(range_.id) is range_  # an inline range wins the merge
    }
    for (range_id, element_id), reference in sorted(mismatched.items()):
        yield Problem(
            "warning",
            "normalization-mismatch",
            f"range {range_id!r}: range-element id {element_id!a} is referenced "
            f"as {reference!a}; they match only under Unicode NFC normalization",
            file=ranges_paths.get(range_id) or file,
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
