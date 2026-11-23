# Читать, редактировать, писать

## Загрузка

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` accepts any well-formed LIFT **0.13** document, including schema-invalid real-world files. Все, что не определено в модели (неизвестные элементы/атрибуты, комментарии), передается без потерь в виде остаточного данных LIFT в непрозрачном поле `extra` каждого узла. Другие версии LIFT вызывают исключение `LiftParseError`, указывая номер версии.

## Модель

Every LIFT element is a typed dataclass: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, and so on.

### Multilingual text

Многоязычный текст представляет собой объект `Multitext`, который является `Mapping`, сопоставляющим код языка с объектом `Text`:

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # "poʻo"
entry.lexical_unit["en"] = "head"       # plain strings are coerced
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

`Text` is structured (an ordered list of `str` and `Span` fragments) because `<text>` can contain nested `<span>` markup. `str(text)` преобразует текст в обычный текст; фрагменты сохраняют разметку для обратного преобразования.

The mapping shows one value per language. Underneath, `forms` holds every `<form>` in file order. A schema-valid document has at most one form per language, but real files sometimes repeat one.

Because the mapping is keyed by language, `len()` counts languages rather than forms, and the `keys()`, `values()` and `items()` views list each language once. Both mutators also act on the whole language: `del entry.lexical_unit["en"]` removes every English form, and assigning to `"en"` leaves exactly one.

For a repeated language, `entry.lexical_unit["en"]`, `get()`, `values()` and `items()` all answer with its first form, and [`validate`](validate.md#problem-codes) reports `duplicate-form-lang` until you assign to that language.

A form carrying no `lang` at all cannot be created through the mapping. It is reported as `form-missing-lang`, and is dropped when its node re-serializes.

### Senses and glosses

В LIFT глоссы имеют форму _form_ (каждый `<gloss>` содержит свой собственный язык), поэтому сенс имеет `glosses: list[Form]`, а также вспомогательные функции:

```python
sense = entry.senses[0]       # top level only
sense.gloss("en")             # Text | None
entry.all_senses()            # every sense and subsense, document order
entry.gloss_langs()           # {"en", "id"}, subsenses included
```

Используйте функцию `all_senses()` всякий раз, когда вопрос касается всей записи: подсчёт значений, сбор данных по языкам, поиск медиафайлов. `entry.senses` возвращает верхний уровень, что нужно только в тех случаях, когда само вложение имеет значение.

## Сохранение

```python
lex.save()                    # back to where it was loaded from
lex.save("elsewhere.lift")
```

Записи, которые вы не изменяли, записываются обратно **байт за байтом**; документ, который вы не изменяли вообще, остается байт за байтом идентичным от первого до последнего байта. Точные условия договора см. в разделе [Гарантии Fidelity](../fidelity.md).

### Временные метки

Записи, которые вы изменили, отправляются с новым значением `dateModified` (а также с `dateCreated`, если у них его не было), поэтому отредактированная запись не отправляется с датой, с которой она была загружена. Tools that merge LIFT decide what changed from that attribute. Two arguments adjust the stamping:

- `lex.save(stamp=False)` writes the dates the model holds and nothing more.
- `lex.save(when=...)` pins the moment instead of reading the clock.

Остальные правила см. в разделе [Сгенерированные временные метки](../fidelity.md#generated-timestamps).

### Skipping a save that changes nothing

Чтобы пропустить сохранение, которое ничего не изменит, защитите его с помощью `lex.changes()`:

```python
if lex.changes():
    lex.save()
```

Она возвращает `False` только в том случае, если функция `save()` воспроизведет исходные байты, включая записи, заголовок, корневой элемент и каждый сопутствующий объект `.lift-ranges`. Skipping the write leaves the file's modification time alone and avoids a spurious diff.

The check is cheap. Он останавливается при обнаружении первого различия, поэтому при работе с отредактированным словарем это практически ничего не стоит. Чтобы подтвердить, что лексикон не изменился, его необходимо сериализовать полностью, но это всё равно обходится дешевле, чем пропуск операции сохранения.

Он сравнивает содержимое, а не место назначения, поэтому следует обеспечивать защиту только при сохранении на месте. `lex.save("elsewhere.lift")` writes the document and its companions to the new path even when `changes()` is `False`, so guarding it would skip that copy.

## Создание с нуля

```python
lex = sil_lift.Lexicon(producer="my-script 1.0")
entry = sil_lift.Entry(id="hello", guid="...")
entry.lexical_unit["en"] = "hello"
sense = sil_lift.Sense()
sense.glosses.append(sil_lift.Form("fr", sil_lift.Text(["bonjour"])))
entry.senses.append(sense)
lex.entries.append(entry)
lex.save("new.lift")
```

## Каноническая сортировка

```python
lex.sort()      # записи по (guid, id); диапазоны/определения полей по id/тегу
lex.save()      # неизменённые записи сохраняют свои точные байты в новом порядке

sil_lift.canonicalize("in.lift", "out.lift")   # полностью пересериализовано, готово к сравнению
```

См. также: [Пример с решением: массовое редактирование глосс](bulk-edit-glosses.md).
