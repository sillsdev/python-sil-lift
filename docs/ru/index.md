# sil-lift

Библиотека на языке Python для [LIFT](https://github.com/sillsdev/lift-standard) (Lexicon Interchange FormaT) 0.13: чтение и запись папки LIFT без потерь (`.lift` + `.lift-ranges` + ссылки на медиафайлы), проверка схемы и семантики, а также каноническая сортировка — с потоковыми API для больших лексиконов.

**Статус: предварительная версия, ведётся активная разработка.**

## Установить

С сайта [PyPI](https://pypi.org/project/sil-lift/):

```
pip install sil-lift   # библиотека + команда sil-lift
```

Требуется Python версии 3.11 или выше. Единственной зависимостью на этапе выполнения является lxml.

## 30-секундная экскурсия

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # также отслеживает сопутствующие элементы с расширениями .lift

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("seh") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # или lex.find(id="hoofd_a1b2")
entry.senses[0].definition["en"] = "head (anatomy)"

lex.save()   # неизменённые записи остаются байтово идентичными; отредактированная запись сериализуется заново
```
