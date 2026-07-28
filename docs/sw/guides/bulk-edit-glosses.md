# Worked example: bulk-editing glosses

A common maintenance task: normalize spelling across every English gloss in a lexicon (British → American, or vice versa) without disturbing anything else in the file. This walks through one script that loads, edits, validates, and saves — showing the editing API and the fidelity guarantee working together.

## The script

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)


def iter_senses(senses):
    """Yield every sense, including subsenses (recursive)."""
    for sense in senses:
        yield sense
        yield from iter_senses(sense.subsenses)


edited_glosses = 0
touched_entries = set()

for entry in lex.entries:
    for sense in iter_senses(entry.senses):
        for gloss in sense.glosses:
            if gloss.lang != "en":
                continue
            old = str(gloss.text)
            new = old.replace("colour", "color")
            if new != old:
                gloss.text = sil_lift.Text([new])
                edited_glosses += 1
                touched_entries.add(entry.id)

errors = [p for p in lex.iter_problems() if p.level == "error"]
if errors:
    for problem in errors:
        print(problem)
    sys.exit(f"aborting: {len(errors)} validation error(s), nothing saved")

lex.save()
print(f"edited {edited_glosses} gloss(es) across {len(touched_entries)} entry(ies)")
```

A few things worth noting:

- `Sense.subsenses` is itself a `list[Sense]`, so `iter_senses` recurses into it — a bulk edit that only walked `entry.senses` would silently skip any gloss nested under a subsense.
- `gloss.text` is a `Text`, not a plain string: `str(gloss.text)` flattens it for matching, and the replacement is written back with `sil_lift.Text([new])` rather than mutating the string in place.
- Validating in memory (`lex.iter_problems()`) serializes the edited state first, so it correctly reflects the edit before anything is written to disk. Aborting on any `"error"`-level `Problem` — warnings are left for the caller to judge — means a bad edit never reaches `save()`.

Glosses aren't the only thing worth touching this way. The same `Multitext` mapping surface applies to definitions and every other multilingual field on an entry or sense:

```python
sense.definition["en"] = "the color of a thing"
```

## Running it

Run against a small lexicon with a gloss and a subsense gloss that both say "colour":

```
edited 2 gloss(es) across 1 entry(ies)
```

## The fidelity payoff

The guarantee is per _entry_: an entry whose model didn't change comes back out **byte-identical** to how it was read in, and only the entries you actually touched are re-serialized. In the run above, one entry had glosses edited — every other entry in the file kept its exact bytes. (Note the granularity: editing any part of an entry re-serializes that whole entry, including its untouched sibling senses.) Editing one gloss in a 50,000-entry lexicon therefore produces a diff touching one entry, not a reformatted file. See [Fidelity guarantees](../fidelity.md) for the precise contract.
