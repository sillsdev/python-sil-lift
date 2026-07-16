# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
During 0.x, minor releases may contain breaking changes.

## [Unreleased]

### Added

- Project scaffolding: package skeleton, vendored LIFT 0.13 RELAX NG schema,
  test corpus with provenance, corpus-prep and large-file-generator tooling.
- M1: full object model (all 35 LIFT 0.13 elements as typed dataclasses),
  `sil_lift.load()` / `Lexicon.load()` full-document reader with per-node
  `Extras` residue capture, LIFT-version guard.
- M2: `Lexicon.save()` writer with byte-fidelity passthrough — unchanged
  documents and untouched entries are written byte-identically; touched
  entries re-serialize canonically with all out-of-schema content preserved.
  Fidelity contract documented in `docs/en/fidelity.md` and enforced by
  corpus byte-identity tests plus Hypothesis round-trip properties.
- Docs: "Differences from the C# libraries" page summarizing where sil-lift
  deviates from SIL.Lift/LiftSorter/Chorus behavior and why.
- M7: the `sil-lift` CLI (`validate` / `stats` / `sort` / `check-media`,
  stdlib-only, installed via the `[cli]` extra) and the documentation site
  (task-oriented guides, fidelity contract, mkdocstrings API reference,
  mkdocs-static-i18n wired for future localization).
- M6: streaming — `open_reader()` (lazy entry iterator with the parsed
  header available up front; iterparse cleanup internal) and `open_writer()`
  (header + one canonical chunk per entry; byte-identical to
  `canonical_document` output by construction), both over the same `Entry`
  types as full-document mode and O(one entry) in memory (verified on a
  ~340 MB generated file).
- M5: canonical sort — `Lexicon.sort()` / `RangesFile.sort()` (entries by
  case-folded guid/id, ranges/range-elements by id, field definitions by
  tag; LiftSorter-informed, locale-independent) and `sil_lift.canonicalize()`
  for fully re-serialized diff-ready output. Sorting composes with the
  passthrough: sort + save moves untouched entries' bytes without rewriting
  them. Text whitespace is never normalized (unlike `canonicalizeLift.xsl`).
- M4: validation — `validate_file()` / `iter_problems()` /
  `Lexicon.iter_problems()` returning an addressable `Problem` stream
  (file/entry/line). RELAX NG layer with two documented deviations from raw
  libxml2 (href masking with `uri-not-rfc` warnings; tag-grouped validation
  to sidestep libxml2's interleave limitation); authored ranges schema over
  companions; semantic checks: duplicate-guid, dangling-ref, range-parent,
  undefined-range-value (NFC-normalized), duplicate-form-lang,
  missing-media. Hand-authored negative corpus under `tests/corpus/negative/`.
- M3: LIFT-folder handling — `RangesFile` (standalone `.lift-ranges`
  documents, same fidelity guarantees), automatic companion
  discovery/tracking on load (`Lexicon.ranges_files`), `save()` writes
  companions together, `all_ranges()` merged view, `media_refs()` /
  `missing_media()` helpers; authored `schemas/lift-ranges-0.13.rng` — the
  first schema for standalone ranges documents (spec-faithful, built from
  the vendored grammar's own defines).
