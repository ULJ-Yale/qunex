"""
The three movement figures ``create_stats_report`` produces.

Split out of ``mov_stats`` so that matplotlib is imported only when there is
something to draw: the reports and the fidl snippets have to be computable on a
checkout that has numpy and nothing else. ``mov_stats`` imports this module
inside the branch that plots, which is the only place matplotlib is needed.

The figures replace the ggplot2 ones the R script drew. They carry the same
content -- one panel per BOLD sharing a frame axis, the same traces, the same
threshold lines and the same shading of rejected frames -- but they are not
pixel copies, and the axis limits that R hard-coded are kept because clipping
is what makes the three panels comparable, not because it is desirable.
"""

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os

import matplotlib

# no display anywhere this runs: a container, a cluster node, or CI
matplotlib.use("Agg")

import matplotlib.colors as colors  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from qx_utilities.processing.mov_stats import PARAMETERS  # noqa: E402

WIDTH = 10

# R fixed these limits and they are kept: the dvars traces run far higher than
# the interesting range, and an autoscaled axis would flatten every panel to
# accommodate one spike
LIMITS = {"dvars": 10, "dvarsme": 6}

# the displacement trace and the dvars trace, and with them the threshold line
# and the rejected frame shading that belong to each. Tying all three to one
# colour is what lets a band be read back to the criterion that raised it
TRACE_COLOURS = {"fd": "tab:blue", "dvars": "tab:orange"}

# the threshold lines: the trace colour taken towards black, enough to read as
# a reference rather than as data, and dashed so it is never mistaken for one
THRESHOLD_SHADE = 0.75
THRESHOLD_DASHES = (6, 4)

# light enough that two overlapping bands are visibly darker than one, which is
# how a frame that crossed both thresholds shows itself
SHADING_ALPHA = 0.25

# ggplot2's grey theme, which these figures had before and which suits them: the
# panel carries a pale fill with white gridlines, so the grid separates without
# drawing a line of its own, and the frame is light enough to bound the panel
# without competing with the data inside it
PANEL_BACKGROUND = "#f2f2f2"
GRID_COLOUR = "white"
FRAME_COLOUR = "#c8c8c8"
TEXT_COLOUR = "#4d4d4d"

# the run name, in the corner of its own panel rather than on a strip outside.
# Larger than the tick labels: it names the panel, so it should be findable at a
# glance rather than read
FACET_LABEL = {"color": TEXT_COLOUR, "fontweight": "bold", "fontsize": "large"}

# Helvetica where it exists, then its metric-compatible clones, then whatever a
# machine does have. The list is walked in order and DejaVu Sans ships with
# matplotlib, so it always resolves and never falls back with a warning --
# which matters because the container's font set is not this machine's.
FONTS = [
    "Helvetica",
    "Nimbus Sans",
    "FreeSans",
    "Liberation Sans",
    "Arial",
    "DejaVu Sans",
]

# applied around the drawing rather than to the global rcParams, which belong to
# whoever imported matplotlib, not to us
THEME = {
    "font.family": "sans-serif",
    "font.sans-serif": FONTS,
    "font.size": 8.5,
    "figure.facecolor": "white",
    "text.color": TEXT_COLOUR,
    "axes.labelcolor": TEXT_COLOUR,
    "axes.titlecolor": TEXT_COLOUR,
    # the axis titles carry the units, so they are bold while the tick labels
    # they sit under stay at the base size. `figure.labelweight` is the same
    # setting for `supylabel`, which is where "mm / deg" lives
    "axes.labelweight": "bold",
    "figure.labelweight": "bold",
    "xtick.color": FRAME_COLOUR,
    "ytick.color": FRAME_COLOUR,
    "xtick.labelcolor": TEXT_COLOUR,
    "ytick.labelcolor": TEXT_COLOUR,
}


def _darken(colour, factor=THRESHOLD_SHADE):
    """A paler dark version of a colour: the same hue, moved towards black."""
    red, green, blue = colors.to_rgb(colour)

    return (red * factor, green * factor, blue * factor)


def _style(axis):
    """Give one panel the grey-and-white ggplot look."""
    axis.set_facecolor(PANEL_BACKGROUND)

    for spine in axis.spines.values():
        spine.set_color(FRAME_COLOUR)
        spine.set_linewidth(0.8)

    axis.tick_params(width=0.8)

    # under the data, and white rather than grey: on the pale fill it reads as a
    # separation instead of as another set of lines to look at
    axis.grid(True, color=GRID_COLOUR, linewidth=0.8)
    axis.set_axisbelow(True)


def _tick_spacing(nframes):
    """
    Major tick spacing, widening in steps of 10 every 300 frames.

    R computed this from whichever run happened to be last in the loop; here it
    is the longest, which is the same answer whenever the runs are of a length
    and a better one when they are not.
    """
    return (nframes // 300 + 2) * 10


def _panels(count, height_per_panel, nframes, title):
    """A stack of panels sharing one frame axis, tallest run setting the ticks."""
    figure, axes = plt.subplots(
        count,
        1,
        sharex=True,
        # R's facets shared both scales, and the y axis is the one that matters:
        # a per panel scale makes a still run look as agitated as a moving one
        sharey=True,
        squeeze=False,
        figsize=(WIDTH, height_per_panel * count),
    )
    axes = [row[0] for row in axes]

    for axis in axes:
        axis.set_xlim(0.5, nframes + 0.5)
        axis.set_xticks(range(0, nframes + 1, _tick_spacing(nframes)))
        _style(axis)

    axes[0].set_title(title)
    axes[-1].set_xlabel("frame")

    return figure, axes


def _label(axis, run):
    """
    Name the run in the top right of its own panel.

    Inside the panel rather than on a strip beside it: the strip cost a column
    of width on every figure to carry one short word per row.
    """
    axis.text(
        0.995,
        0.94,
        run,
        transform=axis.transAxes,
        ha="right",
        va="top",
        **FACET_LABEL,
    )


def _shade(axis, frames, rejected, height, colour):
    """
    Shade the frames one criterion rejected, in that criterion's own colour.

    The spans stop at ``height`` rather than filling the panel, as they did in
    the R figures: a rejected frame is read against the threshold line, and a
    full height band hides the traces it is meant to annotate.

    Each criterion is shaded separately rather than as a union, and faintly, so
    that a frame both of them rejected shows as the darker overlap of two bands
    instead of hiding one criterion behind the other.
    """
    for frame in frames[rejected > 0]:
        axis.axvspan(
            frame - 0.5,
            frame + 0.5,
            ymax=height,
            color=colour,
            alpha=SHADING_ALPHA,
            linewidth=0,
        )


def _save(figure, axes, folder, root, suffix, written):
    """Add the legend beside the panels, then write the file."""
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="center right", frameon=False)

    path = os.path.join(folder, f"{root}_{suffix}.pdf")

    figure.tight_layout(rect=(0, 0, 0.9, 1))
    figure.savefig(path)
    plt.close(figure)
    written.append(path)


def _plot_parameters(folder, runs, session, root, nframes, written):
    """The six movement correction parameters, one panel per BOLD."""
    figure, axes = _panels(
        len(runs), 3.3, nframes, f"Movement correction parameters {session}"
    )

    for axis, (run, movement, _, _, _, _) in zip(axes, runs):
        frames = range(1, len(movement) + 1)

        for n, name in enumerate(PARAMETERS):
            axis.plot(frames, movement[:, n], linewidth=0.8, label=name)

        _label(axis, run)

    # set once for the figure: _label has already claimed each panel's own
    # ylabel for the run name, on the right where ggplot's facet strip was
    figure.supylabel("mm / deg")

    _save(figure, axes, folder, root, "cor", written)


def _plot_displacement(folder, runs, session, root, nframes, options, measure, written):
    """
    Framewise displacement against one dvars measure, with rejections shaded.

    ``measure`` is ``dvars`` or ``dvarsme``; the trace it draws alongside the
    displacement is ``dvarsm`` or ``dvarsme`` from the ``.bstats`` file, and the
    frames it shades are those either the movement or that measure rejected.
    """
    trace = {"dvars": "dvarsm", "dvarsme": "dvarsme"}[measure]
    threshold = float(options["mov_" + measure])
    movement_threshold = float(options["mov_fd"])

    figure, axes = _panels(
        len(runs),
        2,
        nframes,
        f"Movement and signal change ({trace}) across frames {session}",
    )

    limit = LIMITS[measure]

    for axis, (run, _, _, fd, flags, stats) in zip(axes, runs):
        frames = flags["frame"]

        # one band per criterion, in the colour of the trace it belongs to.
        # Both rise to the same height, as they did in the R figures: scaling
        # each to its own threshold would leave the movement band a sliver a
        # twentieth of the panel high, and would stop the two from overlapping
        # where it matters -- on a frame both criteria rejected
        height = threshold / limit
        _shade(axis, frames, flags["mov"], height, TRACE_COLOURS["fd"])
        _shade(axis, frames, flags[measure], height, TRACE_COLOURS["dvars"])

        axis.plot(frames, fd, linewidth=0.8, color=TRACE_COLOURS["fd"], label="fd")
        axis.plot(frames, stats[trace], linewidth=0.8, color=TRACE_COLOURS["dvars"], label=trace)

        for level, colour in [
            (movement_threshold, TRACE_COLOURS["fd"]),
            (threshold, TRACE_COLOURS["dvars"]),
        ]:
            axis.axhline(
                level,
                color=_darken(colour),
                linewidth=0.8,
                dashes=THRESHOLD_DASHES,
            )

        axis.set_ylim(0, LIMITS[measure])
        _label(axis, run)

    _save(figure, axes, folder, root, measure, written)


def plot_movement(folder, runs, session, plot, options):
    """
    Draw the three movement figures, returning the paths written.

    Args:
        folder (str): where the figures go, the session's movement folder.
        runs (list): one ``(run, movement, deltas, fd, flags, stats)`` tuple per
            BOLD, in the order they are to be stacked.
        session (str): session id, quoted in every title.
        plot (str): root name for the files.
        options (dict): read here are ``mov_fd``, ``mov_dvars``,
            ``mov_dvarsme``, ``mov_pref``, ``boldname`` and ``nifti_tail``.
    """
    root = f"{options['boldname']}{options['nifti_tail']}_{options['mov_pref']}{plot}"
    nframes = max(len(entry[1]) for entry in runs)
    written = []

    with plt.rc_context(THEME):
        _plot_parameters(folder, runs, session, root, nframes, written)

        for measure in ["dvars", "dvarsme"]:
            _plot_displacement(
                folder, runs, session, root, nframes, options, measure, written
            )

    return written
