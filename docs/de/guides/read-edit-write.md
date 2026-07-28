# Lesen, bearbeiten, schreiben

## Wird geladen

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` akzeptiert jedes wohlgeformte LIFT-**0.13**-Dokument – einschließlich schemaverstossender Dateien aus der Praxis. Alles, was das Modell nicht definiert (unbekannte Elemente/Attribute, Kommentare), wird verlustfrei im undurchsichtigen `extra`-Bereich jedes Knotens übertragen. Andere LIFT-Versionen lösen einen `LiftParseError` aus, in dem die Version angegeben wird.

## Das Modell

Jedes LIFT-Element ist eine typisierte Datenklasse: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal` und so weiter. Mehrsprachiger Text ist ein `Multitext`, der sich wie eine Zuordnung vom Sprachcode zu `Text` verhält:

```python
entry = lex.find(id="abat")

str(entry.lexical_unit["seh"])          # "abat"
entry.lexical_unit["en"] = "grove"      # einfache Zeichenketten werden umgewandelt
"en" in entry.citation                  # False
```

`Text` ist strukturiert – eine geordnete Liste aus `str`- und `Span`-Fragmenten –, da `<text>` verschachtelte `<span>`-Markups enthalten kann. `str(text)` wandelt den Text in reinen Text um; die Fragmente behalten das Markup für den Hin- und Rücktransport bei.

Glossare sind in LIFT _form-förmig_ (jedes `<gloss>` enthält eine eigene Sprache), daher hat ein Sense `glosses: list[Form]` sowie eine Hilfsfunktion:

```python
sense = entry.senses[0]
sense.gloss("en")                       # Text | None
entry.gloss_langs()                     # {"en", "id"}
```

## Speichern

```python
lex.save()                # zurück an den Ort, von dem es geladen wurde
lex.save("elsewhere.lift")
```

Einträge, die Sie nicht geändert haben, werden **byte-identisch** zurückgeschrieben; ein Dokument, das Sie überhaupt nicht geändert haben, ist vom ersten bis zum letzten Byte byte-identisch. Den genauen Vertragsinhalt finden Sie unter [Fidelity-Garantien](../fidelity.md).

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
