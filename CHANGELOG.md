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

## [0.1.0] - 2026-11-TBD

### Added

- Project scaffolding: package skeleton, vendored LIFT 0.13 RELAX NG schema,
  and a test corpus with provenance.
- A typed object model covering all 35 LIFT 0.13 elements.
  - Multilingual fields are `Multitext`, a mapping from language code to
    `Text`.
  - Every public dataclass is keyword-only past its leading fields.
- Reading: `sil_lift.load()` / `Lexicon.load()`, keeping out-of-schema
  content (LIFT residue) on each node in `Extras`.
- Writing with byte fidelity: `Lexicon.save()` writes unchanged documents and
  untouched entries back byte-identically.
  - Edited entries re-serialize canonically, out-of-schema content included.
  - Edited entries get a fresh `dateModified`; `when=` pins the moment for
    reproducible output, and `stamp=False` turns stamping off.
  - The contract is documented in `docs/en/fidelity.md`.
- Change detection against the loaded document.
  - `Lexicon.changes()` and `RangesFile.changes()` say whether a save would
    differ from the source, as a guard for skipping the write.
  - `Lexicon.changed_entries()` lists the entries whose content changed.
- LIFT folders: `.lift-ranges` companions are discovered on load and saved
  with the document, and `RangesFile` handles a standalone ranges document.
  - `check_media()` reports media references that don't resolve.
  - Helpers build a lexicon and its companions from scratch.
- Zipped LIFT packages: `sil_lift.load()` reads a `.zip`, and
  `Lexicon.save_zip()` writes one.
  - The CLI's `validate`, `stats`, `check-media`, and `export` accept a
    `.zip` path directly.
  - Extraction is capped (100,000 members, 10 GiB) and refuses members
    whose paths escape the extraction directory.
- Validation: `iter_problems()` and `Lexicon.iter_problems()` report
  `Problem`s from the RELAX NG schemas and thirteen semantic checks.
  - FLEx's `file://` hrefs, which the schema rejects, are reported as
    `uri-not-rfc` warnings, so real FLEx exports pass.
  - Every problem code is described in `docs/en/guides/validate.md`.
- Canonical sorting with `Lexicon.sort()` and `RangesFile.sort()`, and
  `sil_lift.canonicalize()` for fully re-serialized, diff-ready output.
  - Sorting moves untouched entries without rewriting them.
- Streaming for large files: `open_reader()` and `open_writer()` hold one
  entry in memory at a time.
- The `sil-lift` CLI: `validate`, `stats`, `sort`, `check-media`, and
  `export` (to CSV/TSV).
  - `validate` takes `--strict`, `--allow CODE`, `--require-ids`,
    `--no-check-media`, and `-` for stdin.
  - `validate`'s exit codes and `--format json` output are a supported
    interface for CI.
- A container image and GitHub Action that run `sil-lift validate` in CI with
  no Python toolchain.
- A documentation site: task-oriented guides, worked examples, an API
  reference, and a page on differences from the C# libraries.
