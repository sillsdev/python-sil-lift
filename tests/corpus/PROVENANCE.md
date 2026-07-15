# Test corpus provenance

All files fetched 2026-07-14 as byte-identical copies from public GitHub repos at
the commits recorded below (raw.githubusercontent.com at pinned SHA). Git
line-ending normalization is disabled for everything under `tests/corpus/`
(`.gitattributes`) — fidelity tests depend on the bytes staying exactly as fetched.

**License review flag (pre-release)**: `lift-standard` and `LiftTweaker` have no
license file; `flashgrab`'s LICENSE reads "Free and open source, under Anki's
license" (Anki is AGPL-3.0). All are SIL-authored repos and this use is
SIL-internal test data, but resolve licensing before any public release
(tracked with the other release gates in milestone M7).

## spec-examples/0.12/ — 19 files

- **Source**: `sillsdev/lift-standard` `examples/*.lift`
- **Commit**: `39a83be083174a40dff5b7bacac86b4f5e68afe4` (master)
- **License**: none in repo (see flag above)
- All are `<lift version="0.12">`, small (≤205 lines). Includes
  `fields any order.lift` (filename with a space — path-handling edge case).
  The upstream `VerifyExamples.proj` (MSBuild/Jing harness) was not taken —
  not corpus data. These originals also serve as version-guard fixtures
  (the library rejects non-0.13 input per decision D2).

## spec-examples/0.13/ — generated

Produced from `spec-examples/0.12/` by `tests/tools/migrate_corpus.py` using the
vendored upstream XSLT (`tests/tools/xslt/LIFT-0.12-0.13.xsl`). Regenerate with
that script; committed so tests don't depend on regeneration.

## ranges/ — test20080407 pair

- **Source**: `sillsdev/lift-standard` `LIFTDotNet/LiftIO.Tests/test20080407.lift`
  + `.lift-ranges`
- **Commit**: `39a83be083174a40dff5b7bacac86b4f5e68afe4`
- **License**: none in repo (see flag above)
- The only `.lift` + external `.lift-ranges` sample pair in existence
  (research finding 05); primary ranges fixture. `version="0.13"`,
  `producer="hand crafted"`.

## flex/AllFLExFields/ — FLEx-flavored 0.13 reference fixture

- **Source**: `sillsdev/web-languageforge`
  `sample_data/lift/AllFLExFields/{AllFLExFields.lift, AllFLExFields.lift-ranges,
  WritingSystems/{en,fr,th}.ldml}`
- **Commit**: `6ea4d7b0d39c0263f531e13246d5942550bf58ba` (HEAD of default branch
  at fetch time)
- **License**: MIT
- A FLEx export (`producer="SIL.FLEx 8.0.9.41689"`) exercising all FLEx fields —
  the reference file for residue/round-trip tests. **Deliberately not taken**:
  the upstream `audio/Kalimba.mp3` (8.4 MB), `pictures/Desert.jpg`, and
  `others/Hydrangeas.jpg` — Windows sample-file filler with no test value beyond
  existence; media-existence tests use the Moma folder fixture instead. The
  LDML files are carried (never parsed — out of scope) as folder-layout data.

## folder/Moma/ — complete LIFT folder fixture

- **Source**: `sillsdev/flashgrab` `tests/Moma/{Moma.lift, audio/*.wav, pictures/*.png}`
- **Commit**: `b75f7e2fa178aa27f1fd6c7789032f2087e3e0a7` (HEAD of default branch
  at fetch time)
- **License**: see flag above (flashgrab/Anki)
- A WeSay-produced lexicon (`producer="Palaso.DictionaryServices.LiftWriter"`,
  `version="0.13"`) with real referenced media: 5 wav + 2 png, including
  `pictures/cultural law.png` (space in filename). The file has a UTF-8 BOM and
  tab-indented attribute-per-line formatting — a byte-fidelity edge case.
  Upstream `Moma.WeSayConfig` not taken (not LIFT). Primary fixture for
  media_refs()/missing_media() (milestone M3).

## misc/sample.lift

- **Source**: `sillsdev/LiftTweaker` `sample/sample.lift`
- **Commit**: `b7857369ccca99884c911515b8ad46cd7ba0155c` (HEAD of default branch
  at fetch time)
- **License**: none in repo (see flag above)
- **Note**: contrary to the Phase 1 triage note, this file is
  `<lift version="0.12">` (`producer="SIL.FLEx 2.4.0.39737"`), so
  `migrate_corpus.py` also produces `misc/sample.0.13.lift` from it.

## large/sango/ — real 3507-entry FLEx export

- **Source**: `sil-car/lift-utils` `tests/data/sango/{sango.lift, sango.lift-ranges}`
- **Commit**: `3b2359defe6c4ac0c223864cdcff8925778538b9` (HEAD of default branch
  at fetch time)
- **License**: MIT
- 4.8 MB / 3507 entries (`producer="SIL.FLEx 9.1.15.658"`, `version="0.13"`) +
  1.5 MB ranges companion. Credit Nate Marti (SIL Cameroon) if used in any
  published material (decision D1). Upstream `WritingSystems/` not taken (the
  AllFLExFields fixture already covers LDML-carry).

## Not fetchable as files

- **chorus / LiftTools test data** (corpus plan §C.4): verified at the Phase 1
  pinned SHAs (`7313dd6…`, `f3e87cc…`) that neither repo contains any standalone
  `.lift`/`.lift-ranges` file — their LIFT test data is inline C# strings. The
  C# suites remain a behavioral oracle; targeted extraction into
  `negative/`/edge-case fixtures happens per-milestone (§C.5, M4).
- **libpalaso inline edge-case XML** (§C.5): extracted per-milestone as needed.
- **Enggano export** (§C.8): license/permission check pending; not fetched.

## generated/ — synthetic large files (not committed)

Produced by `tests/tools/generate_large.py` for streaming/perf tests (M6);
git-ignored, regenerated on demand.

## negative/ — invalid fixtures (milestone M4)

Hand-authored schema-invalid / semantically-broken files; authored with the
validator (§C.7), each documenting the defect it carries.
