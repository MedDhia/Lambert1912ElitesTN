"""Fig. 57 — Both states decorated both sides at much the same rate.

If the colonial order ran through the honours system, the colonist side should
carry more of it. It does not. The one gap that opens runs the other way.
"""
import collections
import statistics

import numpy as np

import _positionality as P
import _style as S

people = collections.defaultdict(list)
for person in P.placed():
    people[person["positionality"]].append(person)

MEASURES = [
    ("Decorations held\nmean per person", lambda r: int(r["n_decorations"]), "{:.2f}"),
    ("Légion d'honneur\nshare holding it", lambda r: int(r["has_legion_honneur"] == "1"), "{:.0%}"),
    ("Nichan Iftikhar\nshare holding it", lambda r: int(r["has_nichan_iftikhar"] == "1"), "{:.0%}"),
]

fig, axes = S.plt.subplots(1, len(MEASURES), figsize=(7.8, 3.8))
results = []
for ax, (heading, read_value, fmt) in zip(axes, MEASURES):
    samples = {side: [read_value(r) for r in people[side]]
               for side in (P.COLONIST, P.NATIVE)}
    means = [statistics.fmean(samples[side]) for side in (P.COLONIST, P.NATIVE)]
    difference, p = P.permutation_p(samples[P.COLONIST], samples[P.NATIVE])
    results.append((heading.split("\n")[0], difference, p))

    S.grid(ax)
    bars = ax.bar(np.arange(2), means, width=0.56,
                  color=[P.COLOUR[P.COLONIST], P.COLOUR[P.NATIVE]], zorder=3)
    for bar, mean in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.03,
                fmt.format(mean), ha="center", va="bottom", fontsize=9,
                color=S.INK_SECONDARY)
    ax.set_xticks(np.arange(2), ["Colonist", "Native"], fontsize=8.5)
    ax.set_yticks([])
    ax.set_ylim(0, max(means) * 1.28)
    S.despine(ax)
    ax.set_title(heading, fontsize=8.5, color=S.INK_SECONDARY, loc="left", pad=6)
    ax.text(0.5, -0.17, P.p_text(p), transform=ax.transAxes, ha="center", va="top",
            fontsize=8, color=S.ORANGE if p < 0.05 else S.INK_MUTED)

fig.subplots_adjust(wspace=0.3, bottom=0.17, top=0.74)
legion = next(r for r in results if r[0].startswith("Légion"))
fig.suptitle("Both states decorated both sides at the same rate",
             x=0.008, y=1.15, ha="left", fontsize=12, fontweight="bold", color=S.INK)
fig.text(
    0.008, 1.10,
    f"{len(people[P.COLONIST])} colonists and {len(people[P.NATIVE])} natives — everyone "
    f"the coding places, not only those in the network, since an honour does not\n"
    f"depend on a tie. Nothing here separates the two sides. The nearest thing to a "
    f"gap is the French Légion d'honneur, which the native side holds\nmore often, not "
    f"less ({P.p_text(legion[2])}). The beylical order reaches a clear majority of both. "
    f"Whatever the colonial line organised in 1912\nTunisia, the distribution of "
    "decorations among the people this volume chose to print is not it.",
    ha="left", va="top", fontsize=8.5, color=S.INK_SECONDARY, linespacing=1.5)
S.save(fig, "fig57_position_and_honours",
       "Two-sided permutation test, 20,000 seeded relabellings")
