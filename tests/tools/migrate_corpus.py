"""Corpus prep: migrate the 0.12 fixtures to 0.13 (tooling, not a library feature).

Applies the upstream migration XSLT (vendored at tests/tools/xslt/, provenance in
tests/corpus/PROVENANCE.md) to:

- tests/corpus/spec-examples/0.12/*.lift  ->  tests/corpus/spec-examples/0.13/
- tests/corpus/misc/sample.lift           ->  tests/corpus/misc/sample.0.13.lift

Output honors the stylesheet's <xsl:output> settings, then each result is checked
against the vendored 0.13 RELAX NG schema; failures are reported but still written
(so they can be inspected).

Some source files are inherently schema-invalid in ways migration cannot (and must
not) fix — see "Known RNG-invalid fixtures" in tests/corpus/PROVENANCE.md. Those are
listed in EXPECTED_INVALID; the script exits nonzero only on unexpected results.

Usage: python tests/tools/migrate_corpus.py
"""

import sys
from pathlib import Path

from lxml import etree

TOOLS_DIR = Path(__file__).resolve().parent
CORPUS_DIR = TOOLS_DIR.parent / "corpus"
XSL_PATH = TOOLS_DIR / "xslt" / "LIFT-0.12-0.13.xsl"
RNG_PATH = TOOLS_DIR.parents[1] / "src" / "sil_lift" / "schemas" / "lift-0.13.rng"

EXPECTED_INVALID = {
    "dialects.lift",  # <form> without @lang inside <etymology>
    "fields any order.lift",  # same
    "header.lift",  # range/@href "file://C:/..." fails the anyURI datatype
    "sample.0.13.lift",  # same
}


def migrate(src: Path, dst: Path, transform: etree.XSLT, schema: etree.RelaxNG) -> bool:
    result = transform(etree.parse(src))
    dst.parent.mkdir(parents=True, exist_ok=True)
    # lxml-stubs is missing write_output(); it's the one API that honors <xsl:output>.
    result.write_output(str(dst))  # type: ignore[attr-defined]
    if schema.validate(etree.parse(dst)):
        print(f"  ok      {src.name} -> {dst.relative_to(CORPUS_DIR)}")
        return True
    print(f"  INVALID {src.name} -> {dst.relative_to(CORPUS_DIR)}")
    for error in schema.error_log:
        print(f"          {error.line}: {error.message}")
    return False


def main() -> int:
    transform = etree.XSLT(etree.parse(XSL_PATH))
    schema = etree.RelaxNG(etree.parse(RNG_PATH))

    jobs: list[tuple[Path, Path]] = [
        (src, CORPUS_DIR / "spec-examples" / "0.13" / src.name)
        for src in sorted((CORPUS_DIR / "spec-examples" / "0.12").glob("*.lift"))
    ]
    jobs.append((CORPUS_DIR / "misc" / "sample.lift", CORPUS_DIR / "misc" / "sample.0.13.lift"))

    unexpected: list[str] = []
    for src, dst in jobs:
        valid = migrate(src, dst, transform, schema)
        if valid == (dst.name in EXPECTED_INVALID):
            unexpected.append(dst.name)
    print(f"{len(jobs)} migrated, {len(EXPECTED_INVALID)} known-invalid expected")
    if unexpected:
        print(f"UNEXPECTED validity change: {', '.join(unexpected)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
