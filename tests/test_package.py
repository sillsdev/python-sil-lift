from pathlib import Path

from lxml import etree

import sil_lift


def test_version() -> None:
    assert sil_lift.__version__


def test_vendored_rng_is_loadable() -> None:
    rng_path = Path(sil_lift.__file__).parent / "schemas" / "lift-0.13.rng"
    schema = etree.RelaxNG(etree.parse(rng_path))
    assert schema is not None
