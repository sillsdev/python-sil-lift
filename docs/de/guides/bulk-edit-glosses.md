# Anwendungsbeispiel: Massenbearbeitung von Glossaren

Eine häufige Wartungsaufgabe: Die Schreibweise aller englischen Begriffserklärungen in einem Lexikon vereinheitlichen (britisch → amerikanisch oder umgekehrt), ohne dabei andere Teile der Datei zu verändern. Hier wird ein Skript Schritt für Schritt erläutert, das Daten lädt, bearbeitet, validiert und speichert, wobei gezeigt wird, wie die Bearbeitungs-API und die Genauigkeitsgarantie zusammenwirken.

## Das Drehbuch

```python
import sys

import sil_lift

path = "dictionary.lift"
lex = sil_lift.load(path)

edited_glosses = 0

for entry in lex.entries:
    for sense in entry.all_senses():
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

- `entry.all_senses()` gibt jede Bedeutung _und Unterbedeutung_ zurück, und zwar in der Reihenfolge des Dokuments und nach der Tiefe.
  - `entry.senses` enthält nur die oberste Ebene; daher würde eine Massenbearbeitung, die diese Struktur durchläuft, alle unter einer Unterbedeutung verschachtelten Erläuterungen stillschweigend überspringen.
- `gloss.text` ist ein `Text` und keine einfache Zeichenkette: `str(gloss.text)` wandelt ihn für den Abgleich in eine Zeichenkette um, und die Ersetzung wird mit `sil_lift.Text([new])` zurückgeschrieben, anstatt die Zeichenkette direkt zu ändern.
- `lex.changed_entries()` gibt die Einträge zurück, deren Inhalt sich von dem der geladenen Datei unterscheidet. Jede Änderung an einer beliebigen Stelle innerhalb eines Eintrags, selbst in einer verschachtelten Unterbedeutung, führt dazu, dass dieser Eintrag gemeldet wird. Wenn man einem Feld den Wert zuweist, den es bereits hatte, wird nichts gemeldet, da sich der Inhalt nicht geändert hat.
- `changed_entries()` erfasst nur den Inhalt der Einträge; es handelt sich also um eine Zählung und nicht um einen Schreibschutz. Um eine Speicherung zu überspringen, die keine Änderungen zur Folge hätte, verwende `lex.changes()`; siehe [Speichern](read-edit-write.md#saving).
- Bei der Validierung im Arbeitsspeicher (`lex.iter_problems()`) wird der bearbeitete Zustand zunächst serialisiert, sodass er die Änderungen korrekt widerspiegelt, bevor Daten auf die Festplatte geschrieben werden. Das Abbrechen bei jedem `"error"`-Problem (Warnungen werden dem Aufrufer zur Entscheidung überlassen) bedeutet, dass eine fehlerhafte Bearbeitung niemals die Funktion `save()` erreicht.
- `lex.save()` versieht genau die Einträge, die dieses Skript geändert hat, mit einem neuen `dateModified`-Zeitstempel und füllt dabei `dateCreated` aus, sofern dieses Feld leer war.
  - Sowohl FieldWorks als auch der LIFT-Import von The Combine legen anhand von `dateModified` fest, was aktualisiert werden soll. Ohne das aktuelle Datum würden sie die bearbeiteten Einträge daher als unverändert behandeln.
  - Es werden nur Elemente vom Typ `<entry>` mit einem Stempel versehen. Wenn eine Erläuterung zu einer Unterbedeutung bearbeitet wird, wird das Datum dem übergeordneten Eintrag zugeordnet, nicht der Bedeutung.

## Ausführen

Führe eine Suche in einem kleinen Lexikon durch, in dem sowohl die Erläuterung als auch die Erläuterung einer Unterbedeutung „Farbe“ lauten:

```
2 Begriffserklärungen in 1 Eintrag bearbeitet
```

## Der Lohn für Treue

Die Garantie gilt pro _Eintrag_: Ein Eintrag, dessen Modell sich nicht geändert hat, wird **byte-identisch** so zurückgegeben, wie er eingelesen wurde, und nur die Einträge, die Sie tatsächlich bearbeitet haben, werden erneut serialisiert. In dem oben genannten Durchlauf wurden bei einem Eintrag die Glossen bearbeitet; alle anderen Einträge in der Datei behielten ihre exakten Bytes bei. Das Bearbeiten eines Eintrags in einem Lexikon mit 50.000 Einträgen führt daher zu einer Diff-Datei, die nur einen Eintrag betrifft, und nicht zu einer neu formatierten Datei.

Beachten Sie die Detailgenauigkeit: Wenn Sie einen beliebigen Teil eines Eintrags bearbeiten, wird der gesamte Eintrag neu serialisiert, einschließlich der davon unberührten verwandten Bedeutungen. Den genauen Vertragsinhalt finden Sie unter [Fidelity-Garantien](../fidelity.md).

## Jenseits der Glosse

Der gleiche Ansatz funktioniert auch bei anderen mehrsprachigen Feldern. Glossare sind eine Liste von `Form`-Objekten, während Definitionen und die meisten anderen mehrsprachigen Felder `Multitext`-Zuordnungen sind, die nach Sprache indiziert sind. Daher handelt es sich bei einer Bearbeitung um eine einfache Zuweisung:

```python
sense.definition["en"] = "die Farbe eines Gegenstands"
```

Informationen zum Verhalten der Zuordnung finden Sie unter [Mehrsprachiger Text](read-edit-write.md#multilingual-text).
