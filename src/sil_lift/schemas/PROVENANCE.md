# Schema provenance

## lift-0.13.rng

- **Source**: `sillsdev/lift-standard`, path `LIFTDotNet/LiftIO/Validation/lift-0.13.rng`
- **Commit**: `39a83be083174a40dff5b7bacac86b4f5e68afe4` (master)
- **Fetched**: 2026-07-14, byte-identical copy (17,885 bytes); stored with git
  line-ending normalization disabled (`.gitattributes`)
- **Note**: this is the operative LIFT 0.13 grammar. The same content (modulo
  whitespace/comment ordering) is embedded as `lift.rng` in both the spec repo's
  LiftIO and libpalaso's `SIL.Lift/Validation/` and used by the C# `Validator`.
- **License**: MIT — `sillsdev/lift-standard` carries a
  [LICENSE](https://github.com/sillsdev/lift-standard/blob/master/LICENSE)
  compatible with this package's own MIT license.

## lift-ranges-0.13.rng

- **Source**: authored by this project — no schema for standalone
  `.lift-ranges` files exists upstream. Built from the `range`/`range-element`
  defines of the vendored `lift-0.13.rng` so the content model matches the
  spec exactly (regenerate with `tests/tools/build_ranges_schema.py`).
- **License**: MIT — this project's own `LICENSE`.
