# sil-lift

A Python library for [LIFT](https://github.com/sillsdev/lift-standard) (Lexicon
Interchange Format) 0.13: lossless read/write of the LIFT folder (`.lift` +
`.lift-ranges` + media references), RELAX NG and semantic validation, and
canonical sorting — with streaming APIs for large lexicons.

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")
for entry in lex.entries:
    ...
lex.save()
```

**Status: pre-release, under active development.** The API is not yet stable.

## Fidelity guarantees

`sil-lift` treats LIFT as an *interchange* format: it never drops what it does
not understand.

- Entries you did not modify are written back **byte-identical**.
- Entries you did modify are re-serialized in a documented canonical form, with
  all out-of-schema content (unknown elements, attributes, comments) preserved.

## Scope

- LIFT **0.13 only** — the de facto standard version. Other versions are
  rejected with a clear error; one-off migration of legacy files is possible
  with the XSLTs in the [lift-standard](https://github.com/sillsdev/lift-standard)
  repository.
- No merging (see [Chorus](https://github.com/sillsdev/chorus)) and no LDML
  interpretation (writing-system files are carried, not parsed).

## Versioning

[SemVer](https://semver.org/). During 0.x, minor releases may contain breaking
changes; see `CHANGELOG.md`. The public API is exactly what `sil_lift`
re-exports at the top level.

## License

[MIT](LICENSE)
