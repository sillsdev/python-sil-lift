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
