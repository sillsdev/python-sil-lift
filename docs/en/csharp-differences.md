# Differences from the C# libraries

sil-lift is loosely analogous to SIL's C# LIFT tooling — chiefly `SIL.Lift` in [libpalaso](https://github.com/sillsdev/libpalaso) (parser, validator, migrator, `LiftSorter`) and the LIFT handlers in [Chorus](https://github.com/sillsdev/chorus). It is a fresh implementation, not a port. This page summarizes where behavior deliberately differs.

## Scope

| Capability         | C# libraries                       | sil-lift                                                   |
| ------------------ | ---------------------------------- | ---------------------------------------------------------- |
| LIFT versions      | 0.10–0.13 (migration built in)     | **0.13 only**; older versions rejected with a clear error  |
| Version migration  | `Migrator` (XSLT chain)            | none — use the XSLTs in lift-standard for one-off upgrades |
| 3-way merge / sync | Chorus                             | out of scope                                               |
| Validation         | RELAX NG only (`Validator`)        | RELAX NG + ranges schema + semantic checks                 |
| Streaming          | internal entry-granularity parsing | public `open_reader` / `open_writer` API                   |

## API shape

`SIL.Lift`'s parser is callback-driven (`ILexiconMerger`): it pushes parse events at a consumer. sil-lift instead returns a plain object graph — typed dataclasses for every LIFT element — because Python scripters want objects, not callbacks. The streaming API yields the _same_ `Entry` type, so there is no capability-reduced twin model.

## Round-trip fidelity

The strongest deliberate difference. Saving with `SIL.Lift` re-serializes the whole document. sil-lift guarantees:

- an unchanged document saves **byte-identically**, and
- untouched entries keep their exact source bytes even when other entries change (Chorus-grade byte chunking, applied automatically).

See [Fidelity guarantees](fidelity.md).

## Validation

The C# `Validator` runs one RELAX NG pass and reports the first errors as strings. sil-lift reports a structured, entry/line-addressed `Problem` stream, and its schema layer knowingly diverges in three places:

- **Invalid URIs are warnings, not errors.** The C# RELAX NG engine never enforced the `anyURI` datatype, so FLEx has been writing `file://C:/...` hrefs into real lexicons for years. Rejecting those files would flag virtually every FLEx export.
- **Schematron rules are enforced** (as semantic checks): duplicate form languages and similar co-constraints in the LIFT grammar were silently ignored by both C# and raw lxml validation.
- **Cross-file comparisons are Unicode-normalized**, because FLEx writes the `.lift` in NFC and the companion `.lift-ranges` in NFD.

sil-lift also validates standalone `.lift-ranges` files against a schema this project authored — no such schema (or check) exists in the C# world.

## Canonical sorting

`Lexicon.sort()` mirrors `LiftSorter`'s core rules (entries by case-insensitive guid; ranges and range-elements by id; header field definitions by tag; senses kept in file order; whitespace inside `<text>` never touched), with three differences:

- entries without a guid sort deterministically by id (`LiftSorter` assumes a guid is present);
- ordering is locale-independent (plain case-folded code points, not .NET invariant-culture collation);
- same-type lists such as notes, relations, and forms keep their document order rather than being re-sorted by key — grouping is already deterministic, and reordering them only adds diff noise.

The spec repo's `canonicalizeLift.xsl` is not used at all: it collapses whitespace inside lexical text (destructive) and its generated ids differ on every run.

## Not carried over

- WeSay-specific conveniences (dashboard/config handling around LIFT files).
- `SynchronicMerger` (Chorus update merging) — the byte-chunking idea lives on in the fidelity layer, the merging does not.
- LDML writing-system parsing: files in `WritingSystems/` are treated as opaque folder content.
