# Worked example: bulk-editing glosses

A common maintenance task: normalize spelling across every English gloss in a lexicon (British → American, or vice versa) without disturbing anything else in the file. This walks through one script that loads, edits, validates, and saves — showing the editing API and the fidelity guarantee working together.

## The script

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)

edited_glosses = 0

for entry in lex.entries:
    for sense in entry.all_senses():
        for gloss in sense.glosses:
            if gloss.lang != "en":
                continue
            old = str(gloss.text)
            new = old.replace("colour", "color")
            if new != old:
                gloss.text = sil_lift.Text([new])
                edited_glosses += 1

changed = lex.changed_entries()

errors = [p for p in lex.iter_problems() if p.level == "error"]
if errors:
    for problem in errors:
        print(problem)
    sys.exit(f"aborting: {len(errors)} validation error(s), nothing saved")

lex.save()
print(f"edited {edited_glosses} gloss(es) across {len(changed)} entry(ies)")
```

A few things worth noting:

- `entry.all_senses()` yields every sense _and subsense_, depth-first in document order.
    - `entry.senses` holds only the top level, so a bulk edit that walked it would silently skip any gloss nested under a subsense.
- `gloss.text` is a `Text`, not a plain string: `str(gloss.text)` flattens it for matching, and the replacement is written back with `sil_lift.Text([new])` rather than mutating the string in place.
- `lex.changed_entries()` reports which entries differ from the file as loaded. Since an entry's digest covers its whole subtree, an edit to a nested subsense reports the entry that contains it, while assigning a field the value it already had isn't reported.
- `changed_entries()` covers entry content only, so it is a count, not a write guard. To skip a save that would change nothing, use `lex.changes()`; see [Saving](read-edit-write.md#saving).
- Validating in memory (`lex.iter_problems()`) serializes the edited state first, so it correctly reflects the edit before anything is written to disk. Aborting on any `"error"`-level `Problem` — warnings are left for the caller to decide about — means a bad edit never reaches `save()`.
- `lex.save()` stamps a fresh `dateModified` on exactly the entries this script changed, filling `dateCreated` where it was blank. Without it a lexicon this script has rewritten would look untouched to FieldWorks or to The Combine's LIFT import, both of which decide what to update from that attribute — and it stamps `<entry>` only, however deep the edit went: the entry containing the edited subsense gloss, not the sense.

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
