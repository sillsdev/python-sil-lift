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

Each `Problem` carries `level` (`"error"`/`"warning"`), a stable `code`, `message`, and as much of an address as the finding has: `file` (`None` when the lexicon has no path), `entry_id` when it concerns one entry, `guid` when the object it concerns has one (an entry, or a range-element), and `line` when it maps to a line in the document. A finding about a range is addressed to the `.lift-ranges` companion that defines it, and carries no entry. Unset fields are `None` — `null` in `--format json`, where every key is always present.

## The layers

1. **RELAX NG** against the LIFT 0.13 grammar (vendored from lift-standard — a byte-identical copy committed into this package).
2. **Ranges schema** — this project's `lift-ranges-0.13.rng` — over every tracked `.lift-ranges` companion, addressed to the companion rather than the `.lift`.
3. **Semantic checks** the grammar cannot express — ten of them, one code each.

## Problem codes

Every finding carries one of these, whichever layer produced it — `schema` and `uri-not-rfc` come from the schema layers, the other ten are semantic checks. The strings are a supported interface; `--strict` promotes every warning to an error.

| code                     | level   | what it flags                                                              |
| ------------------------ | ------- | -------------------------------------------------------------------------- |
| `ambiguous-ranges-file`  | warning | several files answering to one companion name under case folding and NFC   |
| `dangling-ranges-href`   | warning | a header `range/@href` resolving to no companion file                      |
| `dangling-ref`           | error   | a `relation/@ref` or `variant/@ref` matching no entry or sense             |
| `duplicate-form-lang`    | warning | two forms in one multitext sharing a language                              |
| `duplicate-guid`         | error   | a guid reused among entries, or among one document's ranges/range-elements |
| `missing-id`             | error   | opt-in via `require_ids`: an entry without a guid, a sense without an id   |
| `missing-media`          | warning | a referenced audio or picture file not on disk                             |
| `normalization-mismatch` | warning | a name that reaches the id it refers to only under NFC                     |
| `range-parent`           | error   | a `range-element/@parent` no sibling id defines                            |
| `schema`                 | error   | a RELAX NG grammar violation, in the `.lift` or in a companion             |
| `undefined-range-value`  | warning | a grammatical-info or range-keyed trait value the range does not list      |
| `uri-not-rfc`            | warning | an href that is not a valid URI — FLEx's `file://C:/...`                   |

All three layers work from the document serialized as it stands, so one that cannot be serialized at all is reported as a single `lone-surrogate` error instead — see [Fidelity guarantees](../fidelity.md#content-xml-cannot-represent). Validating is read-only, which is the one way those bytes differ from the bytes `save()` writes: it reports the document before the `dateModified` stamping a save does. Nothing generated is ever a finding, so validate-then-save is sound.

A companion name matching several files loads none of them: the ranges they define go absent until all but one is renamed or removed.

## Real-world FieldWorks (FLEx) output

FieldWorks systematically writes some content that strict tooling rejects. Here is sil-lift's policy, so that real lexicons validate usefully:

- `file://C:/...` hrefs (invalid URIs) are reported as **warnings** (`uri-not-rfc`), not schema errors — the C# validator never rejected them.
- Legally interleaved children (e.g. `field, note, field, note` in a sense) are **not** flagged, working around a false positive in libxml2.
- FLEx's `trait`/`field` extensions inside `range-element` **are** reported (schema errors against the ranges schema): they are genuine spec deviations.
- Names are resolved against range and range-element `id`s under Unicode **NFC normalization** — `parent` links, range values, and the `trait` name or header `range` id that keys a range. FLEx normalizes to NFC on export, but some writes used to bypass that step, so a range-element `id` can be NFD while its labels, its own `parent`, and the `.lift` values naming it are NFC.
    - Compared exactly, a sound export looks broken — and a range whose `id` is spelled the other way goes unchecked entirely, since a trait name that reaches no range is silently accepted.
    - A name that matched only after normalizing is reported as a `normalization-mismatch` **warning**, once per id however many references differ, addressed to the file that defines it. The data is sound, but a consumer comparing raw strings will not resolve those references.
    - The ids are never rewritten: the file keeps the spellings it came with.
