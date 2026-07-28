# Отличия от библиотек C\#

sil-lift в общих чертах аналогичен инструментарию SIL для C# LIFT — в первую очередь `SIL.Lift` из [libpalaso](https://github.com/sillsdev/libpalaso) (парсер, валидатор, мигратор, `LiftSorter`), `SIL.DictionaryServices` в том же репозитории (модель `LexEntry`/`LexSense` с собственным считывателем/записывателем LIFT, которую используют The Combine и WeSay), а также обработчики LIFT в [Chorus](https://github.com/sillsdev/chorus). Это новая реализация, а не порт. На этой странице приведены краткие сведения о том, в каких случаях поведение намеренно отличается.

## Область применения

| Возможности                         | Библиотеки C#                                    | sil-lift                                                                                |
| ----------------------------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------- |
| Версии LIFT                         | 0,10–0,13 (с учётом миграции) | **Только версия 0.13**; более старые версии отклоняются с явной ошибкой |
| Переход на новую версию             | `Migrator` (цепочка XSLT)     | нет — использовать XSLT-файлы из пакета lift-standard для разовых обновлений            |
| 3-стороннее слияние / синхронизация | Chorus                                           | out of scope                                                                            |
| Validation                          | RELAX NG only (`Validator`)   | RELAX NG + ranges schema + semantic checks                                              |
| Streaming                           | internal entry-granularity parsing               | public `open_reader` / `open_writer` API                                                |

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
