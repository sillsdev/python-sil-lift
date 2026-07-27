# Schema provenance

## lift-0.13.rng

- **Source**: `sillsdev/lift-standard`, path `LIFTDotNet/LiftIO/Validation/lift-0.13.rng`
- **Commit**: `328bb2770042bd012abd6a903edda705a273386c` (master)
- **Fetched**: 2026-07-27, byte-identical copy (17,885 bytes); stored with git
  line-ending normalization disabled (`.gitattributes`)
- **Note**: this is the operative LIFT 0.13 grammar. The same content (modulo
  whitespace/comment ordering) is embedded as `lift.rng` in both the spec repo's
  LiftIO and libpalaso's `SIL.Lift/Validation/` and used by the C# `Validator`.
- **License**: MIT — `sillsdev/lift-standard` carries a
  [LICENSE](https://github.com/sillsdev/lift-standard/blob/master/LICENSE)
  compatible with this package's own MIT license.

## lift-ranges-0.13.rng

- **Source**: `sillsdev/lift-standard`, path
  `LIFTDotNet/LiftIO/Validation/lift-ranges-0.13.rng`
- **Commit**: `328bb2770042bd012abd6a903edda705a273386c` (master)
- **Fetched**: 2026-07-27, byte-identical copy (4,250 bytes); stored with git
  line-ending normalization disabled (`.gitattributes`)
- **Note**: covers standalone `.lift-ranges` documents, which the base LIFT
  0.13 grammar doesn't (it only defines `<ranges>` inside `<header>`). Its
  `<define>` blocks are copied verbatim from `lift-0.13.rng` so the content
  model matches the spec exactly; only the `<lift-ranges>` root is new.
- **License**: MIT — `sillsdev/lift-standard` carries a
  [LICENSE](https://github.com/sillsdev/lift-standard/blob/master/LICENSE)
  compatible with this package's own MIT license.
