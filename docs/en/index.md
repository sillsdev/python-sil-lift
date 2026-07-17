# sil-lift

A Python library for [LIFT](https://github.com/sillsdev/lift-standard) (Lexicon Interchange Format) 0.13: lossless read/write of the LIFT folder (`.lift` + `.lift-ranges` + media references), schema and semantic validation, and canonical sorting — with streaming APIs for large lexicons.

**Status: pre-release, under active development.**

## Install

From [PyPI](https://pypi.org/project/sil-lift/):

```
pip install sil-lift        # library
pip install sil-lift[cli]   # library + the sil-lift command
```

Requires Python 3.11+. The only runtime dependency is lxml.

## The 30-second tour

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # tracks .lift-ranges companions too

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("seh") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # or lex.find(id="hoofd_a1b2")
entry.senses[0].definition["en"] = "head (anatomy)"

lex.save()   # untouched entries byte-identical; edited entry re-serialized
```
