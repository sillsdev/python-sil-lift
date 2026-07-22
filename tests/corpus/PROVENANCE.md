# Test corpus provenance

All files fetched 2026-07-14 as byte-identical copies from public GitHub repos at
the commits recorded below (raw.githubusercontent.com at pinned SHA). Git
line-ending normalization is disabled for everything under `tests/corpus/`
(`.gitattributes`) — fidelity tests depend on the bytes staying exactly as fetched.

Files under `tests/corpus/` retain their upstream licenses (recorded per
fixture below) and are **not** covered by this repository's MIT license.

**License review (2026-07-22, re-verified against the live repos)**:
`lift-standard` and `LiftTweaker` carry MIT LICENSE files; `flashgrab`'s
LICENSE reads "Free and open source, under Anki's license" (Anki is
AGPL-3.0). All are SIL-authored repos, so carrying their fixtures in this SIL
repo with provenance is fine. And the sdist excludes `tests/` (pyproject
`[tool.hatch.build.targets.sdist]`) so release artifacts ship none of them.
The only required exclusion is for the flashgrab/Moma fixture, whose LICENSE
ambiguously defers to Anki's AGPL-3.0 (unsafe to bundle in an MIT release).
flashgrab license/attribution cleanup is the remaining open ask, tracked at
https://github.com/sillsdev/flashgrab/issues/20.

## spec-examples/0.12/ — 19 files

- **Source**: `sillsdev/lift-standard` `examples/*.lift`
- **Commit**: `39a83be083174a40dff5b7bacac86b4f5e68afe4` (master)
- **License**: MIT (see flag above)
- All are `<lift version="0.12">`, small (≤205 lines). Includes
  `fields any order.lift` (filename with a space — path-handling edge case).
  The upstream `VerifyExamples.proj` (MSBuild/Jing harness) was not taken —
  not corpus data. These originals also serve as version-guard fixtures
  (the library rejects non-0.13 input).

## spec-examples/0.13/ — generated

Produced from `spec-examples/0.12/` by `tests/tools/migrate_corpus.py` using the
vendored upstream XSLT (`tests/tools/xslt/LIFT-0.12-0.13.xsl`). Regenerate with
that script; committed so tests don't depend on regeneration.

## ranges/ — test20080407 pair

- **Source**: `sillsdev/lift-standard` `LIFTDotNet/LiftIO.Tests/test20080407.lift`
  \+ `.lift-ranges`
- **Commit**: `39a83be083174a40dff5b7bacac86b4f5e68afe4`
- **License**: MIT (see flag above)
- The only known `.lift` \+ external `.lift-ranges` sample pair; primary ranges
  fixture. `version="0.13"`, `producer="hand crafted"`.

## flex/AllFLExFields/ — FLEx-flavored 0.13 reference fixture

- **Source**: `sillsdev/web-languageforge`
  `sample_data/lift/AllFLExFields/{AllFLExFields.lift, AllFLExFields.lift-ranges,WritingSystems/{en,fr,th}.ldml}`
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
  `version="0.13"`) with real referenced media: 5 wav \+ 2 png, including
  `pictures/cultural law.png` (space in filename). The file has a UTF-8 BOM and
  tab-indented attribute-per-line formatting — a byte-fidelity edge case.
  Upstream `Moma.WeSayConfig` not taken (not LIFT). Primary fixture for
  media_refs()/missing_media().

## misc/sample.lift

- **Source**: `sillsdev/LiftTweaker` `sample/sample.lift`
- **Commit**: `b7857369ccca99884c911515b8ad46cd7ba0155c` (HEAD of default branch
  at fetch time)
- **License**: MIT (see flag above)
- **Note**: this file is `<lift version="0.12">`
  (`producer="SIL.FLEx 2.4.0.39737"`), so `migrate_corpus.py` also produces
  `misc/sample.0.13.lift` from it.

## large/sango/ — real 3507-entry FLEx export

- **Source**: `sil-car/lift-utils` `tests/data/sango/{sango.lift, sango.lift-ranges}`
- **Commit**: `3b2359defe6c4ac0c223864cdcff8925778538b9` (HEAD of default branch
  at fetch time)
- **License**: MIT
- 4.8 MB / 3507 entries (`producer="SIL.FLEx 9.1.15.658"`, `version="0.13"`) \+
  1.5 MB ranges companion. Credit Nate Marti (SIL Cameroon) if used in any
  published material. Upstream `WritingSystems/` not taken (the AllFLExFields
  fixture already covers LDML-carry).

## Not fetchable as files

- **chorus / LiftTools test data**: verified at pinned SHAs (`7313dd6…`,
  `f3e87cc…`) that neither repo contains any standalone `.lift`/`.lift-ranges`
  file — their LIFT test data is inline C# strings. The C# suites remain a
  behavioral oracle; targeted extraction into `negative/`/edge-case fixtures
  happens as needed.
- **libpalaso inline edge-case XML**: extracted as needed.
- **Enggano export**: license/permission check pending; not fetched.

## Known RNG-invalid fixtures (kept deliberately)

Validated 2026-07-14 against the vendored `lift-0.13.rng` via `lxml.etree.RelaxNG`.
Two real-world quirk classes make some fixtures schema-invalid; they are kept
as-is — the library's losslessness contract must carry exactly this kind of
content, and the validator needs realistic subjects:

1. **`<form>` without `@lang` inside `<etymology>`** — the RNG requires `@lang`
   on every form. Affects: `spec-examples/0.13/dialects.lift`,
   `spec-examples/0.13/fields any order.lift` (and their 0.12 originals).
2. **`range/@href` of the shape `file://C:/...`** — fails the RNG's `anyURI`
   datatype under libxml2 (malformed authority; often unencoded spaces too).
   This is how FLEx actually writes range hrefs: **every real FLEx export in
   this corpus** has it. Affects: `spec-examples/0.13/header.lift`,
   `misc/sample.0.13.lift`, `flex/AllFLExFields/AllFLExFields.lift`,
   `large/sango/sango.lift`.

   **Design implication**: the C# validator's RELAX NG engine evidently did
   not enforce anyURI syntax, so "RNG-valid" per SIL.Lift ≠ RNG-valid per lxml
   on real FLEx output. The validation layer must account for this (e.g.
   downgrade/annotate anyURI-only failures) or it will flag virtually every
   FLEx lexicon.

RNG-valid fixtures: the other 16 migrated spec examples,
`ranges/test20080407.lift`, and `folder/Moma/Moma.lift` (WeSay writes relative
hrefs, which pass). `tests/test_corpus.py` locks in both lists.

3. **`trait`/`field` inside `range-element`** (`.lift-ranges` files, validated
   against the project-authored `lift-ranges-0.13.rng`): FLEx extends range
   elements beyond the spec's description/label/abbrev content model (e.g.
   morph-type traits). Affects `flex/AllFLExFields/AllFLExFields.lift-ranges`
   and `large/sango/sango.lift-ranges`; the hand-crafted
   `ranges/test20080407.lift-ranges` validates. Carried losslessly in
   `Extras`; same implication as the anyURI quirk.

## generated/ — synthetic large files (not committed)

Produced by `tests/tools/generate_large.py` for streaming/perf tests;
git-ignored, regenerated on demand.

## negative/ — invalid fixtures (hand-authored)

Each file carries an XML comment documenting its defect and the expected
Problem code: `duplicate-guid`, `dangling-ref`, `range-parent`,
`undefined-range-value` (2 warnings \+ a clean control entry),
`duplicate-form-lang` (the Schematron-only rule), `schema-invalid`
(structural), `missing-media/` (a folder fixture), and `flex-quirks`
(URI quirks that must yield warnings, never schema errors).
`schema-invalid.lift` and `flex-quirks.lift` are raw-RNG-invalid (the
latter only under libxml2's anyURI check) and appear in the corpus test's
expected-invalid list.
