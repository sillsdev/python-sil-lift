# Große Dateien (Streaming)

`load()` baut den gesamten Objektgraphen auf. Bei Lexika mit einer Größe von mehreren hundert MB verarbeitet die Streaming-API jeweils einen Eintrag nach dem anderen in einem begrenzten Speicherbereich – dabei handelt es sich um denselben `Entry`-Typ, sodass Code, der für einen Modus geschrieben wurde, auch im anderen Modus funktioniert.

```python
import sil_lift

with sil_lift.open_reader("big.lift") as reader:
    header = reader.header            # wird vorab geparst (steht vor den Einträgen)
    for entry in reader:              # verzögerter Iterator[Entry]
        ...
```

```python
mit sil_lift.open_reader("big.lift") als reader, sil_lift.open_writer(
    "out.lift", header=reader.header, producer="my-script"
) als writer:
    for entry in reader:
        if not entry.date_deleted:    # z. B. Tombstones entfernen
            writer.write(entry)
```

Anmerkungen:

- Die Ausgabe des Writers entspricht genau dem, was der kanonische Serializer für das gesamte Dokument bei denselben Inhalten erzeugen würde – die beiden Modi weichen nie voneinander ab.
- Der Streaming-Modus verfügt über keine Byte-Passthrough-Schicht: Die Ausgabe erfolgt immer im kanonischen Format. Reste auf der obersten Ebene – Kommentare zwischen Einträgen und schemenfremde Attribute unter `<lift>` – werden nicht übertragen; Einträge und der Header sind vollständig, einschließlich der Reste.
- Wenn im Hauptteil eines `open_writer`-Blocks ein Fehler ausgelöst wird, bleibt die Datei sichtbar unvollständig (kein abschließendes `</lift>`) – ein nur zur Hälfte geschriebenes Lexikon darf nicht vollständig erscheinen.
