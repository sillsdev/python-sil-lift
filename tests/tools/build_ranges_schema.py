"""Author schemas/lift-ranges-0.13.rng from the vendored lift-0.13.rng.

No known schema for standalone ``.lift-ranges`` exists: the LIFT RNG defines
``<ranges>`` only inside ``<header>``. This tool builds one by copying the
relevant ``<define>`` blocks verbatim from the vendored grammar and adding a
``<lift-ranges>`` root, so the range content model stays byte-faithful to the
spec's.

Usage: python tests/tools/build_ranges_schema.py
"""

import re
import sys
from pathlib import Path

SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "src" / "sil_lift" / "schemas"
SOURCE = SCHEMAS_DIR / "lift-0.13.rng"
TARGET = SCHEMAS_DIR / "lift-ranges-0.13.rng"

# range-content and everything it transitively references.
DEFINES = [
    "date.or.dateTime",
    "span-content",
    "inner-span-content",
    "form-content",
    "form-no-lang-content",
    "multitext-content",
    "annotation-content",
    "range-content",
    "range-element-content",
]

HEADER = """\
<?xml version="1.0" encoding="UTF-8"?>
<!--
  RELAX NG grammar for standalone .lift-ranges documents (LIFT 0.13).

  Authored by the sil-lift project: the LIFT 0.13 grammar has no root element
  for a ranges-only document, yet FieldWorks and The Combine write them
  routinely. The <define> blocks below are copied verbatim from lift-0.13.rng
  (see PROVENANCE.md in this directory) so the content model is exactly the
  spec's; only the <lift-ranges> root is new.
-->
"""


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8")
    grammar_match = re.match(r"(<grammar[^>]*>)", source.lstrip())
    if grammar_match is None:
        print("cannot find <grammar> open tag in the vendored schema")
        return 1
    blocks: list[str] = []
    for name in DEFINES:
        pattern = rf'<define name="{re.escape(name)}"[^>]*>.*?</define>'
        match = re.search(pattern, source, re.S)
        if match is None:
            print(f"define {name!r} not found in the vendored schema")
            return 1
        blocks.append("  " + match.group(0))
    start = (
        "  <start>\n"
        '    <element name="lift-ranges">\n'
        "      <zeroOrMore>\n"
        '        <element name="range">\n'
        '          <ref name="range-content"/>\n'
        "        </element>\n"
        "      </zeroOrMore>\n"
        "    </element>\n"
        "  </start>\n"
    )
    body = "\n\n".join(blocks)
    TARGET.write_text(
        f"{HEADER}{grammar_match.group(1)}\n\n{start}\n{body}\n\n</grammar>\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
