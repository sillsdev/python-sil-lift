"""Tests for the Extras debug accessors (__repr__ and to_string).

The fidelity tests already exercise carrying out-of-schema content through the
reader/writer; these cover the two human-readable helpers, which no round-trip
test invokes.

The residue under test is produced by parsing hand-written documents rather than
by populating Extras' fields directly, so everything asserted here is reachable
from the public surface (construction, bool, repr, to_string, equality) that
`_extras`' module docstring promises while leaving the internal representation
swappable.
"""

from __future__ import annotations

from pathlib import Path

import sil_lift
from sil_lift import Extras, Lexicon

# One of every residue shape repr and to_string report -- unknown attributes, an
# unknown child element, and a comment -- all on a single entry.
RESIDUE = b"""<?xml version="1.0" encoding="UTF-8"?>
<lift version="0.13">
<entry id="one" x-flavor="strawberry" x-color="red">
<lexical-unit><form lang="en"><text>one</text></form></lexical-unit>
<!-- note --><x-unknown a="1">payload</x-unknown>
</entry>
</lift>
"""

# The same residue on both entries, at different child positions.
MOVED_RESIDUE = b"""<?xml version="1.0" encoding="UTF-8"?>
<lift version="0.13">
<entry id="one" x-flavor="strawberry">
<lexical-unit><form lang="en"><text>one</text></form></lexical-unit>
<x-unknown a="1">payload</x-unknown>
</entry>
<entry id="two" x-flavor="strawberry">
<x-unknown a="1">payload</x-unknown>
<lexical-unit><form lang="en"><text>two</text></form></lexical-unit>
</entry>
</lift>
"""


def _load(tmp_path: Path, data: bytes) -> Lexicon:
    path = tmp_path / "residue.lift"
    path.write_bytes(data)
    return sil_lift.load(path)


def test_empty_extras_is_falsy_with_bare_repr() -> None:
    extras = Extras()
    assert not extras
    assert repr(extras) == "Extras()"
    assert extras.to_string() == ""


def test_node_without_residue_has_empty_extras(tmp_path: Path) -> None:
    lexicon = _load(tmp_path, RESIDUE)
    assert not lexicon.extra
    assert repr(lexicon.extra) == "Extras()"


def test_populated_extras_repr_counts_attrs_and_nodes(tmp_path: Path) -> None:
    entry = _load(tmp_path, RESIDUE).entries[0]
    assert entry.extra
    assert repr(entry.extra) == "Extras(2 attrs, 2 nodes)"


def test_to_string_dumps_every_carried_item_one_per_line(tmp_path: Path) -> None:
    """Attributes render as @name='value', nodes as their XML, one item per line.

    Their order is deliberately not asserted: to_string is a debug dump, not a
    serialization format, so how residue collection happens to order attributes
    and nodes today is not something callers may rely on.
    """
    entry = _load(tmp_path, RESIDUE).entries[0]
    assert sorted(entry.extra.to_string().splitlines()) == sorted(
        [
            "@x-flavor='strawberry'",
            "@x-color='red'",
            "<!-- note -->",
            '<x-unknown a="1">payload</x-unknown>',
        ]
    )


def test_same_residue_at_different_positions_is_equal(tmp_path: Path) -> None:
    """Child position is a re-emit anchor, not content -- it is not compared."""
    one, two = _load(tmp_path, MOVED_RESIDUE).entries
    assert one.extra == two.extra
