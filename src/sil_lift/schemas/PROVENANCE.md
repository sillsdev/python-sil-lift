# Schema provenance

## lift-0.13.rng

- **Source**: `sillsdev/lift-standard`, path `LIFTDotNet/LiftIO/Validation/lift-0.13.rng`
- **Commit**: `39a83be083174a40dff5b7bacac86b4f5e68afe4` (master; the commit examined
  throughout Phase 1 research)
- **Fetched**: 2026-07-14, byte-identical copy (17,885 bytes); stored with git
  line-ending normalization disabled (`.gitattributes`)
- **Note**: this is the operative LIFT 0.13 grammar. The same content (modulo
  whitespace/comment ordering) is embedded as `lift.rng` in both the spec repo's
  LiftIO and libpalaso's `SIL.Lift/Validation/` and used by the C# `Validator`.
- **License**: the lift-standard repo has **no license file** (known upstream gap,
  research finding 05). SIL-internal use; resolve with upstream before any public
  release of this package.

## lift-ranges-0.13.rng (planned, milestone M3)

To be authored by this project — no schema for standalone `.lift-ranges` files
exists anywhere (research finding 05). Will reuse the `range`/`range-element`
defines from `lift-0.13.rng`.
