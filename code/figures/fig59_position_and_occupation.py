"""Fig. 59 — Where the colonial line actually shows: what people did.

Honours, page space and network position barely separate the two sides. Careers
do, and in the way the Protectorate's own structure implies: two administrations,
one for each side, and no traffic between them.
"""
import collections

import numpy as np

import _positionality as P
import _style as S

people = collections.defaultdict(list)
for person in P.placed():
    if person["occupation_primary"]:
        people[person["positionality"]].append(person)

sides = (P.COLONIST, P.NATIVE)
counts = {side: collections.Counter(r["occupation_primary"] for r in people[side])
          for side in sides}
totals = {side: sum(counts[side].values()) for side in sides}
share = {side: {k: 100 * v / totals[side] for k, v in counts[side].items()}
         for side in sides}

# Ordered by how far the two sides diverge, so the chart's own order carries the
# finding rather than leaving it to be hunted for.
categories = sorted(
    set(counts[P.COLONIST]) | set(counts[P.NATIVE]),
    key=lambda c: (-(share[P.NATIVE].get(c, 0) - share[P.COLONIST].get(c, 0)), c),
)
categories = [c for c in categories
              if max(share[P.COLONIST].get(c, 0), share[P.NATIVE].get(c, 0)) >= 3]
labels = [c.replace("_", " ").replace("politics native admin", "native administration")
          for c in categories]

fig, ax = S.figure(7.8, 4.8)
S.grid(ax, axis="x")
y = np.arange(len(categories))
height = 0.38
for offset, side in ((-0.5, P.COLONIST), (0.5, P.NATIVE)):
    values = [share[side].get(c, 0) for c in categories]
    bars = ax.barh(y + offset * (height + 0.02), values, height,
                   color=P.COLOUR[side], zorder=3,
                   label=f"{P.LABEL[side]} (n={totals[side]})")
    for bar, value in zip(bars, values):
        ax.text(bar.get_width() + 0.4, bar.get_y() + bar.get_height() / 2,
                f"{value:.0f}%", va="center", ha="left", fontsize=7.5,
                color=S.INK_SECONDARY)
ax.set_yticks(y, labels, fontsize=8.5)
ax.invert_yaxis()
ax.set_xticks([])
ax.set_xlim(0, max(max(share[s].values()) for s in sides) * 1.16)
S.despine(ax, keep=("left",))
ax.legend(loc="lower right")

native_admin = share[P.NATIVE].get("politics_native_admin", 0)
colonist_admin = share[P.COLONIST].get("politics_native_admin", 0)
military_gap = share[P.COLONIST].get("military", 0) - share[P.NATIVE].get("military", 0)
S.titles(
    ax,
    "The native administration is a career ladder with almost no colonists on it",
    f"Primary occupation as a share of each side, for the people the volume gives one "
    f"to, ordered by the size of the gap. The largest is the beylical and local "
    f"administration — caids, khalifas, cadis and the councils around them — which is "
    f"{native_admin:.0f}% of native careers and {colonist_admin:.0f}% of colonist ones. "
    f"The French army runs the other way, {military_gap:.0f} points heavier on the "
    f"colonist side. The professions in between — law, medicine, teaching, commerce — "
    "are shared almost evenly. The line divides the state, not the market.",
    xlabel="Share of that side's recorded careers",
    wrap=104,
)
S.save(fig, "fig59_position_and_occupation",
       "Categories under 3% on both sides are omitted; one primary occupation per person")
