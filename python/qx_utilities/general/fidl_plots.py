"""
The event figure ``check_fidl`` draws for a fidl file.

Split out of ``fidl.py`` so that matplotlib is imported only when there is
something to draw: everything else in that file -- reading, joining, splitting
and melting fidl files -- has to work on a checkout that has no matplotlib.
``check_fidl`` imports this module inside the branch that plots.

The figure replaces the ggplot2 one ``check_fidl.R`` drew and carries the same
content: one row per event code, each event a bar spanning its duration, and a
row of onset marks along the top. It differs in two ways that were asked for.
The panel has **no frame at all** -- the pale fill and the white gridlines are
what bound it -- and there is **no legend**: the rows are named down the right
hand side, each level with the row it belongs to, which is what the legend was
for. A legend on a figure whose rows are the categories is the same information
twice, read in two places.
"""

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import colorsys

import matplotlib

# no display anywhere this runs: a container, a cluster node, or CI
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

# R drew these 15 inches wide at 1/2.5 inch a row. The width is kept -- a fidl
# file is a long thin thing and the figure should be too -- and the rows are a
# little tighter than R's, which the larger type can afford. Plus a fixed
# allowance for the onset row, the axis below and the margins
WIDTH = 15
ROW_HEIGHT = 0.8 / 2.5
MARGIN = 1.0

# ggplot2's grey theme, as in `processing/mov_plots.py`, less the frame: the
# panel is bounded by its own fill here, and the request was for nothing else
PANEL_BACKGROUND = "#f2f2f2"
GRID_COLOUR = "white"
TEXT_COLOUR = "#4d4d4d"

FONTS = [
    "Helvetica",
    "Nimbus Sans",
    "FreeSans",
    "Liberation Sans",
    "Arial",
    "DejaVu Sans",
]

THEME = {
    "font.family": "sans-serif",
    "font.sans-serif": FONTS,
    # this figure is 15 inches wide and gets looked at whole, so it is read at
    # a reduction; the type has to survive that
    "font.size": 12,
    "figure.facecolor": "white",
    "text.color": TEXT_COLOUR,
    "axes.labelcolor": TEXT_COLOUR,
    "axes.labelweight": "bold",
    "xtick.labelcolor": TEXT_COLOUR,
    "ytick.labelcolor": TEXT_COLOUR,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
}

# an event row is one unit tall; the onset row above them is three quarters of
# that, and its marks are short because they say when, not how long
ROW = 1.0
ONSET_HEIGHT = 0.75
ONSET_MARK = 0.5
HEADROOM = 0.25

# the onset marks are drawn narrower than an event bar of the same duration.
# Every event in the file lands on that one row, so at full width the busy
# stretches close up into a solid band and stop saying how many
ONSET_MARK_SCALE = 0.7

# the bars, as R had them: translucent enough that two events overlapping in
# time on one row show themselves as a darker patch rather than hiding
BAR_ALPHA = 0.7

# the narrowest a bar may be drawn, as a fraction of the time span. A fidl file
# runs for twenty minutes and a stimulus lasts a second, so at true width the
# short events come out under a quarter of a point and vanish -- the onset marks
# and the baseline events both. 1/400 of the span is about 2.5pt at this figure
# width, which is the least that reads as a mark rather than as a hairline
MIN_BAR_FRACTION = 1 / 400

# the gap between the panel and the row names down its right side, in points
LABEL_GAP = 8


def _palette(count):
    """
    ``count`` evenly spaced hues, ggplot2's default discrete scale in effect.

    ``hue_pal()`` walks the hue circle at one lightness and one chroma, which is
    what keeps no single category louder than the rest. This is the same idea in
    HLS, which is in the standard library.
    """
    return [
        colorsys.hls_to_rgb(n / count, 0.6, 0.6) for n in range(count)
    ]


def _rows(codes, events, allcodes):
    """
    The event codes to give a row to, in code order, and their names.

    Without ``allcodes`` a code that no event uses gets no row, which is what
    makes the figure shorter for a session that used 16 of the 21 declared
    codes. The row order is the order the codes are declared in, never the
    alphabetical order of their names -- the declaration order is the one the
    person who wrote the fidl file chose.
    """
    if allcodes:
        return list(range(len(codes)))

    used = {int(event[1]) for event in events}

    return [code for code in range(len(codes)) if code in used]


def plot_fidl(fidl, target, allcodes=False):
    """
    Draw one fidl file's events and write the figure to ``target``.

    Args:
        fidl (dict): as returned by ``fidl.read_fidl`` -- ``header`` carries the
            TR and the declared code names, ``events`` the ``[time, code,
            duration, ...]`` rows.
        target (str): the file to write. The extension picks the format.
        allcodes (bool): give every declared code a row, not only the ones an
            event uses.

    Returns:
        The path written.

    Raises:
        ValueError: an event names a code the header does not declare.
    """
    codes = fidl["header"].split()[1:]
    events = fidl["events"]

    unknown = sorted({int(e[1]) for e in events} - set(range(len(codes))))
    if unknown:
        raise ValueError(
            f"{fidl['source']}: event code(s) {unknown} are not among the "
            f"{len(codes)} codes the header declares"
        )

    rows = _rows(codes, events, allcodes)
    # the row a code is drawn on, counting down from the onset row
    place = {code: n for n, code in enumerate(rows)}
    colours = dict(zip(rows, _palette(len(rows))))

    height = MARGIN + (len(rows) + ONSET_HEIGHT + HEADROOM) * ROW_HEIGHT

    # a bar narrower than this does not survive being drawn, so it is widened to
    # it. The onset marks are all at the floor, and so are the shortest events
    span = max(e[0] + float(e[2]) for e in events) - min(e[0] for e in events)
    floor = span * MIN_BAR_FRACTION

    with plt.rc_context(THEME):
        figure, axis = plt.subplots(figsize=(WIDTH, height))

        for event in events:
            code = int(event[1])
            start, duration = event[0], float(event[2])
            row = place[code]

            # the event on its own row, and its onset on the row along the top
            axis.barh(-(row + 0.5), max(duration, floor), ROW, left=start,
                      color=colours[code], alpha=BAR_ALPHA, linewidth=0)
            axis.barh(ONSET_HEIGHT / 2,
                      max(ONSET_MARK, floor) * ONSET_MARK_SCALE, ONSET_HEIGHT,
                      left=start, color=colours[code], alpha=BAR_ALPHA,
                      linewidth=0)

        _style(axis, [codes[code] for code in rows])

        axis.set_xlabel("time (s)")
        # headroom above the onset row only: without it the marks run into the
        # top edge of the panel, and with no frame there is nothing to stop them
        axis.set_ylim(-len(rows), ONSET_HEIGHT + HEADROOM)

        figure.tight_layout()
        figure.savefig(target)
        plt.close(figure)

    return target


def _style(axis, names):
    """
    The grey panel, the white grid, and a name beside every row.

    Two sets of y ticks do the work: the major ones sit at the middle of each
    row and carry its name, the minor ones at the boundaries between rows and
    carry the grid. Without that split the row names would land on the lines
    that separate the rows rather than inside them.

    The names go down the **right** side. A row is read left to right and ends
    at the name that says what it was, and on that side they are left aligned
    against the panel edge by default, so they line up as a list without any of
    the padding a set of right aligned labels needs.
    """
    axis.set_facecolor(PANEL_BACKGROUND)
    axis.yaxis.tick_right()

    # no frame at all, and no tick marks -- the fill bounds the panel and the
    # grid divides it, which is the whole of the furniture this figure gets
    for spine in axis.spines.values():
        spine.set_visible(False)
    # `which="both"`: the minor ticks carry the row boundaries, and left at
    # their default length they draw a row of dashes down the side of the panel
    # -- exactly the furniture the frame was taken off to be rid of
    axis.tick_params(which="both", length=0)
    axis.tick_params(axis="y", pad=LABEL_GAP)

    # the onset row is not a code and so has no name of its own; it is titled
    # instead, in bold, which is what marks it as the heading of the stack
    axis.set_yticks(
        [ONSET_HEIGHT / 2] + [-(n + 0.5) for n in range(len(names))],
        ["events"] + names,
    )
    axis.set_yticks([-n for n in range(len(names) + 1)], minor=True)
    axis.get_yticklabels()[0].set_fontweight("bold")

    axis.grid(True, which="major", axis="x", color=GRID_COLOUR, linewidth=0.8)
    axis.grid(True, which="minor", axis="y", color=GRID_COLOUR, linewidth=0.8)
    axis.set_axisbelow(True)
