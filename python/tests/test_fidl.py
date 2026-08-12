# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for the two ways a utility command reports a failure it used to print.

``split_fidl`` records the error and raises, so a conc file it cannot use
fails the run. ``map_to_qunex_cpls`` records and returns, so the file it could
not parse is a failure without aborting the files after it -- its ``False``
return is also what it gives for a legitimate skip, which is why the record
rather than the return is what the run reads.
"""

import os

import pytest

import qx_utilities.general.core as gc
import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl
from qx_utilities.general.fidl import split_fidl
from qx_utilities.hcp.import_hcp import map_to_qunex_cpls

STAMP = "2026-08-09_12.00.00.000000"

NAMEFORMAT = r"(?P<subject_id>[^/]+?)_(?P<session_name>[^/]+?)/unprocessed/(?P<data>.*)"


def test_split_fidl_on_an_unusable_conc_file_is_a_failed_run(tmp_path):
    """
    The conc file names an image that is not there.

    ``read_conc`` printed the error and returned an empty list, ``split_fidl``
    looped over nothing and returned, and the run exited 0 having split
    nothing.
    """
    conc = tmp_path / "s.conc"
    conc.write_text("number_of_files: 1\n    file:%s\n" % (tmp_path / "missing.nii.gz"))

    fidl = tmp_path / "s.fidl"
    fidl.write_text("2.5 one\n0.0\t1\t1.0\n")

    run = gl.RunContext(
        "split_fidl",
        {},
        gl.LogSettings(),
        {"basefolder": str(tmp_path)},
        timestamp=STAMP,
    )
    run.header()
    outcome = gc.run_with_log(
        split_fidl,
        args={"concfile": str(conc), "fidlfile": str(fidl)},
        run=run,
        tags=["split_fidl"],
    )

    assert outcome.failed == 1
    assert isinstance(outcome.error, ge.CommandFailed)
    with open(outcome.comlog) as f:
        assert "image does not exist!" in f.read()


def test_split_fidl_raises_rather_than_splitting_nothing(tmp_path):
    conc = tmp_path / "s.conc"
    conc.write_text("number_of_files: 2\n    file:%s\n" % (tmp_path / "one.nii.gz"))

    fidl = tmp_path / "s.fidl"
    fidl.write_text("2.5 one\n0.0\t1\t1.0\n")

    with pytest.raises(ge.CommandFailed):
        split_fidl(str(conc), str(fidl))


def test_an_unparsable_file_is_recorded_and_the_next_file_still_maps(tmp_path):
    """The record is the failure; the loop over the remaining files goes on."""
    log = gl.ReportLog()
    sessions = {"list": [], "skip": [], "clean": [], "map": []}

    unparsable = map_to_qunex_cpls(
        "no_such_shape.txt",
        str(tmp_path),
        "HCPLS",
        sessions,
        "no",
        NAMEFORMAT,
        _log=log,
    )
    mapped = map_to_qunex_cpls(
        "S01_MR/unprocessed/T1w/T1w.nii.gz",
        str(tmp_path),
        "HCPLS",
        sessions,
        "no",
        NAMEFORMAT,
        _log=log,
    )

    assert unparsable is False
    assert log.has_errors
    assert "Could not parse file: no_such_shape.txt" in log.text
    assert mapped == os.path.join(
        str(tmp_path), "S01_MR", "hcpls", "T1w", "T1w.nii.gz"
    )
    assert sessions["map"] == ["S01_MR"]
