# The command line (cli)

Installing the package (`pip install sil-lift`) also installs the `sil-lift` command.

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media]
                  [--allow CODE[,CODE...]]... [--require-ids]
    all problems, with file/entry/line; exit 1 on errors

sil-lift stats PATH [--format {text,json}]
    entry/sense/language counts (streaming; any size)

sil-lift sort PATH [-o OUT]
    canonically sorted, diff-ready copy (default: in place)

sil-lift check-media PATH
    missing, misspelled, and orphaned media report; exit 1 if missing/misspelled

sil-lift export PATH [-o OUT] [--langs L] [--tsv]
    one row per leaf sense (subsenses flattened) to CSV/TSV (streaming)
```

## validate

`validate` prints one line per finding, then a summary. `--format json` gives the same findings as one JSON object:

```
$ sil-lift validate dictionary.lift
warning [uri-not-rfc] dictionary.lift:6: <range href='file://C:/...'>: Windows drive letter used as URI authority (FLEx-style file://C:/)
error [dangling-ref] dictionary.lift:88 (entry poʻo_a1b2): ref 'nope' matches no entry id/guid or sense id
1 error(s), 1 warning(s)

$ sil-lift validate dictionary.lift --format json
{
  "problems": [
    {
      "level": "warning",
      "code": "uri-not-rfc",
      "message": "<range href='file://C:/...'>: Windows drive letter used as URI authority (FLEx-style file://C:/)",
      "file": "dictionary.lift",
      "entry_id": null,
      "guid": null,
      "line": 6
    },
    {
      "level": "error",
      "code": "dangling-ref",
      "message": "ref 'nope' matches no entry id/guid or sense id",
      "file": "dictionary.lift",
      "entry_id": "po\u02bbo_a1b2",
      "guid": null,
      "line": 88
    }
  ],
  "summary": {
    "errors": 1,
    "warnings": 1,
    "allowed": 0
  }
}
```

`validate`'s options:

- `--format json` writes a single JSON object to stdout (and nothing else) for CI/automation consumption. See the schema in the example above.
- `--strict` treats warnings as errors, exiting 1 if any are found. Use it to gate a build on no warnings at all rather than on errors alone.
- `--no-check-media` skips the filesystem media-presence check, suppressing `missing-media` and `media-href-mismatch` findings. Useful when an export's audio and photo files are kept somewhere else, or haven't been copied next to the `.lift` yet.
- `--allow CODE[,CODE...]` (repeatable) reports the given codes' findings but leaves them out of the pass/fail decision.
    - It applies to errors and warnings alike, so an allowed warning does not trip `--strict` either.
    - The summary line tallies allowed findings per code; the JSON summary's `allowed` gives their total.
    - A code that never occurs is ignored, so an allow list keeps working if a check is retired.
- `--require-ids` additionally fails (a `missing-id` error) on any entry lacking a `guid` or sense lacking an `id`. That is stricter than LIFT, for workflows that re-import by a stable id.

Passing `-` as the path reads the document from stdin. A piped document has no folder, so its companion `.lift-ranges` and media are not resolved.

!!! note

    `validate`'s exit codes and `--format json` schema are a supported automation interface: both are covered by tests and change only under SemVer.

## stats

```
$ sil-lift stats sango.lift
entries:   3507
senses:    4541
...
```

`stats` likewise takes `--format json`, emitting the counts as a single JSON object.

## sort

`sort` rewrites only the `.lift` file; companion `.lift-ranges` files are left untouched (sort those separately with the [`RangesFile` API](folder-media.md#ranges)).

## export

`export` writes one row per leaf sense. `--langs` picks which languages get `gloss_` and `definition_` columns; by default they are detected from the document.

```
$ sil-lift export dictionary.lift --langs en,id -o dictionary.csv
```

## Zipped packages

`validate`, `stats`, `check-media`, and `export` also accept a zipped (`.zip`) LIFT package. Its files can sit at the archive root or inside one top-level folder. Whatever a command extracts goes to a temporary directory and is discarded when the command finishes.

- The streaming commands `stats` and `export` extract only the `.lift` itself, so they stay cheap on media-heavy packages.
- `validate` and `check-media` need the whole folder and extract all of it.

## Output encoding

All output is UTF-8, on every platform and whether it goes to a console, a pipe, or a `>` redirect. It is never the locale encoding (cp1252 on Windows, ASCII under a C/POSIX locale), which cannot represent LIFT content. `sil-lift export dictionary.lift > dictionary.csv` therefore writes exactly the bytes `-o dictionary.csv` writes, CRLF row terminators included.

## Exit codes

- `0`: success. Warnings do not fail the run unless `--strict`.
- `1`: findings. A validation error, missing or misspelled media, or a warning under `--strict` exits 1, unless its code was given to `--allow`.
- `2`: I/O failure. The input could not be read, or the output could not be written, for example because the disk is full or a reader like `head` closed the pipe.
