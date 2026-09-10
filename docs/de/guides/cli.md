# Die Befehlszeile

Durch die Installation des Pakets (`pip install sil-lift`) wird auch der Befehl `sil-lift` installiert – ein unterstütztes Tool im Stil von LiftTools, das im Lieferumfang des Pakets enthalten ist (und für `validate` ein Beispiel für die Anwendung der Bibliotheks-API).

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media] [--require-ids]
                                           alle Probleme, mit Datei/Eintrag/Zeile; Beenden mit Status 1 bei Fehlern
sil-lift stats PATH [--format {text,json}]
                                           Anzahl der Einträge/Bedeutungen/Sprachen (Streaming; beliebige Größe)
sil-lift sort PATH [-o OUT]               kanonisch sortierte, diff-fähige Kopie (Standard: an Ort und Stelle)
sil-lift check-media PATH                 Bericht über fehlende und verwaiste Medien; Beendet mit 1, wenn Medien fehlen
sil-lift export PATH [-o OUT] [--langs L] [--tsv]
                                           eine Zeile pro Blatt-Sense (Subsenses abgeflacht) in CSV/TSV (Streaming)
```

`--format json` gibt ein einzelnes JSON-Objekt an die Standardausgabe aus (und sonst nichts), das für CI- und Automatisierungszwecke verwendet werden kann; siehe das Schema im folgenden Beispiel. `--strict` behandelt Warnungen als Fehler und gibt den Wert 1 zurück, wenn welche gefunden werden – verwenden Sie diese Option, um einen Build davon abhängig zu machen, dass überhaupt keine Warnungen auftreten, anstatt nur von Fehlern. `--no-check-media` überspringt die Überprüfung des Vorhandenseins der Medien im Dateisystem (wodurch `missing-media`-Fehler unterdrückt werden), was bei der Validierung eines frisch generierten Exports nützlich ist, dessen Audio- und Fotodateien sich nicht im selben Ordner, sondern an einem anderen Speicherort befinden. `--require-ids` führt zudem zu einem Fehler (einem `missing-id`-Fehler), wenn bei einem Eintrag die `guid` fehlt oder bei einem Sense die `id` fehlt – dies ist strenger als bei LIFT und dient Workflows, bei denen der Reimport anhand einer stabilen ID erfolgt. Wird `-` als Pfad übergeben, wird das Dokument aus der Standard-Eingabe gelesen (ein über eine Pipe übermitteltes Dokument hat keinen Ordner, daher werden die zugehörige Datei `.lift-ranges` und die Medien nicht aufgelöst). `stats` akzeptiert ebenfalls die Option `--format json` und gibt die Zählwerte als einzelnes JSON-Objekt aus.

!!! note
    Die Exit-Codes von `validate` und das Schema von `--format json` stellen eine unterstützte Automatisierungsschnittstelle dar: Beide werden durch Tests abgedeckt und ändern sich nur gemäß SemVer.

`sort` schreibt nur die `.lift`-Datei neu; die zugehörigen `.lift-ranges`-Dateien bleiben unberührt
(sortieren Sie diese separat mit der `RangesFile`-API).

`validate`, `stats`, `check-media` und `export` akzeptieren ebenfalls ein komprimiertes LIFT-Paket (eine `.zip`-Datei in einem der beiden Layouts – entweder mit Dateien im Stammverzeichnis des Archivs oder verschachtelt unter einem Ordner der obersten Ebene); dieses wird in ein temporäres Verzeichnis entpackt und nach Abschluss des Befehls gelöscht. Die Streaming-Befehle `stats` und `export` extrahieren nur die `.lift`-Datei selbst, sodass sie bei datenintensiven Paketen ressourcenschonend bleiben; `validate` und `check-media` benötigen den gesamten Ordner und extrahieren dessen gesamten Inhalt.

Beispiele:

```
$ sil-lift validate dictionary.lift
Fehler [dangling-ref] dictionary.lift:88 (Eintrag „apu“): Die Referenz „nope“ entspricht keiner Eintrags-ID/GUID oder Bedeutungs-ID
Warnung [uri-not-rfc] dictionary.lift:6: <range href='file://C:/...'>: Windows-Laufwerksbuchstabe als URI-Autorität verwendet (im FLEx-Stil file://C:/)
1 Fehler, 1 Warnung

$ sil-lift validate dictionary.lift --format json
{
  „problems“: [
    {
      "level": "error",
      "code": "dangling-ref",
      "message": "ref 'nope' passt zu keiner Eintrags-ID/GUID oder Sinn-ID",
      "file": "dictionary.lift",
      "entry_id": "apu",
      "guid": null,
      "line": 88
    },
    {
      "level": "warning",
      "code": "uri-not-rfc",
      "message": "<range href='file://C:/...'>: Windows-Laufwerksbuchstabe als URI-Autorität verwendet (im FLEx-Stil file://C:/)",
      "file": "dictionary.lift",
      "entry_id": null,
      "guid": null,
      "line": 6
    }
  ],
  „summary“: {
    „errors“: 1,
    „warnings“: 1
  }
}

$ sil-lift stats sango.lift
Einträge:   3507
Bedeutungen:    4541
...

$ sil-lift export dictionary.lift --langs en,fr -o dictionary.csv
```

Die gesamte Ausgabe erfolgt in UTF-8 – auf jeder Plattform und unabhängig davon, ob sie an eine Konsole, eine Pipe oder eine `>`-Umleitung gesendet wird. Es wird niemals die Locale-Kodierung (cp1252 unter Windows, ASCII unter einer C/POSIX-Locale) verwendet, da diese LIFT-Inhalte nicht darstellen kann. `sil-lift export dictionary.lift > dictionary.csv` schreibt daher genau dieselben Bytes wie `-o dictionary.csv`, einschließlich der CRLF-Zeilenenden.

Exit-Codes: `0` Erfolg (Warnungen zulässig, sofern nicht `--strict` angegeben), `1` Beanstandungen (Validierungsfehler / fehlende Medien / Warnungen bei Verwendung von `--strict`), `2` ein E/A-Fehler an einer der beiden Seiten – Eingabe, die nicht gelesen werden kann, oder Ausgabe, die nicht geschrieben werden kann (z. B. weil ein Leser wie `head` die Pipe schließt oder die Festplatte voll ist).
