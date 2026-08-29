"""Fig. 58 — The volume gives both sides the same space on the page.

Entry length and the presence of a portrait are the volume's own measures of
how much a person mattered to it (figs. 6 and 10). Neither divides on the
colonial line — which is a fact about Lambert's editing, not about Tunisia.
"""
import collections
import statistics

import numpy as np

import _positionality as P
import _style as S

people = collections.defaultdict(list)
for person in P.placed():
    people[person["positionality"]].append(person)

sides = (P.COLONIST, P.NATIVE)
lengths = {side: [int(r["n_chars"]) for r in people[side]] for side in sides}
portraits = {side: [int(int(r["n_portraits"]) > 0) for r in people[side]] for side in sides}

fig, (ax_length, ax_portrait) = S.plt.subplots(1, 2, figsize=(8.0, 4.0),
                                               gridspec_kw={"width_ratios": [1.55, 1]})

# Left: the whole length distribution, not just its mean -- entry length is
# heavily skewed and two equal means could still hide very different volumes.
CUTS = [(0, 299, "under 300"), (300, 599, "300–599"), (600, 1199, "600–1,199"),
        (1200, 2399, "1,200–2,399"), (2400, 10**9, "2,400+")]
S.grid(ax_length)
x = np.arange(len(CUTS))
width = 0.38
for offset, side in ((-0.5, P.COLONIST), (0.5, P.NATIVE)):
    values = lengths[side]
    shares = [100 * sum(1 for v in values if low <= v <= high) / len(values)
              for low, high, _ in CUTS]
    bars = ax_length.bar(x + offset * (width + 0.02), shares, width,
                         color=P.COLOUR[side], zorder=3,
                         label=f"{P.LABEL[side]} (n={len(values)})")
    for bar, share in zip(bars, shares):
        ax_length.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                       f"{share:.0f}%", ha="center", va="bottom", fontsize=7.5,
                       color=S.INK_SECONDARY)
ax_length.set_xticks(x, [label for _, _, label in CUTS], fontsize=8)
ax_length.set_yticks([])
ax_length.set_ylim(0, 46)
S.despine(ax_length)
ax_length.legend(loc="upper right")
ax_length.set_title("Entry length, in characters", fontsize=8.5,
                    color=S.INK_SECONDARY, loc="left", pad=6)

S.grid(ax_portrait)
shares = [100 * statistics.fmean(portraits[side]) for side in sides]
bars = ax_portrait.bar(np.arange(2), shares, width=0.5,
                       color=[P.COLOUR[s] for s in sides], zorder=3)
for bar, share in zip(bars, shares):
    ax_portrait.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                     f"{share:.0f}%", ha="center", va="bottom", fontsize=9,
                     color=S.INK_SECONDARY)
ax_portrait.set_xticks(np.arange(2), [P.LABEL[s] for s in sides], fontsize=8.5)
ax_portrait.set_yticks([])
ax_portrait.set_ylim(0, max(shares) * 1.3)
S.despine(ax_portrait)
ax_portrait.set_title("Share with a portrait", fontsize=8.5,
                      color=S.INK_SECONDARY, loc="left", pad=6)

length_diff, length_p = P.permutation_p(lengths[P.COLONIST], lengths[P.NATIVE])
portrait_diff, portrait_p = P.permutation_p(portraits[P.COLONIST], portraits[P.NATIVE])
fig.subplots_adjust(wspace=0.22, bottom=0.1, top=0.76)
fig.suptitle("The volume gives both sides the same space on the page",
             x=0.008, y=1.14, ha="left", fontsize=12, fontweight="bold", color=S.INK)
fig.text(
    0.008, 1.09,
    f"Entry length and portraits, for everyone the coding places. Mean length differs by "
    f"{abs(length_diff):.0f} characters ({P.p_text(length_p)}) on means of about 700, and\n"
    f"the shape of the two distributions is the same; the portrait share differs by "
    f"{abs(portrait_diff) * 100:.0f} points ({P.p_text(portrait_p)}). Lambert allotted a "
    f"native notable\nwhat he allotted a colonist. That is a finding about the editing of "
    "this volume and not about the society it describes: the people in it are already "
    "the\nones he chose to print, and figs. 54 and 55 are about who that leaves out.",
    ha="left", va="top", fontsize=8.5, color=S.INK_SECONDARY, linespacing=1.5)
S.save(fig, "fig58_position_and_attention",
       "Two-sided permutation test, 20,000 seeded relabellings")
