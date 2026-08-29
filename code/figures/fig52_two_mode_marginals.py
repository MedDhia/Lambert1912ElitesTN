"""Fig. 52 — Both sides of the two-mode network are mostly ones.

Before reading any structure off this network it is worth seeing its raw shape:
most people belong to one body, and most bodies record one person. Whatever
structure exists is carried by a thin minority on both sides.
"""
import collections

import numpy as np

import _networks as N
import _style as S

giant = N.giant(N.affiliation_graph()[0])
people = sorted(n for n in giant if giant.nodes[n]["kind"] == "person")
bodies = sorted(n for n in giant if giant.nodes[n]["kind"] == "org")

BINS = [(1, 1, "1"), (2, 2, "2"), (3, 4, "3–4"), (5, 9, "5–9"), (10, 10_000, "10+")]


def profile(nodes):
    degrees = [giant.degree(n) for n in nodes]
    return [100 * sum(1 for d in degrees if low <= d <= high) / len(degrees)
            for low, high, _ in BINS], degrees


people_share, people_degrees = profile(people)
body_share, body_degrees = profile(bodies)
labels = [label for _, _, label in BINS]

x = np.arange(len(BINS))
width = 0.36
fig, ax = S.figure(7.6, 4.4)
S.grid(ax)
for values, colour, name, offset in (
    (people_share, S.BLUE, f"A person, by bodies joined (n={len(people)})", -0.5),
    (body_share, S.ORANGE, f"A body, by people recorded (n={len(bodies)})", 0.5),
):
    bars = ax.bar(x + offset * (width + 0.02), values, width, color=colour,
                  label=name, zorder=3)
    for bar, value in zip(bars, values):
        # A non-empty bin that rounds to zero gets "<1%": a visible sliver
        # labelled "0%" reads as a rendering fault rather than a small share.
        text = "<1%" if 0 < value < 0.5 else f"{value:.0f}%"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.2,
                text, ha="center", va="bottom", fontsize=8,
                color=S.INK_SECONDARY)
ax.set_xticks(x, labels)
ax.set_yticks([])
ax.set_ylim(0, max(people_share + body_share) * 1.2)
S.despine(ax)
ax.legend(loc="upper right")

S.titles(
    ax,
    "Both sides of the network are mostly ones",
    f"Degree on each side of the two-mode giant component. "
    f"{people_share[0]:.0f}% of the {len(people)} people appear in a single body "
    f"and {body_share[0]:.0f}% of the {len(bodies)} bodies record a single person, "
    f"though the maxima are {max(people_degrees)} and {max(body_degrees)}. The "
    "network's shape therefore rests on a small minority at both margins, and any "
    "measure computed over it inherits that: most nodes carry no structural "
    "information at all beyond being attached.",
    ylabel="Share of that side",
    wrap=100,
)
S.save(fig, "fig52_two_mode_marginals",
       "Largest connected component only; isolated pairs are excluded by construction")
