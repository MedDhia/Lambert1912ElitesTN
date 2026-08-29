"""Fig. 49 — Network position and state recognition rise together.

Whether that is one thing causing the other, or both tracking a third, this
dataset cannot say — and fig. 34 gives good reason to suspect the third.
"""
import collections
import statistics

import numpy as np

import _style as S

persons = {p["entry_id"]: p for p in S.read("persons.csv")}
rows = collections.defaultdict(list)
for measure in S.read("person_network_measures.csv"):
    person = persons.get(measure["entry_id"])
    if not person or not measure["comem_betweenness"]:
        continue
    band = min(int(person["n_decorations"]), 4)
    rows[band].append((float(measure["comem_betweenness"]), int(measure["affil_degree"])))

bands = sorted(rows)
# The n goes on the tick, not floating under the bar: a separate line of text
# below the axis collides with the axis label at this figure height.
labels = [f"{b if b < 4 else '4 or more'}\nn={len(rows[b])}" for b in bands]
betweenness = [statistics.fmean(v[0] for v in rows[b]) for b in bands]

fig, ax = S.figure(7.6, 4.4)
S.grid(ax)
bars = ax.bar(np.arange(len(bands)), betweenness, width=0.62,
              color=[S.RAMP[250], S.RAMP[300], S.RAMP[400], S.RAMP[500], S.RAMP[650]][:len(bands)],
              zorder=3)
for bar, value in zip(bars, betweenness):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.03,
            f"{value:.4f}", ha="center", va="bottom", fontsize=8.5,
            color=S.INK_SECONDARY)
ax.set_xticks(np.arange(len(bands)), labels)
ax.set_yticks([])
ax.set_ylim(0, max(betweenness) * 1.2)
S.despine(ax)

top, bottom = betweenness[-1], betweenness[0]
dip = min(range(1, len(bands)), key=lambda i: (betweenness[i], i))
S.titles(
    ax,
    "The most decorated sit on nine times as many paths as the undecorated",
    f"Mean betweenness in the co-membership giant component, by how many honours "
    f"the notice records. It runs from {bottom:.4f} among the undecorated to "
    f"{top:.4f} among those with four or more — a factor of {top / bottom:.0f} — "
    f"but not step by step: the {len(rows[bands[dip]])} people with "
    f"{bands[dip]} honours sit below the {len(rows[bands[dip - 1]])} with "
    f"{bands[dip - 1]}, and with bands this small one hub moves a column. Read it "
    "as association and nothing more: fig. 34 shows honours accumulate with time "
    "served, and a man thirty years into a career has had thirty years to join "
    "things too. Both columns may simply be counting seniority.",
    xlabel="Honours recorded",
    ylabel="Mean betweenness",
    wrap=100,
)
S.save(fig, "fig49_centrality_and_honours",
       "People with a notice and a place in the co-membership giant component")
