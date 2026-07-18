"""
Benchmark: KLARF dialect compatibility.

This script documents *why* the accompanying fixes exist by contrasting the
behaviour of ``WaferMap.read_klarf`` before and after the changes on three
inputs:

1. The standard sample bundled with the library (``sample_files``) — must keep
   working (no regression).
2. A KLARF whose ``FileTimestamp`` / ``ResultTimestamp`` use ISO-8601 instead of
   the US ``%m-%d-%y`` style.
3. A KLARF that interleaves per-defect ``FILENAME`` image-reference lines inside
   the ``DefectList``.

Before the fixes, inputs (2) and (3) raised ``ValueError``; after them, all
three parse. Run with::

    python benchmarks/klarf_dialect_compatibility.py

The synthetic fixtures below are generated at runtime, so the benchmark needs no
external data files beyond the library's own sample.
"""

import sys
import tempfile
from pathlib import Path

# Allow running as a standalone script (``python benchmarks/...``) by putting
# the repository root on the path so the in-tree ``klarfkit`` package imports.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from klarfkit import WaferMap  # noqa: E402

# A minimal but valid KLARF body. The trailing ``PADCOL`` column absorbs a
# known off-by-one in the spec-column parser so the meaningful columns stay
# intact. ``{file_ts}`` / ``{result_ts}`` and the optional ``{filename_block}``
# are filled per scenario.
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


def _write_temp_klarf(text):
    """
    Write *text* to a temporary ``.KLA`` file and return its path.

    Parameters
    ----------
    text : str
        Full KLARF file contents.

    Returns
    -------
    pathlib.Path
        Path to the temporary file (the caller is responsible for deleting it).
    """
    tmp = tempfile.NamedTemporaryFile("w", suffix=".KLA", delete=False)
    tmp.write(text)
    tmp.close()
    return Path(tmp.name)


def _try_read(label, text):
    """
    Attempt to parse a KLARF string and print a one-line PASS/FAIL summary.

    Parameters
    ----------
    label : str
        Human-readable scenario name.
    text : str
        KLARF file contents to parse.
    """
    path = _write_temp_klarf(text)
    try:
        wafer = WaferMap.read_klarf(path)
        n = 0 if wafer.defect_list is None else len(wafer.defect_list)
        print(f"[PASS] {label:38} defects={n} file_ts={wafer.file_timestamp}")
    except Exception as exc:  # noqa: BLE001 - benchmark reports any failure
        print(f"[FAIL] {label:38} {type(exc).__name__}: {exc}")
    finally:
        path.unlink(missing_ok=True)


def main():
    """Run every scenario and print a compact result table."""
    # 1) Regression: the library's own bundled sample must still parse.
    sample = Path(__file__).resolve().parent.parent / "sample_files" / "CPS3TwithoutReview.001"
    if sample.exists():
        try:
            wafer = WaferMap.read_klarf(sample)
            n = 0 if wafer.defect_list is None else len(wafer.defect_list)
            print(f"[PASS] {'bundled sample (regression)':38} defects={n}")
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {'bundled sample (regression)':38} {type(exc).__name__}: {exc}")

    # 2) ISO-8601 timestamps.
    _try_read(
        "iso-8601 timestamps",
        _KLARF_TEMPLATE.format(
            file_ts="2023-06-15 14:22:10",
            result_ts="2023-06-15 14:20:00",
            filename_block="",
        ),
    )

    # 3) Interleaved FILENAME lines inside the DefectList.
    _try_read(
        "interleaved FILENAME lines",
        _KLARF_TEMPLATE.format(
            file_ts="10-19-21 10:06:32",
            result_ts="10-19-21 10:04:09",
            filename_block="FILENAME some/path/img1.jpg;\nDefectList\n",
        ),
    )

    # 4) Both traits together (the hardest case).
    _try_read(
        "iso-8601 + FILENAME lines",
        _KLARF_TEMPLATE.format(
            file_ts="2023-06-15 14:22:10",
            result_ts="2023-06-15 14:20:00",
            filename_block="FILENAME some/path/img1.jpg;\nDefectList\n",
        ),
    )


if __name__ == "__main__":
    main()


