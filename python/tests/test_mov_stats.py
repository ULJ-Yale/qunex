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

import pytest

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
