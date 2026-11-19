# Large files (streaming)

`load()` builds the whole object graph. For multi-hundred-MB lexicons, the streaming API processes one entry at a time in bounded memory. It yields the same `Entry` type, so code written against one mode works in the other.

## Reading

```python
import sil_lift

with sil_lift.open_reader("big.lift") as reader:
    header = reader.header            # parsed up front (precedes entries)
    for entry in reader:              # lazy Iterator[Entry]
        ...
```

## Writing

```python
with sil_lift.open_reader("big.lift") as reader, sil_lift.open_writer(
    "out.lift", header=reader.header, producer="my-script"
) as writer:
    for entry in reader:
        if not entry.date_deleted:    # e.g. skip entries marked deleted
            writer.write(entry)
```

Notes:

- The writer's output is exactly what the full-document canonical serializer would produce for the same content; the two modes never drift apart.
- Streaming mode reuses no source bytes: output is always canonical. Root-level LIFT residue (comments between entries and out-of-schema attributes on `<lift>`) is dropped, but entries and the header keep their own residue.
- Unlike [`Lexicon.save()`](../fidelity.md#saving-an-edited-document), streaming mode generates no timestamps. An entry is written with the dates it already has: a streaming pass never sees the document as it was, so it cannot tell which entries you changed. Set `entry.date_modified` yourself on the ones this pass rewrites.
- If the body of an `open_writer` block raises, the file is left visibly unterminated (no closing `</lift>`). This prevents a half-written lexicon from looking complete.
