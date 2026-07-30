"""Tests for the Extras debug accessors (__repr__ and to_string).

The fidelity tests already exercise carrying out-of-schema content through the
reader/writer; these cover the two human-readable helpers, which no round-trip
test invokes.
"""

from __future__ import annotations

from sil_lift._extras import Extras, _ExtraNode


def test_empty_extras_is_falsy_with_bare_repr() -> None:
    extras = Extras()
    assert not extras
    assert repr(extras) == "Extras()"
    assert extras.to_string() == ""


def test_populated_extras_repr_counts_attrs_and_nodes() -> None:
    extras = Extras(
        _attrs={"lang": "en", "type": "note"},
        _nodes=[_ExtraNode(kind="comment", xml="<!-- c -->", index=0)],
    )
    assert extras
    assert repr(extras) == "Extras(2 attrs, 1 nodes)"


def test_to_string_dumps_attrs_then_nodes() -> None:
    extras = Extras(
        _attrs={"lang": "en"},
        _nodes=[_ExtraNode(kind="element", xml="<x/>", index=0)],
    )
    assert extras.to_string() == "@lang='en'\n<x/>"
