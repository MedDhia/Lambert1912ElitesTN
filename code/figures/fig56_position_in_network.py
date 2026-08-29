"""Fig. 56 — Where the two sides sit in the network, compared like with like.

Restricted to people placed on the same kind of evidence and sitting in the same
component, the colonial line does not show up in brokerage at all. It shows up
in distance: natives are as likely to broker, from further out.
"""
import statistics

import numpy as np

import _positionality as P
import _style as S

matched = P.matched()

MEASURES = [
    ("comem_betweenness", "Betweenness\nshare of paths brokered", "{:.4f}", float),
    ("comem_closeness", "Closeness\nnearness to everyone else", "{:.3f}", float),
    ("comem_degree", "Co-members\npeople sharing a body", "{:.1f}", int),
    ("affil_degree", "Bodies joined", "{:.2f}", int),
]

fig, axes = S.plt.subplots(1, len(MEASURES), figsize=(9.0, 3.9))
lines = []
for ax, (column, heading, fmt, cast) in zip(axes, MEASURES):
    samples = {side: [cast(row[column]) for _, row in matched[side]]
               for side in (P.COLONIST, P.NATIVE)}
    means = [statistics.fmean(samples[side]) for side in (P.COLONIST, P.NATIVE)]
    difference, p = P.permutation_p(samples[P.COLONIST], samples[P.NATIVE])
    lines.append((heading.split("\n")[0], difference, p))

    S.grid(ax)
    bars = ax.bar(np.arange(2), means, width=0.56,
                  color=[P.COLOUR[P.COLONIST], P.COLOUR[P.NATIVE]], zorder=3)
    for bar, mean in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.03,
                fmt.format(mean), ha="center", va="bottom", fontsize=8.5,
                color=S.INK_SECONDARY)
    ax.set_xticks(np.arange(2), ["Colonist", "Native"], fontsize=8)
    ax.set_yticks([])
    ax.set_ylim(0, max(means) * 1.28)
    S.despine(ax)
    ax.set_title(heading, fontsize=8.5, color=S.INK_SECONDARY, loc="left", pad=6)
    ax.text(0.5, -0.16, P.p_text(p), transform=ax.transAxes, ha="center",
            va="top", fontsize=8,
            color=S.ORANGE if p < 0.05 else S.INK_MUTED)

fig.subplots_adjust(wspace=0.32, bottom=0.16, top=0.72)
n_colonist, n_native = len(matched[P.COLONIST]), len(matched[P.NATIVE])
# The prose names whichever measures actually separated, rather than asserting a
# result: on an earlier run this figure claimed one difference and drew two.
separating = [name for name, _, p in lines if p < 0.05]
null = [name for name, _, p in lines if p >= 0.05]


def listed(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + f" and {names[-1]}"


fig.suptitle("Natives broker as much as colonists, from fewer memberships and further out",
             x=0.008, y=1.16, ha="left", fontsize=12, fontweight="bold", color=S.INK)
fig.text(
    0.008, 1.11,
    f"{n_colonist} colonists and {n_native} natives, all placed by a body they belonged "
    f"to and all in the co-membership giant component — the only comparison fig. 55\n"
    f"permits. {listed(null).capitalize()} do not separate the two sides. "
    f"{listed(separating).capitalize()} do: a native belongs to about a third fewer "
    f"bodies and sits\nfurther from everyone else. The pairing is the point — the same "
    f"share of brokerage on fewer ties means a native's memberships each carry more of "
    f"it,\nwhich is what a tie that crosses the colonial line rather than running along "
    f"it would do. With samples this small and this zero-inflated, read a null as "
    "'no\ndifference these numbers can detect' rather than as no difference.",
    ha="left", va="top", fontsize=8.5, color=S.INK_SECONDARY, linespacing=1.5)
S.save(fig, "fig56_position_in_network",
       "Two-sided permutation test, 20,000 seeded relabellings; giant component only")
