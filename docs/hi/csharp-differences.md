# C# लाइब्रेरियों से अंतर

sil-lift मोटे तौर पर SIL के C# LIFT टूलिंग के समान है — मुख्य रूप से [libpalaso](https://github.com/sillsdev/libpalaso) में `SIL.Lift` (पार्सर, वैलिडेटर, माइग्रेटर, `LiftSorter`), `SIL.DictionaryServices` उसी रिपॉजिटरी में (`LexEntry`/`LexSense` मॉडल, अपने स्वयं के LIFT रीडर/राइटर के साथ, जिसका उपयोग The Combine और WeSay करते हैं), और [Chorus](https://github.com/sillsdev/chorus) में LIFT हैंडलर। यह एक नया कार्यान्वयन है, पोर्ट नहीं। यह पृष्ठ उन स्थानों का सारांश प्रस्तुत करता है जहाँ व्यवहार जानबूझकर भिन्न होता है।

## दायरा

| क्षमता              | सी# लाइब्रेरीज़                                                                      | सिल-लिफ्ट                                                                                            |
| ------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| लिफ्ट संस्करण       | 0.10–0.13 (स्थानांतरण अंतर्निहित) | केवल **0.13**; पुराने संस्करणों को एक स्पष्ट त्रुटि के साथ अस्वीकार कर दिया जाता है। |
| संस्करण माइग्रेशन   | `Migrator` (XSLT श्रृंखला)                                        | कोई नहीं — एकमुश्त अपग्रेड के लिए लिफ्ट-स्टैंडर्ड में मौजूद XSLTs का उपयोग करें।                     |
| 3-तरफ़ा मर्ज / सिंक | Chorus                                                                               | out of scope                                                                                         |
| Validation          | RELAX NG only (`Validator`)                                       | RELAX NG + ranges schema + semantic checks                                                           |
| Streaming           | internal entry-granularity parsing                                                   | public `open_reader` / `open_writer` API                                                             |

## API shape

`SIL.Lift`'s parser is callback-driven (`ILexiconMerger`): it pushes parse events at a consumer. sil-lift instead returns a plain object graph — typed dataclasses for every LIFT element — because Python scripters want objects, not callbacks. `SIL.DictionaryServices` does layer a `LexEntry`/`LexSense` object model over `SIL.Lift`, but as an application model it represents only the constructs those apps use — so re-serializing through it can't preserve out-of-model content the way sil-lift's residue capture and byte fidelity do (see below). The streaming API yields the _same_ `Entry` type, so there is no capability-reduced twin model.

## Round-trip fidelity

The strongest deliberate difference. Saving with `SIL.Lift` re-serializes the whole document. sil-lift guarantees:

- an unchanged document saves **byte-identically**, and
- untouched entries keep their exact source bytes even when other entries change (Chorus-grade byte chunking, applied automatically).

See [Fidelity guarantees](fidelity.md).

## Validation

The C# `Validator` runs one RELAX NG pass and reports the first errors as strings. sil-lift reports a structured, entry/line-addressed `Problem` stream, and its schema layer knowingly diverges in three places:

- **Invalid URIs are warnings, not errors.** The C# RELAX NG engine never enforced the `anyURI` datatype, so FieldWorks (FLEx) has been writing `file://C:/...` hrefs into real lexicons for years. Rejecting those files would flag virtually every FLEx export.
- **Schematron rules are enforced** (as semantic checks): duplicate form languages and similar co-constraints in the LIFT grammar were silently ignored by both C# and raw lxml validation.
- **Cross-file comparisons are Unicode-normalized**, because FLEx writes the `.lift` in NFC and the companion `.lift-ranges` in NFD.

sil-lift also validates the `.lift-ranges` companions of a loaded lexicon against a schema for standalone ranges documents (vendored from `lift-standard` alongside the base LIFT grammar) — every tracked external ranges file is checked whenever the `.lift` is validated — with no such schema (or check) in the C# world. (There is no entry point for validating a `.lift-ranges` file on its own, detached from a `.lift`.)

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
