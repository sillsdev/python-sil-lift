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
    sys.exit(f"Abbruch: {len(errors)} Validierungsfehler, nichts gespeichert")

lex.save()
print(f"Bearbeitete {edited_glosses} Glossare in {len(changed)} Einträgen")
```

Ein paar Dinge, die es zu beachten gilt:

- `Sense.subsenses` ist selbst eine `list[Sense]`, daher wird sie von `iter_senses` rekursiv durchlaufen – eine Massenbearbeitung, die nur `entry.senses` durchläuft, würde alle unter einer Unterbedeutung verschachtelten Erläuterungen stillschweigend überspringen.
- `gloss.text` ist ein `Text` und keine einfache Zeichenkette: `str(gloss.text)` wandelt ihn für den Abgleich in eine Zeichenkette um, und die Ersetzung wird mit `sil_lift.Text([new])` zurückgeschrieben, anstatt die Zeichenkette direkt zu ändern.
- `lex.changed_entries()` gibt an, welche Einträge sich von der geladenen Datei unterscheiden. Da die Zusammenfassung eines Eintrags dessen gesamten Teilbaum abdeckt, wird bei einer Bearbeitung einer verschachtelten Teilbedeutung der Eintrag gemeldet, in dem diese enthalten ist.
  - Da serialisierte Inhalte verglichen werden, wird die Zuweisung eines Werts zu einem Feld, den dieses bereits hatte, nicht gemeldet.
  - Es werden ausschließlich inhaltliche Änderungen gemeldet; `lex.added_entries()` und `lex.removed_entries()` erfassen Einträge, die seit dem Laden hinzugekommen sind bzw. verschwunden sind.
  - Es gibt die Einträge selbst zurück, unabhängig davon, ob `id` doppelt vorhanden ist oder fehlt (was LIFT zulässt).
  - Als Zahl ist sie nur dann aussagekräftig, wenn es etwas gibt, mit dem man sie vergleichen kann. Wenn der Byte-Scanner das Lesen der Quelle verweigert – sei es aufgrund einer nicht ASCII-kompatiblen Kodierung oder einer Diskrepanz zwischen Scanner und Parser –, gibt es keine Basislinie, und `changed_entries()` meldet _jeden_ Eintrag. Das ist die ehrliche Antwort in Bezug auf einen Schreibschutz, da `save()` in diesem Fall die gesamte Datei erneut serialisiert; das bedeutet jedoch, dass der Wert der Größe des Lexikons entspricht und nicht der Größe der Bearbeitung.
- `lex.changes()` gibt an, ob sich das Dokument _überhaupt_ geändert hat. Es umfasst nicht nur die Einträge, sondern auch die Kopfzeile, das Stammelement und jedes `.lift-ranges`-Element.
  - Es ist nur dann falsch, wenn `save()` die Quellbytes reproduzieren würde; daher ist `if not lex.changes(): ...` der richtige Weg, um einen unnötigen Schreibvorgang zu überspringen. Die Garantie gilt nur in eine Richtung: Bei einem Dokument, das neu geschrieben würde, wird niemals „nichts zu schreiben“ gemeldet, während eine Änderung, die eine vollständige Neuserialisierung erzwingt, wieder zu den ursprünglichen Bytes führen kann und dennoch gemeldet wird.
  - Da dabei der Inhalt und nicht der Speicherort verglichen wird, sollten Sie damit nur das Speichern am aktuellen Speicherort absichern: `lex.save(some_other_dir / "dictionary.lift")` schreibt das Dokument und die zugehörigen Dateien an einen Speicherort, der noch leer ist – unabhängig davon, ob sich etwas geändert hat oder nicht.
  - Es handelt sich um eine Sicherheitsmaßnahme, nicht um eine Beschleunigung – die Ausführung dieses Befehls wertet jeden Eintrag aus, was dem Aufwand entspricht, den `save()` betreibt, um zu entscheiden, welche Quellbytes wiederverwendet werden können. Was Sie also überspringen, ist der Schreibvorgang selbst (unveränderter Zeitpunkt der Dateiänderung, kein falscher Diff), nicht der Aufwand für die Entscheidung.
- Bei der Validierung im Arbeitsspeicher (`lex.iter_problems()`) wird der bearbeitete Zustand zunächst serialisiert, sodass er die Änderungen korrekt widerspiegelt, bevor Daten auf die Festplatte geschrieben werden. Ein Abbruch bei jedem `"error"`-Level-`Problem` – Warnungen werden dem Aufrufer zur Entscheidung überlassen – bedeutet, dass eine fehlerhafte Bearbeitung niemals die Funktion `save()` erreicht.

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
