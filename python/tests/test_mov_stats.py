"""
Oracle for the movement statistics reporting that replaces ``bold_stats.R``.

The files under ``test_data/mov_stats/r_reference`` are what
``r/qx_utilities/bold_stats.R`` produced from ``test_data/mov_stats/movement``,
captured before the R script was removed. They are the reference the Python
implementation is checked against, so the comparison lives here rather than in
the test that uses it.

The check is for **equivalence, not byte identity**: R writes its numbers with
``cat()`` at seven significant digits, which is a formatting choice no Python
implementation should have to imitate. So the reports are parsed into values and
compared with a relative tolerance, and seven digits is what sets that tolerance.

The reference was produced with ``create_stats_report``'s defaults --
``mov_fidl=udvarsme``, ``mov_post=udvarsme``, ``mov_fd=0.5``, ``mov_dvars=3.0``,
``mov_dvarsme=1.5``, ``mov_radius=50.0``, ``tr=2.5``, ``boldname=bold``,
``nifti_tail=""`` -- and session id ``REF01``. Anything comparing against it has
to use the same ones.

The three BOLDs are chosen for what they cover: ``bold1`` has 145 frames and
nothing flagged, so its fidl snippet is the header alone; ``bold5`` has 329
frames, crossing the ``nframes %/% 300`` branch in the plot tick spacing;
``bold9`` is the busiest, with 7 mov / 31 dvars / 20 dvarsme flagged frames and
four ignore blocks in its snippet.
"""

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import math
import os
import shutil
import sys

import numpy as np
import pytest

from qx_utilities.processing import mov_stats

PYTHON = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(os.path.dirname(__file__), "test_data", "mov_stats")
MOVEMENT = os.path.join(DATA, "movement")
REFERENCE = os.path.join(DATA, "r_reference")

SESSION = "REF01"
BOLDS = ["1", "5", "9"]

# the eight rows bold_stats.R writes per bold, in order. mean_dvars is not among
# them: the script hard-codes dodv <- FALSE, so that row has never been written
STATS = ["mean", "sd", "span", "max", "md", "med", "md2_max", "frame_dspl"]

# seven significant digits is all R's cat() gives, so it is all the reference
# can be trusted to
TOLERANCE = 1e-6


def read_report(path):
    """
    Parse a movement or scrubbing report into ``{(run, stat): [float, ...]}``.

    The row width varies -- ``frame_dspl`` carries four values under six column
    headings -- so the values are kept as a list rather than mapped onto the
    header. The scrubbing report has one row per bold and no stat column; it is
    keyed with a stat of ``""``.
    """
    parsed = {}

    with open(path) as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]

    header = lines.pop(0).split("\t")

    for line in lines:
        fields = [e for e in line.split("\t") if e != ""]
        if header[2] == "stat":
            run, stat, values = fields[1], fields[2], fields[3:]
        else:
            run, stat, values = fields[1], "", fields[2:]
        parsed[(run, stat)] = [float(e) for e in values]

    return parsed


def read_fidl_snippet(path):
    """Parse a ``_scrub.fidl`` snippet into ``(tr, [(onset, length), ...])``."""
    with open(path) as f:
        lines = [line.strip() for line in f if line.strip()]

    tr = float(lines.pop(0))
    blocks = [tuple(float(e) for e in line.split()) for line in lines]

    return tr, blocks


def compare(produced, reference, tolerance=TOLERANCE):
    """
    Compare two parsed reports, returning a list of differences.

    An empty list means the two are equivalent. Differences are returned rather
    than asserted so that a failure names every row that moved, not just the
    first one -- with 24 rows of 6 values, one at a time is a slow way to find
    out what changed.
    """
    problems = []

    missing = sorted(set(reference) - set(produced))
    extra = sorted(set(produced) - set(reference))

    problems += [f"row missing: {key}" for key in missing]
    problems += [f"unexpected row: {key}" for key in extra]

    for key in sorted(set(reference) & set(produced)):
        want, got = reference[key], produced[key]

        if len(want) != len(got):
            problems.append(f"{key}: {len(got)} values, expected {len(want)}")
            continue

        for n, (w, g) in enumerate(zip(want, got)):
            if not math.isclose(w, g, rel_tol=tolerance, abs_tol=1e-9):
                problems.append(f"{key} value {n}: {g} != {w}")

    return problems


def reference_report(name):
    return read_report(os.path.join(REFERENCE, name))


def test_fixture_is_intact():
    """The inputs the reference was generated from are all present."""
    for bold in BOLDS:
        for name in [f"bold{bold}_mov.dat", f"bold{bold}.scrub", f"bold{bold}.bstats"]:
            assert os.path.exists(os.path.join(MOVEMENT, name)), name


@pytest.mark.parametrize("name", ["bold_movement_report.txt", "bold_movement_report_post.txt"])
def test_reference_movement_reports_have_the_expected_shape(name):
    """Eight stat rows per bold, six values each bar frame_dspl's four."""
    report = reference_report(name)

    assert sorted(report) == sorted((f"bold{b}", s) for b in BOLDS for s in STATS)

    for (_, stat), values in report.items():
        assert len(values) == (4 if stat == "frame_dspl" else 6), stat


def test_reference_scrubbing_report_matches_the_scrub_files():
    """
    The scrubbing report's counts are sums of the .scrub columns.

    This is the one row of the reference that can be checked against its own
    input rather than taken on trust, so it is worth checking: it confirms the
    reference was generated from the fixture that sits next to it.
    """
    report = reference_report("bold_movement_scrubbing_report.txt")

    for bold in BOLDS:
        with open(os.path.join(MOVEMENT, f"bold{bold}.scrub")) as f:
            rows = [line.split() for line in f if line.strip() and not line.startswith("#")]

        columns = rows.pop(0)
        counts = [
            sum(float(row[columns.index(name)]) for row in rows)
            for name in ["mov", "dvars", "dvarsme", "idvars", "idvarsme", "udvars", "udvarsme"]
        ]

        assert report[(f"bold{bold}", "")][:7] == counts


def test_reference_fidl_snippets_agree_with_the_scrubbing_report():
    """
    Total frames in the snippet's ignore blocks equal the udvarsme count.

    bold1 has nothing flagged and so has no blocks at all -- the header-only
    snippet is a real case, and one an implementation can get wrong by writing
    an empty file or none.
    """
    report = reference_report("bold_movement_scrubbing_report.txt")

    for bold in BOLDS:
        tr, blocks = read_fidl_snippet(os.path.join(REFERENCE, f"bold{bold}_scrub.fidl"))

        assert tr == 2.5
        # udvarsme is the seventh count, and lengths are written negated
        assert sum(-length for _, length in blocks) == report[(f"bold{bold}", "")][6]

    assert read_fidl_snippet(os.path.join(REFERENCE, "bold1_scrub.fidl"))[1] == []


def test_compare_accepts_a_copy_and_catches_a_nudged_value():
    """
    The comparison has to fail on a difference the tolerance should not absorb.

    Without this the oracle is a function that returns an empty list, and every
    test built on it passes for the wrong reason.
    """
    reference = reference_report("bold_movement_report.txt")

    assert compare(dict(reference), reference) == []

    nudged = {key: list(values) for key, values in reference.items()}
    nudged[("bold9", "mean")][0] += 0.001
    assert len(compare(nudged, reference)) == 1

    dropped = {key: values for key, values in reference.items() if key != ("bold5", "sd")}
    assert compare(dropped, reference) == ["row missing: ('bold5', 'sd')"]

    truncated = {key: list(values) for key, values in reference.items()}
    truncated[("bold1", "span")].pop()
    assert compare(truncated, reference) == ["('bold1', 'span'): 5 values, expected 6"]


# ---> the implementation, against the reference above

# create_stats_report's defaults, which are what the reference was made with
OPTIONS = {
    "boldname": "bold",
    "nifti_tail": "",
    "mov_radius": 50.0,
    "mov_fd": 0.5,
    "mov_dvars": 3.0,
    "mov_dvarsme": 1.5,
    "mov_fidl": "udvarsme",
    "mov_post": "udvarsme",
    "mov_pref": "",
    "tr": 2.5,
}


@pytest.fixture
def produced(tmp_path):
    """Run the reporting over a copy of the fixture, returning where it wrote."""
    folder = str(tmp_path / "movement")
    shutil.copytree(MOVEMENT, folder)

    reports = {
        name: str(tmp_path / os.path.basename(path))
        for name, path in [
            ("mov_mreport", "bold_movement_report.txt"),
            ("mov_preport", "bold_movement_report_post.txt"),
            ("mov_sreport", "bold_movement_scrubbing_report.txt"),
        ]
    }

    mov_stats.report_movement_statistics(
        folder, BOLDS, SESSION, reports, OPTIONS, plot=""
    )

    return folder, reports


@pytest.mark.parametrize(
    "report",
    ["bold_movement_report.txt", "bold_movement_report_post.txt", "bold_movement_scrubbing_report.txt"],
)
def test_reports_are_equivalent_to_the_r_reference(produced, report):
    folder, reports = produced
    written = [path for path in reports.values() if path.endswith(report)][0]

    assert compare(read_report(written), reference_report(report)) == []


def test_fidl_snippets_are_identical_to_the_r_reference(produced):
    """
    The snippets match byte for byte, trailing tabs included.

    Equivalence is the standard everywhere else, but these cost nothing to
    match, and a user regenerating them over unchanged data should get an empty
    diff rather than one that has to be explained.
    """
    folder, _ = produced

    for bold in BOLDS:
        name = f"bold{bold}_scrub.fidl"
        with open(os.path.join(folder, name)) as f:
            written = f.read()
        with open(os.path.join(REFERENCE, name)) as f:
            assert written == f.read(), name


def test_a_report_that_is_not_asked_for_is_not_written(tmp_path):
    """An empty path means the report is off, not that it lands somewhere odd."""
    folder = str(tmp_path / "movement")
    shutil.copytree(MOVEMENT, folder)

    reports = {"mov_mreport": "", "mov_preport": "", "mov_sreport": ""}
    mov_stats.report_movement_statistics(
        folder, BOLDS, SESSION, reports, dict(OPTIONS, mov_fidl="none"), plot=""
    )

    assert sorted(os.listdir(folder)) == sorted(os.listdir(MOVEMENT))


def test_the_header_is_written_once_however_many_sessions_append(tmp_path):
    """
    Two sessions appending to one report leave one header, not two.

    This is what the lock is for. Running them in sequence does not exercise
    the concurrency, but it does exercise the decision the lock protects.
    """
    folder = str(tmp_path / "movement")
    shutil.copytree(MOVEMENT, folder)

    report = str(tmp_path / "movement_report.txt")
    reports = {"mov_mreport": report, "mov_preport": "", "mov_sreport": ""}

    for session in ["REF01", "REF02"]:
        mov_stats.report_movement_statistics(
            folder, BOLDS, session, reports, dict(OPTIONS, mov_fidl="none"), plot=""
        )

    with open(report) as f:
        lines = f.readlines()

    assert sum(line.startswith("session\t") for line in lines) == 1
    assert len(lines) == 1 + 2 * len(BOLDS) * len(STATS)


def test_an_unknown_criterion_is_refused_by_name(tmp_path):
    """
    A criterion that is not a .scrub column fails with the columns listed.

    The R script indexed the column with ``sc[[fidl]]``, which yields NULL for a
    name that is not there and writes an empty snippet -- the docstring's own
    ``u`` and ``ume`` did exactly that.
    """
    folder = str(tmp_path / "movement")
    shutil.copytree(MOVEMENT, folder)

    reports = {"mov_mreport": "", "mov_preport": "", "mov_sreport": ""}

    with pytest.raises(ValueError, match="not a column"):
        mov_stats.report_movement_statistics(
            folder, BOLDS, SESSION, reports, dict(OPTIONS, mov_fidl="ume"), plot=""
        )


@pytest.mark.parametrize(
    "rejected,expected",
    [
        ([0, 0, 0, 0], []),
        ([0, 1, 1, 0], [(1, 3)]),
        # open on the first frame, and on the last: the two edges R special-cased
        ([1, 1, 0, 0], [(0, 2)]),
        ([0, 0, 1, 1], [(2, 4)]),
        ([1, 1, 1, 1], [(0, 4)]),
        ([0, 1, 0, 1], [(1, 2), (3, 4)]),
    ],
)
def test_ignore_blocks_closes_runs_at_both_edges(rejected, expected):
    """
    Run-length encoding, including the runs that touch an edge.

    The onset is an index into the frames counting from zero, because it is
    multiplied by the TR to give a time. R found it with a 1-based ``which()``
    over a diff, which lands on the same frame by a coincidence of index bases
    -- worth pinning rather than reasoning about twice.
    """
    flags = {"frame": np.arange(len(rejected)), "x": np.array(rejected)}

    assert mov_stats.ignore_blocks(flags, "x") == expected


def test_importing_the_module_does_not_require_matplotlib():
    """
    The reporting half has to work on a checkout without matplotlib.

    CI installs numpy but not matplotlib, and a module level import here would
    fail at collection -- taking down every test in this file, not just the one
    that plots. The plotting lives in mov_plots, imported inside the branch
    that needs it.
    """
    import subprocess

    check = (
        "import sys;"
        "from qx_utilities.processing import mov_stats;"
        "sys.exit('matplotlib' in sys.modules)"
    )
    assert subprocess.call([sys.executable, "-c", check], cwd=PYTHON) == 0


def test_create_stats_report_produces_the_reports_end_to_end(tmp_path):
    """
    The command, not just the module, against the same reference.

    This is the path that used to go out to ``Rscript``. It covers what the
    module's own tests cannot: the report paths assembled from ``--boldname``,
    ``--nifti_tail`` and ``--mov_mreport``, the bold list ``use_or_skip_bold``
    returns from the batch information, and the call that replaced the
    subprocess.
    """
    import qx_utilities.processing.workflow as wf
    from tests.utils import default_options

    sessions = tmp_path / "sessions"
    movement = sessions / SESSION / "images" / "functional" / "movement"
    movement.mkdir(parents=True)
    for name in os.listdir(MOVEMENT):
        shutil.copy(os.path.join(MOVEMENT, name), str(movement / name))

    options = default_options(sessionsfolder=str(sessions), run="run")
    # `default_options` recodes "" to None, which the file name builders
    # concatenate; the CLI supplies real empty strings for these
    for name, value in list(options.items()):
        if value is None and ("tail" in name or "variant" in name or "pref" in name):
            options[name] = ""
    # the reference's settings, plus no plots: matplotlib is not a given here,
    # and the figures have their own test
    options.update(OPTIONS, mov_plot="", event_file="")

    sinfo = {"id": SESSION}
    sinfo.update({b: {"name": f"bold{b}", "task": "rest"} for b in BOLDS})

    log = wf.create_stats_report(sinfo, options, thread=1)

    assert "BOLDs ok:  3" in log.status[1], log.text
    assert "processing: ok" in log.status[1], log.text

    qc = sessions / "QC" / "movement"
    for name in ["bold_movement_report.txt", "bold_movement_report_post.txt",
                 "bold_movement_scrubbing_report.txt"]:
        assert compare(read_report(str(qc / name)), reference_report(name)) == [], name

    for bold in BOLDS:
        name = f"bold{bold}_scrub.fidl"
        with open(os.path.join(REFERENCE, name)) as f:
            assert (movement / name).read_text() == f.read(), name


def test_plots_are_written(tmp_path):
    pytest.importorskip("matplotlib")

    folder = str(tmp_path / "movement")
    shutil.copytree(MOVEMENT, folder)

    reports = {"mov_mreport": "", "mov_preport": "", "mov_sreport": ""}
    mov_stats.report_movement_statistics(
        folder,
        BOLDS,
        SESSION,
        reports,
        dict(OPTIONS, mov_fidl="none"),
        plot="mov_report",
    )

    written = sorted(e for e in os.listdir(folder) if e.endswith(".pdf"))

    assert written == [
        "bold_mov_report_cor.pdf",
        "bold_mov_report_dvars.pdf",
        "bold_mov_report_dvarsme.pdf",
    ]
    assert all(os.path.getsize(os.path.join(folder, e)) > 0 for e in written)
