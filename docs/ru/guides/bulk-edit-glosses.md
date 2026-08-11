# Пример с решением: массовое редактирование глосс

Типичная задача по обслуживанию: привести правописание всех английских терминов в словаре к единому стандарту (британский → американский или наоборот), не затрагивая при этом остальные элементы файла. В этом примере подробно рассматривается один скрипт, который выполняет загрузку, редактирование, проверку и сохранение данных, демонстрируя совместную работу API редактирования и гарантии точности.

## Сценарий

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)


def iter_senses(senses):
    """Yield every sense, including subsenses (recursive)."""
    for sense in senses:
        yield sense
        yield from iter_senses(sense.subsenses)


edited_glosses = 0

for entry in lex.entries:
    for sense in iter_senses(entry.senses):
        for gloss in sense.glosses:
            if gloss.lang != "en":
                continue
            old = str(gloss.text)
            new = old.replace("colour", "color")
            if new != old:
                gloss.text = sil_lift.Text([new])
                edited_glosses += 1

changed = lex.changed_entries()

errors = [p for p in lex.iter_problems() if p.level == "error"]
if errors:
    for problem in errors:
        print(problem)
    sys.exit(f"aborting: {len(errors)} validation error(s), nothing saved")

lex.save()
print(f"edited {edited_glosses} gloss(es) across {len(changed)} entry(ies)")
```

Несколько моментов, на которые стоит обратить внимание:

- `Sense.subsenses` само по себе представляет собой `list[Sense]`, поэтому `iter_senses` выполняет рекурсию по нему — при массовом редактировании, которое бы просматривало только `entry.senses`, любые глоссы, вложенные под подзначениями, были бы незаметно пропущены.
- `gloss.text` — это объект типа `Text`, а не обычная строка: функция `str(gloss.text)` преобразует его в строку для сопоставления, а результат замены записывается обратно с помощью `sil_lift.Text([new])`, а не путем изменения исходной строки на месте.
- `lex.changed_entries()` reports which entries differ from the file as loaded. Since an entry's digest covers its whole subtree, an edit to a nested subsense reports the entry that contains it.
  - It compares serialized content, so assigning a field the value it already had isn't reported.
  - It reports content changes only; `lex.added_entries()` and `lex.removed_entries()` cover entries that appeared or disappeared since loading.
  - It returns the entries themselves, unaffected by `id` being duplicated or absent (which LIFT allows).
  - As a count, it is meaningful only where there is something to compare against. When the passthrough layer declines to byte-scan the source — an encoding that is not ASCII-compatible, or a scanner/parser disagreement — there is no baseline, and `changed_entries()` reports _every_ entry. That is the honest answer for a write guard, since `save()` re-serializes the whole file in that case, but it means the count is the size of the lexicon rather than the size of the edit.
- `lex.changes()` reports whether the document changed _at all_. It covers not just the entries, but also the header, the root element, and every `.lift-ranges` companion.
  - It is falsy only when `save()` would reproduce the source bytes, which makes `if not lex.changes(): ...` the right way to skip an unnecessary write. The guarantee runs one way: it never reports "nothing to write" for a document that would be rewritten, while a change that forces a full re-serialization can land back on the original bytes and still be reported.
  - It compares content, not destination, so guard only an in-place save with it: `lex.save(some_other_dir / "dictionary.lift")` writes the document and its companions to a location that has nothing in it yet, whether or not anything changed.
  - It is a guard, not a speed-up — answering it digests every entry, which is the same work `save()` does to decide passthrough, so what you skip is the write itself (an untouched mtime, no spurious diff), not the effort of deciding.
- При проверке в памяти (`lex.iter_problems()`) сначала выполняется сериализация отредактированного состояния, благодаря чему оно правильно отражает внесенные изменения ещё до записи на диск. Прерывание при возникновении любого объекта `Problem` уровня `"error"` — предупреждения оставляются на усмотрение вызывающего кода — означает, что некорректное изменение никогда не доходит до вызова `save()`.

Не только глянцевые поверхности стоит обрабатывать таким образом. Та же самая поверхность сопоставления `Multitext` применяется к определениям и всем другим многоязычным полям в записи или значении:

```python
sense.definition["en"] = "цвет предмета"
```

## Запуск программы

Проведите сравнение с небольшим лексиконом, в котором есть термин и его подзначение, обозначающие «цвет»:

```
внесено 2 исправления в 1 запись
```

## Выгода от точности воспроизведения

Гарантия распространяется на каждую отдельную запись: запись, модель которой не изменилась, возвращается в виде **байтово идентичного** копирования исходного содержимого, а повторная сериализация производится только для тех записей, в которые вы действительно вносили изменения. В приведенном выше фрагменте в одной записи были отредактированы глоссы — все остальные записи в файле сохранили свои байты без изменений. (Обратите внимание на степень детализации: при редактировании любой части записи происходит повторная сериализация всей записи целиком, включая нетронутые родственные значения.) Таким образом, при редактировании одного глоссария в словаре, содержащем 50 000 статей, создается файл diff, затрагивающий одну статью, а не переформатированный файл. Точные условия договора см. в разделе [Гарантии Fidelity](../fidelity.md).
