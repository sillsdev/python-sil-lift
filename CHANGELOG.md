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
  `sil_lift.load()` / `Lexicon.load()` full-document reader with per-node
  `Extras` residue capture; LIFT-version guard.
- `Lexicon.save()` writer with byte-fidelity passthrough — unchanged
  documents and untouched entries are written byte-identically; touched entries
  re-serialize canonically with all out-of-schema content preserved. Fidelity
  contract documented in `docs/en/fidelity.md` and enforced by corpus
  byte-identity tests plus Hypothesis round-trip properties.
- LIFT-folder handling: `RangesFile` (standalone `.lift-ranges` documents,
  same fidelity guarantees), automatic companion discovery/tracking on load
  (`Lexicon.ranges_files`), `save()` writes companions together,
  `all_ranges()` merged view, `media_refs()` / `missing_media()` helpers,
  build-from-scratch helpers `Lexicon.add_ranges_file()` /
  `RangesFile.add_range()` / `Range.add_element()` (`save()` writes and
  header-references a new companion beside the `.lift`); authored
  `schemas/lift-ranges-0.13.rng` — the first schema for standalone
  ranges documents (spec-faithful, built from the vendored grammar's own
  defines).
- Zipped LIFT packages: `sil_lift.load()` reads a `.zip` (both the flat and
  folder-wrapped layouts, junk entries like `__MACOSX` ignored),
  `Lexicon.save_zip()` writes one (carrying media, `WritingSystems/`, and other
  package files through verbatim); `validate`, `stats`, `check-media`, and
  `export` accept a `.zip` path on the CLI. Extraction rejects path-traversal
  members and is capped (entry count and a 10 GiB uncompressed total) against
  zip bombs.
- Validation: `validate_file()` / `iter_problems()` /
  `Lexicon.iter_problems()` returning an addressable `Problem` stream
  (file/entry/line). RELAX NG layer with two documented deviations from raw
  libxml2 (href masking with `uri-not-rfc` warnings; tag-grouped validation to
  sidestep libxml2's interleave limitation); authored ranges schema over
  companions; semantic checks: duplicate-guid, dangling-ref, range-parent,
  undefined-range-value (NFC-normalized), duplicate-form-lang, missing-media,
  dangling-ranges-href, and (opt-in via `require_ids`) missing-id.
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
  over the same `Entry` types as full-document mode and O(one entry) in
  memory (verified on a ~340 MB generated file).
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
  deviates from SIL.Lift/LiftSorter/Chorus behavior and why.
