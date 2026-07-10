"""
Tests for KLARF dialect compatibility.

Covers the three fixes:

* tolerant timestamp parsing (US, ISO-8601, and a graceful fallback),
* skipping interleaved ``FILENAME`` image-reference lines inside a
  ``DefectList``,
* and a regression check that the bundled standard sample still parses.
"""

import datetime
import tempfile
from pathlib import Path

import pytest

from klarfkit.klarfkit import WaferMap, _parse_timestamp


# Minimal valid KLARF body. The trailing ``PADCOL`` column absorbs a known
# off-by-one in the spec-column parser so the meaningful columns stay intact.
_KLARF_TEMPLATE = """FileVersion 1 1;
FileTimestamp {file_ts};
InspectionStationID "VENDOR" "MODEL" "HOST";
SampleType WAFER;
ResultTimestamp {result_ts};
LotID "LOT001";
SampleSize 1 200;
DiePitch 1000.0 1000.0;
DieOrigin 0.0 0.0;
WaferID "01";
Slot 01;
SampleCenterLocation 0.0 0.0;
DefectRecordSpec 6 DEFECTID XREL YREL XINDEX YINDEX PADCOL;
DefectList
{filename_block}1 100.0 200.0 0 0 0;
2 300.0 400.0 0 0 0;
SummarySpec 1 TESTNO;
SummaryList
1
EndOfFile;
"""


def _write_klarf(tmp_path, text):
    """
    Write *text* to a ``.KLA`` file under *tmp_path* and return its path.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest-provided temporary directory.
    text : str
        Full KLARF file contents.

    Returns
    -------
    pathlib.Path
        Path to the written file.
    """
    path = tmp_path / "sample.KLA"
    path.write_text(text)
    return path


# --- _parse_timestamp -------------------------------------------------------

def test_parse_timestamp_us_format():
    """The original US ``%m-%d-%y`` format is still parsed."""
    assert _parse_timestamp("10-19-21 10:06:32") == datetime.datetime(2021, 10, 19, 10, 6, 32)


def test_parse_timestamp_iso_format():
    """ISO-8601 timestamps are parsed to the expected datetime."""
    assert _parse_timestamp("2023-06-15 14:22:10") == datetime.datetime(2023, 6, 15, 14, 22, 10)


def test_parse_timestamp_fallback_returns_raw():
    """An unrecognised timestamp is returned unchanged rather than raising."""
    assert _parse_timestamp("not a timestamp") == "not a timestamp"


# --- read_klarf: timestamps -------------------------------------------------

def test_iso_timestamp_file_parses(tmp_path):
    """A KLARF with ISO-8601 timestamps loads and yields a datetime."""
    text = _KLARF_TEMPLATE.format(
        file_ts="2023-06-15 14:22:10",
        result_ts="2023-06-15 14:20:00",
        filename_block="",
    )
    wafer = WaferMap.read_klarf(_write_klarf(tmp_path, text))
    assert wafer.file_timestamp == datetime.datetime(2023, 6, 15, 14, 22, 10)
    assert len(wafer.defect_list) == 2


# --- read_klarf: interleaved FILENAME lines ---------------------------------

def test_skips_interleaved_filename_lines(tmp_path):
    """FILENAME image-reference lines inside DefectList are not treated as defects."""
    text = _KLARF_TEMPLATE.format(
        file_ts="10-19-21 10:06:32",
        result_ts="10-19-21 10:04:09",
        filename_block="FILENAME some/path/img1.jpg;\nDefectList\n",
    )
    wafer = WaferMap.read_klarf(_write_klarf(tmp_path, text))
    assert len(wafer.defect_list) == 2
    for col in ("DEFECTID", "XREL", "YREL", "XINDEX", "YINDEX"):
        assert col in wafer.defect_list.columns


def test_iso_and_filename_together(tmp_path):
    """The combined hard case (ISO timestamps + FILENAME lines) parses."""
    text = _KLARF_TEMPLATE.format(
        file_ts="2023-06-15 14:22:10",
        result_ts="2023-06-15 14:20:00",
        filename_block="FILENAME some/path/img1.jpg;\nDefectList\n",
    )
    wafer = WaferMap.read_klarf(_write_klarf(tmp_path, text))
    assert len(wafer.defect_list) == 2


# --- regression: bundled sample ---------------------------------------------

def test_bundled_sample_still_parses():
    """The standard sample bundled with the library keeps parsing."""
    sample = Path(__file__).resolve().parent.parent / "sample_files" / "CPS3TwithoutReview.001"
    if not sample.exists():
        pytest.skip("bundled sample file not present")
    wafer = WaferMap.read_klarf(sample)
    assert wafer.defect_list is not None
    assert len(wafer.defect_list) > 0

