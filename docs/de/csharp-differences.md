# Unterschiede zu den C#-Bibliotheken

sil-lift lässt sich in groben Zügen mit den C#-LIFT-Tools von SIL vergleichen und besteht im Wesentlichen aus zwei Teilen von [libpalaso](https://github.com/sillsdev/libpalaso):

- `SIL.Lift`: Parser, Validator, Migrator, `LiftSorter`.
- `SIL.DictionaryServices`: das `LexEntry`/`LexSense`-Modell mit eigenem LIFT-Lese-/Schreibmodul, das von „The Combine“ und „WeSay“ verwendet wird.

sil-lift ist eine neue Implementierung, keine Portierung. Auf dieser Seite wird zusammengefasst, in welchen Punkten sich das Verhalten bewusst unterscheidet.

## Geltungsbereich

| Fähigkeit         | C#-Bibliotheken                                     | sil-lift                                                                                            |
| ----------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| LIFT-Versionen    | 0,10–0,13 (Migration integriert) | **nur 0.13**; ältere Versionen werden mit einer eindeutigen Fehlermeldung abgelehnt |
| Versionsmigration | `Migrator` (XSLT-Kette)          | keine; verwenden Sie die XSLT-Dateien aus „lift-standard“ für einmalige Upgrades                    |
| Validierung       | Nur RELAX NG (`Validator`)       | RELAX NG + Schema- und Semantikprüfungen                                                            |
| Streaming         | interne Analyse auf Eintragsebene                   | Öffentliche `open_reader`-/`open_writer`-API                                                        |

## API-Form

Der Parser von `SIL.Lift` ist callback-gesteuert (`ILexiconMerger`): Er übergibt Parsing-Ereignisse an einen Verbraucher. sil-lift gibt stattdessen einen einfachen Objektgraphen zurück (typisierte Dataklassen für jedes LIFT-Element), da Python-Skriptentwickler Objekte und keine Callbacks wünschen.

`SIL.DictionaryServices` legt zwar ein `LexEntry`/`LexSense`-Objektmodell über `SIL.Lift`, doch handelt es sich dabei um ein Anwendungsmodell: Es repräsentiert lediglich die Konstrukte, die diese Anwendungen verwenden. Eine erneute Serialisierung über diese Funktion kann daher Inhalte, die außerhalb des Modells liegen, nicht in derselben Weise beibehalten wie die Behandlung von LIFT-Resten und die Byte-Fidelity von sil-lift (siehe unten).

Die Streaming-API liefert denselben `Entry`-Typ, sodass kein zweites, vereinfachtes Modell erlernt werden muss.

## Round-Trip-Genauigkeit

Der deutlichste bewusste Unterschied. Beim Speichern mit `SIL.Lift` wird das gesamte Dokument erneut serialisiert. sil-lift garantiert:

- Ein unverändertes Dokument wird **byte-identisch** gespeichert, und
- Unveränderte Einträge behalten ihre exakten Quellbytes bei, auch wenn sich andere Einträge ändern: automatische Byte-Aufteilung pro Eintrag.

Siehe [Garantien zur Richtigkeit](fidelity.md).

## Validierung

Der C#-`Validator` führt einen RELAX-NG-Durchlauf durch und gibt die ersten Fehler als Zeichenfolgen zurück. sil-lift liefert einen strukturierten `Problem`-Stream, wobei jeder Eintrag die betreffende Datei, den Eintrag und die Zeile enthält. Die Schemaebene weicht an drei Stellen bewusst ab:

- **Ungültige URIs sind Warnungen, keine Fehler.** Die C#-RELAX-NG-Engine hat den Datentyp `anyURI` nie erzwungen, weshalb FieldWorks (FLEx) seit Jahren `file://C:/...`-href-Links in echte Lexika schreibt. Würden diese Dateien abgelehnt, würde dies praktisch jeden FLEx-Export als fehlerhaft kennzeichnen.
- **Schematron-Regeln werden durchgesetzt** (als semantische Prüfungen): Doppelte Formularsprachen und ähnliche Ko-Einschränkungen in der LIFT-Grammatik wurden bei der C#-Validierung stillschweigend ignoriert.
- **Die Vergleiche der Bereichs-IDs erfolgen in Unicode-normalisierter Form** (NFC), da FLEx-Exporte sowohl NFC- als auch NFD-IDs enthalten. Verweise, die erst nach der Normalisierung aufgelöst werden, werden als Warnungen vom Typ „`normalization-mismatch`“ gemeldet – eine Prüfung, für die es in C# keine Entsprechung gibt. Siehe [Ausgabe von „Real-world FieldWorks (FLEx)“](guides/validate.md#real-world-fieldworks-flex-output).

Wenn sil-lift eine `.lift`-Datei validiert, überprüft es gleichzeitig die zugehörigen `.lift-ranges`-Dateien anhand eines Schemas für eigenständige Bereichsdokumente, das aus `lift-standard` bezogen wird. Der C#-`Validator` überprüft keine `.lift-ranges`-Dateien.

## Kanonische Sortierung

`Lexicon.sort()` spiegelt die Kernregeln von `LiftSorter` wider (Einträge nach GUID ohne Berücksichtigung der Groß-/Kleinschreibung; Bereiche und Bereichselemente nach ID; Definitionen von Header-Feldern nach Tag; Bedeutungen werden in der Reihenfolge der Datei beibehalten; Leerzeichen innerhalb von `<text>` werden nie verändert), mit drei Unterschieden:

- Einträge ohne GUID werden deterministisch nach ID sortiert (`LiftSorter` geht davon aus, dass eine GUID vorhanden ist);
- Die Sortierreihenfolge ist lokalisierungsunabhängig (reine, groß-/kleinschreibungsunabhängige Codepunkte, nicht die .NET-Sortierreihenfolge für kulturunabhängige Sortierung);
- Listen desselben Typs, wie Notizen, Beziehungen und Formulare, behalten ihre Reihenfolge im Dokument bei, anstatt nach dem Schlüssel neu sortiert zu werden; die Gruppierung ist bereits deterministisch, und eine Neuanordnung würde nur unnötigen Diff-Lärm verursachen.

Die Datei `canonicalizeLift.xsl` aus dem Spec-Repo wird überhaupt nicht verwendet: Sie komprimiert Leerzeichen innerhalb des lexikalischen Texts (destruktiv) und die von ihr generierten IDs unterscheiden sich bei jedem Durchlauf.

## Nicht übernommen

- WeSay-spezifische Funktionen (Dashboard/Konfiguration im Zusammenhang mit LIFT-Dateien).
- `SynchronicMerger` (LIFT-Zusammenführung von Update-Dateien): Das Konzept der Byte-Chunks wird in der Fidelity-Schicht weitergeführt, die Zusammenführung hingegen nicht.
- LDML-Schriftsystem-Analyse: Dateien im Verzeichnis `WritingSystems/` werden als undurchsichtiger Ordnerinhalt behandelt.
