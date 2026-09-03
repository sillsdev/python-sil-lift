"""Direct tests for the byte-region scanner's happy path and its conservative
bail-out branches.

``_scan.scan`` underpins byte-identity reuse: it returns a ``ScanResult``
locating each root child's exact bytes, or ``None`` for anything it cannot scan
safely (malformed/truncated markup, DOCTYPE, or an unterminated construct), in
which case the writer falls back to canonical serialization. The corpus is all
well-formed LIFT, so those ``None`` paths were previously unexercised; these
tests feed hand-crafted byte strings to prove the safety net actually fires.
"""

from __future__ import annotations

from sil_lift._scan import ScanResult, scan

# --- happy path (incl. exotic-but-valid CDATA / processing instruction /
# self-closing root and child / ">" inside an attribute value) ---


def test_scans_simple_document() -> None:
    data = b'<?xml version="1.0"?>\n<lift version="0.13"><entry id="a"></entry></lift>'
    result = scan(data)
    assert result is not None
    assert isinstance(result, ScanResult)
    assert not result.root_self_closing
    assert [c.tag for c in result.children] == ["entry"]
    region = result.children[0]
    assert data[region.start : region.end] == b'<entry id="a"></entry>'


def test_gt_inside_an_attribute_value_is_not_the_tag_end() -> None:
    """What ``_tag_end``'s quote tracking is for: searching for the delimiter
    instead ends the root's open tag inside the attribute value."""
    data = b'<lift version="0.13" note="a>b"><entry id="c" note="x>y"></entry></lift>'
    result = scan(data)
    assert result is not None
    root = data[result.root_open_start : result.root_open_end]
    assert root == b'<lift version="0.13" note="a>b">'
    region = result.children[0]
    assert data[region.start : region.end] == b'<entry id="c" note="x>y"></entry>'


def test_self_closing_root_returns_empty_children() -> None:
    result = scan(b'<lift version="0.13"/>')
    assert result is not None
    assert result.root_self_closing
    assert result.children == []


def test_self_closing_root_child_gets_the_element_as_its_region() -> None:
    """The child half of the empty-element rule ``_scan.end_element`` explains.

    The self-closing *root* above appends no region, so only this reaches the
    branch that produces one, and a sibling after it is pushed by the same
    mistake.
    """
    data = b'<lift version="0.13"><header/><entry id="a"></entry></lift>'
    result = scan(data)
    assert result is not None
    assert [c.tag for c in result.children] == ["header", "entry"]
    header, entry = result.children
    assert data[header.start : header.end] == b"<header/>"
    assert data[entry.start : entry.end] == b'<entry id="a"></entry>'


def test_self_closing_child_with_a_gt_in_an_attribute() -> None:
    """Where the two rules meet: an empty child's region is its start tag.

    Its ``end`` comes from the measured tag end rather than from the end
    event, so a tag end that stopped inside the attribute value would corrupt
    the region itself. Below the root, this is the only case that does.
    """
    data = b'<lift version="0.13"><entry id="c" note="x>y"/></lift>'
    result = scan(data)
    assert result is not None
    region = result.children[0]
    assert data[region.start : region.end] == b'<entry id="c" note="x>y"/>'


def test_cdata_root_child_is_skipped() -> None:
    data = b'<lift version="0.13"><![CDATA[<not a tag>]]><entry id="a"></entry></lift>'
    result = scan(data)
    assert result is not None
    assert [c.tag for c in result.children] == ["entry"]


def test_cdata_inside_element_is_skipped() -> None:
    data = b'<lift version="0.13"><entry id="a"><![CDATA[</entry>]]></entry></lift>'
    result = scan(data)
    assert result is not None
    # The CDATA-embedded "</entry>" must not be mistaken for the real end tag.
    region = result.children[0]
    assert data[region.start : region.end] == b'<entry id="a"><![CDATA[</entry>]]></entry>'


def test_processing_instructions_are_skipped() -> None:
    data = b'<lift version="0.13"><?php ?><entry id="a"><?pi?></entry></lift>'
    result = scan(data)
    assert result is not None
    assert [c.tag for c in result.children] == ["entry"]


def test_comment_root_child_is_skipped() -> None:
    data = b'<lift version="0.13"><!-- note --><entry id="a"></entry></lift>'
    result = scan(data)
    assert result is not None
    assert [c.tag for c in result.children] == ["entry"]


def test_nested_same_name_elements_track_depth() -> None:
    data = b'<lift version="0.13"><entry id="a"><entry id="inner"/></entry></lift>'
    result = scan(data)
    assert result is not None
    assert len(result.children) == 1
    region = result.children[0]
    assert data[region.start : region.end].endswith(b"</entry>")


# --- conservative bail-outs: every one must return None ---


def test_no_markup_at_all() -> None:
    assert scan(b"no markup here") is None


def test_doctype_in_prolog() -> None:
    assert scan(b'<!DOCTYPE lift>\n<lift version="0.13"></lift>') is None


def test_doctype_as_root_child() -> None:
    assert scan(b'<lift version="0.13"><!DOCTYPE x><entry id="a"/></lift>') is None


def test_doctype_inside_element() -> None:
    assert scan(b'<lift version="0.13"><entry id="a"><!ENTITY x></entry></lift>') is None


def test_truncated_root_open_tag() -> None:
    assert scan(b'<lift version="0.13"') is None


def test_truncated_child_start_tag() -> None:
    assert scan(b'<lift version="0.13"><entry id="a"') is None


def test_truncated_child_end_tag() -> None:
    assert scan(b'<lift version="0.13"><entry id="a"></entry') is None


def test_unclosed_nested_element() -> None:
    assert scan(b'<lift version="0.13"><entry id="a"><sense>') is None


def test_missing_root_close_tag() -> None:
    assert scan(b'<lift version="0.13"><entry id="a"></entry>') is None


def test_unterminated_comment_in_prolog() -> None:
    assert scan(b"<!-- never closed") is None


def test_unterminated_comment_root_child() -> None:
    assert scan(b'<lift version="0.13"><!-- never closed') is None


def test_unterminated_comment_inside_element() -> None:
    assert scan(b'<lift version="0.13"><entry id="a"><!-- never closed</entry></lift>') is None
