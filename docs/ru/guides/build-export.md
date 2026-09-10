# Пример с расчетами: создание экспорта LIFT с нуля

Если вы экспортируете данные другого приложения в формате LIFT — что и является целью задачи [Создание LIFT-документов, соответствующих стандарту](lift-export-interop.md) — `sil-lift` может сформировать документ объект за объектом и сериализовать его, вместо того чтобы вручную генерировать XML. Здесь подробно описан один скрипт, который формирует запись, содержащую все элементы, присущие реальному словарю (несколько систем письма, произношение, значение с примером, иллюстрацию, характеристику семантической области и поле, специфичное для приложения), записывает контролируемые словари в сопутствующий файл `.lift-ranges`, проверяет их на корректность и сохраняет.

## Сценарий

```python
from pathlib import Path

import sil_lift

lex = sil_lift.Lexicon(producer="my-exporter")

# Одна запись, построенная на основе исходной модели.
entry = sil_lift.Entry(id="kanga", guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d")
entry.lexical_unit["seh"] = "nkhuku"
entry.lexical_unit["pt"] = "galinha"

pron = sil_lift.Pronunciation()
pron.forms["en"] = "Speaker: Ana"  # Конвенция Combine для обозначения говорящего
pron.media.append(sil_lift.URLRef(href="audio/nkhuku.wav"))
entry.pronunciations.append(pron)

sense = sil_lift.Sense(id="kanga_s1")
sense.grammatical_info = sil_lift.GrammaticalInfo(value="Noun")
sense.glosses.append(sil_lift.Form(lang="en", text=sil_lift.Text(["chicken"])))
sense.definition["en"] = "a domestic fowl kept for its eggs and meat"

example = sil_lift.Example()
example.forms["seh"] = "Ndinafuna nkhuku."
translation = sil_lift.Translation()
translation.forms["en"] = "I want a chicken."
example.translations.append(translation)
sense.examples.append(example)

photo = sil_lift.URLRef(href="pictures/hen.jpg")
photo.label["en"] = "Курица"
sense.illustrations.append(photo)

sense.traits.append(sil_lift.Trait(name="semantic-domain-ddp4", value="1.6.1.2"))

scientific = sil_lift.Field(type="scientific-name")  # дополнительное поле, специфичное для приложения
scientific.content["en"] = "Gallus gallus domesticus"
sense.fields.append(scientific)

entry.senses.append(sense)
lex.entries.append(entry)

# Контролируемые словари, на которые ссылается запись, в сопутствующем файле .lift-ranges.
ranges = sil_lift.RangesFile()
ranges.add_range("grammatical-info").add_element("Noun").label["en"] = "noun"
ranges.add_range("semantic-domain-ddp4").add_element("1.6.1.2").label["en"] = "Bird"
lex.add_ranges_file(ranges, href="birds.lift-ranges")

# Проверить, что запишет функция save(), прежде чем записывать на диск.
problems = list(lex.iter_problems())
print(f"validation: {len(problems)} проблема(ы)")

out = Path("export")
out.mkdir(exist_ok=True)
lex.save(out / "birds.lift")
print("=== birds.lift ===")
print((out / "birds.lift").read_text(encoding="utf-8"), end="")
print("=== birds.lift-ranges ===")
print((out / "birds.lift-ranges").read_text(encoding="utf-8"), end="")
```

## Что он производит

`validation: 0 problem(s)`, а затем `.lift` и его сопутствующий код рядом:

```
=== birds.lift ===
<?xml version="1.0" encoding="UTF-8"?>
<lift version="0.13" producer="my-exporter">
<header>
  <ranges>
    <range id="grammatical-info" href="birds.lift-ranges"/>
    <range id="semantic-domain-ddp4" href="birds.lift-ranges"/>
  </ranges>
</header>
<entry id="kanga" guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d">
  <lexical-unit>
    <form lang="seh">
      <text>nkhuku</text>
    </form>
    <form lang="pt">
      <text>galinha</text>
    </form>
  </lexical-unit>
  <pronunciation>
    <form lang="en">
      <text>Speaker: Ana</text>
    </form>
    <media href="audio/nkhuku.wav"/>
  </pronunciation>
  <sense id="kanga_s1">
    <grammatical-info value="Noun"/>
    <gloss lang="en">
      <text>chicken</text>
    </gloss>
    <definition>
      <form lang="en">
        <text>a domestic fowl kept for its eggs and meat</text>
      </form>
    </definition>
    <example>
      <form lang="seh">
        <text>Ndinafuna nkhuku.</text>
      </form>
      <translation>
        <form lang="en">
          <text>I want a chicken.</text>
        </form>
      </translation>
    </example>
    <illustration href="pictures/hen.jpg">
      <label>
        <form lang="en">
          <text>A hen</text>
        </form>
      </label>
    </illustration>
    <trait name="semantic-domain-ddp4" value="1.6.1.2"/>
    <field type="scientific-name">
      <form lang="en">
        <text>Gallus gallus domesticus</text>
      </form>
    </field>
  </sense>
</entry>
</lift>
=== birds.lift-ranges ===
<?xml version="1.0" encoding="UTF-8"?>
<lift-ranges>
<range id="grammatical-info">
  <range-element id="Noun">
    <label>
      <form lang="en">
        <text>noun</text>
      </form>
    </label>
  </range-element>
</range>
<range id="semantic-domain-ddp4">
  <range-element id="1.6.1.2">
    <label>
      <form lang="en">
        <text>Bird</text>
      </form>
    </label>
  </range-element>
</range>
</lift-ranges>
```

## Примечания по API

- Поля с несколькими текстами (`lexical_unit`, `definition`, метка `Form`/`URLRef`, содержимое `Field`, ...) Через интерфейс сопоставления передать по одной строке для каждой системы письма: `entry.lexical_unit["seh"] = "nkhuku"` добавляет `<form lang="seh">`. Модель исходных данных, в которой строки индексируются по коду языка, напрямую соответствует этой схеме.
- `RangesFile.add_range()` / `Range.add_element()` формируют контролируемые словари, а `Lexicon.add_ranges_file(ranges, href=...)` присоединяет сопутствующий файл и добавляет ссылки в заголовок `<range href>` — таким образом, ссылки `<grammatical-info value="Noun">` и `<trait name="semantic-domain-ddp4" value="1.6.1.2">` в записи разрешаются в соответствии с заданными вами диапазонами.
- `URLRef` — это атрибут `href` с дополнительным многострочным текстом подписи или метки (необязательным) — используется как для `<media>` (аудио), так и для `<illustration>` (фотографии). Произношение здесь соответствует принятой в «The Combine» конвенции, согласно которой форма «en» читается как «Speaker: <name> ».
- Данные, специфичные для приложения, не содержащие данных о поездках домой по системе LIFT, в формате `<field>` (или `<trait>`): FieldWorks интерпретирует их как пользовательские поля, а The Combine сохраняет их.
- Присваивайте каждой записи уникальный и стабильный `guid` (например, с помощью `uuid.uuid4()`, который используется повторно при всех экспортах) — при последующем повторном импорте запись будет обновлена на месте, а не дублирована. Команда `sil-lift validate --require-ids` обеспечивает соблюдение этого требования.
- Функция `lex.iter_problems()` проверяет документ, хранящийся в памяти (то, что записала бы функция `save()`), прежде чем какие-либо данные поступят на диск; в данном случае он находится в исправном состоянии. Поскольку для лексикона пока не создана папка, проверки наличия медиафайлов и ссылок на сопутствующие ресурсы пропускаются — запустите команду [`sil-lift validate`](cli.md) на сохраненном выводе (или с параметром `--no-check-media`), как только аудио- и фотофайлы будут размещены в соответствующих папках.

## Упаковка

Команда `lex.save("export/birds.lift")` записывает папку в формате (файлы `.lift` и `.lift-ranges`, расположенные рядом). Чтобы сгенерировать единый ZIP-архив, который программы FieldWorks и The Combine могут импортировать напрямую, вместо этого используйте `lex.save_zip("birds.zip")` — см. [Создание LIFT-файлов, соответствующих стандарту](lift-export-interop.md).
