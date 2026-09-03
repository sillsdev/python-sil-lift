# Читать, редактировать, писать

## Загрузка

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

Функция `load()` принимает любой корректно сформированный документ LIFT **0.13** — в том числе реальные файлы, не соответствующие схеме. Все, что не определено в модели (неизвестные элементы/атрибуты, комментарии), передается без потерь в виде остаточного данных LIFT в непрозрачном поле `extra` каждого узла. Другие версии LIFT вызывают исключение `LiftParseError`, указывая номер версии.

## Модель

Каждый элемент LIFT представляет собой типизированный класс данных: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal` и т. д. Многоязычный текст представляет собой объект `Multitext`, который работает как отображение кода языка на объект `Text`:

```python
entry = lex.find(id="abat")

str(entry.lexical_unit["seh"])          # "abat"
entry.lexical_unit["en"] = "grove"      # простые строки преобразуются
"en" in entry.citation                  # False
```

`Text` имеет структуру — это упорядоченный список фрагментов `str` и `Span` — поскольку `<text>` может содержать вложенную разметку `<span>`. `str(text)` преобразует текст в обычный текст; фрагменты сохраняют разметку для обратного преобразования.

В LIFT глоссы имеют форму _form_ (каждый `<gloss>` содержит свой собственный язык), поэтому сенс имеет `glosses: list[Form]`, а также вспомогательную функцию:

```python
sense = entry.senses[0]
sense.gloss("en")                       # Text | None
entry.gloss_langs()                     # {"en", "id"}
```

## Сохранение

```python
lex.save()                # сохранить в том же месте, откуда было загружено
lex.save("elsewhere.lift")
```

Записи, которые вы не изменяли, записываются обратно **байт за байтом**; документ, который вы не изменяли вообще, остается байт за байтом идентичным от первого до последнего байта. Точные условия договора см. в разделе [Гарантии Fidelity](../fidelity.md).

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
