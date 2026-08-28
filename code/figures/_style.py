"""Shared chart style: one place for the palette, the marks, and the axes.

Colours are the validated reference palette (categorical slots, the blue
sequential ramp, and the chrome/ink tokens). The subsets actually used here were
re-checked with the palette validator before being written down:

* 2 slots, all-pairs .............. PASS (grouped bars, dumbbells, two-series)
* 3 slots, all-pairs .............. PASS (network node classes -- scatter forms
                                    are all-pairs, so three is the ceiling)
* 4 slots, adjacent ............... PASS, with a contrast WARN on aqua and
                                    yellow: those two carry direct labels
                                    wherever they are used (the "relief" rule)
* 4-step ordinal blue ramp ........ PASS (ordered categories)

Every figure is also backed by a table: the CSV it reads is in data/processed/,
so no value is reachable only by looking at a colour.

Figures are written to output/figures/ as PNG (for reading) and PDF (vector, for
inclusion in a paper).
"""

from __future__ import annotations

import csv
import pathlib
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "processed"
OUT = ROOT / "output" / "figures"

# --- palette ---------------------------------------------------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]  # categorical slots 1-4
BLUE, ORANGE, AQUA, YELLOW = SERIES
DE_EMPHASIS = "#c3c2b7"  # the "rest" in an emphasis chart

# Single-hue blue ramp: sequential for magnitude, ordinal (>= step 250) for
# ordered categories.
RAMP = {
    100: "#cde2fb", 150: "#b7d3f6", 200: "#9ec5f4", 250: "#86b6ef",
    300: "#6da7ec", 350: "#5598e7", 400: "#3987e5", 450: "#2a78d6",
    500: "#256abf", 550: "#1c5cab", 600: "#184f95", 650: "#104281",
    700: "#0d366b",
}
ORDINAL_4 = [RAMP[250], RAMP[350], RAMP[450], RAMP[600]]

SOURCE_NOTE = (
    "Lambert, Dictionnaire illustré de la Tunisie (Tunis, 1912) · "
    "BnF ark:/12148/bpt6k5505300s"
)

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "font.family": "sans-serif",
    # system-ui is unavailable to Matplotlib; DejaVu Sans is its metric-
    # compatible default sans. No serif or display face anywhere.
    "font.sans-serif": ["DejaVu Sans"],
    "font.size": 9,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 9,
    "axes.labelcolor": INK_SECONDARY,
    "axes.edgecolor": AXIS,
    "axes.linewidth": 0.8,
    "xtick.color": INK_MUTED,
    "ytick.color": INK_MUTED,
    "xtick.labelcolor": INK_SECONDARY,
    "ytick.labelcolor": INK_SECONDARY,
    "xtick.major.size": 0,
    "ytick.major.size": 0,
    "legend.frameon": False,
    "legend.fontsize": 8.5,
    "lines.linewidth": 2.0,
    "lines.solid_capstyle": "round",
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "grid.linestyle": "-",  # never dashed
    "figure.dpi": 110,
    "savefig.dpi": 220,
    "savefig.bbox": "tight",
    "pdf.fonttype": 42,
})


def read(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def figure(width: float = 7.2, height: float = 4.4):
    fig, ax = plt.subplots(figsize=(width, height))
    return fig, ax


def titles(ax, title: str, subtitle: str = "", xlabel: str = "", ylabel: str = "",
           wrap: int = 96):
    """Title carries the claim; the subtitle carries the n and the caveat.

    The subtitle is wrapped rather than left to run: an over-long line widens the
    saved figure (savefig uses a tight bounding box) and leaves the plot itself
    stranded in the left half of the image.
    """
    if subtitle:
        lines = textwrap.wrap(subtitle, wrap)
        ax.set_title(title, loc="left", pad=12 + 12 * len(lines), color=INK)
        ax.text(
            0.0, 1.012, "\n".join(lines), transform=ax.transAxes,
            ha="left", va="bottom", fontsize=8.5, color=INK_SECONDARY, linespacing=1.5,
        )
    else:
        ax.set_title(title, loc="left", pad=10, color=INK)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


def grid(ax, axis: str = "y"):
    """Hairline, solid, behind the marks."""
    ax.grid(axis=axis, zorder=0)
    ax.set_axisbelow(True)


def despine(ax, keep=("bottom",)):
    for side, spine in ax.spines.items():
        spine.set_visible(side in keep)


def value_labels(ax, bars, values, horizontal=True, fmt="{:,.0f}", pad=0.01):
    """Label the tip of every bar in a single-series chart.

    Bar charts get tip labels rather than a value axis: the label is the value,
    which is why the y-axis ticks can then be dropped entirely.
    """
    span = (ax.get_xlim()[1] if horizontal else ax.get_ylim()[1])
    for bar, value in zip(bars, values):
        if horizontal:
            ax.text(
                bar.get_width() + span * pad, bar.get_y() + bar.get_height() / 2,
                fmt.format(value), va="center", ha="left",
                fontsize=8.5, color=INK_SECONDARY,
            )
        else:
            ax.text(
                bar.get_x() + bar.get_width() / 2, bar.get_height() + span * pad,
                fmt.format(value), ha="center", va="bottom",
                fontsize=8.5, color=INK_SECONDARY,
            )


def shorten(label: str, width: int = 20, lines: int = 2) -> str:
    """Wrap a hub label to at most `lines` lines, eliding rather than clipping."""
    wrapped = textwrap.wrap(label, width)
    if len(wrapped) > lines:
        wrapped = wrapped[:lines]
        wrapped[-1] = wrapped[-1][: width - 1].rstrip() + "\u2026"
    return "\n".join(wrapped)


def network_figure(positions, width: float = 8.2, header: float = 1.75):
    """A canvas shaped to the graph, with the axes filling it.

    A force-directed layout is drawn at equal aspect so distances stay
    comparable. Left to the default subplot margins, that leaves a band of empty
    surface below the graph: the axes box shrinks to the data ratio inside a box
    sized for something else. Sizing the figure from the layout and letting the
    axes fill it removes the band. `header` reserves room for the title block
    and legend.
    """
    xs = [p[0] for p in positions.values()]
    ys = [p[1] for p in positions.values()]
    ratio = (max(ys) - min(ys)) / max(max(xs) - min(xs), 1e-9)
    plot_h = min(max(width * 0.96 * ratio, 3.4), 8.5)
    fig, ax = plt.subplots(figsize=(width, plot_h + header))
    fig.subplots_adjust(
        left=0.02, right=0.98, bottom=0.01, top=plot_h / (plot_h + header)
    )
    dx = (max(xs) - min(xs)) * 0.06
    dy = (max(ys) - min(ys)) * 0.06
    ax.set_xlim(min(xs) - dx, max(xs) + dx)
    ax.set_ylim(min(ys) - dy, max(ys) + dy)
    ax.set_aspect("equal", adjustable="box")
    ax.set_axis_off()
    return fig, ax


def annotate_nodes(ax, items, fontsize=7.5, width=20) -> int:
    """Direct-label network hubs, skipping any label that cannot be placed clear.

    A label that overlaps another label is worse than no label, so each one is
    measured against those already placed and dropped if no offset is free. The
    node stays in the plot either way -- only its name is withheld.

    An item is `(position, label)`, or `(position, label, clearance)` where
    clearance is the mark's radius in points. Pass it whenever marks vary in
    size: the label sits on a fixed offset otherwise, which on a large mark
    means the label's own background patch covers the very node it names.
    """
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    placed = []
    for item in items:
        (x, y), label = item[0], item[1]
        gap = item[2] if len(item) > 2 else 0.0
        offsets = [(0, 11 + gap), (0, -13 - gap), (16 + gap, 4), (-16 - gap, 4),
                   (0, 22 + gap), (0, -24 - gap), (26 + gap, -10)]
        text = shorten(label, width)
        for dx, dy in offsets:
            ann = ax.annotate(
                text, xy=(x, y), xytext=(dx, dy), textcoords="offset points",
                ha="center", va="center", fontsize=fontsize, color=INK, zorder=6,
                bbox=dict(boxstyle="round,pad=0.24", fc=SURFACE, ec="none", alpha=0.9),
            )
            box = ann.get_window_extent(renderer=renderer).expanded(1.05, 1.15)
            if any(box.overlaps(other) for other in placed):
                ann.remove()
                continue
            placed.append(box)
            break
    return len(placed)


def betweenness_sizes(betweenness, nodes, floor: float = 7.0, ceiling: float = 520.0):
    """Marker areas linear in betweenness, so area reads as share of paths brokered.

    Both Matplotlib's `s` and NetworkX's `node_size` are areas, so a linear map
    from the value to the area is the one that lets a reader compare two marks
    by eye and be right.

    The scale is deliberately not square-rooted. Betweenness in this network is
    extremely concentrated -- most nodes sit on no shortest path at all -- and a
    compressing transform would flatter the many zeroes into looking like small
    positive values. The floor keeps a zero-betweenness node visible as a point
    without pretending it brokers anything.
    """
    top = max(betweenness.values()) or 1.0
    return [floor + (ceiling - floor) * (betweenness[n] / top) for n in nodes]


def on_color(fill: str) -> str:
    """Ink for a label set *inside* a coloured mark.

    A label inside a fill is the one place text may leave the ink tokens, and it
    has to be picked from the fill's luminance rather than from the value: a dark
    label on the darkest ramp step and a surface-coloured label on the lightest
    are both unreadable.
    """
    r, g, b = (int(fill[i:i + 2], 16) / 255 for i in (1, 3, 5))
    channels = [
        c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)
    ]
    luminance = 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]
    return SURFACE if luminance < 0.35 else INK


def save(fig, name: str, note: str = "") -> None:
    """Write one figure to its own PNG and PDF, with the source line."""
    OUT.mkdir(parents=True, exist_ok=True)
    footer = f"{note}  ·  {SOURCE_NOTE}" if note else SOURCE_NOTE
    # Placed just below the figure box: savefig's tight bounding box grows to
    # include it, so the note never forces a reserved band of empty surface.
    fig.text(0.008, -0.012, footer, ha="left", va="top", fontsize=7, color=INK_MUTED)
    for ext in ("png", "pdf"):
        # The PDF backend stamps the current time into /CreationDate, so an
        # otherwise identical rebuild rewrote all 33 PDFs and every commit
        # carried a binary diff that meant nothing. Passing None omits the key.
        metadata = {"CreationDate": None} if ext == "pdf" else None
        fig.savefig(OUT / f"{name}.{ext}", metadata=metadata)
    plt.close(fig)
    print(f"  wrote output/figures/{name}.png / .pdf")
