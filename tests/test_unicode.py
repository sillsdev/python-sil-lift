"""Non-BMP characters and surrogate encodings, end to end.

Python strings are sequences of codepoints, not UTF-16 code units, so a
"surrogate pair" in a UTF-16 source is just one non-BMP codepoint by the time
the model sees it. Nothing in the reader, the byte-region scanner, or the writer
pairs code units — and these tests pin that down, because the fidelity contract
(``docs/en/fidelity.md``) is a byte-level promise and 4-byte UTF-8 sequences are
exactly the input that would break a scanner that guessed at character
boundaries.

Three parts:

- **Non-BMP content is ordinary content**: byte-identical round trips, exact
  scanner regions, verbatim untouched entries under edit, streaming reads and
  writes, and clean validation — in element text, in a span, and in an
  attribute value.
- **A lone surrogate never reaches the model from a file**: neither as a
  numeric character reference (invalid XML) nor as CESU-8/WTF-8 bytes, which
  tools that mishandle UTF-16 internally emit (each surrogate half individually
  UTF-8-encoded instead of paired first). Both are rejected at parse time as
  ``LiftParseError``, not silently mangled.
- **One assigned through the API is refused on the way out**: XML cannot
  represent it in any encoding, so every entry point that serializes raises
  ``LiftWriteError`` naming the node and the codepoint, and validation reports
  it as a ``lone-surrogate`` error rather than crashing.

UTF-16 sources are covered here too: they load, and — being non-ASCII-compatible
— re-serialize canonically as UTF-8 rather than byte-identically, which is the
documented exception, not a defect.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import sil_lift
from sil_lift import LiftError, LiftParseError, LiftWriteError, Span
from sil_lift._scan import scan
from sil_lift._writer import _guarded

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

PARTY = "\U0001f389"  # PARTY POPPER, plane 1 (emoji)
CJK_B = "\U00020000"  # CJK Ext. B ideograph, plane 2
ADLAM = "\U0001e900"  # ADLAM CAPITAL LETTER ALIF, plane 1 (a real orthography)
NON_BMP = PARTY + CJK_B + ADLAM

# Non-BMP codepoints in every place a LIFT document can hold text: an attribute
# value, element text, and a nested <span> run.
NON_BMP_LIFT = f"""<?xml version="1.0" encoding="UTF-8"?>
<lift version="0.13" producer="test_unicode">
<entry id="nb-{NON_BMP}" guid="6b1b7ce6-4b3a-4d16-9a1f-8f1e3b0f2a01">
<lexical-unit><form lang="qaa-x-nb"><text>{ADLAM}{ADLAM}</text></form></lexical-unit>
<sense id="nb_s1">
<gloss lang="en"><text>party <span class="emphasis">{PARTY}</span> {CJK_B}</text></gloss>
</sense>
</entry>
<entry id="ascii" guid="6b1b7ce6-4b3a-4d16-9a1f-8f1e3b0f2a02">
<lexical-unit><form lang="en"><text>ascii</text></form></lexical-unit>
</entry>
</lift>
""".encode()

UTF16_NON_BMP_LIFT = f"""<?xml version="1.0" encoding="UTF-16"?>
<lift version="0.13">
<entry id="nb-{ADLAM}"><lexical-unit><form lang="qaa-x-nb"><text>{NON_BMP}</text></form>\
</lexical-unit></entry>
</lift>
""".encode("utf-16")

# A numeric character reference to a lone surrogate: not a valid XML character,
# whatever the encoding. Written by tools that emit UTF-16 code units as if they
# were codepoints.
LONE_SURROGATE_REF_LIFT = b"""<?xml version="1.0" encoding="UTF-8"?>
<lift version="0.13">
<entry id="one"><lexical-unit><form lang="en"><text>&#xD800;</text></form></lexical-unit></entry>
</lift>
"""

# CESU-8/WTF-8: U+1F389 as its two UTF-16 halves (U+D83C, U+DF89), each
# UTF-8-encoded on its own instead of paired into one 4-byte sequence. Valid
# UTF-8 would be f0 9f 8e 89.
CESU8_LIFT = (
    b'<?xml version="1.0" encoding="UTF-8"?>\n<lift version="0.13">\n'
    b'<entry id="one"><lexical-unit><form lang="en"><text>'
    b"\xed\xa0\xbc\xed\xbe\x89"
    b"</text></form></lexical-unit></entry>\n</lift>\n"
)


def _write(tmp_path: Path, name: str, data: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(data)
    return path


# --- non-BMP content is ordinary content ---------------------------------------


def test_non_bmp_round_trips_byte_identically(tmp_path: Path) -> None:
    source = _write(tmp_path, "non-bmp.lift", NON_BMP_LIFT)
    lexicon = sil_lift.load(source)

    entry = lexicon.entries[0]
    assert entry.id == f"nb-{NON_BMP}"  # attribute value
    assert str(entry.lexical_unit["qaa-x-nb"]) == ADLAM * 2  # element text
    gloss = entry.senses[0].gloss("en")
    assert gloss is not None
    (span,) = [fragment for fragment in gloss.fragments if isinstance(fragment, Span)]
    assert str(span) == PARTY  # span content
    assert str(gloss) == f"party {PARTY} {CJK_B}"

    out = tmp_path / "out.lift"
    lexicon.save(out)
    assert out.read_bytes() == NON_BMP_LIFT


def test_scanner_regions_land_on_four_byte_utf8_boundaries() -> None:
    """The scanner only ever matches ASCII structural bytes, which no UTF-8
    continuation byte can impersonate — so a 4-byte sequence in an attribute
    value cannot shift a region's start or end."""
    result = scan(NON_BMP_LIFT)
    assert result is not None
    assert [region.tag for region in result.children] == ["entry", "entry"]

    non_bmp_region, ascii_region = result.children
    reused = NON_BMP_LIFT[non_bmp_region.start : non_bmp_region.end]
    assert reused.startswith(f'<entry id="nb-{NON_BMP}"'.encode())
    assert reused.endswith(b"</entry>")
    assert reused.decode()  # a region boundary mid-codepoint would not decode
    assert NON_BMP_LIFT[ascii_region.start : ascii_region.end].startswith(b'<entry id="ascii"')


def test_untouched_non_bmp_entry_stays_verbatim_under_edit(tmp_path: Path) -> None:
    source = _write(tmp_path, "non-bmp.lift", NON_BMP_LIFT)
    lexicon = sil_lift.load(source)
    lexicon.entries[1].lexical_unit["qaa-x-nb"] = CJK_B  # touch the *other* entry

    out = tmp_path / "out.lift"
    lexicon.save(out)
    written = out.read_bytes()

    result = scan(NON_BMP_LIFT)
    assert result is not None
    region = result.children[0]
    assert NON_BMP_LIFT[region.start : region.end] in written
    # The re-serialized entry carries raw UTF-8, not a numeric character
    # reference — the canonical path escapes markup, never non-ASCII text.
    assert CJK_B.encode() in written
    assert b"&#x" not in written

    reloaded = sil_lift.load(out)
    assert reloaded.entries[0] == lexicon.entries[0]
    assert str(reloaded.entries[1].lexical_unit["qaa-x-nb"]) == CJK_B


def test_non_bmp_survives_streaming_read_and_write(tmp_path: Path) -> None:
    source = _write(tmp_path, "non-bmp.lift", NON_BMP_LIFT)
    with sil_lift.open_reader(source) as reader:
        entries = list(reader)
    assert [entry.id for entry in entries] == [f"nb-{NON_BMP}", "ascii"]

    out = tmp_path / "streamed.lift"
    with sil_lift.open_writer(out, producer="test_unicode") as writer:
        for entry in entries:
            writer.write(entry)

    reloaded = sil_lift.load(out)
    assert str(reloaded.entries[0].lexical_unit["qaa-x-nb"]) == ADLAM * 2
    assert reloaded.entries == entries


def test_non_bmp_document_validates_clean(tmp_path: Path) -> None:
    """Non-BMP text is not a validation finding: the model, the RELAX NG layer,
    and the semantic checks all treat it as ordinary character data."""
    source = _write(tmp_path, "non-bmp.lift", NON_BMP_LIFT)
    assert list(sil_lift.iter_problems(source)) == []


# --- lone surrogates never reach the model from a file --------------------------


@pytest.mark.parametrize(
    ("data", "name"),
    [
        (LONE_SURROGATE_REF_LIFT, "lone-surrogate-ref.lift"),
        (CESU8_LIFT, "cesu8.lift"),
    ],
    ids=["character-reference", "cesu-8-bytes"],
)
def test_lone_surrogate_sources_are_rejected(data: bytes, name: str, tmp_path: Path) -> None:
    source = _write(tmp_path, name, data)
    with pytest.raises(LiftParseError, match="not well-formed"):
        sil_lift.load(source)


@pytest.mark.parametrize(
    ("data", "name"),
    [
        (LONE_SURROGATE_REF_LIFT, "lone-surrogate-ref.lift"),
        (CESU8_LIFT, "cesu8.lift"),
    ],
    ids=["character-reference", "cesu-8-bytes"],
)
def test_lone_surrogate_sources_are_rejected_when_streaming(
    data: bytes, name: str, tmp_path: Path
) -> None:
    """Same refusal on the streaming path, which pumps events past the first
    entry at open time and so fails there rather than mid-iteration."""
    source = _write(tmp_path, name, data)
    with (
        pytest.raises(LiftParseError, match="not well-formed"),
        sil_lift.open_reader(source) as reader,
    ):
        list(reader)


# --- UTF-16 sources -------------------------------------------------------------


def test_utf16_source_with_non_bmp_loads_and_saves_as_utf8(tmp_path: Path) -> None:
    """A UTF-16 source loads with its non-BMP content intact; saving falls back
    to canonical UTF-8, the documented byte-identity exception for a
    non-ASCII-compatible encoding."""
    source = _write(tmp_path, "utf16.lift", UTF16_NON_BMP_LIFT)
    lexicon = sil_lift.load(source)
    (entry,) = lexicon.entries
    assert entry.id == f"nb-{ADLAM}"
    assert str(entry.lexical_unit["qaa-x-nb"]) == NON_BMP

    out = tmp_path / "out.lift"
    lexicon.save(out)
    written = out.read_bytes()
    assert written != UTF16_NON_BMP_LIFT, "expected the canonical fallback, not passthrough"
    assert written.startswith(b'<?xml version="1.0" encoding="UTF-8"?>')
    assert NON_BMP.encode() in written  # one 4-byte sequence per codepoint

    reloaded = sil_lift.load(out)
    assert reloaded.entries == lexicon.entries
    # Byte identity resumes once the document is UTF-8: re-saving changes nothing.
    again = tmp_path / "again.lift"
    reloaded.save(again)
    assert again.read_bytes() == written


# --- lone surrogates assigned through the API -----------------------------------

LONE = "a\ud800b"  # the only way in: no LIFT file can carry U+D800


def _lexicon_with_lone_surrogate() -> sil_lift.Lexicon:
    lexicon = sil_lift.Lexicon()
    entry = sil_lift.Entry(id="abat", guid="6b1b7ce6-4b3a-4d16-9a1f-8f1e3b0f2a03")
    entry.lexical_unit["en"] = LONE
    lexicon.entries.append(entry)
    return lexicon


def test_save_refuses_a_lone_surrogate_and_writes_nothing(tmp_path: Path) -> None:
    lexicon = _lexicon_with_lone_surrogate()
    out = tmp_path / "lone.lift"
    with pytest.raises(LiftWriteError) as caught:
        lexicon.save(out)
    message = str(caught.value)
    assert "entry 'abat'" in message  # which node
    assert "U+D800" in message  # which codepoint
    assert not out.exists()
    assert isinstance(caught.value, LiftError)  # catchable with the base class
    assert str(lexicon.entries[0].lexical_unit["en"]) == LONE  # model untouched


def _stream_out(lexicon: sil_lift.Lexicon, path: Path) -> None:
    with sil_lift.open_writer(path) as writer:
        writer.write(lexicon.entries[0])


@pytest.mark.parametrize(
    "call",
    [
        lambda lexicon, path: lexicon.save(path),
        lambda lexicon, path: lexicon.changes(),
        lambda lexicon, path: lexicon.changed_entries(),
        _stream_out,
    ],
    ids=["save", "changes", "changed-entries", "streaming-write"],
)
def test_every_serializing_entry_point_refuses(
    call: Callable[[sil_lift.Lexicon, Path], object], tmp_path: Path
) -> None:
    """Not just save(): the change guard serializes to compare digests, and the
    streaming writer builds the same entry elements. All three used to surface a
    bare UnicodeEncodeError from inside lxml."""
    source = _write(tmp_path, "loaded.lift", NON_BMP_LIFT)
    lexicon = sil_lift.load(source)  # loaded, so the change guard has a baseline
    lexicon.entries[0].lexical_unit["en"] = LONE

    with pytest.raises(LiftWriteError, match=r"U\+D800"):
        call(lexicon, tmp_path / "out.lift")


def test_lone_surrogate_in_the_root_or_a_range_names_that_node(tmp_path: Path) -> None:
    """The refusal covers every node the writer builds, not only entries."""
    lexicon = sil_lift.Lexicon(producer=LONE)
    with pytest.raises(LiftWriteError, match="<lift> root"):
        lexicon.save(tmp_path / "root.lift")

    ranges_file = sil_lift.RangesFile()
    ranges_file.ranges.append(sil_lift.Range(id=f"etymology{LONE}"))
    with pytest.raises(LiftWriteError, match="range 'etymology"):
        ranges_file.save(tmp_path / "companion.lift-ranges")


def test_validation_reports_a_lone_surrogate_instead_of_crashing() -> None:
    """Validation renders the document first, so it cannot check an unrenderable
    one — it reports the reason as its single finding."""
    (problem,) = _lexicon_with_lone_surrogate().iter_problems()
    assert problem.level == "error"
    assert problem.code == "lone-surrogate"
    assert "U+D800" in problem.message


def test_validation_reports_a_lone_surrogate_in_a_companion(tmp_path: Path) -> None:
    """An unwritable companion is addressed to the companion, and the .lift's own
    layers keep running around it."""
    source = _write(tmp_path, "with-companion.lift", NON_BMP_LIFT)
    lexicon = sil_lift.load(source)
    ranges_file = lexicon.add_ranges_file(href="with-companion.lift-ranges")
    ranges_file.add_range("etymology")
    lexicon.save()  # the companion exists on disk, so findings can address it
    ranges_file.add_range(f"borrowed{LONE}")
    # A finding on the .lift side, to show it is still reached.
    lexicon.entries[1].relations.append(sil_lift.Relation(type="synonym", ref="nope"))

    problems = list(lexicon.iter_problems())
    (surrogate,) = [problem for problem in problems if problem.code == "lone-surrogate"]
    assert surrogate.message.startswith("range 'borrowed")
    assert "U+D800" in surrogate.message
    assert surrogate.file is not None
    assert surrogate.file.name == "with-companion.lift-ranges"
    assert "dangling-ref" in {problem.code for problem in problems}


def test_guard_re_raises_anything_that_is_not_a_surrogate() -> None:
    """Nothing else in a str is unencodable as UTF-8, so the guard must not
    relabel a hypothetical other UnicodeEncodeError as a lone surrogate."""
    other = UnicodeEncodeError("ascii", "é", 0, 1, "ordinal not in range(128)")

    def build() -> bytes:
        raise other

    with pytest.raises(UnicodeEncodeError):
        _guarded("entry 'x'", build)
