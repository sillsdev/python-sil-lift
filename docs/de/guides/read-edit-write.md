# Lesen, bearbeiten, schreiben

## Wird geladen

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` akzeptiert jedes wohlgeformte LIFT-**0.13**-Dokument, einschließlich schemaverstossender Dateien aus der Praxis. Alles, was das Modell nicht definiert (unbekannte Elemente/Attribute, Kommentare), wird verlustfrei als LIFT-Rest im undurchsichtigen `extra`-Feld jedes Knotens übertragen. Andere LIFT-Versionen lösen einen `LiftParseError` aus, in dem die Version angegeben wird.

## Das Modell

Jedes LIFT-Element ist eine typisierte Datenklasse: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal` und so weiter.

### Mehrsprachiger Text

Mehrsprachiger Text ist ein `Multitext`, also eine `Zuordnung` vom Sprachcode zum `Text`:

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # „poʻo“
entry.lexical_unit["en"] = „head“       # einfache Zeichenketten werden umgewandelt
„en“ in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

`Text` ist strukturiert (eine geordnete Liste aus `str`- und `Span`-Fragmenten), da `<text>` verschachtelte `<span>`-Markups enthalten kann. `str(text)` wandelt den Text in reinen Text um; die Fragmente behalten das Markup für den Hin- und Rücktransport bei.

Die Zuordnung zeigt einen Wert pro Sprache. Darunter enthält `forms` alle `<form>` in der Reihenfolge, in der sie in der Datei stehen. Ein schemakonformes Dokument enthält höchstens eine Formularvariante pro Sprache, doch in realen Dateien kommt es manchmal vor, dass sich eine davon wiederholt.

Da die Zuordnung nach Sprache sortiert ist, zählt `len()` die Sprachen und nicht die Formen, und die Ansichten `keys()`, `values()` und `items()` listen jede Sprache nur einmal auf. Beide Mutatoren wirken sich zudem auf die gesamte Sprache aus: `del entry.lexical_unit["en"]` entfernt alle englischen Formen, und durch die Zuweisung an `"en"` bleibt genau eine übrig.

Bei einer wiederholten Sprache geben `entry.lexical_unit["en"]`, `get()`, `values()` und `items()` jeweils die erste Form zurück, und [`validate`](validate.md#problem-codes) meldet den Fehler `duplicate-form-lang`, bis Sie dieser Sprache einen Wert zuweisen.

Ein Formular, das überhaupt kein `lang`-Attribut enthält, kann über das Mapping nicht erstellt werden. Es wird als „form-missing-lang“ gemeldet und bei der erneuten Serialisierung des Knotens verworfen.

### Bedeutungen und Erläuterungen

Glossare sind in LIFT _Form-förmig_ (jede `<gloss>` enthält ihre eigene Sprache), daher hat ein Sense `glosses: list[Form]` sowie Hilfsfunktionen:

```python
sense = entry.senses[0]       # nur oberste Ebene
sense.gloss("en")             # Text | None
entry.all_senses()            # alle Bedeutungen und Unterbedeutungen, in der Reihenfolge des Dokuments
entry.gloss_langs()           # {"en", "id"}, einschließlich Unterbedeutungen
```

Verwenden Sie `all_senses()`, wann immer sich eine Frage auf den gesamten Eintrag bezieht: zum Zählen von Bedeutungen, zum Erfassen von Sprachen oder zum Suchen von Medien. `entry.senses` gibt die oberste Ebene an, was nur dann sinnvoll ist, wenn die Verschachtelung selbst eine Rolle spielt.

## Speichern

```python
lex.save()                    # zurück an den Ort, von dem es geladen wurde
lex.save("elsewhere.lift")
```

Einträge, die Sie nicht geändert haben, werden **byte-identisch** zurückgeschrieben; ein Dokument, das Sie überhaupt nicht geändert haben, ist vom ersten bis zum letzten Byte byte-identisch. Den genauen Vertragsinhalt finden Sie unter [Fidelity-Garantien](../fidelity.md).

### Zeitstempel

Die von Ihnen geänderten Einträge werden mit einem neuen `dateModified`-Wert (und einem `dateCreated`-Wert, falls noch keiner vorhanden war) ausgegeben, sodass eine Bearbeitung nicht unter dem Datum erscheint, mit dem sie geladen wurde. Tools, die LIFT zusammenführen, entscheiden, was sich bei diesem Attribut geändert hat. Zwei Argumente dienen zur Anpassung der Prägung:

- `lex.save(stamp=False)` schreibt lediglich die im Modell enthaltenen Datumsangaben und sonst nichts.
- `lex.save(when=...)` hält den Moment fest, anstatt die Uhr abzulesen.

Die übrigen Regeln finden Sie unter [Generierte Zeitstempel](../fidelity.md#generated-timestamps).

### Ein Speichern überspringen, das nichts ändert

Um ein Speichern zu überspringen, das keine Änderungen zur Folge hätte, schütze es mit `lex.changes()`:

```python
if lex.changes():
    lex.save()
```

Die Funktion gibt nur dann `False` zurück, wenn `save()` die Quellbytes reproduzieren würde, einschließlich der Einträge, des Headers, des Stammelements und aller zugehörigen `.lift-ranges`-Elemente. Wird der Schreibvorgang übersprungen, bleibt der Änderungszeitstempel der Datei unverändert, und es wird ein falscher Diff vermieden.

Der Scheck ist günstig. Es hört beim ersten Unterschied auf, sodass es bei einem bearbeiteten Lexikon fast nichts kostet. Ein unverändertes Lexikon muss vollständig serialisiert werden, um nachzuweisen, dass es unverändert ist, doch das kostet immer noch weniger als der Speichervorgang, der dadurch übersprungen wird.

Da dabei der Inhalt und nicht das Ziel verglichen wird, sollte nur eine Speicherung am ursprünglichen Speicherort geschützt werden. `lex.save("elsewhere.lift")` schreibt das Dokument und die zugehörigen Dateien in den neuen Pfad, selbst wenn `changes()` den Wert `False` hat; durch eine Abfrage würde diese Kopie also übersprungen werden.

## Von Grund auf neu aufbauen

```python
lex = sil_lift.Lexicon(producer="my-script 1.0")
entry = sil_lift.Entry(id="hello", guid="...")
entry.lexical_unit["en"] = "hello"
sense = sil_lift.Sense()
sense.glosses.append(sil_lift.Form("fr", sil_lift.Text(["bonjour"])))
entry.senses.append(sense)
lex.entries.append(entry)
lex.save("new.lift")
```

## Kanonische Sortierung

```python
lex.sort()      # Einträge nach (GUID, ID); Bereiche/Felddefinitionen nach ID/Tag
lex.save()      # Unveränderte Einträge behalten ihre exakten Bytes in der neuen Reihenfolge

sil_lift.canonicalize("in.lift", "out.lift")   # vollständig neu serialisiert, bereit für den Vergleich
```

Siehe auch: [Beispiel: Massenbearbeitung von Glossaren](bulk-edit-glosses.md).
