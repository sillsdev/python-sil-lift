# sil-lift

A Python library for [LIFT](https://github.com/sillsdev/lift-standard) (Lexicon
Interchange FormaT) 0.13: lossless read/write of the LIFT folder (`.lift` \+
`.lift-ranges` \+ media references), RELAX NG and semantic validation, and
canonical sorting — with streaming APIs for large lexicons.

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")      # tracks .lift-ranges companions too
for entry in lex.entries:
    ...
entry = lex.find(id="hoofd_a1b2")
entry.senses[0].definition["en"] = "head (anatomy)"
lex.save()                                 # untouched entries byte-identical
```

**Status: pre-release, under active development.** The API is not yet stable.

Requires Python 3.11+; the only runtime dependency is lxml. Install it
[from PyPI](https://pypi.org/project/sil-lift/) with `pip install sil-lift`;
that includes the `sil-lift` command (`validate` / `stats` / `sort` /
`check-media` / `export`).
Documentation is at <https://sillsdev.github.io/python-sil-lift/> (source in
`docs/en/`, mkdocs-material; build locally with
`pip install -e .[docs] && mkdocs build --strict`).

## Fidelity guarantees

`sil-lift` treats LIFT as an _interchange_ format: it never drops what it does
not understand.

- Saving an unchanged document is **byte-identical** (no reformatting, ever).
- Entries you did not modify are written back **byte-identical**, even when
  other entries changed.
- Entries you did modify are re-serialized in a documented canonical form, with
  all out-of-schema content (unknown elements, attributes, comments) preserved.
- Whitespace inside `<text>` is never altered — not even for indentation.

The precise rules and their few edge cases are documented in
[docs/en/fidelity.md](docs/en/fidelity.md); they are enforced by corpus-wide
byte-identity tests and property-based (Hypothesis) round-trip tests.

## Scope

- LIFT **0.13 only** — the de facto standard version. Other versions are
  rejected with a clear error; one-off migration of legacy files is possible
  with the XSLTs in the
  [lift-standard](https://github.com/sillsdev/lift-standard) repository.
- No merging and no LDML interpretation (writing-system files are carried, not
  parsed).

## Versioning

[SemVer](https://semver.org/). During 0.x, minor releases may contain breaking
changes; see [CHANGELOG.md](CHANGELOG.md). The public API is exactly what
`sil_lift` re-exports at the top level.

## Contributing

[CONTRIBUTING.md](CONTRIBUTING.md)

## License

[MIT](LICENSE)
