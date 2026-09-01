# The command line

Installing the package (`pip install sil-lift`) also installs the `sil-lift` command — a supported tool in the spirit of LiftTools that ships with the package (and, for `validate`, a worked example of the library API).

```
sil-lift validate PATH [--format {text,json}] [--strict] [--no-check-media] [--require-ids]
                                           all problems, with file/entry/line; exit 1 on errors
sil-lift stats PATH [--format {text,json}]
                                           entry/sense/language counts (streaming; any size)
sil-lift sort PATH [-o OUT]               canonically sorted, diff-ready copy (default: in place)
sil-lift check-media PATH                 missing and orphaned media report; exit 1 if missing
sil-lift export PATH [-o OUT] [--langs L] [--tsv]
                                           one row per leaf sense (subsenses flattened) to CSV/TSV (streaming)
```

`--format json` writes a single JSON object to stdout (and nothing else) for CI/automation consumption; see the schema in the example below. `--strict` treats warnings as errors, exiting 1 if any are found — use it to gate a build on no warnings at all rather than on errors alone. `--no-check-media` skips the filesystem media-presence check (suppressing `missing-media` findings), which is useful when validating a freshly generated export whose audio/photo files live elsewhere rather than in the same folder. `--require-ids` additionally fails (a `missing-id` error) on any entry lacking a `guid` or sense lacking an `id` — stricter than LIFT, for workflows that re-import by a stable id. Passing `-` as the path reads the document from stdin (a piped document has no folder, so its companion `.lift-ranges` and media are not resolved). `stats` likewise takes `--format json`, emitting the counts as a single JSON object.

!!! note
    `validate`'s exit codes and `--format json` schema are a supported automation interface: both are covered by tests and change only under SemVer.

`sort` rewrites only the `.lift` file; companion `.lift-ranges` files are left
untouched (sort those separately with the `RangesFile` API).

`validate`, `stats`, `check-media`, and `export` also accept a zipped LIFT package (a `.zip` in either layout — files at the archive root, or nested under one top-level folder); it is extracted to a temporary directory and discarded when the command finishes. The streaming commands `stats` and `export` extract only the `.lift` itself, so they stay cheap on media-heavy packages; `validate` and `check-media` need the whole folder and extract all of it.

Examples:

```
$ sil-lift validate dictionary.lift
error [dangling-ref] dictionary.lift:88 (entry apu): ref 'nope' matches no entry id/guid or sense id
warning [uri-not-rfc] dictionary.lift:6: <range href='file://C:/...'>: Windows drive letter used as URI authority (FLEx-style file://C:/)
1 error(s), 1 warning(s)

$ sil-lift validate dictionary.lift --format json
{
  "problems": [
    {
      "level": "error",
      "code": "dangling-ref",
      "message": "ref 'nope' matches no entry id/guid or sense id",
      "file": "dictionary.lift",
      "entry_id": "apu",
      "guid": null,
      "line": 88
    },
    {
      "level": "warning",
      "code": "uri-not-rfc",
      "message": "<range href='file://C:/...'>: Windows drive letter used as URI authority (FLEx-style file://C:/)",
      "file": "dictionary.lift",
      "entry_id": null,
      "guid": null,
      "line": 6
    }
  ],
  "summary": {
    "errors": 1,
    "warnings": 1
  }
}

$ sil-lift stats sango.lift
entries:   3507
senses:    4541
...

$ sil-lift export dictionary.lift --langs en,fr -o dictionary.csv
```

All output is UTF-8, on every platform and whether it goes to a console, a pipe, or a `>` redirect — never the locale encoding (cp1252 on Windows, ASCII under a C/POSIX locale), which cannot represent LIFT content. `sil-lift export dictionary.lift > dictionary.csv` therefore writes exactly the bytes `-o dictionary.csv` writes, CRLF row terminators included.

Exit codes: `0` success (warnings allowed, unless `--strict`), `1` findings (validation errors / missing media / warnings under `--strict`), `2` an I/O failure at either end — input that cannot be read, or output that cannot be written (a reader like `head` closing the pipe, a full disk).
