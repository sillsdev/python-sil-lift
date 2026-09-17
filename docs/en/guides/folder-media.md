# The LIFT folder: ranges and media

A LIFT lexicon is usually a _folder_: the `.lift` file, one or more `.lift-ranges` companions (sidecar files), and `audio/` / `pictures/` media.

## Ranges

```python
lex = sil_lift.load("dictionary.lift")      # companions tracked automatically

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # merged {id: Range} view
lex.all_ranges()["grammatical-info"].elements
```

`lex.save()` writes the `.lift` and every tracked companion together. Edits to a `RangesFile` save back to _its_ file; untouched ranges keep their exact bytes. Standalone use:

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

### Companion discovery

Several candidates are tried, and every distinct file among them is loaded.

- A header `range/@href` that points at an existing file is used as given.
- An href that resolves to nothing falls back to its basename next to the `.lift` — FieldWorks writes dangling absolute `file://C:/...` paths from the exporting machine, and that fallback is what makes them work locally.
- The conventional `<name>.lift-ranges` sibling is picked up even when nothing references it.

Names that differ only in case or Unicode normalization still match — `Dict.LIFT` finds `Dict.lift-ranges` — unless several files match one name, which loads none of them and is reported as [`ambiguous-ranges-file`](validate.md#problem-codes).

Companion discovery never fails the load. A candidate that exists but cannot be read as a `<lift-ranges>` document — a zero-byte or truncated sidecar from an interrupted export, another `.lift`, an unrelated file a header href happens to name — is skipped, so the lexicon's entries still load, and it is reported as [`unreadable-ranges-file`](validate.md#problem-codes). `RangesFile.load()` still raises, so opening a companion directly is as strict as ever.

Pass `resolve_ranges=False` to `load()` to skip companion discovery.

## Media

```python
for ref in lex.media_refs():        # every <media> and <illustration>
    print(ref.kind, ref.href, ref.entry_id)

lex.missing_media()                 # refs whose files don't exist
```

Resolution follows the conventional layout: a relative href is checked as given (backslashes normalized — WeSay writes `pictures\photo with space.png`) and under `audio/` (for pronunciation media) or `pictures/` (for illustrations). Remote/absolute hrefs can't be checked and are skipped.

## Other folder contents

A LIFT folder often holds files sil-lift doesn't model — writing-system LDML under `WritingSystems/`, The Combine's speaker consent audio/image files under `consent/`, and the like; `load()`/`save()` leave these untouched, and [`Lexicon.save_zip()`](lift-export-interop.md) carries them through verbatim when packaging the folder.
