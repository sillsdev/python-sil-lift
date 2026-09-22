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


def test_media_refs_and_check_media_on_moma_folder() -> None:
    lexicon = sil_lift.load(CORPUS_DIR / "folder" / "Moma" / "Moma.lift")
    refs = list(lexicon.media_refs())
    assert {r.href for r in refs} == {"pictures\\cultural law.png", "pictures\\sdd.png"}
    assert all(r.kind == "illustration" for r in refs)
    assert all(r.entry_id for r in refs)
    # Every href spells its file exactly, so nothing is reported at all.
    assert lexicon.check_media() == []


def test_check_media_on_all_flex_fields() -> None:
    # The corpus deliberately omits the upstream filler media (PROVENANCE.md),
    # so these references must be reported missing.
    lexicon = sil_lift.load(CORPUS_DIR / "flex" / "AllFLExFields" / "AllFLExFields.lift")
    missing = {(r.ref.kind, r.ref.href) for r in lexicon.check_media() if r.status == "missing"}
    assert ("media", "Kalimba.mp3") in missing
    assert ("illustration", "Desert.jpg") in missing


def test_check_media_flags_broken_ref(tmp_path: Path) -> None:
    src = CORPUS_DIR / "folder" / "Moma"
    shutil.copytree(src, tmp_path / "Moma")
    lexicon = sil_lift.load(tmp_path / "Moma" / "Moma.lift")
    (tmp_path / "Moma" / "pictures" / "sdd.png").unlink()
    assert [(r.ref.href, r.status) for r in lexicon.check_media()] == [
        ("pictures\\sdd.png", "missing")
    ]


def _write_lift_with_illustration(folder: Path, href: str) -> Path:
    """A minimal loadable .lift whose one sense illustrates ``href``."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "media.lift"
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<lift version="0.13">\n'
        '<entry id="one">\n'
        '<lexical-unit><form lang="en"><text>one</text></form></lexical-unit>\n'
        f'<sense id="s1"><illustration href="{href}"/></sense>\n'
        "</entry>\n"
        "</lift>\n",
        encoding="utf-8",
    )
    return path


def test_check_media_reports_a_normalization_only_match(tmp_path: Path) -> None:
    # Not a corpus fixture: every checkout filesystem preserves case in a
    # filename, but HFS+ rewrites normalization, so a committed NFD/NFC pair
    # has a premise the checkout itself could alter.
    name_nfc = unicodedata.normalize("NFC", "café.png")
    name_nfd = unicodedata.normalize("NFD", "café.png")
    assert name_nfc != name_nfd
    (tmp_path / "pictures").mkdir()
    (tmp_path / "pictures" / name_nfd).write_bytes(b"")
    path = _write_lift_with_illustration(tmp_path, f"pictures/{name_nfc}")
    resolutions = sil_lift.load(path).check_media()
    assert [r.status for r in resolutions] == ["mismatch"]
    assert resolutions[0].found is not None
    assert resolutions[0].found.name == name_nfd


def test_check_media_reports_a_href_that_several_files_fold_onto(tmp_path: Path) -> None:
    if not _case_sensitive(tmp_path):
        pytest.skip("needs a case-sensitive filesystem to hold both spellings")
    (tmp_path / "pictures").mkdir()
    for name in ("SDD.PNG", "sdd.png"):
        (tmp_path / "pictures" / name).write_bytes(b"")
    # Matching neither exactly is what makes it ambiguous; it is still one
    # defect with one fix, so it reports as an ordinary mismatch.
    path = _write_lift_with_illustration(tmp_path, "pictures/Sdd.png")
    assert [r.status for r in sil_lift.load(path).check_media()] == ["mismatch"]


def test_check_media_resolves_an_exactly_spelled_href_above_the_folder(tmp_path: Path) -> None:
    # ".." names no directory to search, so it is probed as written rather than
    # folded -- and must keep resolving.
    (tmp_path / "shared").mkdir()
    (tmp_path / "shared" / "one.png").write_bytes(b"")
    path = _write_lift_with_illustration(tmp_path / "lex", "../shared/one.png")
    assert sil_lift.load(path).check_media() == []


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


def _case_sensitive(folder: Path) -> bool:
    probe = folder / "CaseProbe"
    probe.mkdir(exist_ok=True)
    sensitive = not (folder / "caseprobe").exists()
    probe.rmdir()
    return sensitive


def _keeps_candidate_case(folder: Path) -> bool:
    """Whether the filesystem folds case but resolve() keeps the spelling given.

    True on macOS, where one file reached under two spellings resolves to two
    distinct paths. Windows folds and canonicalizes, so both spellings resolve
    alike; Linux does not fold, so only the real one is ever reached.
    """
    probe = folder / "ResolveProbe"
    probe.write_bytes(b"")
    other = folder / "RESOLVEPROBE"
    keeps = other.is_file() and other.resolve().name == "RESOLVEPROBE"
    probe.unlink()
    return keeps


def test_companion_resolves_when_lift_suffix_is_uppercase(tmp_path: Path) -> None:
    lift = _write_case_variant_pair(tmp_path / "pkg", "Dict.LIFT", "Dict.lift-ranges")
    lexicon = sil_lift.load(lift)
    assert lexicon.all_ranges()["grammatical-info"].elements


def test_companion_resolves_when_companion_suffix_is_uppercase(tmp_path: Path) -> None:
    lift = _write_case_variant_pair(tmp_path / "pkg", "Dict.lift", "Dict.LIFT-RANGES")
    lexicon = sil_lift.load(lift)
    assert lexicon.all_ranges()["grammatical-info"].elements


@pytest.mark.parametrize("companion", ["Dict.lift-ranges", "Dict.LIFT-RANGES"])
def test_a_companion_that_is_not_a_ranges_document_is_skipped(
    tmp_path: Path, companion: str
) -> None:
    # A sibling match leaves no href to dangle and no collision to report, so
    # skipping a broken companion would be silent - hence the dedicated code,
    # however the companion is spelled.
    folder = tmp_path / "pkg"
    folder.mkdir(parents=True)
    lift = (PAIR_DIR / "test20080407.lift").read_bytes()
    (folder / "Dict.lift").write_bytes(lift)
    (folder / companion).write_bytes(lift)
    lexicon = sil_lift.load(folder / "Dict.lift")
    assert lexicon.entries
    assert lexicon.ranges_files == {}
    problems = [p for p in lexicon.iter_problems() if p.code == "unreadable-ranges-file"]
    assert [p.level for p in problems] == ["warning"]
    # resolve() canonicalizes case on Windows but not on macOS, so the recorded
    # path can carry the candidate's spelling rather than the file's own.
    assert problems[0].file is not None
    assert problems[0].file.samefile(folder / companion)
    assert "the conventional companion beside 'Dict.lift'" in problems[0].message
    assert "expected <lift-ranges>" in problems[0].message


@pytest.mark.parametrize("payload", [b"", b"<lift-ranges><range id="])
def test_an_empty_or_truncated_sidecar_still_loads_the_entries(
    tmp_path: Path, payload: bytes
) -> None:
    # The realistic trigger: an interrupted export or a partial sync, which
    # must not cost the lexicon its entries.
    folder = tmp_path / "pkg"
    folder.mkdir(parents=True)
    (folder / "Dict.lift").write_bytes((PAIR_DIR / "test20080407.lift").read_bytes())
    (folder / "Dict.lift-ranges").write_bytes(payload)
    lexicon = sil_lift.load(folder / "Dict.lift")
    assert lexicon.entries
    assert [p.code for p in lexicon.iter_problems()] == ["unreadable-ranges-file"]


def _lift_with_href(href: str) -> bytes:
    """A minimal LIFT 0.13 document whose one header range points at ``href``."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<lift version="0.13"><header><ranges>'
        f'<range id="etymology" href="{href}"/>'
        '</ranges></header><entry id="a"/></lift>'
    ).encode()


def test_an_href_naming_an_unrelated_file_names_the_header_range(tmp_path: Path) -> None:
    # Addressed to the file, but the actionable fix is the href: the png is
    # intact and must not be touched.
    folder = tmp_path / "pkg"
    folder.mkdir(parents=True)
    (folder / "Dict.lift").write_bytes(_lift_with_href("pictures.png"))
    (folder / "pictures.png").write_bytes(bytes.fromhex("89504E470D0A1A0A") + b" not xml at all")
    lexicon = sil_lift.load(folder / "Dict.lift")
    problems = [p for p in lexicon.iter_problems() if p.code == "unreadable-ranges-file"]
    assert len(problems) == 1
    assert problems[0].file is not None
    assert problems[0].file.samefile(folder / "pictures.png")
    assert "header range 'etymology' href 'pictures.png'" in problems[0].message


def test_a_rejection_is_dropped_once_its_file_is_gone(tmp_path: Path) -> None:
    # The record is discovery-time; the checks beside it read the folder as it
    # stands, so a replayed rejection would contradict dangling-ranges-href.
    folder = tmp_path / "pkg"
    folder.mkdir(parents=True)
    (folder / "Dict.lift").write_bytes(_lift_with_href("bad.lift-ranges"))
    (folder / "bad.lift-ranges").write_bytes(b"<nope>")
    lexicon = sil_lift.load(folder / "Dict.lift")
    assert [p.code for p in lexicon.iter_problems()] == ["unreadable-ranges-file"]
    (folder / "bad.lift-ranges").unlink()
    assert [p.code for p in lexicon.iter_problems()] == ["dangling-ranges-href"]


def test_a_case_only_href_edit_still_reaches_the_rejected_file(tmp_path: Path) -> None:
    if not _keeps_candidate_case(tmp_path):
        pytest.skip("needs a filesystem that folds case but resolves to the spelling given")
    # The rejection is keyed by the spelling discovery resolved, so a candidate
    # reaching the same file under another one matches only by identity.
    folder = tmp_path / "pkg"
    folder.mkdir(parents=True)
    (folder / "Dict.lift").write_bytes(_lift_with_href("bad.lift-ranges"))
    (folder / "bad.lift-ranges").write_bytes(b"<nope>")
    lexicon = sil_lift.load(folder / "Dict.lift")
    assert [p.code for p in lexicon.iter_problems()] == ["unreadable-ranges-file"]
    lexicon.header.ranges[0].href = "BAD.lift-ranges"
    problems = [p for p in lexicon.iter_problems() if p.code == "unreadable-ranges-file"]
    assert len(problems) == 1
    assert "href 'BAD.lift-ranges'" in problems[0].message


def test_a_rejection_is_dropped_once_the_href_moves(tmp_path: Path) -> None:
    folder = tmp_path / "pkg"
    folder.mkdir(parents=True)
    (folder / "Dict.lift").write_bytes(_lift_with_href("bad.lift-ranges"))
    (folder / "bad.lift-ranges").write_bytes(b"<nope>")
    lexicon = sil_lift.load(folder / "Dict.lift")
    lexicon.header.ranges[0].href = "elsewhere.lift-ranges"
    # Nothing in the document names bad.lift-ranges any more, so nothing may
    # report it -- least of all under the href it no longer carries.
    assert [p.code for p in lexicon.iter_problems()] == ["dangling-ranges-href"]


def test_two_candidate_spellings_of_one_rejected_file_report_once(tmp_path: Path) -> None:
    # Candidates dedup on spelling, so a .. segment survives as a second route
    # to the sibling's own file. The first route is the one load took.
    folder = tmp_path / "pkg"
    (folder / "sub").mkdir(parents=True)
    (folder / "Dict.lift").write_bytes(_lift_with_href("sub/../Dict.lift-ranges"))
    (folder / "Dict.lift-ranges").write_bytes(b"<nope>")
    lexicon = sil_lift.load(folder / "Dict.lift")
    problems = [p for p in lexicon.iter_problems() if p.code == "unreadable-ranges-file"]
    assert len(problems) == 1
    assert "the conventional companion beside 'Dict.lift'" in problems[0].message


def test_companion_findings_need_companion_discovery(tmp_path: Path) -> None:
    # resolve_ranges=False puts companions out of scope for the load, so no
    # finding about one is reported -- accurate or not. missing-media is not a
    # companion finding and is unaffected.
    folder = tmp_path / "pkg"
    folder.mkdir(parents=True)
    (folder / "Dict.lift").write_bytes(_lift_with_href("gone.lift-ranges"))
    (folder / "Dict.lift-ranges").write_bytes(b"")
    lift = folder / "Dict.lift"
    assert {p.code for p in sil_lift.load(lift).iter_problems()} == {
        "dangling-ranges-href",
        "unreadable-ranges-file",
    }
    resolved = sil_lift.load(lift, resolve_ranges=False)
    assert list(resolved.iter_problems()) == []


def test_attaching_a_companion_does_not_reopen_companion_findings(tmp_path: Path) -> None:
    # add_ranges_file attaches a companion and writes its header href, but it
    # reads nothing from the folder, so the folder stays out of scope. Running
    # the checks over what a non-resolving load holds would misreport it.
    folder = tmp_path / "pkg"
    folder.mkdir(parents=True)
    (folder / "Dict.lift").write_bytes(_lift_with_href("gone.lift-ranges"))
    (folder / "Dict.lift-ranges").write_bytes(b"")
    lexicon = sil_lift.load(folder / "Dict.lift", resolve_ranges=False)
    ranges = RangesFile()
    ranges.add_range("semantic-domain-ddp4").add_element("1.6.1.2")
    lexicon.add_ranges_file(ranges, href="Other.lift-ranges")
    assert list(lexicon.iter_problems()) == []


def test_a_second_lift_named_by_an_href_is_skipped_not_fatal(tmp_path: Path) -> None:
    folder = tmp_path / "pkg"
    folder.mkdir(parents=True)
    (folder / "Dict.lift").write_bytes(_lift_with_href("Other.lift"))
    shutil.copy(PAIR_DIR / "test20080407.lift", folder / "Other.lift")
    lexicon = sil_lift.load(folder / "Dict.lift")
    assert len(lexicon.entries) == 1
    problems = [p for p in lexicon.iter_problems() if p.code == "unreadable-ranges-file"]
    assert "root element is <lift>" in problems[0].message


def test_case_folded_companions_resolve_to_neither(tmp_path: Path) -> None:
    if not _case_sensitive(tmp_path):
        pytest.skip("needs a case-sensitive filesystem to hold both spellings at once")
    # Neither spelling matches the Dict.LIFT-ranges candidate exactly, and
    # nothing says which one it meant, so no companion is loaded for it.
    folder = tmp_path / "pkg"
    lift = _write_case_variant_pair(folder, "Dict.LIFT", "Dict.lift-ranges")
    (folder / "Dict.Lift-ranges").write_bytes((folder / "Dict.lift-ranges").read_bytes())
    lexicon = sil_lift.load(lift)
    assert lexicon.ranges_files == {}
    ambiguous = [p for p in lexicon.iter_problems() if p.code == "ambiguous-ranges-file"]
    assert [p.level for p in ambiguous] == ["warning"]
    assert "'Dict.LIFT-ranges' matches 'Dict.Lift-ranges', 'Dict.lift-ranges'" in (
        ambiguous[0].message
    )


def test_an_exactly_named_companion_ignores_the_variant_beside_it(tmp_path: Path) -> None:
    if not _case_sensitive(tmp_path):
        pytest.skip("needs a case-sensitive filesystem to hold both spellings at once")
    # The candidate names one of the two exactly, so folding never runs: a case
    # variant is only ambiguous when nothing answers to the name as written.
    folder = tmp_path / "pkg"
    lift = _write_case_variant_pair(folder, "Dict.lift", "Dict.lift-ranges")
    (folder / "Dict.LIFT-ranges").write_bytes((folder / "Dict.lift-ranges").read_bytes())
    lexicon = sil_lift.load(lift)
    assert [path.name for path in lexicon.ranges_files] == ["Dict.lift-ranges"]
    assert [p for p in lexicon.iter_problems() if p.code == "ambiguous-ranges-file"] == []


# One stem (Ñandú) in the four spellings a filesystem that folds case still
# keeps apart: each accent composed or decomposed, independently.
_COMPOSED = "\N{LATIN CAPITAL LETTER N WITH TILDE}and\N{LATIN SMALL LETTER U WITH ACUTE}"
_N_SPLIT = "N\N{COMBINING TILDE}and\N{LATIN SMALL LETTER U WITH ACUTE}"
_U_SPLIT = "\N{LATIN CAPITAL LETTER N WITH TILDE}andu\N{COMBINING ACUTE ACCENT}"
_BOTH_SPLIT = "N\N{COMBINING TILDE}andu\N{COMBINING ACUTE ACCENT}"


def _normalization_sensitive(folder: Path) -> bool:
    probe = folder / "NormProbe\N{COMBINING ACUTE ACCENT}"
    probe.mkdir()
    sensitive = not (folder / unicodedata.normalize("NFC", probe.name)).exists()
    probe.rmdir()
    return sensitive


def test_normalization_folded_companions_resolve_to_neither(tmp_path: Path) -> None:
    if not _normalization_sensitive(tmp_path):
        pytest.skip("needs a filesystem that keeps normalization forms apart")
    # Which accent is decomposed, rather than case, is what separates these two
    # companions — the only way to reach the collision where the exact-name stat
    # is itself case-insensitive, as it is on NTFS and APFS.
    folder = tmp_path / "pkg"
    # The sibling candidate is fully composed and the href fully decomposed:
    # two names folding onto the same pair, so one finding covers both.
    lift = _write_lift_with_href(folder, f"{_COMPOSED}.lift", f"{_BOTH_SPLIT}.lift-ranges")
    source = (PAIR_DIR / "test20080407.lift-ranges").read_bytes()
    (folder / f"{_N_SPLIT}.lift-ranges").write_bytes(source)
    (folder / f"{_U_SPLIT}.lift-ranges").write_bytes(source)
    lexicon = sil_lift.load(lift)
    assert lexicon.ranges_files == {}
    problems = list(lexicon.iter_problems())
    ambiguous = [p for p in problems if p.code == "ambiguous-ranges-file"]
    assert [p.level for p in ambiguous] == ["warning"]
    # Spellings that render identically, named by code point.
    assert ascii(f"{_N_SPLIT}.lift-ranges") in ambiguous[0].message
    assert ascii(f"{_U_SPLIT}.lift-ranges") in ambiguous[0].message
    # The collision says why nothing resolved; the href, which range went unmet.
    assert "dangling-ranges-href" in [p.code for p in problems]


def test_a_collision_including_the_loaded_companion_is_not_reported(tmp_path: Path) -> None:
    if not _normalization_sensitive(tmp_path):
        pytest.skip("needs a filesystem that keeps normalization forms apart")
    # The sibling names the composed spelling exactly and loads it; the href,
    # spelled a third way, folds onto both files and resolves to neither.
    folder = tmp_path / "pkg"
    lift = _write_lift_with_href(folder, f"{_COMPOSED}.lift", f"{_BOTH_SPLIT}.lift-ranges")
    source = (PAIR_DIR / "test20080407.lift-ranges").read_bytes()
    (folder / f"{_COMPOSED}.lift-ranges").write_bytes(source)
    (folder / f"{_N_SPLIT}.lift-ranges").write_bytes(source)
    lexicon = sil_lift.load(lift)
    assert [path.name for path in lexicon.ranges_files] == [f"{_COMPOSED}.lift-ranges"]
    assert lexicon.all_ranges()["grammatical-info"].elements
    assert [p for p in lexicon.iter_problems() if p.code == "ambiguous-ranges-file"] == []


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
    # Dict.lift beside a Dict.LIFT is the document being loaded, which is not
    # its own ranges whatever it holds — identity settles it, not the root.
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
    if not _case_sensitive(tmp_path):
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
