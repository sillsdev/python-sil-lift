# Read, edit, write

## Loading

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` accepts any well-formed LIFT **0.13** document, including schema-invalid real-world files. Anything the model doesn't define (unknown elements/attributes, comments) is carried losslessly as LIFT residue in each node's opaque `extra` field. Other LIFT versions raise `LiftParseError` naming the version.

## The model

Every LIFT element is a typed dataclass: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, and so on.

### Multilingual text

Multilingual text is a `Multitext`, which is a `Mapping` from language code to `Text`:

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # "poʻo"
entry.lexical_unit["en"] = "head"       # plain strings are coerced
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

`Text` is structured (an ordered list of `str` and `Span` fragments) because `<text>` can contain nested `<span>` markup. `str(text)` flattens to plain text; the fragments keep the markup for round-tripping.

The mapping shows one value per language. Underneath, `forms` holds every `<form>` in file order. A schema-valid document has at most one form per language, but real files sometimes repeat one.

Because the mapping is keyed by language, `len()` counts languages rather than forms, and the `keys()`, `values()` and `items()` views list each language once. Both mutators also act on the whole language: `del entry.lexical_unit["en"]` removes every English form, and assigning to `"en"` leaves exactly one.

For a repeated language, `entry.lexical_unit["en"]`, `get()`, `values()` and `items()` all answer with its first form, and [`validate`](validate.md#problem-codes) reports `duplicate-form-lang` until you assign to that language.

A form carrying no `lang` at all cannot be created through the mapping. It is reported as `form-missing-lang`, and is dropped when its node re-serializes.

### Senses and glosses

Glosses are _form-shaped_ in LIFT (each `<gloss>` carries its own language), so a sense has `glosses: list[Form]` plus helpers:

```python
sense = entry.senses[0]       # top level only
sense.gloss("en")             # Text | None
entry.all_senses()            # every sense and subsense, document order
entry.gloss_langs()           # {"en", "id"}, subsenses included
```

Reach for `all_senses()` whenever a question concerns the whole entry: counting senses, collecting languages, finding media. `entry.senses` gives the top level, which is what you want only when the nesting itself matters.

## Saving

```python
lex.save()                    # back to where it was loaded from
lex.save("elsewhere.lift")
```

Entries you didn't modify are written back **byte-identical**; a document you didn't modify at all is byte-identical from the first byte to the last. See [Fidelity guarantees](../fidelity.md) for the precise contract.

### Timestamps

The entries you did modify go out with a fresh `dateModified` (and a `dateCreated` if they had none), so an edit doesn't ship under the date it was loaded with. Tools that merge LIFT decide what changed from that attribute. Two arguments adjust the stamping:

- `lex.save(stamp=False)` writes the dates the model holds and nothing more.
- `lex.save(when=...)` pins the moment instead of reading the clock.

See [Generated timestamps](../fidelity.md#generated-timestamps) for the rest of the rules.

### Skipping a save that changes nothing

To skip a save that would change nothing, guard it with `lex.changes()`:

```python
if lex.changes():
    lex.save()
```

It returns `False` only when `save()` would reproduce the source bytes, covering the entries, the header, the root element, and every `.lift-ranges` companion. Skipping the write leaves the file's modification time alone and avoids a spurious diff.

The check is cheap. It stops at the first difference, so on an edited lexicon it costs almost nothing. An unchanged lexicon has to be serialized in full to prove it unchanged, but that still costs less than the save it skips.

It compares content, not destination, so guard only an in-place save. `lex.save("elsewhere.lift")` writes the document and its companions to the new path even when `changes()` is `False`, so guarding it would skip that copy.

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
