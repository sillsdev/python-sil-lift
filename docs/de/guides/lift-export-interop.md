# Erstellung eines konformen LIFT

Dieser Leitfaden richtet sich an alle, die einen LIFT-_Exporter_ schreiben – also Code in einer beliebigen Sprache, der das Datenmodell einer anderen Anwendung in LIFT 0.13 umwandelt. `sil-lift` erfüllt bei dieser Arbeit zwei Funktionen: zum einen dient es als Konformitätsprüfung, die die Ausgabe anhand des Schemas und der Semantik, die ein Schema nicht ausdrücken kann, überprüft, und zum anderen als Referenz für die Formen und Textregeln, denen die Ausgabe entsprechen muss.

Das Schreiben von LIFT ist viel einfacher als dessen Analyse: Ein Exporter gibt nur die Teilmenge der Konstrukte aus, die sein eigenes Modell erzeugt, und muss sich nie mit den optionalen Elementen der vollständigen Spezifikation auseinandersetzen. Das Schwierige sind die Details – der `.lift-ranges`-Begleiter, der schriftsystemspezifische Text, die stabilen IDs und die XML-Escape-Zeichen – und genau diese werden durch die folgenden Prüfungen erfasst.

## ZIP-Dateien

LIFT wird in der Regel als einzelne `.zip`-Datei weitergegeben – sowohl FieldWorks als auch The Combine importieren und exportieren auf diese Weise –, daher liest und schreibt `sil-lift` komprimierte Pakete direkt, und zwar in beiden vom Ökosystem verwendeten Strukturen: entweder mit den Dateien im Stammverzeichnis des Archivs oder verschachtelt unter einem Ordner der obersten Ebene.

- **Hinweis:** `sil_lift.load("package.zip")` entpackt die Datei in ein temporäres Verzeichnis, sucht die einzelne `.lift`-Datei und lädt sie (Begleitdateien und Medien werden wie gewohnt aufgelöst). Die CLI-Befehle `validate`, `stats`, `check-media` und `export` akzeptieren ebenfalls einen `.zip`-Pfad, sodass das unten stehende Skript direkt auf ein Paket in seiner aktuellen Form angewendet werden kann. Die Extraktion ist gegen bösartige Archive abgesichert – Elemente, die eine Pfadüberquerung bewirken, werden abgelehnt, und die Anzahl der Einträge sowie die Gesamtgröße im unkomprimierten Zustand (10 GiB) sind zur Abwehr von ZIP-Bomben begrenzt.
- **Schreiben Sie:** `Lexicon.save_zip("out.zip", wrap_folder="MyDict")` packt die `.lift`-Datei, deren `.lift-ranges` sowie alle anderen Dateien im Quellordner (media, `WritingSystems/`, `consent/`, ...) zusammen. in eine ZIP-Datei. `wrap_folder` ist standardmäßig auf einen Ordner auf oberster Ebene eingestellt, der nach der ZIP-Datei benannt ist (gemäß der Importkonvention von FieldWorks/Combine); übergeben Sie `False`, um ein flaches Archiv zu erhalten.

Die Dateien `.lift` und `.lift-ranges` behalten ihre Byte-Genauigkeit innerhalb des Pakets bei; der ZIP-Container selbst ist nicht byte-reproduzierbar.

## Die Ausgabe als Konformitätsprüfung validieren

Richten Sie den Befehl `sil-lift validate` auf die erstellte `.lift`-Datei aus. Es führt RELAX NG-Prüfungen durch (sowohl für die `.lift`-Datei als auch für die zugehörige `.lift-ranges`-Datei) sowie semantische Prüfungen, die die Grammatik nicht ausdrücken kann: frei schwebende `relation`-/`variant`-Verweise, doppelte GUIDs, die Integrität der übergeordneten Elemente von Bereichselementen, in ihrem Bereich nicht definierte Werte für Merkmale und grammatikalische Informationen sowie `range/@href`-Verweise in Headern, die auf kein zugehöriges Element verweisen.

Bei CI: Bei jedem Fehler den Vorgang abbrechen und maschinenlesbare Ergebnisse ausgeben:

```
sil-lift validate export.lift --strict --no-check-media --format json
```

- Mit `--strict` führen bereits Warnungen (nicht nur Fehler) zum Abbruch der Ausführung.
- `--no-check-media` überspringt die Überprüfung auf das Vorhandensein von Mediendateien im Dateisystem, deren `missing-media`-Funde irreführend sind, wenn sich die Audio- und Fotodateien in der CI nicht im selben Ordner wie die `.lift`-Datei befinden.
- `--format json` gibt anstelle von lesbarem Text ein einzelnes JSON-Objekt aus (`{"problems": [...], "summary": {...}}`); die Rückgabecodes und das Schema bilden eine unterstützte, SemVer-konforme Schnittstelle (siehe [das Handbuch zur Befehlszeile](cli.md)).
- `--require-ids` gibt zusätzlich Fehlermeldungen aus, wenn bei Einträgen eine `guid` fehlt oder bei Sensoren eine `id` fehlt – nützlich, wenn bei einem späteren erneuten Import die Einträge aktualisiert und nicht dupliziert werden sollen.

Schützen Sie sich vor unbemerktem Datenverlust (dem Fehlermodus, der den Export als flache CSV-Datei verlustbehaftet macht), indem Sie die Zählwerte mit `stats --format json` für Ihr Quellmodell überprüfen:

```
sil-lift stats export.lift --format json
```

Es gibt die Anzahl der „Einträge“, „Bedeutungen“, „Beispiele“, „Medienverweise“, „Sprachen“ sowie die Anzahl der „Merkmale“ pro Name an.

### Ausführung von „gate“ ohne Python-Toolchain

Die CI eines TypeScript- oder C#-Projekts kann dieselbe Überprüfung über die mitgelieferte GitHub-Action ausführen, ohne dass Python installiert werden muss:

```yaml
- uses: sillsdev/python-sil-lift@v0.1.0
  with:
    path: export.lift
    strict: "true"
    no-check-media: "true"
    format: json
```

oder das Container-Image, das anhand der `Dockerfile`-Datei aus dem Repository erstellt wurde:

```
docker build -t sil-lift .
docker run --rm -v "$PWD:/work" -w /work sil-lift validate export.lift --strict
```

## Der `.lift-ranges`-Begleiter

Kontrollierte Vokabulare – Wortarten, semantische Domänen und alle anderen auf Merkmalen basierenden Wertemengen – befinden sich in einer gleichrangigen `.lift-ranges`-Datei, auf die in der Datei `<header>` verwiesen wird:

```xml
<header>
  <ranges>
    <range id="grammatical-info" href="mydict.lift-ranges"/>
    <range id="semantic-domain-ddp4" href="mydict.lift-ranges"/>
  </ranges>
</header>
```

Das Begleitheft enthält die vollständige Definition der einzelnen Bereiche. Die Werte sind `<range-element>`s; `parent` bildet eine Hierarchie; `label` / `abbrev` / `description` sind Multitexte:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<lift-ranges>
  <range id="grammatical-info">
    <range-element id="Noun">
      <label><form lang="en"><text>Substantiv</text></form></label>
      <abbrev><form lang="en"><text>n</text></form></abbrev>
    </range-element>
  </range>
  <range id="semantic-domain-ddp4">
    <range-element id="1.6.1.2">
      <label><form lang="en"><text>Vogel</text></form></label>
    </range-element>
  </range>
</lift-ranges>
```

Ein Eintrag verweist dann anhand der ID auf einen Wert: Die Wortart einer Bedeutung lautet `<grammatical-info value="Noun"/>`, und eine semantische Domäne lautet `<trait name="semantic-domain-ddp4" value="1.6.1.2"/>`. `sil-lift validate` gibt eine Warnung (`undefined-range-value`) aus, wenn ein Wert nicht innerhalb seines Bereichs definiert ist, und einen Fehler (`range-parent`), wenn ein `parent` keine Geschwister-ID ist – geben Sie daher die Bereiche an, die Ihre Daten tatsächlich verwenden. Siehe auch [Bereiche und Medien](folder-media.md).

Wenn Sie den Export in Python erstellen, erstellen `Lexicon.add_ranges_file()`, `RangesFile.add_range()` und `Range.add_element()` das zugehörige Objekt und fügen die Header-Referenzen für Sie hinzu; `open_writer(..., ranges=...)` führt dasselbe auf dem Streaming-Pfad durch.

## Text und Mehrfachtext

Jede Zeichenkette in einer menschlichen Sprache in LIFT ist ein _Multitext_: ein `<form>` pro Schriftsystem, wobei jedes ein `<text>` umschließt:

```xml
<lexical-unit>
  <form lang="seh"><text>Kanga</text></form>
  <form lang="pt"><text>Huhn</text></form>
</lexical-unit>
```

Ein Modell, das Zeichenfolgen anhand des Sprachcodes indiziert (ein `MultiString`, ein `Record<code, string>`, ein `dict[str, str]`), lässt sich eins-zu-eins auf dieses Modell abbilden: Ein Eintrag pro Schlüssel entspricht einem `<form lang="…">`. In einem einzelnen Multitext ist höchstens eine Form pro Sprache zulässig – andernfalls gibt `sil-lift` die Warnung `duplicate-form-lang` aus.

Das XML-Escaping ist der einzige Teil, bei dem es wirklich auf Korrektheit ankommt. Im Elementtext müssen `&`, `<`, and `>` mit Escape-Zeichen versehen werden (`&amp;`, `&lt;`, `&gt;`); in Attributwerten gilt dies auch für das Anführungszeichen. Der Autor von `sil-lift` wendet genau diese Regeln an und verändert niemals die Leerzeichen innerhalb von `<text>` – er fügt dort keine Einrückungen hinzu, da dies die lexikalischen Daten verfälschen würde. Wenn Sie die Ausgabe des Serialisierers nachbilden möchten, sollten Sie die Escaping-Zeichen eines echten XML-Serialisierers verwenden (und nicht eine selbst programmierte Ersetzungsfunktion, bei der das `&`-Zeichen vergessen wird) und den Inhalt von `<text>` Byte für Byte so belassen, wie er in Ihrer Quelle vorliegt.
