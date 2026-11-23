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

Der Parser von `SIL.Lift` ist callback-gesteuert (`ILexiconMerger`): Er übergibt Parsing-Ereignisse an einen Verbraucher. sil-lift instead returns a plain object graph (typed dataclasses for every LIFT element) because Python scripters want objects, not callbacks.

`SIL.DictionaryServices` does layer a `LexEntry`/`LexSense` object model over `SIL.Lift`, but it is an application model: it represents only the constructs those apps use. Re-serializing through it therefore can't preserve out-of-model content the way sil-lift's LIFT residue handling and byte fidelity do (see below).

Die Streaming-API liefert denselben `Entry`-Typ, sodass kein zweites, vereinfachtes Modell erlernt werden muss.

## Round-Trip-Genauigkeit

Der deutlichste bewusste Unterschied. Beim Speichern mit `SIL.Lift` wird das gesamte Dokument erneut serialisiert. sil-lift garantiert:

- Ein unverändertes Dokument wird **byte-identisch** gespeichert, und
- untouched entries keep their exact source bytes even when other entries change: per-entry byte chunking, applied automatically.

Siehe [Garantien zur Richtigkeit](fidelity.md).

## Validierung

Der C#-`Validator` führt einen RELAX-NG-Durchlauf durch und gibt die ersten Fehler als Zeichenfolgen zurück. sil-lift reports a structured `Problem` stream, each carrying the file, entry, and line it concerns. Its schema layer knowingly diverges in three places:

- **Ungültige URIs sind Warnungen, keine Fehler.** Die C#-RELAX-NG-Engine hat den Datentyp `anyURI` nie erzwungen, weshalb FieldWorks (FLEx) seit Jahren `file://C:/...`-href-Links in echte Lexika schreibt. Würden diese Dateien abgelehnt, würde dies praktisch jeden FLEx-Export als fehlerhaft kennzeichnen.
- **Schematron rules are enforced** (as semantic checks): duplicate form languages and similar co-constraints in the LIFT grammar were silently ignored by C# validation.
- **Range id comparisons are Unicode-normalized** (NFC), because FLEx exports mix NFC and NFD ids. References that resolve only after normalizing are reported as `normalization-mismatch` warnings, a check with no C# counterpart. See [Real-world FieldWorks (FLEx) output](guides/validate.md#real-world-fieldworks-flex-output).

When sil-lift validates a `.lift`, it also validates the `.lift-ranges` companions against a schema for standalone ranges documents, vendored from `lift-standard`. The C# `Validator` does not check `.lift-ranges` files.

## Kanonische Sortierung

`Lexicon.sort()` spiegelt die Kernregeln von `LiftSorter` wider (Einträge nach GUID ohne Berücksichtigung der Groß-/Kleinschreibung; Bereiche und Bereichselemente nach ID; Definitionen von Header-Feldern nach Tag; Bedeutungen werden in der Reihenfolge der Datei beibehalten; Leerzeichen innerhalb von `<text>` werden nie verändert), mit drei Unterschieden:

- Einträge ohne GUID werden deterministisch nach ID sortiert (`LiftSorter` geht davon aus, dass eine GUID vorhanden ist);
- Die Sortierreihenfolge ist lokalisierungsunabhängig (reine, groß-/kleinschreibungsunabhängige Codepunkte, nicht die .NET-Sortierreihenfolge für kulturunabhängige Sortierung);
- same-type lists such as notes, relations, and forms keep their document order rather than being re-sorted by key; grouping is already deterministic, and reordering them only adds diff noise.

Die Datei `canonicalizeLift.xsl` aus dem Spec-Repo wird überhaupt nicht verwendet: Sie komprimiert Leerzeichen innerhalb des lexikalischen Texts (destruktiv) und die von ihr generierten IDs unterscheiden sich bei jedem Durchlauf.

## Nicht übernommen

- WeSay-spezifische Funktionen (Dashboard/Konfiguration im Zusammenhang mit LIFT-Dateien).
- `SynchronicMerger` (LIFT update-file merging): the byte-chunking idea lives on in the fidelity layer, the merging does not.
- LDML-Schriftsystem-Analyse: Dateien im Verzeichnis `WritingSystems/` werden als undurchsichtiger Ordnerinhalt behandelt.
