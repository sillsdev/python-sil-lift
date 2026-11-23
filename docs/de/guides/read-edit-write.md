# Lesen, bearbeiten, schreiben

## Wird geladen

```python
import sil_lift

lex = sil_lift.load("dictionary.lift")
```

`load()` accepts any well-formed LIFT **0.13** document, including schema-invalid real-world files. Alles, was das Modell nicht definiert (unbekannte Elemente/Attribute, Kommentare), wird verlustfrei als LIFT-Rest im undurchsichtigen `extra`-Feld jedes Knotens übertragen. Andere LIFT-Versionen lösen einen `LiftParseError` aus, in dem die Version angegeben wird.

## Das Modell

Every LIFT element is a typed dataclass: `Entry`, `Sense`, `Example`, `Pronunciation`, `Variant`, `Relation`, `Etymology`, `Reversal`, and so on.

### Multilingual text

Mehrsprachiger Text ist ein `Multitext`, also eine `Zuordnung` vom Sprachcode zum `Text`:

```python
entry = lex.find(id="poʻo_a1b2")

str(entry.lexical_unit["haw"])          # "poʻo"
entry.lexical_unit["en"] = "head"       # plain strings are coerced
"en" in entry.citation                  # False
list(entry.lexical_unit.keys())         # ["haw", "en"]
```

`Text` is structured (an ordered list of `str` and `Span` fragments) because `<text>` can contain nested `<span>` markup. `str(text)` wandelt den Text in reinen Text um; die Fragmente behalten das Markup für den Hin- und Rücktransport bei.

The mapping shows one value per language. Underneath, `forms` holds every `<form>` in file order. A schema-valid document has at most one form per language, but real files sometimes repeat one.

Because the mapping is keyed by language, `len()` counts languages rather than forms, and the `keys()`, `values()` and `items()` views list each language once. Both mutators also act on the whole language: `del entry.lexical_unit["en"]` removes every English form, and assigning to `"en"` leaves exactly one.

For a repeated language, `entry.lexical_unit["en"]`, `get()`, `values()` and `items()` all answer with its first form, and [`validate`](validate.md#problem-codes) reports `duplicate-form-lang` until you assign to that language.

A form carrying no `lang` at all cannot be created through the mapping. It is reported as `form-missing-lang`, and is dropped when its node re-serializes.

### Senses and glosses

Glossare sind in LIFT _Form-förmig_ (jede `<gloss>` enthält ihre eigene Sprache), daher hat ein Sense `glosses: list[Form]` sowie Hilfsfunktionen:

```python
sense = entry.senses[0]       # top level only
sense.gloss("en")             # Text | None
entry.all_senses()            # every sense and subsense, document order
entry.gloss_langs()           # {"en", "id"}, subsenses included
```

Verwenden Sie `all_senses()`, wann immer sich eine Frage auf den gesamten Eintrag bezieht: zum Zählen von Bedeutungen, zum Erfassen von Sprachen oder zum Suchen von Medien. `entry.senses` gibt die oberste Ebene an, was nur dann sinnvoll ist, wenn die Verschachtelung selbst eine Rolle spielt.

## Speichern

```python
lex.save()                    # back to where it was loaded from
lex.save("elsewhere.lift")
```

Einträge, die Sie nicht geändert haben, werden **byte-identisch** zurückgeschrieben; ein Dokument, das Sie überhaupt nicht geändert haben, ist vom ersten bis zum letzten Byte byte-identisch. Den genauen Vertragsinhalt finden Sie unter [Fidelity-Garantien](../fidelity.md).

### Zeitstempel

Die von Ihnen geänderten Einträge werden mit einem neuen `dateModified`-Wert (und einem `dateCreated`-Wert, falls noch keiner vorhanden war) ausgegeben, sodass eine Bearbeitung nicht unter dem Datum erscheint, mit dem sie geladen wurde. Tools that merge LIFT decide what changed from that attribute. Two arguments adjust the stamping:

- `lex.save(stamp=False)` writes the dates the model holds and nothing more.
- `lex.save(when=...)` pins the moment instead of reading the clock.

Die übrigen Regeln finden Sie unter [Generierte Zeitstempel](../fidelity.md#generated-timestamps).

### Skipping a save that changes nothing

Um ein Speichern zu überspringen, das keine Änderungen zur Folge hätte, schütze es mit `lex.changes()`:

```python
if lex.changes():
    lex.save()
```

Die Funktion gibt nur dann `False` zurück, wenn `save()` die Quellbytes reproduzieren würde, einschließlich der Einträge, des Headers, des Stammelements und aller zugehörigen `.lift-ranges`-Elemente. Skipping the write leaves the file's modification time alone and avoids a spurious diff.

The check is cheap. Es hört beim ersten Unterschied auf, sodass es bei einem bearbeiteten Lexikon fast nichts kostet. Ein unverändertes Lexikon muss vollständig serialisiert werden, um nachzuweisen, dass es unverändert ist, doch das kostet immer noch weniger als der Speichervorgang, der dadurch übersprungen wird.

Da dabei der Inhalt und nicht das Ziel verglichen wird, sollte nur eine Speicherung am ursprünglichen Speicherort geschützt werden. `lex.save("elsewhere.lift")` writes the document and its companions to the new path even when `changes()` is `False`, so guarding it would skip that copy.

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
