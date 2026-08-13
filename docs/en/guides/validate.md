# Validate

Validation is always explicit — loading and saving never validate implicitly.

```python
import sil_lift

# Exhaustive: a lazy stream of Problems (schema + semantic layers).
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # error [dangling-ref] dictionary.lift:88 (entry apu): ref 'nope' matches ...

# Fail-fast: raises LiftValidationError on the first error-level problem.
sil_lift.validate_file("dictionary.lift")

# In-memory state (serializes first — a documented cost on large lexicons):
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

Each `Problem` carries `level` (`"error"`/`"warning"`), a stable `code`, `message`, and an address: `file`, plus `entry_id`, `guid`, and `line` when the finding belongs to one entry. Findings about a document rather than an entry — `range-parent`, `normalization-mismatch`, `dangling-ranges-href` — carry the file alone (for a finding about a range, the `.lift-ranges` companion that defines it), and the unset fields are `None` (`null` in `--format json`, where every key is always present).

## The layers

1. **RELAX NG** against the LIFT 0.13 grammar (vendored from lift-standard — a byte-identical copy committed into this package).
2. **Ranges schema** — this project's `lift-ranges-0.13.rng` — over every tracked `.lift-ranges` companion.
3. **Semantic checks** the grammar cannot express: `duplicate-guid`, `dangling-ref`, `range-parent`, `undefined-range-value`, `normalization-mismatch`, `duplicate-form-lang`, `missing-media`.

## Real-world FieldWorks (FLEx) output

FieldWorks systematically writes some content that strict tooling rejects. Here is sil-lift's policy, so that real lexicons validate usefully:

- `file://C:/...` hrefs (invalid URIs) are reported as **warnings** (`uri-not-rfc`), not schema errors — the C# validator never rejected them.
- Legally interleaved children (e.g. `field, note, field, note` in a sense) are **not** flagged, working around a false positive in libxml2.
- FLEx's `trait`/`field` extensions inside `range-element` **are** reported (schema errors against the ranges schema): they are genuine spec deviations.
- Names are resolved against range and range-element `id`s under Unicode **NFC normalization** — `parent` links, range values, and the `trait` name or header `range` id that keys a range. FLEx normalizes to NFC on export, but a few writes bypass that step, so a range-element `id` can be NFD while its labels, its own `parent`, and the `.lift` values naming it are NFC.
    - Compared exactly, a sound export looks broken — and a range whose `id` is spelled the other way goes unchecked entirely, since a trait name that reaches no range is silently accepted.
    - A name that matched only after normalizing is reported as a `normalization-mismatch` **warning**, once per id however many references differ, addressed to the file that defines it. The data is sound, but a consumer comparing raw strings — a Send/Receive merge, say — will not resolve those references.
    - The ids are never rewritten: the file keeps the spellings it came with.
