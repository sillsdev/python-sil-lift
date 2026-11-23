# Отличия от библиотек C\#

sil-lift в общих чертах аналогичен инструментарию SIL для C# под названием LIFT, в основном состоящему из двух частей [libpalaso](https://github.com/sillsdev/libpalaso):

- `SIL.Lift`: парсер, валидатор, инструмент миграции, `LiftSorter`.
- `SIL.DictionaryServices`: модель `LexEntry`/`LexSense` с собственным модулем чтения/записи LIFT, которую используют The Combine и WeSay.

sil-lift — это новая реализация, а не порт. На этой странице приведены краткие сведения о том, в каких случаях поведение намеренно отличается.

## Область применения

| Возможности             | Библиотеки C#                                                         | sil-lift                                                                                |
| ----------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Версии LIFT             | 0,10–0,13 (с учётом миграции)                      | **Только версия 0.13**; более старые версии отклоняются с явной ошибкой |
| Переход на новую версию | `Migrator` (цепочка XSLT)                          | нет; для разовых обновлений используйте XSLT-файлы из пакета lift-standard              |
| Валидация               | Только RELAX NG (`Validator`)                      | RELAX NG + проверки схемы и семантики                                                   |
| Потоковое вещание       | внутренний синтаксический анализ с гранулярностью на уровне элементов | публичный API `open_reader` / `open_writer`                                             |

## Формат API

Парсер `SIL.Lift` работает на основе обратных вызовов (`ILexiconMerger`): он передаёт события разбора потребителю. sil-lift instead returns a plain object graph (typed dataclasses for every LIFT element) because Python scripters want objects, not callbacks.

`SIL.DictionaryServices` does layer a `LexEntry`/`LexSense` object model over `SIL.Lift`, but it is an application model: it represents only the constructs those apps use. Re-serializing through it therefore can't preserve out-of-model content the way sil-lift's LIFT residue handling and byte fidelity do (see below).

API потоковой обработки возвращает _тот же самый_ тип `Entry`, поэтому нет необходимости осваивать вторую, упрощённую модель.

## Точность воспроизведения в обоих направлениях

Самое явное намеренное отличие. При сохранении с помощью `SIL.Lift` происходит повторная сериализация всего документа. Компания «Sil-Lift» гарантирует:

- неизменённый документ сохраняется **с идентичным количеством байтов**, и
- untouched entries keep their exact source bytes even when other entries change: per-entry byte chunking, applied automatically.

См. [Гарантии Fidelity](fidelity.md).

## Валидация

Валидатор `Validator` на языке C# выполняет один проход по RELAX NG и возвращает первые ошибки в виде строк. sil-lift reports a structured `Problem` stream, each carrying the file, entry, and line it concerns. Its schema layer knowingly diverges in three places:

- **Недопустимые URI являются предупреждениями, а не ошибками.** Движок C# RELAX NG никогда не обеспечивал соблюдение типа данных `anyURI`, поэтому FieldWorks (FLEx) на протяжении многих лет записывает ссылки `file://C:/...` в реальные лексиконы. Отказ от этих файлов привёл бы к отметке практически каждого экспорта из FLEx.
- **Schematron rules are enforced** (as semantic checks): duplicate form languages and similar co-constraints in the LIFT grammar were silently ignored by C# validation.
- **Range id comparisons are Unicode-normalized** (NFC), because FLEx exports mix NFC and NFD ids. References that resolve only after normalizing are reported as `normalization-mismatch` warnings, a check with no C# counterpart. See [Real-world FieldWorks (FLEx) output](guides/validate.md#real-world-fieldworks-flex-output).

When sil-lift validates a `.lift`, it also validates the `.lift-ranges` companions against a schema for standalone ranges documents, vendored from `lift-standard`. The C# `Validator` does not check `.lift-ranges` files.

## Каноническая сортировка

`Lexicon.sort()` повторяет основные правила `LiftSorter` (записи сортируются по GUID без учета регистра; диапазоны и элементы диапазонов — по ID; определения полей заголовка — по тегам; значения слов сохраняются в том же порядке, что и в файле; пробелы внутри `<text>` никогда не изменяются), за исключением трёх отличий:

- записи без GUID сортируются детерминированно по ID (класс `LiftSorter` предполагает наличие GUID);
- порядок сортировки не зависит от локали (используются кодовые точки без учета регистра, а не сортировка с инвариантной культурой в .NET);
- same-type lists such as notes, relations, and forms keep their document order rather than being re-sorted by key; grouping is already deterministic, and reordering them only adds diff noise.

Файл `canonicalizeLift.xsl` из репозитория спецификаций вообще не используется: он сжимает пробелы внутри лексического текста (деструктивно), а сгенерированные им идентификаторы при каждом запуске отличаются друг от друга.

## Не перенесено

- Удобства, характерные для WeSay (работа с панелью управления и настройками, связанными с файлами LIFT).
- `SynchronicMerger` (LIFT update-file merging): the byte-chunking idea lives on in the fidelity layer, the merging does not.
- Анализ систем письма LDML: файлы в папке `WritingSystems/` рассматриваются как непрозрачное содержимое папки.
