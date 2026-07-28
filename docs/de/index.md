# sil-lift

Eine Python-Bibliothek für [LIFT](https://github.com/sillsdev/lift-standard) (Lexicon Interchange Format) 0.13: verlustfreies Lesen und Schreiben des LIFT-Ordners (`.lift` + `.lift-ranges` + Medienverweise), Schema- und semantische Validierung sowie kanonische Sortierung – mit Streaming-APIs für große Lexika.

**Status: Vorabversion, befindet sich in aktiver Entwicklung.**

## Installieren

Aus [PyPI](https://pypi.org/project/sil-lift/):

```
pip install sil-lift   # Bibliothek + der Befehl „sil-lift“
```

Erfordert Python 3.11 oder höher. Die einzige Laufzeitabhängigkeit ist lxml.

## Die 30-Sekunden-Tour

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # erfasst auch Begleitbegriffe aus .lift-Bereichen

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("seh") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # oder lex.find(id="hoofd_a1b2")
entry.senses[0].definition["en"] = "head (anatomy)"

lex.save()   # Unveränderte Einträge sind byteweise identisch; bearbeitete Einträge werden neu serialisiert
```
