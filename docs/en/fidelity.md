# Fidelity guarantees

LIFT is an *interchange* format: the cardinal rule is **never drop what you do
not understand**. `sil-lift`'s contract:

- **Untouched entries are written back byte-identical.** Opening a file and
  saving it does not reformat, reorder, or re-escape entries you did not
  modify.
- **Modified entries are re-serialized canonically and completely.** All
  out-of-schema content — unknown elements, unknown attributes, XML comments —
  is preserved in place.

The precise rules (including the short list of documented normalizations at
the document level) will be specified here as the writer lands.
