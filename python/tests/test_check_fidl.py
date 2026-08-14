"""
``check_fidl`` after the R script it used to call was removed.

Two Flanker fidl files, chosen for what they do to the figure's height: both
declare 21 event codes, ``OP243`` uses 16 of them and ``OP248`` uses all 21.
Without ``--allcodes`` a code no event uses gets no row, so ``OP243`` is five
rows shorter than ``OP248`` and five rows shorter than itself with the flag on
-- while ``OP248`` is the same either way. That is the whole of what the flag
does, and it is measurable off the page.

The `--fidlfile` path is here because it never worked. ``check_fidl.R``
assigned its output folder only in the branch that globs a folder, then used it
unconditionally, so naming a single file died with *object 'tfolder' not found*
before it drew anything.
"""

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import re
import shutil

import pytest

import qx_utilities.general.exceptions as ge
import qx_utilities.general.fidl as fidl
from qx_utilities.general.log import ReportLog

pytest.importorskip("matplotlib")

DATA = os.path.join(os.path.dirname(__file__), "test_data", "check_fidl")

# both declare 21 codes; the number each uses is what differs
FILES = {"OP243_Flanker.fidl": 16, "OP248_Flanker.fidl": 21}
NCODES = 21


@pytest.fixture
def folder(tmp_path):
    """The two fidl files in a folder of their own, so plots land in tmp_path."""
    for name in FILES:
        shutil.copy(os.path.join(DATA, name), str(tmp_path / name))

    return tmp_path


def page_height(path):
    """The page height in points, off the PDF's MediaBox."""
    with open(path, "rb") as f:
        box = re.search(rb"/MediaBox\s*\[([\d.\s]+)\]", f.read())

    return float(box.group(1).split()[3])


def test_a_folder_is_plotted_into_fidlplots(folder):
    fidl.check_fidl(fidlfolder=str(folder))

    written = sorted(os.listdir(str(folder / "fidlplots")))

    assert written == ["OP243_Flanker-fidlplot.pdf", "OP248_Flanker-fidlplot.pdf"]
    assert all(os.path.getsize(str(folder / "fidlplots" / e)) > 0 for e in written)


def test_a_single_file_can_be_named(folder):
    """
    The `--fidlfile` path, which is the one that has never worked.

    The plot goes into `fidlplots/` beside the file, which is where it would
    have gone had the same file been found by globbing the folder.
    """
    fidl.check_fidl(fidlfile=str(folder / "OP243_Flanker.fidl"))

    assert os.listdir(str(folder / "fidlplots")) == ["OP243_Flanker-fidlplot.pdf"]


def test_a_single_file_is_found_by_its_own_path_not_the_folder_option(folder):
    """
    An absolute `--fidlfile` is not re-joined onto `--fidlfolder`.

    The R script joined the two unconditionally, so an absolute path came out
    mangled. Passing a folder that does not contain the file must not matter.
    """
    fidl.check_fidl(
        fidlfile=str(folder / "OP248_Flanker.fidl"), fidlfolder="/nonexistent"
    )

    assert os.listdir(str(folder / "fidlplots")) == ["OP248_Flanker-fidlplot.pdf"]


def test_plotfile_names_the_output(folder):
    fidl.check_fidl(
        fidlfile=str(folder / "OP243_Flanker.fidl"), plotfile="checked.pdf"
    )

    assert os.listdir(str(folder / "fidlplots")) == ["checked.pdf"]


def test_plotfile_is_ignored_when_it_would_name_every_plot(folder):
    """One name for two files would leave one plot, silently. It is refused."""
    log = ReportLog()

    fidl.check_fidl(fidlfolder=str(folder), plotfile="checked.pdf", _log=log)

    assert len(os.listdir(str(folder / "fidlplots"))) == 2
    assert "--plotfile" in log.text


@pytest.mark.parametrize("name,used", FILES.items())
def test_allcodes_gives_every_declared_code_a_row(folder, name, used):
    """
    The height difference the flag makes, measured off the page.

    `OP243` uses 16 of the 21 declared codes, so the flag adds five rows to it;
    `OP248` uses all 21 and comes out the same height either way.
    """
    fidl.check_fidl(fidlfile=str(folder / name))
    some = page_height(str(folder / "fidlplots" / name.replace(".fidl", "-fidlplot.pdf")))

    fidl.check_fidl(fidlfile=str(folder / name), plotfile="all.pdf", allcodes=True)
    every = page_height(str(folder / "fidlplots" / "all.pdf"))

    from qx_utilities.general import fidl_plots

    rows_added = NCODES - used
    a_row = fidl_plots.ROW_HEIGHT * 72  # inches to points, as the PDF counts them
    assert every == pytest.approx(some + rows_added * a_row, abs=1)


def test_the_rows_are_the_used_codes_in_declaration_order(folder):
    """
    Row order follows the header, never the alphabet.

    R built the ranks through a factor, which is easy to reproduce as an
    alphabetical sort by accident; the order a fidl file declares its codes in
    is the one its author chose.
    """
    from qx_utilities.general import fidl_plots

    parsed = fidl.read_fidl(str(folder / "OP243_Flanker.fidl"))
    codes = parsed["header"].split()[1:]

    rows = fidl_plots._rows(codes, parsed["events"], allcodes=False)

    assert rows == sorted(rows)
    assert len(rows) == 16
    assert rows == sorted({int(e[1]) for e in parsed["events"]})

    assert fidl_plots._rows(codes, parsed["events"], allcodes=True) == list(range(21))


def test_nothing_is_printed_when_a_log_is_given(folder, capsys):
    """
    The R script printed its rank vector to stdout for every file it drew.

    A command given a log reports into it and nowhere else -- that is what
    makes the output readable when several sessions run at once.
    """
    fidl.check_fidl(fidlfolder=str(folder), _log=ReportLog())

    assert capsys.readouterr().out == ""


def test_a_missing_file_is_refused_by_name(tmp_path):
    with pytest.raises(ge.CommandFailed, match="does not exist"):
        fidl.check_fidl(fidlfile=str(tmp_path / "absent.fidl"))


def test_an_empty_folder_is_refused(tmp_path):
    with pytest.raises(ge.CommandFailed, match="No fidl files"):
        fidl.check_fidl(fidlfolder=str(tmp_path))


def test_an_event_code_the_header_does_not_declare_is_refused(tmp_path):
    """
    A code past the end of the header used to draw nothing and say nothing.

    ggplot2 turned the unmatched factor level into `NA`, dropped the row, and
    carried on -- so a fidl file with a code the header does not cover produced
    a plot that was quietly missing events.
    """
    path = tmp_path / "broken.fidl"
    path.write_text("2.5\tone\ttwo\n10\t0\t1.0\n20\t7\t1.0\n")

    # `CommandFailed`'s message is the headline; the detail is in `hints`
    with pytest.raises(ge.CommandFailed) as failure:
        fidl.check_fidl(fidlfile=str(path))

    assert "event code(s) [7] are not among the 2 codes" in failure.value.hints[0]
