import shutil
import unicodedata
from pathlib import Path

import pytest
from lxml import etree

import sil_lift
from sil_lift import LiftParseError, RangesFile, Text
from sil_lift._model import _normalize_href

CORPUS_DIR = Path(__file__).parent / "corpus"
PAIR_DIR = CORPUS_DIR / "ranges"
SANGO_DIR = CORPUS_DIR / "large" / "sango"


def _copy_pair(src_dir: Path, stem: str, dst: Path) -> Path:
    for suffix in (".lift", ".lift-ranges"):
        shutil.copy(src_dir / f"{stem}{suffix}", dst / f"{stem}{suffix}")
    return dst / f"{stem}.lift"


def test_build_lexicon_and_ranges_from_scratch(tmp_path: Path) -> None:
    lexicon = sil_lift.Lexicon(producer="test")
    entry = sil_lift.Entry(id="e1", guid="77777777-7777-4444-8888-777777777777")
    entry.lexical_unit["seh"] = "kanga"
    sense = sil_lift.Sense(id="s1")
    sense.glosses.append(sil_lift.Form(lang="en", text=Text(["chicken"])))
    sense.traits.append(sil_lift.Trait(name="semantic-domain-ddp4", value="1.6.1.2"))
    entry.senses.append(sense)
    lexicon.entries.append(entry)

    ranges = RangesFile()
    domain = ranges.add_range("semantic-domain-ddp4")
    domain.add_element("1.6.1.2").label["en"] = "Bird"
    lexicon.add_ranges_file(ranges, href="dict.lift-ranges")

    lexicon.save(tmp_path / "dict.lift")
    assert (tmp_path / "dict.lift").is_file()
    assert (tmp_path / "dict.lift-ranges").is_file()
    # add_ranges_file registered the companion in the header.
    assert any(
        r.id == "semantic-domain-ddp4" and r.href == "dict.lift-ranges"
        for r in lexicon.header.ranges
    )

    reloaded = sil_lift.load(tmp_path / "dict.lift")
    assert [r.id for rf in reloaded.ranges_files.values() for r in rf.ranges] == [
        "semantic-domain-ddp4"
    ]
    assert list(reloaded.iter_problems()) == []  # trait value is defined; href resolves


def test_sibling_ranges_file_is_discovered_and_tracked() -> None:
    lexicon = sil_lift.load(PAIR_DIR / "test20080407.lift")
    assert len(lexicon.ranges_files) == 1
    (ranges_file,) = lexicon.ranges_files.values()
    assert ranges_file.path is not None
    assert ranges_file.path.name == "test20080407.lift-ranges"
    assert [r.id for r in ranges_file.ranges] == ["grammatical-info"]
    assert [e.id for e in ranges_file.ranges[0].elements] == ["Adverb", "Noun", "Verb"]


def test_resolve_ranges_false_tracks_nothing() -> None:
    lexicon = sil_lift.load(PAIR_DIR / "test20080407.lift", resolve_ranges=False)
    assert lexicon.ranges_files == {}


def test_pair_roundtrips_byte_identically(tmp_path: Path) -> None:
    lift_path = _copy_pair(PAIR_DIR, "test20080407", tmp_path)
    lexicon = sil_lift.load(lift_path)
    lexicon.save()
    for suffix in (".lift", ".lift-ranges"):
        name = f"test20080407{suffix}"
        assert (tmp_path / name).read_bytes() == (PAIR_DIR / name).read_bytes(), name


def test_save_to_new_directory_carries_companions(tmp_path: Path) -> None:
    lexicon = sil_lift.load(PAIR_DIR / "test20080407.lift")
    target_dir = tmp_path / "elsewhere"
    target_dir.mkdir()
    lexicon.save(target_dir / "test20080407.lift")
    assert (target_dir / "test20080407.lift").read_bytes() == (
        PAIR_DIR / "test20080407.lift"
    ).read_bytes()
    assert (target_dir / "test20080407.lift-ranges").read_bytes() == (
        PAIR_DIR / "test20080407.lift-ranges"
    ).read_bytes()
    # The tracking dict must be re-keyed to the companions' new locations.
    assert set(lexicon.ranges_files) == {(target_dir / "test20080407.lift-ranges").resolve()}


def test_save_to_the_same_directory_spelled_differently_keeps_companions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A relative target naming the load directory is not a relocation.

    The companion lives in a subfolder, so a spurious relocation would split it
    in two: the edit would land beside the .lift while the header href still
    points at the now-stale original.
    """
    subfolder = tmp_path / "sub"
    subfolder.mkdir()
    (tmp_path / "dict.lift").write_bytes(
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<lift version="0.13"><header><ranges>'
        b'<range id="grammatical-info" href="sub/shared.lift-ranges"/>'
        b"</ranges></header></lift>\n"
    )
    shutil.copy(PAIR_DIR / "test20080407.lift-ranges", subfolder / "shared.lift-ranges")

    lexicon = sil_lift.load(tmp_path / "dict.lift")
    (ranges_file,) = lexicon.ranges_files.values()
    ranges_file.ranges[0].elements[0].label["en"] = Text(["edited"])
    monkeypatch.chdir(tmp_path)
    lexicon.save("dict.lift")

    assert not (tmp_path / "shared.lift-ranges").exists()
    assert b"edited" in (subfolder / "shared.lift-ranges").read_bytes()
    assert set(lexicon.ranges_files) == {(subfolder / "shared.lift-ranges").resolve()}


def test_ranges_edit_saves_back_to_the_right_file(tmp_path: Path) -> None:
    lift_path = _copy_pair(SANGO_DIR, "sango", tmp_path)
    lexicon = sil_lift.load(lift_path)
    (ranges_file,) = lexicon.ranges_files.values()
    assert len(ranges_file.ranges) == 16

    target = ranges_file.find("etymology")
    assert target is not None
    target.elements[0].label["en"] = Text(["borrowed (edited)"])
    lexicon.save()

    # The .lift itself is untouched -> byte-identical.
    assert (tmp_path / "sango.lift").read_bytes() == (SANGO_DIR / "sango.lift").read_bytes()
    # The ranges file changed, but every untouched range kept its exact bytes.
    original = (SANGO_DIR / "sango.lift-ranges").read_bytes()
    result = (tmp_path / "sango.lift-ranges").read_bytes()
    assert result != original
    from sil_lift._scan import scan

    scanned = scan(original)
    assert scanned is not None
    range_regions = [r for r in scanned.children if r.tag == "range"]
    assert len(range_regions) == 16
    for region in range_regions[1:]:  # etymology is the first range in the file
        assert original[region.start : region.end] in result

    reloaded = RangesFile.load(tmp_path / "sango.lift-ranges")
    edited = reloaded.find("etymology")
    assert edited is not None
    assert str(edited.elements[0].label["en"]) == "borrowed (edited)"


def test_all_ranges_merges_inline_and_external() -> None:
    lexicon = sil_lift.load(PAIR_DIR / "test20080407.lift")
    merged = lexicon.all_ranges()
    # External definition (only in the .lift-ranges file):
    assert [e.id for e in merged["grammatical-info"].elements] == ["Adverb", "Noun", "Verb"]
    # Inline definitions in the header keep winning:
    inline_ids = {r.id for r in lexicon.header.ranges if r.elements}
    for range_id in inline_ids:
        assert merged[range_id] is next(r for r in lexicon.header.ranges if r.id == range_id)


def test_all_ranges_resolves_flex_href_basenames() -> None:
    lexicon = sil_lift.load(CORPUS_DIR / "flex" / "AllFLExFields" / "AllFLExFields.lift")
    # Every header range is href-only (dangling file://C:/ URI); resolution
    # falls back to the basename sibling.
    assert len(lexicon.ranges_files) == 1
    merged = lexicon.all_ranges()
    grammatical = merged["grammatical-info"]
    assert grammatical.elements, "external definition should supply the elements"
    assert any(e.id == "Noun" for e in grammatical.elements)


def test_flex_range_element_extensions_are_carried() -> None:
    """FLEx writes trait/field inside range-element (out of schema, see PROVENANCE)."""
    ranges_file = RangesFile.load(SANGO_DIR / "sango.lift-ranges")
    with_residue = [
        element for range_ in ranges_file.ranges for element in range_.elements if element.extra
    ]
    assert with_residue, "expected FLEx trait/field extensions to land in Extras"


def test_ranges_file_version_guard() -> None:
    with pytest.raises(LiftParseError, match="lift-ranges"):
        RangesFile.load(PAIR_DIR / "test20080407.lift")  # a .lift is not a ranges doc


def test_ranges_schema_is_loadable_and_spec_faithful() -> None:
    schema_path = Path(sil_lift.__file__).parent / "schemas" / "lift-ranges-0.13.rng"
    schema = etree.RelaxNG(etree.parse(schema_path))
    assert schema.validate(etree.parse(PAIR_DIR / "test20080407.lift-ranges"))
    # FLEx files carry out-of-schema extensions (documented in PROVENANCE.md).
    assert not schema.validate(etree.parse(SANGO_DIR / "sango.lift-ranges"))
    assert not schema.validate(
        etree.parse(CORPUS_DIR / "flex" / "AllFLExFields" / "AllFLExFields.lift-ranges")
    )


def test_media_refs_and_missing_media_on_moma_folder() -> None:
    lexicon = sil_lift.load(CORPUS_DIR / "folder" / "Moma" / "Moma.lift")
    refs = list(lexicon.media_refs())
    assert {r.href for r in refs} == {"pictures\\cultural law.png", "pictures\\sdd.png"}
    assert all(r.kind == "illustration" for r in refs)
    assert all(r.entry_id for r in refs)
    assert lexicon.missing_media() == []


def test_missing_media_on_all_flex_fields() -> None:
    # The corpus deliberately omits the upstream filler media (PROVENANCE.md),
    # so these references must be reported missing.
    lexicon = sil_lift.load(CORPUS_DIR / "flex" / "AllFLExFields" / "AllFLExFields.lift")
    missing = {(r.kind, r.href) for r in lexicon.missing_media()}
    assert ("media", "Kalimba.mp3") in missing
    assert ("illustration", "Desert.jpg") in missing


def test_missing_media_flags_broken_ref(tmp_path: Path) -> None:
    src = CORPUS_DIR / "folder" / "Moma"
    shutil.copytree(src, tmp_path / "Moma")
    lexicon = sil_lift.load(tmp_path / "Moma" / "Moma.lift")
    (tmp_path / "Moma" / "pictures" / "sdd.png").unlink()
    missing = lexicon.missing_media()
    assert [r.href for r in missing] == ["pictures\\sdd.png"]


def _write_case_variant_pair(folder: Path, lift_name: str, ranges_name: str) -> Path:
    """A loadable .lift plus companion under arbitrary filename spellings.

    Deliberately not named after the fixture, so the header's ``range/@href``
    basename candidate finds nothing — only the sibling candidate resolves these.
    """
    folder.mkdir(parents=True, exist_ok=True)
    (folder / lift_name).write_bytes((PAIR_DIR / "test20080407.lift").read_bytes())
    (folder / ranges_name).write_bytes((PAIR_DIR / "test20080407.lift-ranges").read_bytes())
    return folder / lift_name


def _write_lift_with_href(folder: Path, lift_name: str, href: str) -> Path:
    """The fixture .lift under another name, its companion href rewritten."""
    folder.mkdir(parents=True, exist_ok=True)
    source = (PAIR_DIR / "test20080407.lift").read_bytes()
    patched = source.replace(b'"file://test20080407.lift-ranges"', f'"{href}"'.encode())
    assert patched != source, "fixture href changed; the replacement no longer matches"
    (folder / lift_name).write_bytes(patched)
    return folder / lift_name


def _case_sensitive_filesystem(folder: Path) -> bool:
    probe = folder / "CaseProbe"
    probe.mkdir(exist_ok=True)
    sensitive = not (folder / "caseprobe").exists()
    probe.rmdir()
    return sensitive


def test_companion_resolves_when_lift_suffix_is_uppercase(tmp_path: Path) -> None:
    lift = _write_case_variant_pair(tmp_path / "pkg", "Dict.LIFT", "Dict.lift-ranges")
    lexicon = sil_lift.load(lift)
    assert lexicon.all_ranges()["grammatical-info"].elements


def test_companion_resolves_when_companion_suffix_is_uppercase(tmp_path: Path) -> None:
    lift = _write_case_variant_pair(tmp_path / "pkg", "Dict.lift", "Dict.LIFT-RANGES")
    lexicon = sil_lift.load(lift)
    assert lexicon.all_ranges()["grammatical-info"].elements


def test_case_folded_companions_resolve_deterministically(tmp_path: Path) -> None:
    if not _case_sensitive_filesystem(tmp_path):
        pytest.skip("needs a case-sensitive filesystem to hold both spellings at once")
    # Neither spelling matches the Dict.LIFT-ranges candidate exactly, so the
    # tie-break picks one: lexicographically first, the same one every run.
    folder = tmp_path / "pkg"
    lift = _write_case_variant_pair(folder, "Dict.LIFT", "Dict.lift-ranges")
    (folder / "Dict.Lift-ranges").write_bytes((folder / "Dict.lift-ranges").read_bytes())
    lexicon = sil_lift.load(lift)
    assert [path.name for path in lexicon.ranges_files] == ["Dict.Lift-ranges"]


def test_absent_companion_stays_absent(tmp_path: Path) -> None:
    # The fallback must not look outside the folder for a name not in it.
    folder = tmp_path / "pkg"
    folder.mkdir()
    (folder / "Dict.lift").write_bytes((PAIR_DIR / "test20080407.lift").read_bytes())
    assert sil_lift.load(folder / "Dict.lift").ranges_files == {}


def test_companion_resolves_across_unicode_normalization(tmp_path: Path) -> None:
    # FLEx mixes NFC and NFD within one export, and the mismatch reaches the
    # filenames; only macOS folds the two forms together on its own.
    composed = "Caf\N{LATIN SMALL LETTER E WITH ACUTE}.lift"
    decomposed = unicodedata.normalize("NFD", f"{composed}-ranges")
    lift = _write_case_variant_pair(tmp_path / "pkg", composed, decomposed)
    lexicon = sil_lift.load(lift)
    assert lexicon.all_ranges()["grammatical-info"].elements


def test_lift_without_an_extension_loads(tmp_path: Path) -> None:
    # Loading never inspects the extension, so the sibling candidate is built
    # from a name that may have none; this companion is the href's basename.
    folder = tmp_path / "pkg"
    folder.mkdir()
    (folder / "Dict").write_bytes((PAIR_DIR / "test20080407.lift").read_bytes())
    shutil.copy(PAIR_DIR / "test20080407.lift-ranges", folder)
    lexicon = sil_lift.load(folder / "Dict")
    assert lexicon.all_ranges()["grammatical-info"].elements


def test_href_folding_onto_the_lift_itself_is_not_a_companion(tmp_path: Path) -> None:
    # Dict.lift beside a Dict.LIFT is the lexicon, not its ranges: loading it
    # as one would raise on the root and take the whole load down.
    lift = _write_lift_with_href(tmp_path / "pkg", "Dict.LIFT", "Dict.lift")
    lexicon = sil_lift.load(lift)
    assert lexicon.ranges_files == {}
    assert "dangling-ranges-href" in [p.code for p in lexicon.iter_problems()]


def test_self_referencing_href_dangles_however_it_is_spelled(tmp_path: Path) -> None:
    # The ".." keeps the href from matching the lexicon's path as spelled, so
    # both sides have to resolve before deciding what the reference supplies.
    lift = _write_lift_with_href(tmp_path / "pkg", "Dict.LIFT", "../pkg/Dict.lift")
    lexicon = sil_lift.load(lift)
    assert lexicon.ranges_files == {}
    assert "dangling-ranges-href" in [p.code for p in lexicon.iter_problems()]


def test_folder_shaped_href_stays_inside_the_folder(tmp_path: Path) -> None:
    if not _case_sensitive_filesystem(tmp_path):
        pytest.skip("needs a case-sensitive filesystem to hold both spellings at once")
    # An empty href names the folder itself; folding it would search the parent.
    lift = _write_lift_with_href(tmp_path / "pkg", "Dict.lift", "")
    (tmp_path / "PKG").write_bytes(b"<lift/>")
    assert sil_lift.load(lift).ranges_files == {}


# Defines the range the header points at, but no elements — so the merged view
# cannot vouch for the href and the check falls through to the filesystem.
ELEMENTLESS_RANGES = b"""<?xml version="1.0" encoding="UTF-8"?>
<lift-ranges>
  <range id="grammatical-info"/>
</lift-ranges>
"""


def test_case_variant_companion_is_not_reported_dangling(tmp_path: Path) -> None:
    folder = tmp_path / "pkg"
    lift = _write_lift_with_href(folder, "Dict.LIFT", "Dict.LIFT-ranges")
    (folder / "Dict.lift-ranges").write_bytes(ELEMENTLESS_RANGES)
    lexicon = sil_lift.load(lift)
    assert lexicon.ranges_files  # the companion resolved
    assert [p for p in lexicon.iter_problems() if p.code == "dangling-ranges-href"] == []


@pytest.mark.parametrize(
    ("href", "expected"),
    [
        ("audio/one.wav", Path("audio/one.wav")),
        ("pictures\\cultural law.png", Path("pictures/cultural law.png")),
        ("C:/dir/pic.png", None),
        ("C:\\dir\\pic.png", None),
        ("/abs/pic.png", None),
        ("//server/share/pic.png", None),
        ("file://C:/x.png", None),
        ("http://example.com/x.png", None),
    ],
)
def test_normalize_href(href: str, expected: Path | None) -> None:
    # WeSay backslash+space stays relative; every absolute form (drive-letter,
    # POSIX, UNC, file://, remote) is refused regardless of host.
    assert _normalize_href(href) == expected


# The DOCTYPE stops the scanner, so this companion has no byte regions to reuse
# and saving must re-serialize it canonically, root-level LIFT residue included.
UNSCANNABLE_RANGES = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE lift-ranges>
<lift-ranges>
<range id="etymology"><range-element id="borrowed"/></range>
<!-- between ranges -->
stray root text
<range id="dialect"><range-element id="north"/></range>
</lift-ranges>
"""


def test_canonical_companion_keeps_root_comments_but_not_root_text(tmp_path: Path) -> None:
    source = tmp_path / "unscannable.lift-ranges"
    source.write_bytes(UNSCANNABLE_RANGES)
    ranges_file = RangesFile.load(source)
    assert ranges_file.extra.to_string() == "<!-- between ranges -->\n\nstray root text\n"

    out = tmp_path / "canonical.lift-ranges"
    ranges_file.save(out)
    result = out.read_bytes()

    assert [r.id for r in RangesFile.load(out).ranges] == ["etymology", "dialect"]
    assert b"<!-- between ranges -->" in result
    # Character data at the root of a ranges document is not representable.
    assert b"stray root text" not in result
