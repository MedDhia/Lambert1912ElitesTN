"""Fig. 65 — Four ways the colonial homophily could have been an artefact.

Fig. 64 reports the result; this reports the attempts to break it. The objection
with real force is the second: the community coding reads some communal bodies
as evidence, so a person placed by one sits in it with others of their kind by
construction.

The three checks that share a statistic share an axis. An earlier draft gave
each check its own panel and its own scale, which let a dot at +0.281 sit level
with a dot at +0.343 — the figure has to make the checks comparable, since
comparing them is the whole point.
"""
import sys

import numpy as np

import _positionality as P
import _style as S

sys.path.insert(0, str(S.ROOT / "code" / "pipeline"))
import homophily as H  # noqa: E402

colonial = H.attributes()["Positionality (colonist / native)"]
checks = H.robustness(colonial)
shared, weighted = checks[:3], checks[3]

CAPTIONS = {
    "Every body": "the result\nas reported",
    "Community-marked bodies removed": "the objection\nwith force",
    "Labels shuffled within degree quartile": "natives hold\nfewer ties",
}

fig, (ax, ax_weighted) = S.plt.subplots(
    1, 2, figsize=(9.0, 4.4), gridspec_kw={"width_ratios": [2.7, 1]})


def draw(axis, items, label):
    x = np.arange(len(items))
    S.grid(axis)
    for index, check in enumerate(items):
        low = check["null_mean"] - 2 * check["null_sd"]
        axis.bar(index, 4 * check["null_sd"], bottom=low, width=0.5,
                 color=S.GRID, zorder=2)
    axis.scatter(x, [c["observed"] for c in items], s=94, color=S.ORANGE,
                 zorder=4, edgecolors=S.SURFACE, linewidths=1.2)
    for index, check in enumerate(items):
        axis.annotate(f"{check['observed']:+.3f}", xy=(index, check["observed"]),
                      xytext=(0, 12), textcoords="offset points", ha="center",
                      fontsize=9, color=S.INK)
        axis.annotate(P.p_text(check["p"]), xy=(index, check["observed"]),
                      xytext=(0, -20), textcoords="offset points", ha="center",
                      fontsize=8, color=S.ORANGE)
    axis.set_xticks(x, [S.shorten(c["check"], 22, lines=3) for c in items],
                    fontsize=8)
    axis.set_xlim(-0.65, len(items) - 0.35)
    S.despine(axis, keep=("bottom", "left"))
    axis.set_ylabel(label)


draw(ax, shared, "Assortativity r")
ax.set_ylim(-0.08, 0.40)
ax.axhline(0, color=S.AXIS, linewidth=0.8, zorder=1)
# Below the tick labels, in axis-fraction space: at a data coordinate these
# captions landed among the ticks they were meant to gloss.
for index, check in enumerate(shared):
    ax.text(index, -0.26, CAPTIONS[check["check"]], ha="center", va="top",
            transform=ax.get_xaxis_transform(), fontsize=7.5,
            color=S.INK_MUTED, style="italic")

draw(ax_weighted, [weighted], "Mean within-body same-side share")
ax_weighted.set_ylim(0.62, 0.94)
ax_weighted.text(0, -0.26, "one big clique\ncould carry it", ha="center", va="top",
                 transform=ax_weighted.get_xaxis_transform(), fontsize=7.5,
                 color=S.INK_MUTED, style="italic")

fig.subplots_adjust(wspace=0.34, bottom=0.26, top=0.74)
base, unmarked = shared[0]["observed"], shared[1]["observed"]
fig.suptitle("The homophily survives every check that could have explained it away",
             x=0.008, y=1.16, ha="left", fontsize=12, fontweight="bold", color=S.INK)
fig.text(
    0.008, 1.11,
    f"Each mark is fig. 64's colonist/native result recomputed under one objection, "
    f"against the middle of {H.N_PERM:,} relabellings of that same graph (grey).\n"
    f"Left: the three checks that share a statistic, drawn to one axis so they can be "
    f"compared. Right: the same question with every body weighted equally rather than\n"
    f"by its pair count, so no single large clique can carry the finding — a different "
    f"statistic, hence a different scale. One objection moves the number: dropping the\n"
    f"bodies whose printed name marks a community, which the coding reads as evidence, "
    f"takes r from {base:+.3f} to {unmarked:+.3f}, about a sixth of it. That much of the "
    "effect is circular; the rest is not.",
    ha="left", va="top", fontsize=8.5, color=S.INK_SECONDARY, linespacing=1.5)
S.save(fig, "fig65_homophily_robustness",
       f"Permutation nulls, {H.N_PERM:,} draws, seed {H.SEED}; "
       "leave-one-body-out is in output/tables/homophily.md")
