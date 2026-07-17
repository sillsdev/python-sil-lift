# sil-lift

A Python library for [LIFT](https://github.com/sillsdev/lift-standard)
(Lexicon Interchange Format) 0.13: lossless read/write of the LIFT folder
(`.lift` + `.lift-ranges` + media references), schema and semantic
validation, and canonical sorting — with streaming APIs for large lexicons.

**Status: pre-release, under active development.**

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")
for entry in lex.entries:
    ...
lex.save()
```

Task-oriented guides (reading and editing a lexicon, validating, working with
large files, media handling) will be added as the corresponding features land.
