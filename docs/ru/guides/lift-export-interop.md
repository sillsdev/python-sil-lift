# Создание LIFT, соответствующего требованиям

Данное руководство предназначено для всех, кто разрабатывает _экспортер_ LIFT — программу на любом языке программирования, преобразующую модель данных другого приложения в формат LIFT 0.13. `sil-lift` выполняет в этой работе две функции: служит механизмом проверки соответствия, который сравнивает выходные данные со схемой и учитывает семантику, которую схема не может выразить, а также выступает в качестве эталона для форм и правил оформления текста, которым должны соответствовать выходные данные.

Писать LIFT гораздо проще, чем его анализировать: экспортер генерирует только подмножество конструкций, которые создает его собственная модель, и никогда не сталкивается с опциональностью полной спецификации. Самое сложное — это детали: сопутствующий элемент `.lift-ranges`, текст для каждой системы письма, стабильные идентификаторы и экранирование XML — и именно их и выявляют приведенные ниже проверки.

## Пакеты с застежкой-молнией

LIFT обычно передаётся в виде одного файла `.zip` — программы FieldWorks и The Combine импортируют и экспортируют данные именно таким образом — поэтому `sil-lift` напрямую считывает и записывает заархивированные пакеты в любом из двух форматов, используемых в этой экосистеме: либо файлы находятся в корневом каталоге архива, либо вложены в одну папку верхнего уровня.

- **Примечание:** Команда `sil_lift.load("package.zip")` распаковывает файл в временный каталог, находит единственный файл `.lift` и загружает его (сопутствующие файлы и мультимедиа обрабатываются как обычно). Команды CLI `validate`, `stats`, `check-media` и `export` также принимают путь к файлу `.zip`, поэтому приведенный ниже скрипт запускается для пакета в том виде, в котором он есть. Функция извлечения защищена от вредоносных архивов — элементы, позволяющие переходить по пути, отклоняются, а количество записей и общий размер в несжатом виде (10 ГиБ) ограничены для защиты от «zip-бомб».
- **Напишите:** `Lexicon.save_zip("out.zip", wrap_folder="MyDict")` упаковывает файл `.lift`, его файлы `.lift-ranges`, а также все остальные файлы из исходной папки (медиафайлы, `WritingSystems/`, `consent/`, ...) в архив ZIP. По умолчанию `wrap_folder` — это папка верхнего уровня, названная в соответствии с именем ZIP-архива (согласно соглашению об импорте FieldWorks/Combine); для создания плоского архива передайте значение `False`.

Файлы `.lift` и `.lift-ranges` сохраняют точность воспроизведения на уровне байтов внутри пакета; сам контейнер zip не обеспечивает точность воспроизведения на уровне байтов.

## Validate the output as a conformance gate

Point `sil-lift validate` at the produced `.lift` file. It runs RELAX NG (over both the `.lift` and its `.lift-ranges` companion) plus semantic checks the grammar can't express: dangling `relation`/`variant` references, duplicate GUIDs, range-element parent integrity, trait and grammatical-info values not defined in their range, and header `range/@href` references that resolve to no companion.

For CI, fail on anything and emit machine-readable findings:

```
sil-lift validate export.lift --strict --no-check-media --format json
```

- `--strict` makes warnings (not just errors) fail the run.
- `--no-check-media` skips the filesystem media-presence check, whose `missing-media` findings are noise when the audio/photo files aren't colocated with the `.lift` in CI.
- `--format json` prints a single JSON object (`{"problems": [...], "summary": {...}}`) instead of human text; its exit codes and schema are a supported, SemVer-covered interface (see [the command line guide](cli.md)).
- `--require-ids` additionally errors on entries missing a `guid` or senses missing an `id` — useful when a later re-import must update rather than duplicate.

Guard against silent data loss (the failure mode that makes flat CSV export lossy) by asserting counts with `stats --format json` against your source model:

```
sil-lift stats export.lift --format json
```

It reports `entries`, `senses`, `examples`, `media_refs`, `languages`, and per-name `traits` counts.

### Running the gate without a Python toolchain

A TypeScript or C# project's CI can run the same check without installing Python, via the bundled GitHub Action:

```yaml
- uses: sillsdev/python-sil-lift@v0.1.0
  with:
    path: export.lift
    strict: "true"
    no-check-media: "true"
    format: json
```

or the container image, built from the repo's `Dockerfile`:

```
docker build -t sil-lift .
docker run --rm -v "$PWD:/work" -w /work sil-lift validate export.lift --strict
```

## The `.lift-ranges` companion

Controlled vocabularies — parts of speech, semantic domains, and any other trait-keyed value set — live in a sibling `.lift-ranges` file, referenced from the `<header>`:

```xml
<header>
  <ranges>
    <range id="grammatical-info" href="mydict.lift-ranges"/>
    <range id="semantic-domain-ddp4" href="mydict.lift-ranges"/>
  </ranges>
</header>
```

The companion carries each range's full definition. Values are `<range-element>`s; `parent` builds a hierarchy; `label` / `abbrev` / `description` are multitexts:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<lift-ranges>
  <range id="grammatical-info">
    <range-element id="Noun">
      <label><form lang="en"><text>noun</text></form></label>
      <abbrev><form lang="en"><text>n</text></form></abbrev>
    </range-element>
  </range>
  <range id="semantic-domain-ddp4">
    <range-element id="1.6.1.2">
      <label><form lang="en"><text>Bird</text></form></label>
    </range-element>
  </range>
</lift-ranges>
```

An entry then refers to a value by id: a sense's part of speech is `<grammatical-info value="Noun"/>`, and a semantic domain is `<trait name="semantic-domain-ddp4" value="1.6.1.2"/>`. `sil-lift validate` warns (`undefined-range-value`) when a value isn't defined in its range and errors (`range-parent`) when a `parent` isn't a sibling id — so emit the ranges your data actually uses. See also [Ranges and media](folder-media.md).

If you build the export in Python, `Lexicon.add_ranges_file()`, `RangesFile.add_range()`, and `Range.add_element()` construct the companion and add the header references for you; `open_writer(..., ranges=...)` does the same on the streaming path.

## Text and multitext

Every human-language string in LIFT is a _multitext_: one `<form>` per writing system, each wrapping a `<text>`:

```xml
<lexical-unit>
  <form lang="seh"><text>kanga</text></form>
  <form lang="pt"><text>galinha</text></form>
</lexical-unit>
```

A model that keys strings by language code (a `MultiString`, a `Record<code, string>`, a `dict[str, str]`) maps onto this one-to-one: one entry per key becomes one `<form lang="…">`. At most one form per language is allowed in a single multitext — `sil-lift` warns `duplicate-form-lang` otherwise.

XML escaping is the one genuinely correctness-sensitive part. In element text, `&`, `<`, and `>` must be escaped (`&amp;`, `&lt;`, `&gt;`); in attribute values, the quote character too. `sil-lift`'s writer applies exactly these rules and never alters whitespace inside `<text>` — it adds no indentation there, because that would corrupt the lexical data. If you aim to match its output, reuse a real XML serializer's escaping (not a hand-rolled replace that forgets `&`) and leave `<text>` content byte-for-byte as your source has it.
