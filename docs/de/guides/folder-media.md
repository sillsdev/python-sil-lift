# Der LIFT-Ordner: Sortimente und Medien

Ein LIFT-Lexikon besteht in der Regel aus einem _Ordner_: der `.lift`-Datei, einer oder mehreren zugehörigen `.lift-ranges`-Dateien (Sidecar-Dateien) sowie Mediendateien in den Ordnern `audio/` und `pictures/`.

## Bereiche

```python
lex = sil_lift.load("dictionary.lift")      # Begleitdateien werden automatisch nachverfolgt

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # zusammengeführte {id: Range}-Ansicht
lex.all_ranges()["grammatical-info"].elements
```

`lex.save()` schreibt die `.lift`-Datei und alle nachverfolgten Companion-Dateien gemeinsam. Änderungen an einer `RangesFile` werden wieder in _diese_ Datei gespeichert; unveränderte Bereiche behalten ihre genauen Byte-Werte bei. Einzelbetrieb:

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

### Entdeckung von Begleitsternen

Es werden mehrere Kandidaten getestet, und jede einzelne Datei unter ihnen wird geladen.

- Ein Header `range/@href`, der auf eine vorhandene Datei verweist, wird wie angegeben verwendet.
- Ein href, der zu nichts führt, greift auf seinen Basisnamen neben dem `.lift` zurück. FieldWorks schreibt unvollständige absolute `file://C:/...`-Pfade vom exportierenden Rechner, und dank dieser Ausweichlösung funktionieren sie lokal.
- Das herkömmliche Geschwisterelement `<name>.lift-ranges` wird auch dann erkannt, wenn es von keiner anderen Stelle referenziert wird.

Namen, die sich lediglich in der Groß-/Kleinschreibung oder der Unicode-Normalisierung unterscheiden, werden weiterhin als übereinstimmend erkannt (`Dict.LIFT` findet `Dict.lift-ranges`), es sei denn, mehrere Dateien entsprechen einem Namen; in diesem Fall wird keine davon geladen und dies wird als [`ambiguous-ranges-file`](validate.md#problem-codes) gemeldet.

Ein Kandidat, der nicht als `<lift-ranges>`-Dokument gelesen werden kann (z. B. eine Null-Byte-Datei aus einem unterbrochenen Export), wird übersprungen, anstatt den Ladevorgang abzubrechen, und als [`unreadable-ranges-file`](validate.md#problem-codes) gemeldet. Wird eine Datei direkt mit `RangesFile.load()` geladen, wird stattdessen ein Fehler ausgelöst.

Übergeben Sie `resolve_ranges=False` an `load()`, um die Erkennung von Begleitkomponenten zu überspringen.

## Medien

```python
for ref in lex.media_refs():        # alle <media> und <illustration>
    print(ref.kind, ref.href, ref.entry_id)

lex.check_media()                   # Verweise, die nicht einwandfrei aufgelöst werden können
```

Die Auflösung erfolgt nach dem herkömmlichen Schema: Ein relativer `href`-Link wird so wie angegeben überprüft und unter `audio/` (für Aussprachedateien) oder `pictures/` (für Abbildungen) gesucht. Backslashes werden als Schrägstriche behandelt, da WeSay HREF-Links wie `pictures\photo with space.png` schreibt. Remote- und absolute „hrefs“ können nicht überprüft werden und werden übersprungen.

`check_media()` meldet nur die Verweise, die nicht einwandfrei aufgelöst werden konnten, jeweils ein `MediaResolution`:

- `status="missing"`: Unter keiner Schreibweise wurde eine Datei für den href-Link gefunden.
- `status="mismatch"`: Eine Übereinstimmung wurde gefunden, jedoch nur bei Groß-/Kleinschreibung ignorieren oder NFC; `found` gibt den Namen der Datei auf der Festplatte an.

Es wird eine Nichtübereinstimmung gemeldet, obwohl die Datei gefunden wurde. Ein Begleitname wird ohne weitere Anmerkung grob abgeglichen, aber ein Medien-href-Link wird anschließend auch von dem Server gelesen, der den Ordner bereitstellt, und ein Host, bei dem die Groß- und Kleinschreibung beachtet wird, findet die Datei nicht. Die Validierung meldet denselben Fall wie [`media-href-mismatch`](validate.md#problem-codes).

## Sonstige Ordnerinhalte

Ein LIFT-Ordner enthält häufig Dateien, die sil-lift nicht modelliert, wie beispielsweise das Schriftsystem LDML unter `WritingSystems/` oder die Dateien zur Sprecherzustimmung von „The Combine“ unter `consent/`. `load()` und `save()` lassen diese unverändert, und [`Lexicon.save_zip()`](lift-export-interop.md) übernimmt sie beim Verpacken des Ordners wortwörtlich.
