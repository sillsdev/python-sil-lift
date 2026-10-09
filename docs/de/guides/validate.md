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
3. **Semantische Prüfungen**, die die Grammatik nicht abbilden kann – dreizehn an der Zahl, jeweils ein Code.

## Fehlercodes

Jeder Befund enthält einen dieser Einträge, unabhängig davon, in welcher Ebene er entstanden ist – `schema` und `uri-not-rfc` stammen aus den Schema-Ebenen, die übrigen dreizehn sind semantische Prüfungen. Die Zeichenketten sind eine unterstützte Schnittstelle; mit `--strict` wird jede Warnung zu einem Fehler. Mit dem Befehl `sil-lift validate --allow CODE` wird ein Code bei der Entscheidung über „bestanden“ oder „nicht bestanden“ nicht berücksichtigt.

| Code                                     | Ebene   | Was es markiert                                                                                                             |
| ---------------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------- |
| `ambiguous-ranges-file`                  | Warnung | mehrere Dateien, die unter „Case Folding“ und „NFC“ denselben Begleitnamen haben                                            |
| `dangling-ranges-href`                   | Warnung | Ein Header `range/@href`, der auf keine zugehörige Datei verweist                                                           |
| `dangling-ref`                           | Fehler  | ein `relation/@ref` oder `variant/@ref`, für das kein Eintrag oder keine Bedeutung gefunden wurde                           |
| `duplicate-form-lang`                    | Warnung | Zwei Formen in einem Multitext, die dieselbe Sprache verwenden                                                              |
| `duplicate-guid`                         | Fehler  | ein GUID, der innerhalb mehrerer Einträge oder innerhalb der Bereiche/Bereichselemente eines Dokuments wiederverwendet wird |
| `form-missing-lang`                      | Fehler  | ein `<form>` oder `<gloss>` ohne das vom Schema geforderte `lang`                                                           |
| `media-href-mismatch`                    | Warnung | Ein Medien-href, der nur bei „Case Folding“ oder NFC auf die entsprechende Datei verweist                                   |
| `fehlende-ID`                            | Fehler  | Opt-in über `require_ids`: Ein Eintrag ohne GUID, ein Eintrag ohne ID                                       |
| `fehlende Medien`                        | Warnung | Eine referenzierte Audio- oder Bilddatei, die sich nicht auf der Festplatte befindet                                        |
| `Normalisierungsabweichung`              | Warnung | ein Name, der nur über NFC auf die ID zugreift, auf die er sich bezieht                                                     |
| `range-parent`                           | Fehler  | Ein `range-element/@parent` ohne definierte ID für ein Geschwisterelement                                                   |
| `Schema`                                 | Fehler  | ein Verstoß gegen die RELAX NG-Grammatik, entweder in der `.lift`-Datei oder in einem Companion                             |
| `Wert außerhalb des zulässigen Bereichs` | Warnung | ein grammatikalischer oder bereichsbezogener Merkmalswert, der in dem Bereich nicht aufgeführt ist                          |
| `unreadable-ranges-file`                 | Warnung | ein zugehöriger Kandidat, der zwar existiert, aber kein lesbares Bereichsdokument ist                                       |
| `uri-not-rfc`                            | Warnung | Ein href, der keine gültige URI ist – FLExs `file://C:/...`                                                                 |

Alle drei Ebenen arbeiten mit dem Dokument in seiner serialisierten Form, sodass ein Dokument, das überhaupt nicht serialisiert werden kann, stattdessen als einzelner `lone-surrogate`-Fehler gemeldet wird – siehe [Genauigkeitsgarantien](../fidelity.md#content-xml-cannot-represent). Die Validierung ist schreibgeschützt: Sie gibt den aktuellen Stand des Dokuments wieder, wie er vor dem `dateModified`-Zeitstempel einer Speicherung war. Nichts, was generiert wird, ist jemals ein Ergebnis, daher ist „zuerst validieren, dann speichern“ sinnvoll.

Ein Begleitname, der mehreren Dateien entspricht, lädt keine davon: Die von ihnen definierten Bereiche sind nicht vorhanden, bis alle bis auf eine umbenannt oder entfernt wurden.

Die drei Codes für zugehörige Ordner (`ambiguous-ranges-file`, `dangling-ranges-href` und `unreadable-ranges-file`) werden nur gemeldet, wenn die Erkennung zugehöriger Ordner durchgeführt wurde. Beim Laden mit `resolve_ranges=False` werden Begleitdateien aus dem Geltungsbereich ausgeschlossen, sodass keine davon gemeldet wird; das nachträgliche Hinzufügen einer solchen Datei mit `add_ranges_file()` bringt sie nicht zurück, da die Datei, auf die sich diese Codes beziehen, nie gelesen wird. `missing-media` und `media-href-mismatch` sind davon nicht betroffen: Medien werden niemals in das Modell aufgelöst, daher wurde nichts ausgeschlossen.

`missing-media` und `media-href-mismatch` teilen sich die Medienprüfung untereinander auf: Ersteres bedeutet, dass unter keiner Schreibweise eine Datei auf den href-Bezug reagiert hat, Letzteres, dass zwar eine Datei reagiert hat, der href-Bezug diese jedoch nicht genau benennt. Der zweite Punkt betrifft die Portabilität – die Datei befindet sich hier, und ein Host, der bei der Angabe des Ordners zwischen Groß- und Kleinschreibung unterscheidet, wird sie nicht finden.

Zwei Regeln legen fest, was `media-href-mismatch` meldet:

- Ein falsch geschriebener _Ordner_ wird nur einmal umbenannt, unabhängig davon, wie viele Verweise darauf bestehen; daher wird er nur einmal gemeldet und führt zu keinem Eintrag. Pro Referenz wird ein falsch geschriebener _Dateiname_ gemeldet, der dem Eintrag zugeordnet ist, der ihn geschrieben hat.
- Der übliche Unterordner „audio/“/„pictures/“ ist eher eine Vermutung von sil-lift als eine Angabe aus dem Dokument; daher wird ein Ordner mit einer anderen Schreibweise ohne Meldung aufgelöst.

## Praktische FieldWorks (FLEx)-Ergebnisse

FieldWorks schreibt systematisch bestimmte Inhalte, die von strengen Validierungstools abgelehnt werden. Hier sind die Richtlinien von sil-lift, damit echte Lexika sinnvoll validiert werden können:

- `file://C:/...`-href-Attribute (ungültige URIs) werden als **Warnungen** (`uri-not-rfc`) gemeldet, nicht als Schemafehler – der C#-Validator hat sie nie abgelehnt.
- Rechtmäßig verschachtelte Kinder (z. B. in gewisser Weise `field, note, field, note`) werden **nicht** markiert, wodurch ein Fehlalarm in libxml2 umgangen wird.
- Die `trait`/`field`-Erweiterungen von FLEx innerhalb von `range-element` **werden** gemeldet (Schemafehler in Bezug auf das Ranges-Schema): Es handelt sich dabei um echte Abweichungen von der Spezifikation.
- Namen werden anhand von Bereichs- und Bereichselement-`id`s unter der Unicode-**NFC-Normalisierung** aufgelöst – `parent`-Links, Bereichswerte und der `trait`-Name oder die Header-`range`-ID, die einen Bereich identifiziert. FLEx wird beim Export auf NFC normalisiert, doch einige Schreibvorgänge umgingen diesen Schritt früher, sodass die `id` eines Bereichselements NFD sein kann, während seine Bezeichnungen, sein eigenes `parent` und die `.lift`-Werte, die es benennen, NFC sind.
  - Bei genauer Betrachtung erscheint ein korrekter Export fehlerhaft – und ein Bereich, dessen `id` anders geschrieben ist, wird überhaupt nicht überprüft, da ein Trait-Name, der keinen Bereich erreicht, stillschweigend akzeptiert wird.
  - Ein Name, der erst nach der Normalisierung übereinstimmt, wird als **Warnung** vom Typ „`normalization-mismatch`“ gemeldet – einmal pro ID, unabhängig davon, wie viele Verweise abweichen –, und zwar in der Datei, in der er definiert ist. Die Daten sind korrekt, aber ein Verbraucher, der die Rohzeichenfolgen vergleicht, wird diese Verweise nicht auflösen können.
  - Die IDs werden niemals überschrieben: Die Datei behält die ursprüngliche Schreibweise bei.
