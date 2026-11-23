# Die Befehlszeile (CLI)

Durch die Installation des Pakets (`pip install sil-lift`) wird auch der Befehl `sil-lift` installiert.

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media]
                  [--allow CODE[,CODE...]]... [--require-ids]
    alle Probleme, mit Datei/Eintrag/Zeile; Beenden mit Status 1 bei Fehlern

sil-lift stats PATH [--format {text,json}]
    Anzahl der Einträge/Bedeutungen/Sprachen (Streaming; beliebige Größe)

sil-lift sort PATH [-o OUT]
    kanonisch sortierte, diff-fähige Kopie (Standard: an Ort und Stelle)

sil-lift check-media PATH
    Bericht über fehlende, falsch geschriebene und verwaiste Medien; Beendet mit 1, wenn Medien fehlen oder falsch geschrieben sind

sil-lift export PATH [-o OUT] [--langs L] [--tsv]
    eine Zeile pro Blatt-Sense (Subsenses abgeflacht) in CSV/TSV (Streaming)
```

## validieren

`validate` gibt pro Befund eine Zeile aus, gefolgt von einer Zusammenfassung. `--format json` liefert dieselben Ergebnisse als ein JSON-Objekt:

```
$ sil-lift validate dictionary.lift
Warnung [uri-not-rfc] dictionary.lift:6: <range href='file://C:/...'>: Windows-Laufwerksbuchstabe als URI-Autorität verwendet (im FLEx-Stil file://C:/)
Fehler [dangling-ref] dictionary.lift:88 (Eintrag poʻo_a1b2): Die Referenz „nope“ stimmt mit keiner Eintrags-ID/GUID oder Sinn-ID überein
1 Fehler, 1 Warnung

$ sil-lift validate dictionary.lift --format json
{
  „problems“: [
    {
      "level": "warning",
      "code": "uri-not-rfc",
      "message": "<range href='file://C:/...'>: Windows-Laufwerksbuchstabe als URI-Autorität verwendet (im FLEx-Stil file://C:/)",
      "file": "dictionary.lift",
      "entry_id": null,
      "guid": null,
      "line": 6
    },
    {
      "level": "error",
      "code": "dangling-ref",
      "message": "Die Referenz 'nope' stimmt mit keiner Eintrags-ID/GUID oder Sense-ID überein",
      "file": "dictionary.lift",
      "entry_id": "po\u02bbo_a1b2",
      "guid": null,
      "line": 88
    }
  ],
  "summary": {
    "errors": 1,
    "warnings": 1,
    "allowed": 0
  }
}
```

Optionen von `validate`:

- `--format json` schreibt ein einzelnes JSON-Objekt in die Standardausgabe (und sonst nichts), damit es von CI-Systemen oder Automatisierungsprozessen verwendet werden kann. Siehe das Schema im obigen Beispiel.
- `--strict` behandelt Warnungen als Fehler und gibt den Wert 1 zurück, wenn welche gefunden werden. Verwenden Sie diese Option, um einen Build erst dann zu stoppen, wenn überhaupt keine Warnungen mehr auftreten, und nicht erst bei Fehlern.
- `--no-check-media` überspringt die Überprüfung auf das Vorhandensein von Medien im Dateisystem und unterdrückt dabei die Fehlermeldungen `missing-media` und `media-href-mismatch`. Nützlich, wenn die Audio- und Fotodateien eines Exports an einem anderen Ort gespeichert sind oder noch nicht neben die `.lift`-Datei kopiert wurden.
- `--allow CODE[,CODE...]` (wiederholbar) gibt die Ergebnisse der angegebenen Codes aus, berücksichtigt diese jedoch nicht bei der Entscheidung über „bestanden“ oder „nicht bestanden“.
  - Dies gilt sowohl für Fehler als auch für Warnungen, sodass eine zulässige Warnung die Option `--strict` ebenfalls nicht auslöst.
  - In der Zusammenfassungszeile werden die zulässigen Ergebnisse pro Code gezählt; das Feld `allowed` der JSON-Zusammenfassung gibt deren Gesamtzahl an.
  - Ein Code, der niemals auftritt, wird ignoriert, sodass eine Zulassungsliste auch dann weiterhin funktioniert, wenn eine Prüfung außer Kraft gesetzt wird.
- `--require-ids` schlägt zudem fehl (Fehler „missing-id“), wenn bei einem Eintrag die `guid` fehlt oder bei einem Sense die `id` fehlt. Das ist strenger als bei LIFT, wenn es um Workflows geht, bei denen anhand einer stabilen ID erneut importiert wird.

Wird `-` als Pfad übergeben, wird das Dokument aus der Standard-Eingabe gelesen. Ein über Piped übermitteltes Dokument hat keinen Ordner, daher werden die zugehörige Datei `.lift-ranges` und die Medien nicht aufgelöst.

!!! note

    Die Exit-Codes von `validate` und das Schema von `--format json` stellen eine unterstützte Automatisierungsschnittstelle dar: Beide werden durch Tests abgedeckt und ändern sich nur gemäß SemVer.

## Statistiken

```
$ sil-lift stats sango.lift
Einträge:   3507
Erfassungen:    4541
...
```

`stats` akzeptiert ebenfalls die Option `--format json` und gibt die Zählwerte als einzelnes JSON-Objekt aus.

## sortieren

`sort` schreibt nur die `.lift`-Datei neu; zugehörige `.lift-ranges`-Dateien bleiben unverändert (sortieren Sie diese separat mit der [`RangesFile`-API](folder-media.md#ranges)).

## Export

`export` schreibt eine Zeile pro Leaf-Sense. `--langs` legt fest, für welche Sprachen die Spalten `gloss_` und `definition_` angezeigt werden; standardmäßig werden diese aus dem Dokument ermittelt.

```
$ sil-lift export dictionary.lift --langs en,id -o dictionary.csv
```

## ZIP-Dateien

`validate`, `stats`, `check-media` und `export` akzeptieren ebenfalls ein komprimiertes (`.zip`) LIFT-Paket. Die Dateien können sich im Stammverzeichnis des Archivs oder in einem Ordner der obersten Ebene befinden. Alles, was ein Befehl extrahiert, wird in ein temporäres Verzeichnis verschoben und nach Beendigung des Befehls gelöscht.

- Die Streaming-Befehle `stats` und `export` extrahieren nur die `.lift`-Datei selbst, sodass sie auch bei datenintensiven Paketen ressourcenschonend bleiben.
- `validate` und `check-media` benötigen den gesamten Ordner und extrahieren dessen gesamten Inhalt.

## Ausgabekodierung

Die gesamte Ausgabe erfolgt im UTF-8-Format, auf jeder Plattform und unabhängig davon, ob sie an eine Konsole, eine Pipe oder eine `>`-Umleitung gesendet wird. Es ist niemals die Locale-Kodierung (cp1252 unter Windows, ASCII unter einer C/POSIX-Locale), die LIFT-Inhalte nicht darstellen kann. `sil-lift export dictionary.lift > dictionary.csv` schreibt daher genau dieselben Bytes wie `-o dictionary.csv`, einschließlich der CRLF-Zeilenenden.

## Exit-Codes

- `0`: Erfolg. Warnungen führen nicht zum Abbruch des Laufs, es sei denn, `--strict` ist angegeben.
- `1`: Ergebnisse. Ein Validierungsfehler, fehlende oder falsch geschriebene Medien oder eine Warnung unter `--strict` führen zum Beenden mit dem Status 1, es sei denn, der entsprechende Code wurde an `--allow` übergeben.
- `2`: E/A-Fehler. Die Eingabe konnte nicht gelesen oder die Ausgabe nicht geschrieben werden, beispielsweise weil der Datenträger voll ist oder ein Leseprogramm wie `head` die Pipe geschlossen hat.
