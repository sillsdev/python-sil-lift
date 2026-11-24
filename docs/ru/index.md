# sil-lift

Библиотека Python для [LIFT](https://github.com/sillsdev/lift-standard) (Lexicon Interchange FormaT) версии 0.13: чтение и запись папки LIFT без потери данных (файлы `.lift`, `.lift-ranges` и ссылки на медиафайлы), проверка соответствия схеме и семантике, а также каноническая сортировка; кроме того, предоставляются потоковые API для работы с большими лексиконами.

**Статус: предварительная версия, ведётся активная разработка.**

## Установить

С сайта [PyPI](https://pypi.org/project/sil-lift/):

```
pip install sil-lift   # библиотека + команда sil-lift
```

Требуется Python версии 3.11 или выше. Единственной зависимостью на этапе выполнения является lxml.

## 30-секундная экскурсия

Загрузите словарь, найдите гавайские слова без английского пояснения, отредактируйте определение и сохраните:

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # также отслеживает сопутствующие записи с расширениями .lift

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("haw") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # или lex.find(id="poʻo_a1b2")
entry.senses[0].definition["en"] = "head (anatomy)"

lex.save()   # отредактированная запись заново сериализована и промаркирована; остальное байт-идентично
```
