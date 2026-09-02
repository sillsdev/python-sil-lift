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
- Streaming mode reuses no source bytes: output is always canonical. Root-level LIFT residue — comments between entries and out-of-schema attributes on `<lift>` — is not carried; entries and the header are complete, residue included.
- Nor does it generate timestamps. An entry is written with the dates it carries, since a streaming writer has no loaded document to compare it against — the stamping [`Lexicon.save()`](../fidelity.md#saving-an-edited-document) does needs that baseline. Set `entry.date_modified` yourself on the entries this pass rewrites.
- If the body of an `open_writer` block raises, the file is left visibly unterminated (no closing `</lift>`) — a half-written lexicon must not look complete.
