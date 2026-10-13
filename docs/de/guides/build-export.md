# Beispiel: Erstellung eines LIFT-Exports von Grund auf

Wenn Sie die Daten einer anderen Anwendung als LIFT exportieren – die Aufgabe, die hinter [Erstellung konformer LIFT-Dateien](lift-export-interop.md) steht –, kann `sil-lift` das Dokument Objekt für Objekt aufbauen und serialisieren, anstatt XML manuell zu generieren. Hier wird ein Skript Schritt für Schritt erläutert, das einen Eintrag mit den Bestandteilen eines echten Wörterbuchs erstellt (mehrere Schriftsysteme, eine Aussprache, eine Bedeutung mit einem Beispiel, eine Illustration, ein Merkmal des semantischen Bereichs und ein anwendungsspezifisches Feld), die kontrollierten Vokabulare in eine zugehörige `.lift-ranges`-Datei schreibt, die Daten validiert und speichert.

## Das Drehbuch

```python
from pathlib import Path

import sil_lift

lex = sil_lift.Lexicon(producer="my-exporter")

# Ein Eintrag, der aus dem Quellmodell erstellt wurde.
entry = sil_lift.Entry(id="kanga", guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d")
entry.lexical_unit["seh"] = "nkhuku"
entry.lexical_unit["pt"] = "galinha"

pron = sil_lift.Pronunciation()
pron.forms["en"] = "Sprecher: Ana"  # Die Konvention des Combine für Sprecherbezeichnungen
pron.media.append(sil_lift.URLRef(href="audio/nkhuku.wav"))
entry.pronunciations.append(pron)

sense = sil_lift.Sense(id="kanga_s1")
sense.grammatical_info = sil_lift.GrammaticalInfo(value="Noun")
sense.glosses.append(sil_lift.Form(lang="en", text=sil_lift.Text(["chicken"])))
sense.definition["en"] = "a domestic fowl kept for its eggs and meat"

example = sil_lift.Example()
example.forms["seh"] = "Ndinafuna nkhuku."
translation = sil_lift.Translation()
translation.forms["en"] = "I want a chicken."
example.translations.append(translation)
sense.examples.append(example)

photo = sil_lift.URLRef(href="pictures/hen.jpg")
photo.label["en"] = "Eine Henne"
sense.illustrations.append(photo)

sense.traits.append(sil_lift.Trait(name="semantic-domain-ddp4", value="1.6.1.2"))

scientific = sil_lift.Field(type="scientific-name")  # ein anwendungsspezifisches Zusatzfeld
scientific.content["en"] = "Gallus gallus domesticus"
sense.fields.append(scientific)

entry.senses.append(sense)
lex.entries.append(entry)

# Die kontrollierten Vokabulare, auf die sich der Eintrag bezieht, in einer zugehörigen .lift-ranges-Datei.
ranges = sil_lift.RangesFile()
ranges.add_range("grammatical-info").add_element("Noun").label["en"] = "noun"
ranges.add_range("semantic-domain-ddp4").add_element("1.6.1.2").label["en"] = "Bird"
lex.add_ranges_file(ranges, href="birds.lift-ranges")

# Das Dokument in seiner aktuellen Form validieren, bevor es auf die Festplatte geschrieben wird.
problems = list(lex.iter_problems())
print(f"Validierung: {len(problems)} Problem(e)")

out = Path("export")
out.mkdir(exist_ok=True)
lex.save(out / "birds.lift")
print("=== birds.lift ===")
print((out / "birds.lift").read_text(encoding="utf-8"), end="")
print("=== birds.lift-ranges ===")
print((out / "birds.lift-ranges").read_text(encoding="utf-8"), end="")
```

## Was dabei entsteht

`Validierung: 0 Problem(e)`, dann das `.lift` und sein Begleitelement nebeneinander:

```
=== birds.lift ===
<?xml version="1.0" encoding="UTF-8"?>
<lift version="0.13" producer="my-exporter">
<header>
  <ranges>
    <range id="grammatical-info" href="birds.lift-ranges"/>
    <range id="semantic-domain-ddp4" href="birds.lift-ranges"/>
  </ranges>
</header>
<entry id="kanga" guid="6b9e7c2a-3f4d-4a1b-8c5e-2d9f0a1b2c3d" dateCreated="2026-09-02T19:19:17Z" dateModified="2026-09-02T19:19:17Z">
  <lexical-unit>
    <form lang="seh">
      <text>nkhuku</text>
    </form>
    <form lang="pt">
      <text>Huhn</text>
    </form>
  </lexical-unit>
  <pronunciation>
    <form lang="en">
      <text>Sprecherin: Ana</text>
    </form>
    <media href="audio/nkhuku.wav"/>
  </pronunciation>
  <sense id="kanga_s1">
    <grammatical-info value="Noun"/>
    <gloss lang="en">
      <text>Huhn</text>
    </gloss>
    <definition>
      <form lang="en">
        <text>ein Hausgeflügel, das wegen seiner Eier und seines Fleisches gehalten wird</text>
      </form>
    </definition>
    <example>
      <form lang="seh">
        <text>Ich möchte ein Huhn.</text>
      </form>
      <translation>
        <form lang="en">
          <text>Ich möchte ein Huhn.</text>
        </form>
      </translation>
    </example>
    <illustration href="pictures/hen.jpg">
      <label>
        <form lang="en">
          <text>Eine Henne</text>
        </form>
      </label>
    </illustration>
    <trait name="semantic-domain-ddp4" value="1.6.1.2"/>
    <field type="scientific-name">
      <form lang="en">
        <text>Gallus gallus domesticus</text>
      </form>
    </field>
  </sense>
</entry>
</lift>
=== birds.lift-ranges ===
<?xml version="1.0" encoding="UTF-8"?>
<lift-ranges>
<range id="grammatical-info">
  <range-element id="Noun">
    <label>
      <form lang="en">
        <text>Substantiv</text>
      </form>
    </label>
  </range-element>
</range>
<range id="semantic-domain-ddp4">
  <range-element id="1.6.1.2">
    <label>
      <form lang="en">
        <text>Vogel</text>
      </form>
    </label>
  </range-element>
</range>
</lift-ranges>
```

## Hinweise zur API

- Multitext-Felder (`lexical_unit`, `definition`, eine `Form`/`URLRef`-Bezeichnung, der Inhalt eines `Field`s, ...) Über die Mapping-Schnittstelle wird pro Schriftsystem eine Zeichenfolge übernommen: `entry.lexical_unit["seh"] = "nkhuku"` fügt ein `<form lang="seh">` hinzu. Ein Quellmodell, das Zeichenfolgen anhand des Sprachcodes zuordnet, lässt sich direkt darauf abbilden.
- `RangesFile.add_range()` / `Range.add_element()` erstellen die kontrollierten Vokabulare, und `Lexicon.add_ranges_file(ranges, href=...)` fügt das zugehörige Dokument hinzu und ergänzt die Header-Referenzen `<range href>` – sodass die Einträge `<grammatical-info value="Noun">` und `<trait name="semantic-domain-ddp4" value="1.6.1.2">` auf die von Ihnen definierten Bereiche verweisen.
- Ein `URLRef` besteht aus einem `href` sowie einem optionalen Multitext für eine Beschriftung oder Bezeichnung – er wird sowohl für `<media>` (Audio) als auch für `<illustration>` (Fotos) verwendet. Die Aussprache folgt hier der Konvention von „The Combine“, wonach die „en“-Form wie folgt ausgesprochen wird: „Sprecher: <name> “.
- App-spezifische Daten ohne native LIFT-Heimfahrten als „<field> “ (oder „<trait> “): FieldWorks interpretiert diese als benutzerdefinierte Felder, und The Combine behält sie bei.
- Weisen Sie jedem Eintrag eine echte, stabile `guid` zu (z. B. aus `uuid.uuid4()`, die bei allen Exporten wiederverwendet wird) – bei einem späteren Reimport wird der Eintrag an Ort und Stelle aktualisiert, anstatt ihn zu duplizieren. `sil-lift validate --require-ids` sorgt dafür, dass dies eingehalten wird.
- Die Angaben `dateCreated`/`dateModified` in der obigen Ausgabe sind nicht im Skript enthalten: `save()` hat sie mit dem Zeitpunkt seiner Ausführung versehen, da ein zum ersten Mal geschriebener Eintrag kein eigenes Datum enthält. `when=` gibt diesen Zeitpunkt an, anstatt die Uhrzeit auszulesen – dadurch ist ein generierter Export für einen CI-Job zum Abgleich byteweise reproduzierbar; `stamp=False` schreibt überhaupt keine Datumsangaben. Den Rest des Vertrags finden Sie unter [Generierte Zeitstempel](../fidelity.md#generated-timestamps).
- `lex.iter_problems()` überprüft das Dokument im Arbeitsspeicher, bevor Daten auf die Festplatte geschrieben werden; hier ist es fehlerfrei. Da das Lexikon noch keinen Ordner hat, werden die Überprüfungen auf Medienpräsenz und Companion-Href übersprungen – führen Sie [`sil-lift validate`](cli.md) auf der gespeicherten Ausgabe aus (oder mit `--no-check-media`), sobald die Audio- und Fotodateien vorhanden sind.

## Verpackung

`lex.save("export/birds.lift")` schreibt die Ordnerstruktur (`.lift` + `.lift-ranges` nebeneinander). Um ein einzelnes ZIP-Paket zu erstellen, das von FieldWorks und The Combine direkt importiert werden kann, verwenden Sie stattdessen `lex.save_zip("birds.zip")` – siehe [Erstellung konformer LIFT-Dateien](lift-export-interop.md).
