# Unterschiede zu den C#-Bibliotheken

sil-lift ist in etwa vergleichbar mit den C#-LIFT-Tools von SIL – vor allem mit `SIL.Lift` in [libpalaso](https://github.com/sillsdev/libpalaso) (Parser, Validator, Migrator, `LiftSorter`), `SIL.DictionaryServices` im selben Repository (das `LexEntry`/`LexSense`-Modell mit eigenem LIFT-Reader/Writer, das von The Combine und WeSay verwendet wird) sowie die LIFT-Handler in [Chorus](https://github.com/sillsdev/chorus). Es handelt sich um eine neue Implementierung, nicht um eine Portierung. Auf dieser Seite wird zusammengefasst, in welchen Punkten sich das Verhalten bewusst unterscheidet.

## Geltungsbereich

| Fähigkeit                                 | C#-Bibliotheken                                     | sil-lift                                                                                            |
| ----------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| LIFT-Versionen                            | 0,10–0,13 (Migration integriert) | **nur 0.13**; ältere Versionen werden mit einer eindeutigen Fehlermeldung abgelehnt |
| Versionsmigration                         | `Migrator` (XSLT-Kette)          | keine — Verwenden Sie die XSLT-Dateien aus „lift-standard“ für einmalige Upgrades                   |
| 3-Wege-Zusammenführung / Synchronisierung | Refrain                                             | fällt nicht in den Geltungsbereich                                                                  |
| Validierung                               | Nur RELAX NG (`Validator`)       | RELAX NG + Schema- und Semantikprüfungen                                                            |
| Streaming                                 | interne Analyse auf Eintragsebene                   | Öffentliche `open_reader`-/`open_writer`-API                                                        |

## API-Form

Der Parser von `SIL.Lift` ist callback-gesteuert (`ILexiconMerger`): Er übergibt Parsing-Ereignisse an einen Verbraucher. sil-lift gibt stattdessen einen einfachen Objektgraphen zurück – typisierte Dataklassen für jedes LIFT-Element –, da Python-Skriptentwickler Objekte und keine Callbacks wünschen. `SIL.DictionaryServices` legt zwar ein `LexEntry`/`LexSense`-Objektmodell über `SIL.Lift“, doch als Anwendungsmodell repräsentiert es lediglich die Konstrukte, die diese Anwendungen verwenden – daher können bei einer erneuten Serialisierung über dieses Modell Inhalte, die außerhalb des Modells liegen, nicht in derselben Weise erhalten bleiben wie bei der Residue-Erfassung und der Byte-Fidelity von sil-lift (siehe unten). Die Streaming-API liefert denselben `Entry\`-Typ, daher gibt es kein Modell mit eingeschränkten Funktionen.

## Round-Trip-Genauigkeit

Der deutlichste bewusste Unterschied. Beim Speichern mit `SIL.Lift` wird das gesamte Dokument erneut serialisiert. sil-lift garantiert:

- Ein unverändertes Dokument wird **byte-identisch** gespeichert, und
- Unveränderte Einträge behalten ihre exakten Quellbytes bei, auch wenn sich andere Einträge ändern (Byte-Chunking auf Chorus-Ebene, wird automatisch angewendet).

Siehe [Garantien zur Richtigkeit](fidelity.md).

## Validierung

Der C#-`Validator` führt einen RELAX-NG-Durchlauf durch und gibt die ersten Fehler als Zeichenfolgen zurück. sil-lift meldet einen strukturierten, nach Einträgen/Zeilen adressierten `Problem`-Stream, und seine Schemaebene weicht an drei Stellen bewusst davon ab:

- **Ungültige URIs sind Warnungen, keine Fehler.** Die C#-RELAX-NG-Engine hat den Datentyp `anyURI` nie erzwungen, weshalb FieldWorks (FLEx) seit Jahren `file://C:/...`-href-Links in echte Lexika schreibt. Würden diese Dateien abgelehnt, würde dies praktisch jeden FLEx-Export als fehlerhaft kennzeichnen.
- **Schematron-Regeln werden durchgesetzt** (als semantische Prüfungen): Doppelte Formularsprachen und ähnliche Ko-Einschränkungen in der LIFT-Grammatik wurden sowohl bei der C#-Validierung als auch bei der reinen lxml-Validierung stillschweigend ignoriert.
- **Dateiübergreifende Vergleiche sind Unicode-normalisiert**, da FLEx die `.lift`-Datei in NFC und die zugehörige `.lift-ranges`-Datei in NFD schreibt.

sil-lift validiert außerdem die `.lift-ranges`-Begleitdateien eines geladenen Lexikons anhand eines Schemas für eigenständige Bereichsdokumente (das zusammen mit der LIFT-Basisgrammatik aus `lift-standard` bereitgestellt wird) — jede nachverfolgte externe Bereichsdatei wird bei jeder Validierung der `.lift`-Datei überprüft — während es in der C#-Welt kein solches Schema (oder keine solche Überprüfung) gibt. (Es gibt keine Möglichkeit, eine `.lift-ranges`-Datei für sich allein, losgelöst von einer `.lift`-Datei, zu validieren.)

## Kanonische Sortierung

`Lexicon.sort()` spiegelt die Kernregeln von `LiftSorter` wider (Einträge nach GUID ohne Berücksichtigung der Groß-/Kleinschreibung; Bereiche und Bereichselemente nach ID; Definitionen von Header-Feldern nach Tag; Bedeutungen werden in der Reihenfolge der Datei beibehalten; Leerzeichen innerhalb von `<text>` werden nie verändert), mit drei Unterschieden:

- Einträge ohne GUID werden deterministisch nach ID sortiert (`LiftSorter` geht davon aus, dass eine GUID vorhanden ist);
- Die Sortierreihenfolge ist lokalisierungsunabhängig (reine, groß-/kleinschreibungsunabhängige Codepunkte, nicht die .NET-Sortierreihenfolge für kulturunabhängige Sortierung);
- Listen desselben Typs wie Notizen, Beziehungen und Formulare behalten ihre Reihenfolge im Dokument bei, anstatt nach dem Schlüssel neu sortiert zu werden – die Gruppierung ist bereits deterministisch, und eine Neuanordnung würde nur unnötiges Rauschen verursachen.

Die Datei `canonicalizeLift.xsl` aus dem Spec-Repo wird überhaupt nicht verwendet: Sie komprimiert Leerzeichen innerhalb des lexikalischen Texts (destruktiv) und die von ihr generierten IDs unterscheiden sich bei jedem Durchlauf.

## Nicht übernommen

- WeSay-spezifische Funktionen (Dashboard/Konfiguration im Zusammenhang mit LIFT-Dateien).
- `SynchronicMerger` (Zusammenführung von Chorus-Updates) – das Konzept der Byte-Chunks lebt in der Fidelity-Schicht weiter, die Zusammenführung hingegen nicht.
- LDML-Schriftsystem-Analyse: Dateien im Verzeichnis `WritingSystems/` werden als undurchsichtiger Ordnerinhalt behandelt.
