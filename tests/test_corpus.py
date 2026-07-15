"""Corpus sanity: fixtures stay exactly as PROVENANCE.md documents them.

Every corpus XML file must be well-formed; RNG validity must match the documented
lists (see "Known RNG-invalid fixtures" in tests/corpus/PROVENANCE.md) — a change
in either direction means the corpus or the vendored schema drifted.
"""

from pathlib import Path

import pytest
from lxml import etree

import sil_lift

CORPUS_DIR = Path(__file__).parent / "corpus"
RNG_PATH = Path(sil_lift.__file__).parent / "schemas" / "lift-0.13.rng"

LIFT_FILES = sorted(
    p for p in CORPUS_DIR.rglob("*") if p.suffix in {".lift", ".lift-ranges"} and p.is_file()
)

# Documented in PROVENANCE.md: lang-less etymology forms / file://C:/ range hrefs.
EXPECTED_INVALID = {
    "spec-examples/0.13/dialects.lift",
    "spec-examples/0.13/fields any order.lift",
    "spec-examples/0.13/header.lift",
    "misc/sample.0.13.lift",
    "flex/AllFLExFields/AllFLExFields.lift",
    "large/sango/sango.lift",
}

VALIDATABLE = [
    p
    for p in LIFT_FILES
    # Only version-0.13 .lift documents are subjects of the 0.13 schema:
    # .lift-ranges files have a different root (no schema exists yet — M3 authors
    # one), and the 0.12 originals (spec-examples/0.12/, misc/sample.lift) are
    # version-guard fixtures.
    if p.suffix == ".lift" and "0.12" not in p.parts and p.name != "sample.lift"
]


def corpus_id(path: Path) -> str:
    return path.relative_to(CORPUS_DIR).as_posix()


def test_corpus_is_present() -> None:
    assert len(LIFT_FILES) >= 45  # 19+20 spec examples, pairs, fixtures


@pytest.mark.parametrize("path", LIFT_FILES, ids=corpus_id)
def test_well_formed(path: Path) -> None:
    etree.parse(path)


@pytest.mark.parametrize("path", VALIDATABLE, ids=corpus_id)
def test_rng_validity_matches_provenance(path: Path) -> None:
    schema = etree.RelaxNG(etree.parse(RNG_PATH))
    valid = schema.validate(etree.parse(path))
    expected = corpus_id(path) not in EXPECTED_INVALID
    assert valid == expected, (
        f"{corpus_id(path)}: RNG validity changed (now valid={valid}); "
        "corpus fixtures or vendored schema drifted — see PROVENANCE.md"
    )
