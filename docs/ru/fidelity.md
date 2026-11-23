# Гарантии Fidelity

LIFT — это _промежуточный_ формат, поэтому первое правило гласит: **никогда не удаляйте то, чего не понимаете**. Контракт `sil-lift`, проверка которого осуществляется набором тестов при каждом запуске (файлы корпуса плюс генерация на основе свойств):

## Чтение

Any well-formed LIFT 0.13 document loads, schema-invalid content included. Whatever the model does not define is carried in the nearest node's opaque `Extras` container as _LIFT residue_. (That is FieldWorks' name for the same idea, which it stores in a `LiftResidue` field.) Residue includes:

- unknown attributes and elements;
- XML comments and processing instructions;
- stray text;
- malformed typed attributes: a bad date stays as the original string in `Extras`, and the typed field is `None`.

## Сохранение документа без изменений

`load()` → `save()` with no edits writes **byte-identical output**: no reformatting, no re-escaping, no reordering, byte-order marks and XML declarations included. В настоящее время список нормализации отсутствует: тождество является точным. Временные метки генерируются на основе содержимого, поэтому в неизменённом документе они также не генерируются.

Исключения (автор переходит к полной канонической сериализации, которая является семантически полной, но не сохраняет байтовую структуру):

- кодировка исходного текста не совместима с ASCII (не UTF-8/US-ASCII), или
- источник содержит DOCTYPE, либо
- the byte scanner and the parser disagree about the document's top-level structure, for instance an out-of-spec second `<header>`, which the parser keeps only once, or
- исходный код был скомпилирован в памяти, а не загружен из файла.

The byte scanner is deliberately conservative: on any doubt it captures no source bytes at all.

## Сохранение отредактированного документа

- **Неизмененные записи выводятся дословно из исходных байтов.** Запись считается измененной, если какая-либо часть её объекта модели изменилась с момента синтаксического анализа (что определяется по моментальному снимку канонической сериализации, а не по флагу «dirty»).
- **Выделенные записи повторно сериализуются в каноническом виде и в полном объёме.** Канонический вид выглядит следующим образом:
  - UTF-8.
  - Отступ в 2 пробела _снаружи_ смешанного контента; пробелы внутри `<text>` и `<span>` никогда не изменяются.
  - Документированная группировка элементов по категориям; для `<entry>`: лексическая единица, цитата, варианты произношения, варианты слова, значения, примечания, связи, этимологии, аннотации, характеристики, области.
  - Исправлен порядок атрибутов.
  - Даты в формате ISO-8601 (символ `Z` обозначает UTC).
- **All residue is re-emitted.** Its position is restored to the original child index, clamped to the new child list; that is an approximation, since exact byte positions are only guaranteed for untouched entries.
- Добавление, удаление или изменение порядка записей приводит к повторной сериализации структуры документа, однако байты каждой неизменённой записи по-прежнему выводятся дословно.
- **A touched entry is stamped** with a fresh `dateModified`, and a `dateCreated` if it had none. See [Generated timestamps](#generated-timestamps).

!!! note "&quot;Канонический XML-файл&quot; , приведенный здесь, не связан с каким-либо другим каноническим XML-файлом"

    Под «канонической формой» на этой странице понимается собственная, задокументированная форма `sil-lift`, описанная в одном из пунктов выше. Это не имеет отношения к процессу W3C по стандарту Canonical XML (C14N). Это не имеет отношения к классу `CanonicalXmlSettings` из `SIL.Core`.

## Сгенерированные временные метки

Сгенерированный штамп — это единственный элемент в выходных данных, который не зависит от входных данных.

### Which entries are stamped

- **Что помечается.** Каждая запись, содержание которой изменилось с момента её прочтения, с обновлённым полем `dateModified` и, если у неё не было этого поля, с полем `dateCreated`, установленным на тот же момент времени. Изменение, отправленное до даты его загрузки, выглядит как неизменённое для всех систем, выполняющих сверку по данному атрибуту, включая FieldWorks и импорт LIFT в The Combine.
- **Только записи.** Никаких узлов ниже `<entry>`, и ничего в заголовке.
- **Что остаётся без изменений.** Запись, дату которой вызывающая сторона установила намеренно, а также запись, созданная после загрузки и уже содержащая такую дату.
- **Очистка даты выполняется.** `entry.date_modified = None` при чтении записи с таким значением — это намеренное значение, как и любое другое, поэтому запись передается без `dateModified` независимо от того, было ли изменено её содержимое.
  - Случай, когда запись считывается без изменения, представляет собой иной случай: значение `None` уже присутствует в поле, и его невозможно отличить от ситуации, когда поле так и не было изменено, поэтому при редактировании на него всё равно ставится отметка.
- **An unparseable date is replaced.** A date the model could not parse is [residue](#reading) rather than a date, so a stamp overwrites it and the original string is dropped. An edited entry is better off carrying a real date than `dateModified="whenever"`.

### How the stamp is applied

- **Момент времени.** Время по UTC с точностью до секунд (`YYYY-MM-DDTHH:MM:SSZ` — формат, используемый во всех экспортируемых данных FieldWorks), считанное с настенных часов. Одна секунда соответствует одной дате, поэтому правка, сохранённая в течение секунды после предыдущей, получает ту же отметку.
- **`save(when=...)`** использует момент времени вместо реального времени, что обеспечивает воспроизводимость отметки времени в выводе для контрольного порога CI, основанного на сравнении разниц. Оно должно учитывать часовой пояс и приведено к целым секундам по UTC.
- **`save(stamp=False)`** сохраняет модель в том виде, в каком она находится в данный момент, включая остаток.
- **Фиксация коммитов с помощью записи `.lift`.** Любой фактор, препятствующий фиксации этой записи, приводит к сдвигу дат назад. Как только он приземлится, они остаются на месте, даже если после него не удастся выполнить сопутствующую команду «write».

## XML-контент не может отображать

Non-BMP characters (emoji, CJK Extension B, Adlam, anything above U+FFFF) are ordinary content and round-trip byte-identically. «Пара-заменитель» — это деталь кодировки UTF-16: строки в Python представляют собой последовательности кодовых точек, поэтому ни считыватель, ни сканер байтов, ни записыватель никогда не сталкиваются с ними напрямую.

_Одиночный_ заменитель (U+D800–U+DFFF) — это другое дело: строка в Python может содержать один такой заменитель, а XML-документ — нет, независимо от кодировки. It can never arrive from a file, because the parser rejects both spellings (a `&#xD800;` character reference and CESU-8/WTF-8 bytes). It can only come from a string assigned through the API.

Saving such a model raises `LiftWriteError` naming the node and the codepoint, and writes nothing. Validation reports it as a single `lone-surrogate` error, since the document cannot be serialized for the schema layers to check.

## Известные приближения (только затронутые узлы)

- Комментарии, расположенные _внутри_ блока `<text>`, сохраняются, но перемещаются рядом с этим блоком, а не остаются на прежнем месте с точным смещением по символам.
- Крестообразный порядок дочерних элементов внутри редактируемого элемента приводится в соответствие с канонической группировкой (параметр `interleave` схемы LIFT делает этот порядок семантически несущественным).
- URL-адрес `<form>` или `<gloss>` без атрибута `lang` не перенаправляется, равно как и все, что он содержал; при валидации это упущение регистрируется как `form-missing-lang`. Нетронутый узел сохраняет исходные байты, поэтому такая форма сохраняется до тех пор, пока не будет отредактирована какая-либо часть его записи.
- A multitext element that is present but carries nothing (no forms, no residue, e.g. `<definition></definition>`) is not re-emitted. Ничего из семантики не теряется.
  - The model represents these fields as an always-present `Multitext`, so an empty one is indistinguishable from an absent one after parsing. The fields are `lexical-unit`, `citation`, `definition`, a relation's `usage`, and `label` / `abbrev` / `description` on url-refs, ranges, range-elements and the header.
