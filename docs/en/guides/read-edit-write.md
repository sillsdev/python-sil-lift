# Read, edit, write

## Loading

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` accepts any well-formed LIFT **0.13** document — including
schema-invalid real-world files. Anything the model doesn't define (unknown
elements/attributes, comments) is carried losslessly in each node's opaque
`extra` bucket. Other LIFT versions raise `LiftParseError` naming the version.

## The model

Every LIFT element is a typed dataclass: `Entry`, `Sense`, `Example`,
`Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, and so on.
Multilingual text is a `Multitext`, which behaves like a mapping from
language code to `Text`:

```python
entry = lex.find(id="abat")

str(entry.lexical_unit["seh"])          # "abat"
entry.lexical_unit["en"] = "grove"      # plain strings are coerced
"en" in entry.citation                  # False
```

`Text` is structured — an ordered list of `str` and `Span` fragments — because
`<text>` can contain nested `<span>` markup. `str(text)` flattens to plain
text; the fragments keep the markup for round-tripping.

Glosses are *form-shaped* in LIFT (each `<gloss>` carries its own language),
so a sense has `glosses: list[Form]` plus a helper:

```python
sense = entry.senses[0]
sense.gloss("en")                       # Text | None
entry.gloss_langs()                     # {"en", "id"}
```

## Saving

```python
lex.save()                # back to where it was loaded from
lex.save("elsewhere.lift")
```

Entries you didn't modify are written back **byte-identical**; a document you
didn't modify at all is byte-identical from the first byte to the last. See
[Fidelity guarantees](../fidelity.md) for the precise contract.

## Building from scratch

```python
lex = sil_lift.Lexicon(producer="my-script 1.0")
entry = sil_lift.Entry(id="hello", guid="...")
entry.lexical_unit["en"] = "hello"
sense = sil_lift.Sense()
sense.glosses.append(sil_lift.Form("fr", sil_lift.Text(["bonjour"])))
entry.senses.append(sense)
lex.entries.append(entry)
lex.save("new.lift")
```

## Canonical sorting

```python
lex.sort()      # entries by (guid, id); ranges/field defs by id/tag
lex.save()      # untouched entries keep their exact bytes, in the new order

sil_lift.canonicalize("in.lift", "out.lift")   # fully re-serialized, diff-ready
```

See also: [Worked example: bulk-editing glosses](bulk-edit-glosses.md).
