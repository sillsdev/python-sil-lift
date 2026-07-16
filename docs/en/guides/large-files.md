# Large files (streaming)

`load()` builds the whole object graph. For multi-hundred-MB lexicons, the streaming API processes one entry at a time in bounded memory — the same `Entry` type, so code written against one mode works in the other.

```python
import sil_lift

with sil_lift.open_reader("big.lift") as reader:
    header = reader.header            # parsed up front (precedes entries)
    for entry in reader:              # lazy Iterator[Entry]
        ...
```

```python
with sil_lift.open_reader("big.lift") as reader, sil_lift.open_writer(
    "out.lift", header=reader.header, producer="my-script"
) as writer:
    for entry in reader:
        if not entry.date_deleted:    # e.g. drop tombstones
            writer.write(entry)
```

Notes:

- The writer's output is exactly what the full-document canonical serializer would produce for the same content — the two modes never drift apart.
- Streaming mode has no byte-passthrough layer: output is always canonical. Root-level comments between entries are not carried; entries and the header are complete, residue included.
- If the body of an `open_writer` block raises, the file is left visibly unterminated (no closing `</lift>`) — a half-written lexicon must not look complete.
