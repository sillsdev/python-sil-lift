# Fidelity-Garantien

LIFT ist ein _Austauschformat_, daher lautet die erste Regel: **Lass niemals etwas weg, was du nicht verstehst**. Der Vertrag von `sil-lift`, der bei jedem Durchlauf durch die Testsuite überprüft wird (Korpusdateien sowie eigenschaftsbasierte Generierung):

## Lesen

Jedes wohlgeformte LIFT 0.13-Dokument wird geladen – auch Inhalte, die nicht dem Schema entsprechen. Alles, was das Modell nicht definiert, wird im opaken `Extras`-Container des nächstgelegenen Knotens als _LIFT-Residuum_ gespeichert – so nennt FieldWorks dieses Konzept, das in einem `LiftResidue`-Feld abgelegt wird: unbekannte Attribute und Elemente, XML-Kommentare und Verarbeitungsanweisungen, verstreuter Text sowie fehlerhaft formatierte typisierte Attribute (ein fehlerhaftes Datum verbleibt als ursprüngliche Zeichenkette in `Extras`; das typisierte Feld ist `None`).

## Ein unverändertes Dokument speichern

`load()` → `save()` ohne Änderungen erzeugt eine **byte-identische Ausgabe** – keine Neuformatierung, kein erneutes Escaping, keine Neuanordnung, einschließlich Byte-Order-Markierungen und XML-Deklarationen. Derzeit gibt es keine Normalisierungsliste: Die Identität ist exakt. Zeitstempel werden aus dem Inhalt generiert, daher werden für ein unverändertes Dokument auch keine Zeitstempel generiert.

Ausnahmen (der Writer greift auf die vollständige kanonische Serialisierung zurück, die zwar semantisch vollständig, jedoch nicht bytekonsistent ist):

- die Quellkodierung ist nicht ASCII-kompatibel (nicht UTF-8/US-ASCII) oder
- der Quelltext enthält einen DOCTYPE oder
- Der Byte-Scanner und der Parser sind sich hinsichtlich der obersten Struktur des Dokuments nicht einig – beispielsweise bei einem nicht spezifikationskonformen zweiten `<header>`, den der Parser nur einmal beibehält (der Scanner ist bewusst konservativ: Im Zweifelsfall erfasst er überhaupt keine Quell-Bytes), oder
- Der Quellcode wurde im Speicher erstellt und nicht aus einer Datei geladen.

## Ein bearbeitetes Dokument speichern

- **Unveränderte Einträge werden wortwörtlich aus ihren ursprünglichen Bytes ausgegeben.** Ein Eintrag gilt als verändert, wenn sich seit dem Parsen ein beliebiger Teil seines Modellobjekts geändert hat (erkannt anhand eines Snapshots der kanonischen Serialisierung, nicht anhand eines „Dirty“-Flags).
- **Die betroffenen Einträge werden kanonisch und vollständig neu serialisiert.** Die kanonische Form lautet:
  - UTF-8.
  - Einrückung mit 2 Leerzeichen _außerhalb_ von gemischtem Inhalt; Leerzeichen innerhalb von `<text>` und `<span>` werden niemals verändert.
  - Eine dokumentierte Gruppierung von Unterelementen pro Element; für `<entry>`: lexikalische Einheit, Zitat, Aussprachen, Varianten, Bedeutungen, Anmerkungen, Beziehungen, Etymologien, Anmerkungen, Merkmale, Felder.
  - Die Reihenfolge der Attribute wurde festgelegt.
  - Datumsangaben nach ISO-8601 (`Z` für UTC).
- **Alle Reste werden erneut ausgegeben.** Ihre Position wird auf den ursprünglichen Unterindex zurückgesetzt und an die neue Unterliste angepasst – dies ist eine Annäherung, da exakte Byte-Positionen nur für unveränderte Einträge garantiert sind.
- Das Hinzufügen, Entfernen oder Neuanordnen von Einträgen führt zu einer erneuten Serialisierung der Dokumentstruktur, wobei die Bytes jedes unveränderten Eintrags jedoch unverändert ausgegeben werden.
- **Ein bearbeiteter Eintrag wird** mit einem neuen `dateModified`-Wert versehen und, falls noch kein `dateCreated` vorhanden war, mit einem solchen – siehe [Generierte Zeitstempel](#generated-timestamps).

!!! note "&quot;Die Canonical-&quot; -Datei hier steht in keinem Zusammenhang mit anderen Canonical-XML-Dateien."
    Unter „kanonischer Form“ wird auf dieser Seite die in einem der obigen Aufzählungspunkte beschriebene, von `sil-lift` selbst dokumentierte Form verstanden. Dies steht in keinem Zusammenhang mit dem „Canonical XML (C14N)“-Prozess des W3C. Es steht in keinem Zusammenhang mit der Klasse `CanonicalXmlSettings` von `SIL.Core`.

## Generierte Zeitstempel

Ein generierter Stempel ist das einzige Element in der Ausgabe, das nicht von der Eingabe abhängt.

- **Was wird markiert?** Jeder Eintrag, dessen Inhalt sich seit dem letzten Lesen geändert hat, mit einem neuen `dateModified` und – falls noch kein `dateModified` vorhanden war – einem `dateCreated` zum selben Zeitpunkt. Eine Bearbeitung, die vor dem Ladedatum vorgenommen wurde, erscheint für alle Anwendungen, die dieses Attribut abgleichen – einschließlich FieldWorks und des LIFT-Imports von The Combine –, als unverändert.
- **Nur Einträge.** Keine Knoten unterhalb von `<entry>` und nichts im Header.
- **Was unverändert bleibt.** Ein Eintrag, dessen Datum der Aufrufer bewusst festgelegt hat, sowie ein Eintrag, der seit dem Laden erstellt wurde und bereits ein Datum enthält.
- **Das Löschen eines Datums wird berücksichtigt.** `entry.date_modified = None` bei einem Eintrag, der mit diesem Wert gelesen wird, ist ein beabsichtigter Wert wie jeder andere auch, sodass der Eintrag ohne `dateModified` ausgegeben wird, unabhängig davon, ob sein Inhalt verschoben wurde oder nicht. Ein Eintrag, der ohne einen solchen Wert gelesen wird, ist ein anderer Fall: `None` ist dort bereits der vorhandene Wert, der nicht davon zu unterscheiden ist, dass das Feld nie berührt wurde, sodass eine Bearbeitung dennoch einen Stempel hinterlässt.
- **Ein nicht auswertbares Datum wird ersetzt.** Ein Datum, das das Modell nicht auswerten konnte, ist [Restwert](#reading) und kein echtes Datum; daher wird es durch einen Zeitstempel überschrieben und die ursprüngliche Zeichenfolge verworfen – ein bearbeiteter Eintrag sollte lieber ein echtes Datum enthalten als `dateModified="whenever"`.
- **Der Zeitpunkt.** UTC auf die Sekunde genau (`YYYY-MM-DDTHH:MM:SSZ`, das Format, das jeder erfasste FieldWorks-Export verwendet), abgelesen von der Wanduhr. Eine Sekunde umfasst ein Datum, daher erhält eine Änderung, die innerhalb einer Sekunde nach der vorherigen gespeichert wird, denselben Zeitstempel.
- **`save(when=...)`** gibt den Zeitpunkt anstelle der Wanduhr an, wodurch die mit einem Zeitstempel versehene Ausgabe für ein diff-basiertes CI-Gate reproduzierbar bleibt. Es muss zeitzonenabhängig sein und wird auf ganze Sekunden in UTC normiert.
- **`save(stamp=False)`** speichert das Modell genau so, wie es ist, einschließlich des Residus.
- **Commits werden mit dem Befehl `.lift` festgeschrieben.** Alles, was verhindert, dass dieser Schreibvorgang durchgeführt wird, versetzt die Datumsangaben zurück. Sobald es landet, bleiben sie stehen, auch wenn ein nachfolgender Schreibvorgang fehlschlägt.

## XML-Inhalte können Folgendes nicht darstellen

Nicht-BMP-Zeichen – Emojis, CJK Extension B, Adlam und alles oberhalb von U+FFFF – sind gewöhnliche Inhalte und werden bei der Hin- und Rücksendung byteweise identisch übertragen. Ein „Surrogate-Paar“ ist ein Detail der UTF-16-Kodierung: Python-Zeichenketten bestehen aus einer Folge von Codepunkten, sodass weder der Leser noch der Byte-Scanner noch der Schreiber jemals eines davon zu Gesicht bekommt.

Ein _einzelner_ Platzhalter (U+D800–U+DFFF) ist etwas anderes: Ein Python-String kann einen enthalten, ein XML-Dokument hingegen nicht, unabhängig von der Kodierung. Es kann niemals aus einer Datei stammen – der Parser lehnt beide Schreibweisen ab, sowohl eine Zeichenreferenz `&#xD800;` als auch CESU-8/WTF-8-Bytes –, sondern nur aus einer über die API zugewiesenen Zeichenkette. Das Speichern eines solchen Modells löst einen `LiftWriteError` aus, der den Knoten und den Codepunkt nennt, und es wird nichts geschrieben; die Validierung meldet dies als einen einzelnen `lone-surrogate`-Fehler, da das Dokument nicht serialisiert werden kann, damit die Schemaebenen es überprüfen können.

## Bekannte Näherungswerte (nur berührte Knoten)

- Kommentare _innerhalb_ eines `<text>`-Laufs bleiben erhalten, werden jedoch neben den Lauf verschoben und nicht an ihrer genauen Zeichenposition beibehalten.
- Die kreuzförmige Reihenfolge der untergeordneten Elemente innerhalb eines bearbeiteten Elements wird auf die kanonische Gruppierung normiert (durch das `interleave`-Schema des LIFT-Schemas wird diese Reihenfolge semantisch irrelevant).
- Ein `<form>` oder `<gloss>` ohne `lang` wird nicht erneut ausgegeben, ebenso wenig wie dessen Inhalt; die Validierung meldet das Fehlen als `form-missing-lang`. Ein unveränderter Knoten behält seine Quellbytes bei, sodass eine solche Form so lange erhalten bleibt, bis etwas in seinem Eintrag bearbeitet wird.
- Ein Multitext-Element, das zwar vorhanden ist, aber nichts enthält – weder Formen noch Reste, z. B. `<definition></definition>` – wird nicht erneut ausgegeben. Das Modell stellt diese Felder als stets vorhandenes `Multitext` dar (`lexical-unit`, `citation`, `definition`, die `usage` einer Relation sowie `label` / `abbrev` / `description` bei URL-Verweisen, Bereichen, Bereichselementen und der Kopfzeile) dar, sodass sich ein leeres Feld nach der Analyse nicht von einem fehlenden unterscheiden lässt. Es geht keine semantische Information verloren.
