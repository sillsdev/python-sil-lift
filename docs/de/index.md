# sil-lift

Eine Python-Bibliothek für [LIFT](https://github.com/sillsdev/lift-standard) (Lexicon Interchange FormaT) 0.13: verlustfreies Lesen und Schreiben des LIFT-Ordners (`.lift` + `.lift-ranges` + Medienverweise), Schema- und semantische Validierung sowie kanonische Sortierung, ergänzt durch Streaming-APIs für große Lexika.

**Status: Vorabversion, befindet sich in aktiver Entwicklung.**

## Installieren

Aus [PyPI](https://pypi.org/project/sil-lift/):

```
pip install sil-lift   # Bibliothek + der Befehl „sil-lift“
```

Erfordert Python 3.11 oder höher. Die einzige Laufzeitabhängigkeit ist lxml.

## Die 30-Sekunden-Tour

Laden Sie ein Lexikon, suchen Sie die hawaiianischen Einträge ohne englische Erläuterung, bearbeiten Sie eine Definition und speichern Sie sie:

```python
import sil_lift

lex = sil_lift.load("thesaurus.lift")     # verfolgt auch .lift-Bereiche und zugehörige Einträge

for entry in lex.entries:
    if "en" not in entry.gloss_langs():
        print(entry.id, str(entry.lexical_unit.get("haw") or ""))

entry = lex.find(guid="0f5a9c3e-...")     # oder lex.find(id="poʻo_a1b2")
entry.senses[0].definition["en"] = "Kopf (Anatomie)"

lex.save()   # bearbeiteter Eintrag neu serialisiert und neu gestempelt; der Rest ist byteweise identisch
```
