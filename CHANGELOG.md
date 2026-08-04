# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). During 0.x, minor
releases may contain breaking changes.

<!-- Available types of changes:
### Added
### Fixed
### Changed
### Deprecated
### Removed
### Security
-->

## [Unreleased]

## [0.1.0] - 2026-07-TBD

### Added

- Project scaffolding: package skeleton, vendored LIFT 0.13 RELAX NG schema,
  test corpus with provenance, corpus-prep and large-file-generator tooling.
- Full object model: all 35 LIFT 0.13 elements as typed dataclasses;
  `sil_lift.load()` / `Lexicon.load()` full-document reader that keeps LIFT
  residue per node in `Extras`; LIFT-version guard.
- `Lexicon.save()` writer with byte-fidelity passthrough — unchanged
  documents and untouched entries are written byte-identically; touched entries
  re-serialize canonically with all out-of-schema content preserved. Fidelity
  contract documented in `docs/en/fidelity.md` and enforced by corpus
  byte-identity tests plus Hypothesis round-trip properties. Content XML cannot
  represent — a lone surrogate, which only an API assignment can introduce — is
  refused with `LiftWriteError` naming the node, and reported by validation as
  `lone-surrogate`.
- Change detection against the loaded document, reading the same parse-time
  digests. `Lexicon.changed_entries()` reports entries whose content differs
  (an entry's digest covers its whole subtree, so an edit at any depth reports
  the entry containing it, while an identical rewrite or a `sort()` reports
  nothing); `added_entries()` and `removed_entries()` report the rest — an
  entry already in the document, appended a second time, counts as an addition
  — and need no serialization. `Lexicon.changes()` and `RangesFile.changes()`
  return `Changes` / `RangesChanges`, covering entry content, additions,
  removals, reordering, the header, the root element, and every tracked
  companion — each falsy only when `save()` would reproduce the source bytes,
  so `if not lex.changes():` is a correct guard for skipping an in-place write
  (content, not destination: a `save(path)` into another directory writes
  there regardless). Comparison is always against the loaded document, never
  against the most recent `save()`.
- LIFT-folder handling: `RangesFile` (standalone `.lift-ranges` documents,
  same fidelity guarantees), automatic companion discovery/tracking on load
  (`Lexicon.ranges_files`, resolving a companion whose filename differs from
  the `.lift` only in case, as Windows-authored folders often do), `save()`
  writes companions together, `all_ranges()` merged view, `media_refs()` /
  `missing_media()` helpers, build-from-scratch helpers
  `Lexicon.add_ranges_file()` / `RangesFile.add_range()` /
  `Range.add_element()` (`save()` writes and header-references a new companion
  beside the `.lift`); vendored `schemas/lift-ranges-0.13.rng` — the first
  schema for standalone ranges documents.
- Zipped LIFT packages: `sil_lift.load()` reads a `.zip` (both the flat and
  folder-wrapped layouts, junk entries like `__MACOSX` ignored),
  `Lexicon.save_zip()` writes one (carrying media, `WritingSystems/`, and other
  package files through verbatim); `validate`, `stats`, `check-media`, and
  `export` accept a `.zip` path on the CLI, and the streaming commands
  (`stats`, `export`) extract only the `.lift` rather than the whole package.
  Extraction is capped at 100,000 members and 10 GiB (the whole package for a
  full extraction, the `.lift` alone for a streaming one), and refuses members
  whose paths escape the extraction directory.
- Validation: `validate_file()` / `iter_problems()` /
  `Lexicon.iter_problems()` returning a `Problem` stream, each carrying the
  file, entry, and line it concerns. RELAX NG layer with two documented
  departures from strict validation (invalid `file://` hrefs downgraded to
  `uri-not-rfc` warnings; legal interleaving not falsely flagged); vendored
  ranges schema over companions; and nine semantic checks the grammar cannot
  express, one `Problem` code each (with missing-id opt-in via `require_ids`).
  Names resolve against range and range-element ids under NFC; a match that
  needed normalizing is reported as normalization-mismatch, once per id.
  Every code is described in `docs/en/guides/validate.md`.
- Canonical sort: `Lexicon.sort()` / `RangesFile.sort()` (entries by
  case-folded guid/id, ranges/range-elements by id, field definitions by tag;
  informed by the C# LiftSorter, locale-independent) and
  `sil_lift.canonicalize()` for fully re-serialized diff-ready output. Sorting
  composes with the passthrough: sort \+ save moves untouched entries' bytes
  without rewriting them. Text whitespace is never normalized.
- Streaming: `open_reader()` (lazy entry iterator with the parsed header
  available up front) and `open_writer()` (header \+ one canonical chunk per
  entry; byte-identical to `canonical_document` output by construction, and
  optionally writing a `.lift-ranges` companion via `ranges=`), both
  over the same `Entry` types as full-document mode, holding one entry in
  memory at a time (verified on a ~340 MB generated file).
- The `sil-lift` CLI (stdlib-only, installed with the package):
  `validate` / `stats` / `sort` / `check-media`, plus `export` — one row per
  leaf sense (subsenses flattened) to CSV/TSV, streaming; analysis languages
  auto-detected or set with `--langs`. `validate` supports `--format json`
  (machine-readable findings), `--strict` (warnings become errors),
  `--no-check-media` (skip the filesystem media-presence check),
  `--require-ids` (error on entries/senses missing a stable id), and `-` to
  read from stdin; `stats` also takes `--format json`. `validate`'s exit codes
  and JSON schema are a supported interface.
- Container image and GitHub Action wrapping `sil-lift validate`, so a
  non-Python CI pipeline can run the conformance check with no local Python
  toolchain (`Dockerfile`, `action.yml`, `docker-entrypoint.sh`).
- Documentation site: task-oriented guides, the fidelity contract, generated
  API reference, localization-ready configuration; includes worked examples
  ("bulk-editing glosses" and "building a LIFT export from scratch", complete
  runnable scripts with verified output) and
  a "Differences from the C# libraries" page summarizing where sil-lift
  deviates from SIL.Lift/LiftSorter behavior and why.
