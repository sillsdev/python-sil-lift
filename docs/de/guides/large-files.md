# Große Dateien (Streaming)

`load()` baut den gesamten Objektgraphen auf. Bei Lexika mit einer Größe von mehreren hundert MB verarbeitet die Streaming-API jeweils einen Eintrag nach dem anderen in einem begrenzten Speicherbereich. Es liefert denselben `Entry`-Typ, sodass Code, der für einen Modus geschrieben wurde, auch im anderen Modus funktioniert.

## Lesen

```python
import sil_lift

with sil_lift.open_reader("big.lift") as reader:
    header = reader.header            # wird vorab geparst (steht vor den Einträgen)
    for entry in reader:              # verzögerter Iterator[Entry]
        ...
```

## Schreiben

```python
mit sil_lift.open_reader("big.lift") als reader, sil_lift.open_writer(
    "out.lift", header=reader.header, producer="my-script"
) als writer:
    for entry in reader:
        if not entry.date_deleted:    # z. B. als gelöscht markierte Einträge überspringen
            writer.write(entry)
```

Anmerkungen:

- Die Ausgabe des Writers entspricht genau dem, was der kanonische Serializer für das gesamte Dokument bei denselben Inhalten erzeugen würde; die beiden Modi weichen nie voneinander ab.
- Im Streaming-Modus werden keine Quellbytes wiederverwendet: Die Ausgabe ist immer kanonisch. LIFT-Reste auf Root-Ebene (Kommentare zwischen Einträgen und schemenfremde Attribute unter `<lift>`) werden entfernt, Einträge und der Header behalten jedoch ihre eigenen Reste bei.
- Im Gegensatz zu [`Lexicon.save()`](../fidelity.md#saving-an-edited-document) werden im Streaming-Modus keine Zeitstempel generiert. Ein Eintrag wird mit den bereits vorhandenen Datumsangaben geschrieben: Ein Streaming-Pass sieht das Dokument nie in seiner ursprünglichen Form, daher kann er nicht erkennen, welche Einträge Sie geändert haben. Setzen Sie `entry.date_modified` selbst bei den Einträgen, die bei diesem Durchlauf überschrieben werden.
- Wenn im Hauptteil eines `open_writer`-Blocks ein Fehler ausgelöst wird, bleibt die Datei sichtbar unvollständig (kein abschließendes `</lift>`). Dadurch wird verhindert, dass ein unvollständiges Lexikon den Anschein erweckt, es sei vollständig.
