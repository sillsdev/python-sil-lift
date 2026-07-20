import os
import sys
from pathlib import Path

import pytest

import sil_lift
from sil_lift import LiftParseError, open_reader, open_writer

CORPUS_DIR = Path(__file__).parent / "corpus"

LOADABLE = sorted(
    p for p in CORPUS_DIR.rglob("*.lift") if "0.12" not in p.parts and p.name != "sample.lift"
)


def corpus_id(path: Path) -> str:
    return path.relative_to(CORPUS_DIR).as_posix()


@pytest.mark.parametrize("path", LOADABLE, ids=corpus_id)
def test_streaming_parse_equals_full_parse(path: Path) -> None:
    full = sil_lift.load(path, resolve_ranges=False)
    with open_reader(path) as reader:
        assert reader.producer == full.producer
        assert reader.header == full.header
        streamed = list(reader)
    assert streamed == full.entries


def test_streaming_version_guard() -> None:
    with pytest.raises(LiftParseError, match=r"0\.12"):
        open_reader(CORPUS_DIR / "spec-examples" / "0.12" / "simple.lift")


def test_streaming_not_xml() -> None:
    with pytest.raises(LiftParseError, match="not well-formed"):
        open_reader(CORPUS_DIR / "PROVENANCE.md")


def test_stream_copy_preserves_models(tmp_path: Path) -> None:
    source = CORPUS_DIR / "large" / "sango" / "sango.lift"
    out = tmp_path / "copy.lift"
    with (
        open_reader(source) as reader,
        open_writer(out, header=reader.header, producer=reader.producer) as writer,
    ):
        count = 0
        for entry in reader:
            writer.write(entry)
            count += 1
    assert count == 3507

    original = sil_lift.load(source, resolve_ranges=False)
    copied = sil_lift.load(out, resolve_ranges=False)
    assert copied.producer == original.producer
    assert copied.header == original.header
    assert copied.entries == original.entries


def test_streaming_write_matches_canonical_document(tmp_path: Path) -> None:
    from sil_lift._writer import canonical_document

    source = CORPUS_DIR / "spec-examples" / "0.13" / "subsenses.lift"
    lexicon = sil_lift.load(source, resolve_ranges=False)
    lexicon.extra._nodes.clear()  # streaming carries no root-level residue
    out = tmp_path / "streamed.lift"
    with open_writer(out, header=lexicon.header, producer=lexicon.producer) as writer:
        for entry in lexicon.entries:
            writer.write(entry)
    assert out.read_bytes() == canonical_document(lexicon)


def test_writer_leaves_unterminated_file_on_error(tmp_path: Path) -> None:
    out = tmp_path / "broken.lift"
    with pytest.raises(RuntimeError), open_writer(out, producer="t") as writer:
        writer.write(sil_lift.Entry(id="only"))
        raise RuntimeError("boom")
    assert not out.read_bytes().rstrip().endswith(b"</lift>")


def _working_set_bytes() -> int | None:
    if not sys.platform.startswith("win"):
        return None
    import ctypes
    import ctypes.wintypes as wintypes

    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = PROCESS_MEMORY_COUNTERS()
    counters.cb = ctypes.sizeof(counters)
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    if not ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        return None
    return int(counters.WorkingSetSize)


# The default run uses a ~35 MB file (quick); set SIL_LIFT_PERF=1 for the
# multi-hundred-MB variant.
_PERF = os.environ.get("SIL_LIFT_PERF") == "1"
_ENTRIES = 400_000 if _PERF else 40_000


def test_large_file_streams_in_bounded_memory(tmp_path: Path) -> None:
    sys.path.insert(0, str(Path(__file__).parent / "tools"))
    try:
        from generate_large import generate
    finally:
        sys.path.pop(0)

    big = tmp_path / "big.lift"
    generate(big, _ENTRIES, seed=0)
    size = big.stat().st_size
    assert size > (300_000_000 if _PERF else 30_000_000)

    out = tmp_path / "copy.lift"
    baseline = _working_set_bytes()
    peak_delta = 0
    count = 0
    with (
        open_reader(big) as reader,
        open_writer(out, header=reader.header, producer=reader.producer) as writer,
    ):
        for entry in reader:
            writer.write(entry)
            count += 1
            if baseline is not None and count % 5000 == 0:
                current = _working_set_bytes()
                if current is not None:
                    peak_delta = max(peak_delta, current - baseline)
    assert count == _ENTRIES
    assert out.stat().st_size > size // 2  # the copy really contains the data

    if baseline is not None:
        # O(one entry): far below file size (full DOM would exceed it severalfold).
        limit = 100 * 1024 * 1024 if _PERF else 60 * 1024 * 1024
        assert peak_delta < limit, f"working-set delta {peak_delta / 1e6:.0f} MB"
