# Validate

Validation is always explicit: loading and saving never validate implicitly.

```python
import sil_lift

# Exhaustive: a lazy stream of Problems (schema + semantic layers).
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # error [dangling-ref] dictionary.lift:88 (entry apu): ref 'nope' matches ...

# Fail-fast: stop at the first error-level problem.
if any(p.level == "error" for p in sil_lift.iter_problems("dictionary.lift")):
    raise SystemExit(1)

# In-memory state (serializes first, a documented cost on large lexicons):
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

Each `Problem` carries `level` (`"error"`/`"warning"`), a stable `code`, and a `message`, plus as much of an address as the finding has:

- `file`: `None` when the lexicon has no path.
- `entry_id`: set when the finding concerns one entry.
- `guid`: set when the object it concerns has one (an entry, or a range-element).
- `line`: set when the finding maps to a line in the document.

A finding about a range is addressed to the `.lift-ranges` companion that defines it, and carries no entry. Unset fields are `None` (`null` in `--format json`, where every key is always present).

## The layers

1. **LIFT schema** (`lift-0.13.rng`, the LIFT 0.13 RELAX NG grammar, vendored byte-identical from lift-standard) over the `.lift`.
2. **Ranges schema** (`lift-ranges-0.13.rng`, also vendored from lift-standard) over every tracked `.lift-ranges` companion, addressed to the companion rather than the `.lift`.
3. **Semantic checks** the schemas cannot express: thirteen of them, one code each.

## Problem codes

Every finding carries one of these, whichever layer produced it: `schema` and `uri-not-rfc` come from the schema layers, the others are semantic checks. Every code is checked by default except `missing-id`, which is opt-in: pass `require_ids=True` (or `--require-ids`) to enable it. The codes are stable, so scripts can match on them. `--strict` promotes every warning to an error. `sil-lift validate --allow CODE` leaves a code out of the pass/fail decision.

| code                     | level   | what it flags                                                              |
| ------------------------ | ------- | -------------------------------------------------------------------------- |
| `ambiguous-ranges-file`  | warning | several files answering to one companion name under case folding and NFC   |
| `dangling-ranges-href`   | warning | a header `range/@href` resolving to no companion file                      |
| `dangling-ref`           | error   | a `relation/@ref` or `variant/@ref` matching no entry or sense             |
| `duplicate-form-lang`    | warning | two forms in one multitext sharing a language                              |
| `duplicate-guid`         | error   | a guid reused among entries, or among one document's ranges/range-elements |
| `form-missing-lang`      | error   | a `<form>` or `<gloss>` without the `lang` the schema requires             |
| `media-href-mismatch`    | warning | a media href that reaches its file only under case folding or NFC          |
| `missing-id`             | error   | **[opt-in]** an entry without a guid, a sense without an id                |
| `missing-media`          | warning | a referenced audio or picture file not on disk                             |
| `normalization-mismatch` | warning | a name that reaches the id it refers to only under NFC                     |
| `range-parent`           | error   | a `range-element/@parent` no sibling id defines                            |
| `schema`                 | error   | a RELAX NG grammar violation, in the `.lift` or in a companion             |
| `undefined-range-value`  | warning | a grammatical-info or range-keyed trait value the range does not list      |
| `unreadable-ranges-file` | warning | a companion candidate that exists but is not a readable ranges document    |
| `uri-not-rfc`            | warning | an href that is not a valid URI (FLEx's `file://C:/...`)                   |

### What validation sees

All three layers work from the document serialized as it stands, so one that cannot be serialized at all is reported as a single `lone-surrogate` error instead. See [Fidelity guarantees](../fidelity.md#content-xml-cannot-represent).

Validation is read-only: it reports the document as it stands, before a save stamps `dateModified`. The stamps never cause a finding, so a document that passes validation still passes once saved.

### Companion-folder codes

A companion name matching several files loads none of them: the ranges they define go absent until all but one is renamed or removed.

The three companion-folder codes (`ambiguous-ranges-file`, `dangling-ranges-href`, and `unreadable-ranges-file`) are reported only when companion discovery ran:

- Loading with `resolve_ranges=False` puts companions out of scope, so none of them is reported.
- Attaching one afterwards with `add_ranges_file()` does not bring them back, since it never reads the folder these codes report on.

`resolve_ranges=False` does not affect `missing-media` or `media-href-mismatch`: media is never resolved into the model, so there is nothing to opt out of.

### Media codes

sil-lift looks for each media file at its href as given, as well as under `audio/` (pronunciation media) or `pictures/` (illustrations). That folder is sil-lift's own guess, not something the document wrote, so it matches any capitalization and its spelling is never reported.

`missing-media` and `media-href-mismatch` divide the media check between them: the first means no file answered the href under any spelling, the second that one did but the href does not name it exactly. The second is the portability finding: the file is here, and a case-sensitive host serving this folder will not find it.

A misspelled _folder_ is one rename however many references cross it, so it is reported once and carries no entry. A misspelled _filename_ is reported per reference, addressed to the entry that wrote it.

## Real-world FieldWorks (FLEx) output

FieldWorks systematically writes some content that strict tooling rejects. Here is sil-lift's policy, so that real lexicons validate usefully:

- `file://C:/...` hrefs (invalid URIs) are reported as **warnings** (`uri-not-rfc`), not schema errors; the C# validator never rejected them.
- Legally interleaved children (e.g. `field, note, field, note` in a sense) are **not** flagged; this ignores a false positive in libxml2.
- FLEx's `trait`/`field` extensions inside `range-element` **are** reported (schema errors against the ranges schema): they are genuine spec deviations.
- Names are resolved against range and range-element `id`s under Unicode **NFC normalization**: `parent` links, range values, and the `trait` name or header `range` id that keys a range.
    - FLEx normalizes to NFC on export, but some writes used to bypass that step, so a range-element `id` can be NFD while its labels, its own `parent`, and the `.lift` values naming it are NFC.
    - Exact comparison would get this wrong in two ways. References to an NFD id would be reported as broken, although the export is sound. And a range whose own `id` is NFD would go unchecked: no trait name would match it, and a trait whose name matches no range is accepted as-is.
    - A name that matched only after normalizing is reported as a `normalization-mismatch` **warning**, once per id rather than once per reference, addressed to the file that defines it. The data is sound, but a consumer comparing raw strings will not resolve those references.
    - The ids are never rewritten: the file keeps the spellings it came with.
