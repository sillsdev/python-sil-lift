# Überprüfen

Die Validierung erfolgt stets explizit: Beim Laden und Speichern findet niemals eine implizite Validierung statt.

```python
import sil_lift

# Vollständig: ein „lazy“ Stream von Problemen (Schema + semantische Ebenen).
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # Fehler [dangling-ref] dictionary.lift:88 (Eintrag apu): ref 'nope' passt zu ...

# Fail-fast: Bei dem ersten Problem auf Fehler-Ebene abbrechen.
if any(p.level == "error" for p in sil_lift.iter_problems("dictionary.lift")):
    raise SystemExit(1)

# Speicherinterner Zustand (wird zunächst serialisiert, was bei großen Lexika dokumentierte Kosten verursacht):
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

Jedes `Problem` enthält einen `Level` (`"Fehler"`/`"Warnung"`), einen festen `Code` und eine `Meldung` sowie, soweit vorhanden, die Adresse des Fundorts:

- `file`: `None`, wenn das Lexikon keinen Pfad hat.
- `entry_id`: Wird gesetzt, wenn sich der Befund auf einen Eintrag bezieht.
- `guid`: Wird gesetzt, wenn das betreffende Objekt über eine solche Kennung verfügt (ein Eintrag oder ein Bereichselement).
- `line`: Wird gesetzt, wenn das Suchergebnis einer Zeile im Dokument entspricht.

Eine Feststellung bezüglich eines Bereichs richtet sich an den Companion `.lift-ranges`, der diesen definiert, und enthält keinen Eintrag. Nicht gesetzte Felder sind `None` (`null` bei `--format json`, wo jeder Schlüssel immer vorhanden ist).

## Die Schichten

1. **LIFT-Schema** (`lift-0.13.rng`, die RELAX-NG-Grammatik von LIFT 0.13, byteweise identisch mit der aus lift-standard) über die `.lift`-Datei.
2. **Ranges-Schema** (`lift-ranges-0.13.rng`, ebenfalls aus lift-standard bereitgestellt) für jeden nachverfolgten `.lift-ranges`-Companion, wobei die Adressierung an den Companion statt an `.lift` erfolgt.
3. **Semantische Prüfungen**, die die Schemata nicht ausdrücken können: dreizehn an der Zahl, jeweils ein Code.

## Fehlercodes

Jeder Befund enthält einen dieser Einträge, je nachdem, in welcher Ebene er entstanden ist: `schema` und `uri-not-rfc` stammen aus den Schema-Ebenen, die übrigen sind semantische Prüfungen. Standardmäßig wird jeder Code überprüft, mit Ausnahme von `missing-id`, das optional aktiviert werden kann: Übergeben Sie `require_ids=True` (oder `--require-ids`), um diese Option zu aktivieren. Die Codes sind stabil, sodass Skripte darauf abgleichen können. `--strict` stuft jede Warnung als Fehler ein. Mit dem Befehl `sil-lift validate --allow CODE` wird ein Code bei der Entscheidung über „bestanden“ oder „nicht bestanden“ nicht berücksichtigt.

| Code                                     | Ebene   | Was es markiert                                                                                                                   |
| ---------------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `ambiguous-ranges-file`                  | Warnung | mehrere Dateien, die unter „Case Folding“ und „NFC“ denselben Begleitnamen haben                                                  |
| `dangling-ranges-href`                   | Warnung | Ein Header `range/@href`, der auf keine zugehörige Datei verweist                                                                 |
| `dangling-ref`                           | Fehler  | ein `relation/@ref` oder `variant/@ref`, für das kein Eintrag oder keine Bedeutung gefunden wurde                                 |
| `duplicate-form-lang`                    | Warnung | Zwei Formen in einem Multitext, die dieselbe Sprache verwenden                                                                    |
| `duplicate-guid`                         | Fehler  | ein GUID, der innerhalb mehrerer Einträge oder innerhalb der Bereiche/Bereichselemente eines Dokuments wiederverwendet wird       |
| `form-missing-lang`                      | Fehler  | ein `<form>` oder `<gloss>` ohne das vom Schema geforderte `lang`                                                                 |
| `media-href-mismatch`                    | Warnung | Ein Medien-href, der nur bei „Case Folding“ oder NFC auf die entsprechende Datei verweist                                         |
| `fehlende-ID`                            | Fehler  | **[opt-in]** Ein Eintrag ohne GUID, ein Sense ohne ID                         |
| `fehlende Medien`                        | Warnung | Eine referenzierte Audio- oder Bilddatei, die sich nicht auf der Festplatte befindet                                              |
| `Normalisierungsabweichung`              | Warnung | ein Name, der nur über NFC auf die ID zugreift, auf die er sich bezieht                                                           |
| `range-parent`                           | Fehler  | Ein `range-element/@parent` ohne definierte ID für ein Geschwisterelement                                                         |
| `Schema`                                 | Fehler  | ein Verstoß gegen die RELAX NG-Grammatik, entweder in der `.lift`-Datei oder in einem Companion                                   |
| `Wert außerhalb des zulässigen Bereichs` | Warnung | ein grammatikalischer oder bereichsbezogener Merkmalswert, der in dem Bereich nicht aufgeführt ist                                |
| `unreadable-ranges-file`                 | Warnung | ein zugehöriger Kandidat, der zwar existiert, aber kein lesbares Bereichsdokument ist                                             |
| `uri-not-rfc`                            | Warnung | Ein `href`-Attribut, das keine gültige URI ist (z. B. `file://C:/...` in FLEx) |

### Was die Validierung erkennt

Alle drei Ebenen arbeiten mit dem Dokument in seiner serialisierten Form, sodass ein Dokument, das überhaupt nicht serialisiert werden kann, stattdessen als einzelner `lone-surrogate`-Fehler gemeldet wird. Siehe [Garantien zur Richtigkeit](../fidelity.md#content-xml-cannot-represent).

Die Validierung ist schreibgeschützt: Sie gibt den aktuellen Stand des Dokuments wieder, bevor durch das Speichern das Feld „dateModified“ aktualisiert wird. Die Stempel führen niemals zu einem Fehler, sodass ein Dokument, das die Validierung besteht, auch nach dem Speichern weiterhin gültig bleibt.

### Codes für Begleitordner

Ein Begleitname, der mehreren Dateien entspricht, lädt keine davon: Die von ihnen definierten Bereiche sind nicht vorhanden, bis alle bis auf eine umbenannt oder entfernt wurden.

Die drei Codes für zugehörige Ordner (`ambiguous-ranges-file`, `dangling-ranges-href` und `unreadable-ranges-file`) werden nur gemeldet, wenn die Erkennung zugehöriger Ordner durchgeführt wurde:

- Beim Laden mit `resolve_ranges=False` werden Begleitobjekte aus dem Geltungsbereich entfernt, sodass keines davon gemeldet wird.
- Wenn man sie nachträglich mit `add_ranges_file()` hinzufügt, werden sie nicht wiederhergestellt, da diese Funktion den Ordner, auf den sich diese Codes beziehen, nie ausliest.

`resolve_ranges=False` hat keine Auswirkungen auf `missing-media` oder `media-href-mismatch`: Medien werden niemals in das Modell aufgelöst, daher gibt es nichts, was man deaktivieren könnte.

### Mediencodes

sil-lift sucht jede Mediendatei sowohl unter dem angegebenen href als auch unter `audio/` (Aussprache-Medien) oder `pictures/` (Illustrationen). Dieser Ordner ist eine eigene Vermutung von sil-lift und geht nicht aus dem Dokument hervor, daher passt er sich der jeweiligen Großschreibung an und seine Schreibweise wird nie angegeben.

`missing-media` und `media-href-mismatch` teilen sich die Medienprüfung untereinander auf: Ersteres bedeutet, dass unter keiner Schreibweise eine Datei auf den href-Bezug reagiert hat, Letzteres, dass zwar eine Datei reagiert hat, der href-Bezug diese jedoch nicht genau benennt. Der zweite Punkt betrifft die Portabilität: Die Datei befindet sich hier, und ein Host, der bei der Angabe des Ordners zwischen Groß- und Kleinschreibung unterscheidet, wird sie nicht finden.

Ein falsch geschriebener _Ordner_ wird nur einmal umbenannt, unabhängig davon, wie viele Verweise darauf bestehen; daher wird er nur einmal gemeldet und enthält keinen Eintrag. Pro Referenz wird ein falsch geschriebener _Dateiname_ gemeldet, der an den Eintrag gerichtet ist, der ihn geschrieben hat.

## Praktische FieldWorks (FLEx)-Ergebnisse

FieldWorks schreibt systematisch bestimmte Inhalte, die von strengen Validierungstools abgelehnt werden. Hier sind die Richtlinien von sil-lift, damit echte Lexika sinnvoll validiert werden können:

- `file://C:/...`-href-Attribute (ungültige URIs) werden als **Warnungen** (`uri-not-rfc`) gemeldet, nicht als Schemafehler; der C#-Validator hat sie nie abgelehnt.
- Rechtmäßig verschachtelte Kinder (z. B. in gewisser Weise `field, note, field, note`) werden **nicht** markiert; dadurch wird ein Fehlalarm in libxml2 umgangen.
- Die `trait`/`field`-Erweiterungen von FLEx innerhalb von `range-element` **werden** gemeldet (Schemafehler in Bezug auf das Ranges-Schema): Es handelt sich dabei um echte Abweichungen von der Spezifikation.
- Namen werden anhand von Bereichen und den `id`s der Bereichselemente unter der Unicode-**NFC-Normalisierung** aufgelöst: `parent`-Links, Bereichswerte sowie der `trait`-Name oder die Header-`range`-ID, die einen Bereich identifiziert.
  - FLEx wird beim Export auf NFC normalisiert, doch einige Schreibvorgänge umgingen diesen Schritt früher, sodass die `id` eines Bereichselements NFD sein kann, während seine Bezeichnungen, sein eigenes `parent` und die `.lift`-Werte, die es benennen, NFC sind.
  - Ein genauer Vergleich würde in zweierlei Hinsicht zu einem falschen Ergebnis führen. Verweise auf eine NFD-ID würden als fehlerhaft gemeldet, obwohl der Export einwandfrei ist. Und ein Bereich, dessen eigene `id` NFD ist, würde unberücksichtigt bleiben: Kein Trait-Name würde damit übereinstimmen, und ein Trait, dessen Name mit keinem Bereich übereinstimmt, wird unverändert akzeptiert.
  - Ein Name, der erst nach der Normalisierung übereinstimmte, wird als **Warnung** vom Typ „`normalization-mismatch`“ gemeldet – einmal pro ID statt einmal pro Referenz –, gerichtet an die Datei, in der er definiert ist. Die Daten sind korrekt, aber ein Verbraucher, der die Rohzeichenfolgen vergleicht, wird diese Verweise nicht auflösen können.
  - Die IDs werden niemals überschrieben: Die Datei behält die ursprüngliche Schreibweise bei.
