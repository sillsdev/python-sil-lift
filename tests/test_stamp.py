"""Generated ``dateModified``/``dateCreated`` on save.

The unit is the entry: across the seven FieldWorks 8.3-9.0 exports in The
Combine's ``Backend.Tests/Assets``, all 35,318 entries carry both stamps and not
one of 69,754 sub-entry nodes carries either. An entry's digest already covers
its whole subtree, so an edit at any depth belongs to the entry containing it.
"""

import zipfile
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

import sil_lift

CORPUS_DIR = Path(__file__).parent / "corpus"
DATED = CORPUS_DIR / "misc" / "sample.0.13.lift"  # every entry carries both stamps
UNDATED = CORPUS_DIR / "spec-examples" / "0.13" / "subsenses.lift"  # no entry carries either

# Dates no typed field can hold: the reader keeps them as residue instead.
UNPARSEABLE_DATES = b"""<?xml version="1.0" encoding="UTF-8"?>
<lift version="0.13">
<entry id="one" dateCreated="nope" dateModified="whenever"><lexical-unit>
<form lang="en"><text>one</text></form></lexical-unit>
</entry>
</lift>
"""

WHEN = datetime(2026, 3, 4, 5, 6, 7, tzinfo=UTC)
LATER = datetime(2026, 3, 4, 5, 6, 8, tzinfo=UTC)
BY_HAND = datetime(1999, 12, 31, 23, 59, 59, tzinfo=UTC)


def _dates(lexicon: sil_lift.Lexicon) -> dict[str | None, tuple[object, object]]:
    """Every entry's stamps, keyed by id so a sort() does not disturb the comparison."""
    return {entry.id: (entry.date_created, entry.date_modified) for entry in lexicon.entries}


def _in_its_own_folder(fixture: Path, tmp_path: Path) -> Path:
    """A copy of a fixture on its own: save_zip packages its whole folder."""
    folder = tmp_path / "src"
    folder.mkdir()
    dest = folder / fixture.name
    dest.write_bytes(fixture.read_bytes())
    return dest


def test_an_untouched_save_stamps_nothing_and_stays_byte_identical(tmp_path: Path) -> None:
    """Stamping is driven by content, so a load-and-save writes the source bytes back."""
    lexicon = sil_lift.load(DATED)
    before = _dates(lexicon)
    out = tmp_path / "out.lift"
    lexicon.save(out, when=WHEN)

    assert _dates(lexicon) == before
    assert out.read_bytes() == DATED.read_bytes()
    # Every entry still matches its parse-time record, so nothing had to be
    # remembered for the next save — the bookkeeping tracks edits, not entries.
    assert lexicon._stamps == {}


def test_an_edit_at_any_depth_stamps_the_containing_entry(tmp_path: Path) -> None:
    lexicon = sil_lift.load(UNDATED)
    entry = lexicon.entries[0]
    entry.senses[0].subsenses[0].glosses[0].text = sil_lift.Text(["edited"])
    out = tmp_path / "out.lift"
    lexicon.save(out, when=WHEN)

    assert entry.date_modified == WHEN
    assert entry.date_created == WHEN  # blank before, so filled with the same moment
    assert b'dateCreated="2026-03-04T05:06:07Z" dateModified="2026-03-04T05:06:07Z"' in (
        out.read_bytes()
    )


def test_only_the_edited_entry_is_stamped(tmp_path: Path) -> None:
    lexicon = sil_lift.load(DATED)
    assert len(lexicon.entries) > 1
    target = lexicon.entries[3]
    untouched = [entry for entry in lexicon.entries if entry is not target]
    before = [(entry.date_created, entry.date_modified) for entry in untouched]
    target.lexical_unit["en"] = "edited"
    lexicon.save(tmp_path / "out.lift", when=WHEN)

    assert target.date_modified == WHEN
    assert [(entry.date_created, entry.date_modified) for entry in untouched] == before


def test_an_existing_date_created_survives_the_stamp(tmp_path: Path) -> None:
    """dateCreated is filled only when blank: an edit does not re-create an entry."""
    lexicon = sil_lift.load(DATED)
    target = lexicon.entries[0]
    created = target.date_created
    assert created is not None
    target.lexical_unit["en"] = "edited"
    lexicon.save(tmp_path / "out.lift", when=WHEN)

    assert target.date_created == created
    assert target.date_modified == WHEN


def test_stamp_false_writes_the_model_exactly_as_it_stands(tmp_path: Path) -> None:
    lexicon = sil_lift.load(DATED)
    target = lexicon.entries[0]
    before = target.date_modified
    target.lexical_unit["en"] = "edited"
    lexicon.save(tmp_path / "out.lift", stamp=False)

    assert target.date_modified == before
    assert lexicon._stamps == {}  # a save that stamps nothing remembers nothing


def test_a_date_the_caller_set_is_left_alone(tmp_path: Path) -> None:
    """Content and date both moved, so the date is the caller's, not a stale one."""
    lexicon = sil_lift.load(DATED)
    target = lexicon.entries[0]
    target.lexical_unit["en"] = "edited"
    target.date_modified = BY_HAND
    lexicon.save(tmp_path / "out.lift", when=WHEN)

    assert target.date_modified == BY_HAND


def test_sorting_alone_stamps_nothing(tmp_path: Path) -> None:
    """Matches the guarantee on Lexicon.sort: reordering leaves entry bytes alone."""
    lexicon = sil_lift.load(DATED)
    before = _dates(lexicon)
    lexicon.sort()
    lexicon.save(tmp_path / "out.lift", when=WHEN)

    assert _dates(lexicon) == before


def test_a_second_round_of_edits_on_the_same_lexicon_is_stamped_too(tmp_path: Path) -> None:
    """The baseline moves with each save; without that, only the first edit would bump.

    After the first save the entry's date differs from the loaded one — this
    library's own stamp — which is indistinguishable from a caller-set date
    unless the save records what it wrote.
    """
    lexicon = sil_lift.load(DATED)
    entry = lexicon.entries[0]
    out = tmp_path / "out.lift"

    entry.lexical_unit["en"] = "first"
    lexicon.save(out, when=WHEN)
    assert entry.date_modified == WHEN

    entry.lexical_unit["en"] = "second"
    lexicon.save(out, when=LATER)
    assert entry.date_modified == LATER


def test_a_save_with_no_intervening_edits_leaves_the_stamp_alone(tmp_path: Path) -> None:
    """Stamping twice for one edit would make every save a change downstream."""
    lexicon = sil_lift.load(DATED)
    entry = lexicon.entries[0]
    entry.lexical_unit["en"] = "edited"
    first = tmp_path / "first.lift"
    lexicon.save(first, when=WHEN)

    second = tmp_path / "second.lift"
    lexicon.save(second, when=LATER)

    assert entry.date_modified == WHEN
    assert second.read_bytes() == first.read_bytes()


def test_a_hand_set_date_becomes_the_baseline_for_the_next_edit(tmp_path: Path) -> None:
    """Deliberate for the save it was set for, stale once the content moves again."""
    lexicon = sil_lift.load(DATED)
    entry = lexicon.entries[0]
    out = tmp_path / "out.lift"

    entry.lexical_unit["en"] = "edited"
    entry.date_modified = BY_HAND
    lexicon.save(out, when=WHEN)
    assert entry.date_modified == BY_HAND

    entry.lexical_unit["en"] = "edited again"
    lexicon.save(out, when=LATER)
    assert entry.date_modified == LATER


def test_an_entry_added_after_load_is_stamped_only_when_its_date_is_blank(
    tmp_path: Path,
) -> None:
    """A new entry has nothing to compare against, so a date on it is taken as meant."""
    lexicon = sil_lift.load(UNDATED)
    blank = sil_lift.Entry(id="blank")
    carried = sil_lift.Entry(id="carried", date_created=BY_HAND, date_modified=BY_HAND)
    lexicon.entries += [blank, carried]
    out = tmp_path / "out.lift"
    lexicon.save(out, when=WHEN)

    assert (blank.date_created, blank.date_modified) == (WHEN, WHEN)
    assert (carried.date_created, carried.date_modified) == (BY_HAND, BY_HAND)

    # Its first save recorded a baseline, so the carried date is not frozen for good.
    carried.lexical_unit["en"] = "edited"
    lexicon.save(out, when=LATER)
    assert carried.date_modified == LATER
    assert carried.date_created == BY_HAND


def test_a_from_scratch_lexicon_is_stamped_on_its_first_save(tmp_path: Path) -> None:
    """The build-an-export case: no baseline anywhere, and every entry is new."""
    entry = sil_lift.Entry(id="kanga")
    entry.lexical_unit["seh"] = "nkhuku"
    lexicon = sil_lift.Lexicon(entries=[entry])
    out = tmp_path / "out.lift"
    lexicon.save(out, when=WHEN)

    assert (entry.date_created, entry.date_modified) == (WHEN, WHEN)

    # Re-saving an unedited from-scratch lexicon is not a modification either.
    lexicon.save(out, when=LATER)
    assert entry.date_modified == WHEN

    entry.lexical_unit["seh"] = "nkhukhu"
    lexicon.save(out, when=LATER)
    assert entry.date_modified == LATER
    assert entry.date_created == WHEN


def test_stamping_does_not_reach_below_the_entry(tmp_path: Path) -> None:
    """Entry-level only: no sub-entry node is stamped, whatever moved inside it."""
    lexicon = sil_lift.load(UNDATED)
    entry = lexicon.entries[0]
    sense = entry.senses[0]
    sense.date_modified = BY_HAND
    sense.subsenses[0].glosses[0].text = sil_lift.Text(["edited"])
    lexicon.save(tmp_path / "out.lift", when=WHEN)

    assert entry.date_modified == WHEN
    assert sense.date_modified == BY_HAND
    assert sense.date_created is None
    assert sense.subsenses[0].date_modified is None


def test_an_unscannable_document_stamps_only_what_changed(tmp_path: Path) -> None:
    """No byte snapshot, but the digests still date the edit and nothing else.

    Note what `changed_entries()` says here by contrast: every entry, because
    `save()` does re-serialize the whole file. Stamping asks the narrower
    question — what the caller modified — and answers it exactly.
    """
    text = UNDATED.read_text(encoding="utf-8").replace('encoding="UTF-8"', 'encoding="UTF-16"')
    source = tmp_path / "utf16.lift"
    source.write_bytes(text.encode("utf-16"))
    lexicon = sil_lift.load(source)
    assert lexicon._source is None  # no byte baseline, only a stamping one
    entry = lexicon.entries[0]
    out = tmp_path / "out.lift"

    lexicon.save(out, when=WHEN)
    assert (entry.date_created, entry.date_modified) == (None, None)
    assert len(lexicon.changed_entries()) == len(lexicon.entries)

    entry.senses[0].subsenses[0].glosses[0].text = sil_lift.Text(["edited"])
    lexicon.save(out, when=WHEN)
    assert (entry.date_created, entry.date_modified) == (WHEN, WHEN)


def test_when_is_normalized_to_utc_at_seconds_precision(tmp_path: Path) -> None:
    """Whatever shape the caller's moment is in, the output keeps the one form."""
    lexicon = sil_lift.load(UNDATED)
    entry = lexicon.entries[0]
    entry.lexical_unit["en"] = "edited"
    out = tmp_path / "out.lift"
    lexicon.save(out, when=datetime(2026, 3, 4, 5, 6, 7, 500000, tzinfo=UTC))

    assert entry.date_modified == WHEN  # the fraction is dropped, not rounded
    assert b'dateModified="2026-03-04T05:06:07Z"' in out.read_bytes()

    entry.lexical_unit["en"] = "edited again"
    offset = timezone(timedelta(hours=5, minutes=30))
    lexicon.save(out, when=datetime(2026, 3, 4, 10, 36, 8, tzinfo=offset))

    assert entry.date_modified == LATER  # the same moment, said in UTC
    assert b'dateModified="2026-03-04T05:06:08Z"' in out.read_bytes()


def test_a_naive_when_is_refused_and_nothing_is_written(tmp_path: Path) -> None:
    """UTC or local would put the stamp hours apart, so neither is assumed."""
    lexicon = sil_lift.load(UNDATED)
    entry = lexicon.entries[0]
    entry.lexical_unit["en"] = "edited"
    out = tmp_path / "out.lift"

    with pytest.raises(ValueError, match="timezone-aware"):
        lexicon.save(out, when=datetime(2026, 3, 4, 5, 6, 7))

    assert entry.date_modified is None
    assert not out.exists()


def test_a_refused_write_leaves_nothing_stamped(tmp_path: Path) -> None:
    """Stamping commits with the write: no file, no modification date.

    The refusal comes from the last entry, so this also pins that the entries
    ahead of it are not left half-stamped — deciding happens before mutating.
    """
    lexicon = sil_lift.load(DATED)
    edited, offending = lexicon.entries[0], lexicon.entries[-1]
    before = _dates(lexicon)
    baseline = dict(lexicon._stamps)
    edited.lexical_unit["en"] = "edited"
    offending.senses[0].glosses.append(sil_lift.Form(lang="en", text=sil_lift.Text(["\ud800"])))
    out = tmp_path / "out.lift"

    with pytest.raises(sil_lift.LiftWriteError):
        lexicon.save(out, when=WHEN)

    assert _dates(lexicon) == before
    assert lexicon._stamps == baseline
    assert not out.exists()


def test_a_refused_zip_write_leaves_nothing_stamped(tmp_path: Path) -> None:
    lexicon = sil_lift.load(_in_its_own_folder(UNDATED, tmp_path))
    entry = lexicon.entries[0]
    entry.lexical_unit["en"] = "edited"
    entry.senses[0].glosses.append(sil_lift.Form(lang="en", text=sil_lift.Text(["\ud800"])))

    with pytest.raises(sil_lift.LiftWriteError):
        lexicon.save_zip(tmp_path / "pkg.zip", when=WHEN)

    assert entry.date_modified is None


def test_a_removed_entry_drops_out_of_the_stamping_baseline(tmp_path: Path) -> None:
    """The baseline dict is rebuilt each save, so it holds no entry the lexicon lost.

    An entry the document was loaded with is retained by its parse-time record
    either way — that is what makes `removed_entries()` work — but one appended
    and then dropped would otherwise be kept alive here, subtree and all.
    """
    lexicon = sil_lift.load(UNDATED)
    appended = sil_lift.Entry(id="temporary")
    lexicon.entries.append(appended)
    out = tmp_path / "out.lift"
    lexicon.save(out, when=WHEN)
    assert [record.entry.id for record in lexicon._stamps.values()] == ["temporary"]

    lexicon.entries.remove(appended)
    lexicon.save(out, when=LATER)

    assert lexicon._stamps == {}


def test_an_aliased_entry_is_stamped_once(tmp_path: Path) -> None:
    """One entry object, one pair of dates — however many list slots point at it."""
    lexicon = sil_lift.load(UNDATED)
    entry = lexicon.entries[0]
    lexicon.entries.append(entry)  # the same object, written out twice
    entry.lexical_unit["en"] = "edited"
    out = tmp_path / "out.lift"
    lexicon.save(out, when=WHEN)

    assert entry.date_modified == WHEN
    assert len(lexicon._stamps) == 1
    assert out.read_bytes().count(b'dateModified="2026-03-04T05:06:07Z"') == 2


def test_two_saves_of_one_moment_share_a_stamp(tmp_path: Path) -> None:
    """The documented limit of seconds precision, said with an explicit moment.

    The same second cannot hold two distinct dates, so a second edit saved
    within one reads as no change to anything comparing dates. The stamping
    baseline still tracks it, so the next distinct moment stamps normally.
    """
    lexicon = sil_lift.load(DATED)
    entry = lexicon.entries[0]
    out = tmp_path / "out.lift"

    entry.lexical_unit["en"] = "one"
    lexicon.save(out, when=WHEN)
    entry.lexical_unit["en"] = "two"
    lexicon.save(out, when=WHEN)
    assert entry.date_modified == WHEN

    entry.lexical_unit["en"] = "three"
    lexicon.save(out, when=LATER)
    assert entry.date_modified == LATER


def test_the_default_clock_is_utc_at_seconds_precision(tmp_path: Path) -> None:
    """No `when`: the wall clock, in the 20-character form real exports use."""
    lexicon = sil_lift.load(UNDATED)
    entry = lexicon.entries[0]
    entry.lexical_unit["en"] = "edited"
    before = datetime.now(UTC).replace(microsecond=0)
    out = tmp_path / "out.lift"
    lexicon.save(out)
    after = datetime.now(UTC)

    stamped = entry.date_modified
    assert isinstance(stamped, datetime)
    assert stamped.utcoffset() == timedelta(0)
    assert stamped.microsecond == 0
    assert before <= stamped <= after
    rendered = f'dateModified="{stamped.strftime("%Y-%m-%dT%H:%M:%SZ")}"'.encode()
    assert rendered in out.read_bytes()


def test_a_stamped_save_is_byte_reproducible_given_when(tmp_path: Path) -> None:
    """`when` is what keeps a stamping pipeline diffable: same input, same bytes."""
    outputs = []
    for name in ("first.lift", "second.lift"):
        lexicon = sil_lift.load(UNDATED)
        lexicon.entries[0].senses[0].subsenses[0].glosses[0].text = sil_lift.Text(["edited"])
        out = tmp_path / name
        lexicon.save(out, when=WHEN)
        outputs.append(out.read_bytes())

    assert outputs[0] == outputs[1]


def test_validation_does_not_stamp(tmp_path: Path) -> None:
    """iter_problems is read-only, so the bytes it reports on precede any stamp."""
    lexicon = sil_lift.load(DATED)
    entry = lexicon.entries[0]
    before = entry.date_modified
    entry.lexical_unit["en"] = "edited"

    assert [problem for problem in lexicon.iter_problems() if problem.level == "error"] == []
    assert entry.date_modified == before

    lexicon.save(tmp_path / "out.lift", when=WHEN)
    assert entry.date_modified == WHEN


def test_changed_entries_still_reports_a_stamped_entry(tmp_path: Path) -> None:
    """The stamping baseline is its own: change detection still answers "since load"."""
    lexicon = sil_lift.load(DATED)
    entry = lexicon.entries[0]
    entry.lexical_unit["en"] = "edited"
    lexicon.save(tmp_path / "out.lift", when=WHEN)

    assert [id(reported) for reported in lexicon.changed_entries()] == [id(entry)]
    assert lexicon.changes()


def test_stamping_replaces_a_date_the_model_could_not_hold(tmp_path: Path) -> None:
    """A generated stamp wins over an unparseable date, which is only residue.

    A model field always beats stale residue in the writer, and that is the
    right way round here: the entry is being rewritten, and "whenever" is no
    date at all, so an edit leaves it with one that is. `stamp=False` is what
    preserves the original strings.
    """
    source = tmp_path / "junk.lift"
    source.write_bytes(UNPARSEABLE_DATES)
    lexicon = sil_lift.load(source)
    entry = lexicon.entries[0]
    assert (entry.date_created, entry.date_modified) == (None, None)

    entry.lexical_unit["en"] = "edited"
    out = tmp_path / "out.lift"
    lexicon.save(out, when=WHEN)
    written = out.read_bytes()
    assert b'dateCreated="2026-03-04T05:06:07Z" dateModified="2026-03-04T05:06:07Z"' in written
    assert b"whenever" not in written

    kept = sil_lift.load(source)
    kept.entries[0].lexical_unit["en"] = "edited"
    unstamped = tmp_path / "unstamped.lift"
    kept.save(unstamped, stamp=False)
    assert b'dateCreated="nope" dateModified="whenever"' in unstamped.read_bytes()


def test_save_zip_stamps_by_default(tmp_path: Path) -> None:
    """A package is the hand-off to the tools that reconcile on dateModified."""
    lexicon = sil_lift.load(_in_its_own_folder(UNDATED, tmp_path))
    entry = lexicon.entries[0]
    entry.senses[0].subsenses[0].glosses[0].text = sil_lift.Text(["edited"])
    dest = tmp_path / "pkg.zip"
    lexicon.save_zip(dest, when=WHEN)

    assert entry.date_modified == WHEN
    with zipfile.ZipFile(dest) as archive:
        member = next(name for name in archive.namelist() if name.endswith(".lift"))
        assert b'dateModified="2026-03-04T05:06:07Z"' in archive.read(member)


def test_save_zip_stamp_false_leaves_the_model_alone(tmp_path: Path) -> None:
    lexicon = sil_lift.load(_in_its_own_folder(UNDATED, tmp_path))
    entry = lexicon.entries[0]
    entry.senses[0].subsenses[0].glosses[0].text = sil_lift.Text(["edited"])
    lexicon.save_zip(tmp_path / "pkg.zip", stamp=False)

    assert entry.date_modified is None
