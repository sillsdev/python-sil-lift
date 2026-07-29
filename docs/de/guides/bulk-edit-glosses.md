# Anwendungsbeispiel: Massenbearbeitung von Glossaren

Eine häufige Wartungsaufgabe: Die Schreibweise aller englischen Begriffserklärungen in einem Lexikon vereinheitlichen (britisch → amerikanisch oder umgekehrt), ohne dabei andere Teile der Datei zu verändern. Hier wird ein Skript Schritt für Schritt erläutert, das Daten lädt, bearbeitet, validiert und speichert – dabei wird gezeigt, wie die Bearbeitungs-API und die Genauigkeitsgarantie zusammenwirken.

## Das Drehbuch

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)


def iter_senses(senses):
    """Gibt jede Bedeutung zurück, einschließlich Unterbedeutungen (rekursiv)."""
    for sense in senses:
        yield sense
        yield from iter_senses(sense.subsenses)


edited_glosses = 0
touched_entries = set()

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
                touched_entries.add(entry.id)

errors = [p for p in lex.iter_problems() if p.level == "error"]
if errors:
    for problem in errors:
        print(problem)
    sys.exit(f"Abbruch: {len(errors)} Validierungsfehler, nichts gespeichert")

lex.save()
print(f" {edited_glosses} -Glossare in {len(touched_entries)} Einträgen bearbeitet")
```

Ein paar Dinge, die es zu beachten gilt:

- `Sense.subsenses` ist selbst eine `list[Sense]`, daher wird sie von `iter_senses` rekursiv durchlaufen – eine Massenbearbeitung, die nur `entry.senses` durchläuft, würde alle unter einer Unterbedeutung verschachtelten Erläuterungen stillschweigend überspringen.
- `gloss.text` ist ein `Text` und keine einfache Zeichenkette: `str(gloss.text)` wandelt ihn für den Abgleich in eine Zeichenkette um, und die Ersetzung wird mit `sil_lift.Text([new])` zurückgeschrieben, anstatt die Zeichenkette direkt zu ändern.
- Bei der Validierung im Arbeitsspeicher (`lex.iter_problems()`) wird der bearbeitete Zustand zunächst serialisiert, sodass er die Änderungen korrekt widerspiegelt, bevor Daten auf die Festplatte geschrieben werden. Ein Abbruch bei jedem `"error"`-Level-`Problem` – Warnungen werden dem Aufrufer zur Beurteilung überlassen – bedeutet, dass eine fehlerhafte Bearbeitung niemals `save()` erreicht.

Nicht nur Glanzlacke lassen sich auf diese Weise gut auftragen. Die gleiche `Multitext`-Zuordnungsfläche gilt für Definitionen und alle anderen mehrsprachigen Felder eines Eintrags oder einer Bedeutung:

```python
sense.definition["en"] = "die Farbe eines Gegenstands"
```

## Ausführen

Führen Sie eine Suche in einem kleinen Lexikon durch, in dem sowohl die Erläuterung als auch die Unterbedeutung mit „Farbe“ angegeben sind:

```
2 Begriffserklärungen in 1 Eintrag bearbeitet
```

## Der Lohn der Treue

Die Garantie gilt pro _Eintrag_: Ein Eintrag, dessen Modell sich nicht geändert hat, wird **byte-identisch** so zurückgegeben, wie er eingelesen wurde, und nur die Einträge, die Sie tatsächlich bearbeitet haben, werden erneut serialisiert. In der obigen Ausführung wurden bei einem Eintrag die Glossen bearbeitet – alle anderen Einträge in der Datei behielten ihre exakten Bytes bei. (Beachten Sie die Detailgenauigkeit: Wenn Sie einen beliebigen Teil eines Eintrags bearbeiten, wird der gesamte Eintrag neu serialisiert, einschließlich der davon nicht betroffenen verwandten Bedeutungen.) Das Bearbeiten eines Eintrags in einem Lexikon mit 50.000 Einträgen führt daher zu einer Diff-Datei, die nur einen Eintrag betrifft, und nicht zu einer neu formatierten Datei. Den genauen Vertragsinhalt finden Sie unter [Fidelity-Garantien](../fidelity.md).
