# The LIFT folder: ranges and media

A LIFT lexicon is usually a _folder_: the `.lift` file, one or more `.lift-ranges` companions, and `audio/` / `pictures/` media.

## Ranges

```python
lex = sil_lift.load("dictionary.lift")      # companions tracked automatically

lex.ranges_files                            # {Path(...): RangesFile}
lex.all_ranges()                            # merged {id: Range} view
lex.all_ranges()["grammatical-info"].elements
```

Companion discovery handles the real world: a `range/@href` that points at an existing file is used; FieldWorks' dangling absolute `file://C:/...` hrefs fall back to the href's basename next to the `.lift`; and the conventional `<name>.lift-ranges` sibling is picked up even when nothing references it.

`lex.save()` writes the `.lift` and every tracked companion together. Edits to a `RangesFile` save back to _its_ file; untouched ranges keep their exact bytes. Standalone use:

```python
ranges = sil_lift.RangesFile.load("dictionary.lift-ranges")
ranges.find("grammatical-info")
ranges.sort()
ranges.save()
```

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
