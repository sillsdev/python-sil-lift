# Fidelity-Garantien

LIFT ist ein _Austauschformat_: Die oberste Regel lautet: **Lass niemals etwas weg, was du nicht verstehst**. Der Vertrag von `sil-lift`, der bei jedem Durchlauf durch die Testsuite überprüft wird (Korpusdateien sowie eigenschaftsbasierte Generierung):

## Lesen

Jedes wohlgeformte LIFT 0.13-Dokument wird geladen – auch Inhalte, die nicht dem Schema entsprechen. Alles, was das Modell nicht definiert, wird im „Extras“-Bereich des nächstgelegenen Knotens gespeichert: unbekannte Attribute und Elemente, XML-Kommentare und Verarbeitungsanweisungen, überflüssiger Text sowie fehlerhaft formatierte typisierte Attribute (ein fehlerhaftes Datum bleibt als ursprüngliche Zeichenkette in „Extras“ erhalten; das typisierte Feld ist „None“).

## Ein unverändertes Dokument speichern

`load()` → `save()` ohne Änderungen erzeugt eine **byte-identische Ausgabe** – keine Neuformatierung, kein erneutes Escaping, keine Neuanordnung, einschließlich Byte-Order-Markierungen und XML-Deklarationen. Derzeit gibt es keine Normalisierungsliste: Die Identität ist exakt.

Ausnahmen (der Writer greift auf die vollständige kanonische Serialisierung zurück, die zwar semantisch vollständig, jedoch nicht bytekonsistent ist):

- die Quellkodierung ist nicht ASCII-kompatibel (nicht UTF-8/US-ASCII) oder
- der Quelltext enthält einen DOCTYPE oder
- Der Byte-Scanner und der Parser sind sich hinsichtlich der obersten Struktur des Dokuments nicht einig – beispielsweise bei einem nicht spezifikationskonformen zweiten `<header>`, den der Parser nur einmal beibehält (der Scanner ist bewusst misstrauisch: Bei jedem Zweifel werden überhaupt keine Quellbytes erfasst), oder
- Der Quellcode wurde im Speicher erstellt und nicht aus einer Datei geladen.

## Ein bearbeitetes Dokument speichern

- **Unveränderte Einträge werden wortwörtlich aus ihren ursprünglichen Bytes ausgegeben.** Ein Eintrag gilt als verändert, wenn sich seit dem Parsen ein beliebiger Teil seines Modellobjekts geändert hat (erkannt anhand eines Snapshots der kanonischen Serialisierung, nicht anhand eines „Dirty“-Flags).
- **Die bearbeiteten Einträge werden kanonisch und vollständig neu serialisiert**: UTF-8, Einrückung mit zwei Leerzeichen _außerhalb_ von gemischtem Inhalt (Leerzeichen innerhalb von `<text>` und `<span>` werden niemals verändert), eine dokumentierte Untergruppierung pro Element (z. B. Eintrag: lexikalische Einheit, Zitat, Aussprachen, Varianten, Bedeutungen, Anmerkungen, Beziehungen, Etymologien, Annotationen, Merkmale, Felder), feste Attributreihenfolge, Datumsangaben nach ISO-8601 (`Z` für UTC). Alle Reste werden erneut ausgegeben; ihre Position wird auf den ursprünglichen Unterindex zurückgesetzt und an die neue Unterliste angepasst (eine Annäherung – exakte Byte-Positionen sind nur für unveränderte Einträge garantiert).
- Das Hinzufügen, Entfernen oder Neuanordnen von Einträgen führt zu einer erneuten Serialisierung der Dokumentstruktur, wobei die Bytes jedes unveränderten Eintrags jedoch unverändert ausgegeben werden.

## Bekannte Näherungswerte (nur berührte Knoten)

- Kommentare _innerhalb_ eines `<text>`-Laufs bleiben erhalten, werden jedoch neben den Lauf verschoben und nicht an ihrer genauen Zeichenposition angezeigt.
- Die kreuzförmige Reihenfolge der untergeordneten Elemente innerhalb eines bearbeiteten Elements wird auf die kanonische Gruppierung normiert (durch das `interleave`-Schema des LIFT-Schemas wird diese Reihenfolge semantisch irrelevant).
- Ein Multitext-Element, das zwar vorhanden ist, aber nichts enthält – weder Formen noch Reste, z. B. `<definition></definition>` – wird nicht erneut ausgegeben. Das Modell stellt diese Felder als stets vorhandenes `Multitext` dar (`lexical-unit`, `citation`, `definition`, die `usage` einer Relation sowie `label` / `abbrev` / `description` bei URL-Verweisen, Bereichen, Bereichselementen und der Kopfzeile) dar, sodass sich ein leeres Feld nach der Analyse nicht von einem fehlenden unterscheiden lässt. Es geht keine semantische Information verloren.
