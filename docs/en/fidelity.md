# Fidelity guarantees

LIFT is an _interchange_ format, so the first rule is **never drop what you do not understand**. `sil-lift`'s contract, verified by the test suite on every run (corpus files plus property-based generation):

## Reading

Any well-formed LIFT 0.13 document loads — schema-invalid content included. Whatever the model does not define is carried in the nearest node's opaque `Extras` container as _LIFT residue_ — FieldWorks' name for the same idea, which it stores in a `LiftResidue` field: unknown attributes and elements, XML comments and processing instructions, stray text, and malformed typed attributes (a bad date stays as the original string in `Extras`; the typed field is `None`).

## Saving an unchanged document

`load()` → `save()` with no edits writes **byte-identical output** — no reformatting, no re-escaping, no reordering, byte-order marks and XML declarations included. There is currently no normalization list: identity is exact. Timestamps are generated from content, so an unchanged document has none generated either.

Exceptions (the writer falls back to full canonical serialization, which is semantically complete but not byte-preserving):

- the source encoding is not ASCII-compatible (not UTF-8/US-ASCII), or
- the source contains a DOCTYPE, or
- the byte scanner and the parser disagree about the document's top-level structure — for instance an out-of-spec second `<header>`, which the parser keeps only once (the scanner is deliberately conservative: on any doubt it captures no source bytes at all), or
- the source was built in memory rather than loaded from a file.

## Saving an edited document

- **Untouched entries are emitted verbatim from their original bytes.** An entry counts as touched if any part of its model object changed since parse (detected by canonical-serialization snapshot, not a dirty flag).
- **Touched entries are re-serialized canonically and completely**: UTF-8, 2-space indentation _outside_ mixed content (whitespace inside `<text>` and `<span>` is never altered), a documented child grouping per element (e.g. entry: lexical-unit, citation, pronunciations, variants, senses, notes, relations, etymologies, annotations, traits, fields), fixed attribute order, dates in ISO-8601 (`Z` for UTC). All residue is re-emitted; its position is restored to the original child index, clamped to the new child list (an approximation — exact byte positions are only guaranteed for untouched entries).
- Adding, removing, or reordering entries re-serializes the document structure but still emits every unchanged entry's bytes verbatim.
- **A touched entry is stamped.** `save()` writes a fresh `dateModified` on every entry whose content changed since it was read, and fills a blank `dateCreated` with the same moment — an edit shipped under its loaded date looks unmodified to everything that reconciles on that attribute, FieldWorks and The Combine's LIFT import included. Only `<entry>` is stamped: no node below one, and nothing in the header. An entry whose date the caller set deliberately keeps it, and so does an entry created since the load that already carries one. A date the model could not parse is [residue](#reading) rather than a date, so a stamp replaces it and the original string is dropped — an edited entry is better off carrying a real date than `dateModified="whenever"`. `save(stamp=False)` writes the model exactly as it stands, residue included.
- **A generated stamp is the one thing in the output that is not a function of the input.** Stamps are UTC at seconds precision (`YYYY-MM-DDTHH:MM:SSZ` — the shape every surveyed FieldWorks export uses), read from the wall clock. `save(when=...)` supplies the moment instead, which is what keeps stamped output reproducible for a diff-based CI gate; it must be timezone-aware, and is normalized to UTC whole seconds so an explicit moment lands in that same form. One second holds one date, so an edit saved within a second of the previous one carries the same stamp.
- **Stamping commits with the write.** A refused or failed write puts the dates back, so the model never carries a modification date for output that does not exist.

!!! note "&quot;Canonical&quot; here is not related to any other Canonical XML"
    Canonical form on this page means `sil-lift`'s own documented shape, described in a bullet above. It is unrelated to W3C's Canonical XML (C14N) process. It is unrelated to `SIL.Core`'s `CanonicalXmlSettings` class.

## Content XML cannot represent

Non-BMP characters — emoji, CJK Extension B, Adlam, anything above U+FFFF — are ordinary content and round-trip byte-identically. A "surrogate pair" is a UTF-16 encoding detail: Python strings are sequences of codepoints, so nothing in the reader, the byte scanner, or the writer ever sees one.

A _lone_ surrogate (U+D800–U+DFFF) is different: a Python string may hold one, an XML document may not, in any encoding. It can never arrive from a file — the parser rejects both spellings, a `&#xD800;` character reference and CESU-8/WTF-8 bytes — only from a string assigned through the API. Saving such a model raises `LiftWriteError` naming the node and the codepoint and writes nothing; validation reports it as a single `lone-surrogate` error, since the document cannot be serialized for the schema layers to check.

## Known approximations (touched nodes only)

- Comments _inside_ a `<text>` run are preserved but moved next to the run, not kept at their exact character offset.
- Cross-type child order within an edited element is normalized to the canonical grouping (the LIFT schema's `interleave` makes this order semantically insignificant).
- A multitext element that is present but carries nothing — no forms, no residue, e.g. `<definition></definition>` — is not re-emitted. The model represents these fields as an always-present `Multitext` (`lexical-unit`, `citation`, `definition`, a relation's `usage`, and `label` / `abbrev` / `description` on url-refs, ranges, range-elements and the header), so an empty one is indistinguishable from an absent one after parsing. Nothing semantic is lost.
