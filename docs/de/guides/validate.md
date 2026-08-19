# Überprüfen

Die Validierung erfolgt immer explizit – beim Laden und Speichern findet niemals eine implizite Validierung statt.

```python
import sil_lift

# Vollständig: ein „lazy“ Stream von Problemen (Schema + semantische Ebenen).
for problem in sil_lift.iter_problems("dictionary.lift"):
    print(problem)
    # Fehler [dangling-ref] dictionary.lift:88 (Eintrag apu): ref 'nope' passt zu ...

# Fail-fast: Löst bei dem ersten Problem auf Fehler-Ebene einen LiftValidationError aus.
sil_lift.validate_file("dictionary.lift")

# In-Memory-Zustand (wird zunächst serialisiert – ein dokumentierter Mehraufwand bei großen Lexika):
lex = sil_lift.load("dictionary.lift")
problems = list(lex.iter_problems())
```

Jedes `Problem` enthält einen `Level` (`„error“`/`„warning“`), einen stabilen `Code`, eine `Meldung` sowie, sofern vorhanden, die Adresse des Befunds: `file` (`None`, wenn das Lexikon keinen Pfad hat), `entry_id`, wenn es sich um einen Eintrag handelt, `guid`, wenn das betreffende Objekt über eine solche verfügt (ein Eintrag oder ein Bereichselement), und `line`, wenn es einer Zeile im Dokument zugeordnet ist. Eine Feststellung bezüglich eines Bereichs richtet sich an den Companion `.lift-ranges`, der diesen definiert, und enthält keinen Eintrag. Nicht festgelegte Felder sind `None` – `null` bei `--format json`, wo jeder Schlüssel immer vorhanden ist.

## Die Schichten

1. **RELAX NG** gemäß der LIFT 0.13-Grammatik (aus „lift-standard“ übernommen – eine byteweise identische Kopie, die in dieses Paket integriert wurde).
2. **Ranges-Schema** – in diesem Projekt `lift-ranges-0.13.rng` – für jeden erfassten `.lift-ranges`-Companion, wobei die Adressierung an den Companion statt an `.lift` erfolgt.
3. **Semantische Prüfungen**, die die Grammatik nicht ausdrücken kann – neun an der Zahl, jeweils ein Code.

## Fehlercodes

Jeder Befund enthält einen dieser Einträge, unabhängig davon, in welcher Ebene er entstanden ist – `schema` und `uri-not-rfc` stammen aus den Schema-Ebenen, die anderen neun sind semantische Prüfungen. Die Zeichenketten sind eine unterstützte Schnittstelle; mit `--strict` wird jede Warnung zu einem Fehler.

| Code                                     | Ebene   | Was es markiert                                                                                                             |
| ---------------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------- |
| `dangling-ranges-href`                   | Warnung | Ein Header `range/@href`, der auf keine zugehörige Datei verweist                                                           |
| `dangling-ref`                           | Fehler  | ein `relation/@ref` oder `variant/@ref`, für das kein Eintrag oder keine Bedeutung gefunden wurde                           |
| `duplicate-form-lang`                    | Warnung | Zwei Formen in einem Multitext, die dieselbe Sprache verwenden                                                              |
| `duplicate-guid`                         | Fehler  | ein GUID, der innerhalb mehrerer Einträge oder innerhalb der Bereiche/Bereichselemente eines Dokuments wiederverwendet wird |
| `fehlende-ID`                            | Fehler  | Opt-in über `require_ids`: Ein Eintrag ohne GUID, ein Eintrag ohne ID                                       |
| `fehlende Medien`                        | Warnung | Eine referenzierte Audio- oder Bilddatei, die sich nicht auf der Festplatte befindet                                        |
| `Normalisierungsabweichung`              | Warnung | ein Name, der nur über NFC auf die ID zugreift, auf die er sich bezieht                                                     |
| `range-parent`                           | Fehler  | Ein `range-element/@parent` ohne definierte ID für ein Geschwisterelement                                                   |
| `Schema`                                 | Fehler  | ein Verstoß gegen die RELAX NG-Grammatik, entweder in der `.lift`-Datei oder in einem Companion                             |
| `Wert außerhalb des zulässigen Bereichs` | Warnung | ein grammatikalischer oder bereichsbezogener Merkmalswert, der in dem Bereich nicht aufgeführt ist                          |
| `uri-not-rfc`                            | Warnung | Ein href, der keine gültige URI ist – FLExs `file://C:/...`                                                                 |

## Praktische FieldWorks (FLEx)-Ergebnisse

FieldWorks schreibt systematisch bestimmte Inhalte, die von strengen Validierungstools abgelehnt werden. Hier sind die Richtlinien von sil-lift, damit echte Lexika sinnvoll validiert werden können:

- `file://C:/...`-href-Attribute (ungültige URIs) werden als **Warnungen** (`uri-not-rfc`) gemeldet, nicht als Schemafehler – der C#-Validator hat sie nie abgelehnt.
- Rechtmäßig verschachtelte Kinder (z. B. in gewisser Weise `field, note, field, note`) werden **nicht** markiert, wodurch ein Fehlalarm in libxml2 umgangen wird.
- Die `trait`/`field`-Erweiterungen von FLEx innerhalb von `range-element` **werden** gemeldet (Schemafehler in Bezug auf das Ranges-Schema): Es handelt sich dabei um echte Abweichungen von der Spezifikation.
- Namen werden anhand von Bereichs- und Bereichselement-`id`s unter der Unicode-**NFC-Normalisierung** aufgelöst – `parent`-Links, Bereichswerte und der `trait`-Name oder die Header-`range`-ID, die einen Bereich identifiziert. FLEx wird beim Export auf NFC normalisiert, doch einige Schreibvorgänge umgingen diesen Schritt früher, sodass die `id` eines Bereichselements NFD sein kann, während seine Bezeichnungen, sein eigenes `parent` und die `.lift`-Werte, die es benennen, NFC sind.
  - Bei genauer Betrachtung erscheint ein korrekter Export fehlerhaft – und ein Bereich, dessen `id` anders geschrieben ist, wird überhaupt nicht überprüft, da ein Trait-Name, der keinen Bereich erreicht, stillschweigend akzeptiert wird.
  - Ein Name, der erst nach der Normalisierung übereinstimmt, wird als **Warnung** vom Typ „`normalization-mismatch`“ gemeldet – einmal pro ID, unabhängig davon, wie viele Verweise abweichen –, und zwar in der Datei, in der er definiert ist. Die Daten sind korrekt, aber ein Verbraucher, der die Rohzeichenfolgen vergleicht, wird diese Verweise nicht auflösen können.
  - Die IDs werden niemals überschrieben: Die Datei behält die ursprüngliche Schreibweise bei.
