# Der LIFT-Ordner: Sortimente und Medien

Ein LIFT-Lexikon besteht in der Regel aus einem _Ordner_: der `.lift`-Datei, einer oder mehreren zugehörigen `.lift-ranges`-Dateien (Sidecar-Dateien) sowie den Mediendateien im Verzeichnis `audio/` bzw. `pictures/`.

## Bereiche

```python
lex = sil_lift.load("dictionary.lift")      # Begleitdateien werden automatisch nachverfolgt

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # zusammengeführte {id: Range}-Ansicht
lex.all_ranges()["grammatical-info"].elements
```

Die Companion-Erkennung berücksichtigt die reale Welt: Es wird ein `range/@href` verwendet, das auf eine vorhandene Datei verweist; Die losen absoluten `file://C:/...`-href-Angaben von FieldWorks greifen auf den Basisnamen des href neben der `.lift`-Datei zurück; und das herkömmliche Geschwisterelement `<name>.lift-ranges` wird auch dann erkannt, wenn nichts darauf verweist.

`lex.save()` schreibt die `.lift`-Datei und alle nachverfolgten Companion-Dateien gemeinsam. Änderungen an einer `RangesFile` werden wieder in _diese_ Datei gespeichert; unveränderte Bereiche behalten ihre genauen Byte-Werte bei. Einzelbetrieb:

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

Übergeben Sie `resolve_ranges=False` an `load()`, um die Erkennung von Begleitkomponenten zu überspringen.

## Medien

```python
for ref in lex.media_refs():        # alle <media> und <illustration>
    print(ref.kind, ref.href, ref.entry_id)

lex.missing_media()                 # Verweise, deren Dateien nicht vorhanden sind
```

Die Auflösung erfolgt nach dem üblichen Schema: Ein relativer href-Link wird unverändert geprüft (Backslashes werden normalisiert – WeSay schreibt „pictures\photo with space.png“) und unter „audio/“ (für Aussprachedateien) oder „pictures/“ (für Abbildungen) gesucht. Externe/absolute „hrefs“ können nicht überprüft werden und werden übersprungen.

## Sonstige Ordnerinhalte

Ein LIFT-Ordner enthält oft Dateien, die sil-lift nicht modelliert – beispielsweise das Schriftsystem LDML unter `WritingSystems/`, die Audio- und Bilddateien zur Einwilligung der Sprecher von „The Combine“ unter `consent/` und Ähnliches; `load()`/`save()` lassen diese unberührt, und [`Lexicon.save_zip()`](lift-export-interop.md) übernimmt sie beim Verpacken des Ordners unverändert.
