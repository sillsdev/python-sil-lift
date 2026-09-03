# Fidelity-Garantien

LIFT ist ein _Austauschformat_, daher lautet die erste Regel: **Lass niemals etwas weg, was du nicht verstehst**. Der Vertrag von `sil-lift`, der bei jedem Durchlauf durch die Testsuite überprüft wird (Korpusdateien sowie eigenschaftsbasierte Generierung):

## Lesen

Jedes wohlgeformte LIFT 0.13-Dokument wird geladen – auch Inhalte, die nicht dem Schema entsprechen. Alles, was das Modell nicht definiert, wird im opaken `Extras`-Container des nächstgelegenen Knotens als _LIFT-Residuum_ gespeichert – so nennt FieldWorks dieses Konzept, das in einem `LiftResidue`-Feld abgelegt wird: unbekannte Attribute und Elemente, XML-Kommentare und Verarbeitungsanweisungen, verstreuter Text sowie fehlerhaft formatierte typisierte Attribute (ein fehlerhaftes Datum verbleibt als ursprüngliche Zeichenkette in `Extras`; das typisierte Feld ist `None`).

## Ein unverändertes Dokument speichern

`load()` → `save()` ohne Änderungen erzeugt eine **byte-identische Ausgabe** – keine Neuformatierung, kein erneutes Escaping, keine Neuanordnung, einschließlich Byte-Order-Markierungen und XML-Deklarationen. Derzeit gibt es keine Normalisierungsliste: Die Identität ist exakt.

Ausnahmen (der Writer greift auf die vollständige kanonische Serialisierung zurück, die zwar semantisch vollständig, jedoch nicht bytekonsistent ist):

- die Quellkodierung ist nicht ASCII-kompatibel (nicht UTF-8/US-ASCII) oder
- der Quelltext enthält einen DOCTYPE oder
- Der Byte-Scanner und der Parser sind sich hinsichtlich der obersten Struktur des Dokuments nicht einig – beispielsweise bei einem nicht spezifikationskonformen zweiten `<header>`, den der Parser nur einmal beibehält (der Scanner ist bewusst konservativ: Im Zweifelsfall erfasst er überhaupt keine Quell-Bytes), oder
- Der Quellcode wurde im Speicher erstellt und nicht aus einer Datei geladen.

## Ein bearbeitetes Dokument speichern

- **Unveränderte Einträge werden wortwörtlich aus ihren ursprünglichen Bytes ausgegeben.** Ein Eintrag gilt als verändert, wenn sich seit dem Parsen ein beliebiger Teil seines Modellobjekts geändert hat (erkannt anhand eines Snapshots der kanonischen Serialisierung, nicht anhand eines „Dirty“-Flags).
- **Die bearbeiteten Einträge werden kanonisch und vollständig neu serialisiert**: UTF-8, Einrückung mit zwei Leerzeichen _außerhalb_ von gemischtem Inhalt (Leerzeichen innerhalb von `<text>` und `<span>` werden niemals verändert), eine dokumentierte Untergruppierung pro Element (z. B. Eintrag: lexikalische Einheit, Zitat, Aussprachen, Varianten, Bedeutungen, Anmerkungen, Beziehungen, Etymologien, Annotationen, Merkmale, Felder), feste Attributreihenfolge, Datumsangaben nach ISO-8601 (`Z` für UTC). Alle Reste werden erneut ausgegeben; ihre Position wird auf den ursprünglichen Unterindex zurückgesetzt und an die neue Unterliste angepasst (eine Annäherung – exakte Byte-Positionen sind nur für unveränderte Einträge garantiert).
- Das Hinzufügen, Entfernen oder Neuanordnen von Einträgen führt zu einer erneuten Serialisierung der Dokumentstruktur, wobei die Bytes jedes unveränderten Eintrags jedoch unverändert ausgegeben werden.

!!! note "&quot;Die Canonical-&quot; -Datei hier steht in keinem Zusammenhang mit anderen Canonical-XML-Dateien."
    Unter „kanonischer Form“ wird auf dieser Seite die in einem der obigen Aufzählungspunkte beschriebene, von `sil-lift` selbst dokumentierte Form verstanden. Dies steht in keinem Zusammenhang mit dem „Canonical XML (C14N)“-Prozess des W3C. Es steht in keinem Zusammenhang mit der Klasse `CanonicalXmlSettings` von `SIL.Core`.

## XML-Inhalte können Folgendes nicht darstellen

Nicht-BMP-Zeichen – Emojis, CJK Extension B, Adlam und alles oberhalb von U+FFFF – sind gewöhnliche Inhalte und werden bei der Hin- und Rücksendung byteweise identisch übertragen. Ein „Surrogate-Paar“ ist ein Detail der UTF-16-Kodierung: Python-Zeichenketten bestehen aus einer Folge von Codepunkten, sodass weder der Leser noch der Byte-Scanner noch der Schreiber jemals eines davon zu Gesicht bekommt.

Ein _einzelner_ Platzhalter (U+D800–U+DFFF) ist etwas anderes: Ein Python-String kann einen enthalten, ein XML-Dokument hingegen nicht, unabhängig von der Kodierung. Es kann niemals aus einer Datei stammen – der Parser lehnt beide Schreibweisen ab, sowohl eine Zeichenreferenz `&#xD800;` als auch CESU-8/WTF-8-Bytes –, sondern nur aus einer über die API zugewiesenen Zeichenkette. Das Speichern eines solchen Modells löst einen `LiftWriteError` aus, der den Knoten und den Codepunkt nennt, und es wird nichts geschrieben; die Validierung meldet dies als einen einzelnen `lone-surrogate`-Fehler, da das Dokument nicht serialisiert werden kann, damit die Schemaebenen es überprüfen können.

## Bekannte Näherungswerte (nur berührte Knoten)

- Kommentare _innerhalb_ eines `<text>`-Laufs bleiben erhalten, werden jedoch neben den Lauf verschoben und nicht an ihrer genauen Zeichenposition beibehalten.
- Die kreuzförmige Reihenfolge der untergeordneten Elemente innerhalb eines bearbeiteten Elements wird auf die kanonische Gruppierung normiert (durch das `interleave`-Schema des LIFT-Schemas wird diese Reihenfolge semantisch irrelevant).
- Ein Multitext-Element, das zwar vorhanden ist, aber nichts enthält – weder Formen noch Reste, z. B. `<definition></definition>` – wird nicht erneut ausgegeben. Das Modell stellt diese Felder als stets vorhandenes `Multitext` dar (`lexical-unit`, `citation`, `definition`, die `usage` einer Relation sowie `label` / `abbrev` / `description` bei URL-Verweisen, Bereichen, Bereichselementen und der Kopfzeile) dar, sodass sich ein leeres Feld nach der Analyse nicht von einem fehlenden unterscheiden lässt. Es geht keine semantische Information verloren.
