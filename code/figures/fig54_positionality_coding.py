"""Fig. 54 — What the colonist/native coding can and cannot reach.

Before any comparison between the two sides, the size and shape of the hole. A
third of the volume is not placed at all, and the evidence that places the rest
is not the same evidence on both sides — which is the subject of fig. 55.
"""
import collections

import numpy as np

import _positionality as P
import _style as S

rows = P.coding()
order = ["colonist", "native", "unknown"]
BASES = [
    ("birthplace", "Where they were born", S.RAMP[250]),
    ("institutional", "A post, school or body of one community", S.RAMP[450]),
    ("reserved_post", "A post reserved to French citizens", S.RAMP[600]),
    ("name", "The construction of the printed name", S.RAMP[700]),
    ("", "Nothing that places them", S.DE_EMPHASIS),
]

counts = collections.Counter(
    (r["positionality"], r["position_basis"]) for r in rows.values())
totals = collections.Counter(r["positionality"] for r in rows.values())

fig, ax = S.figure(7.8, 3.6)
S.grid(ax, axis="x")
y = np.arange(len(order))
left = np.zeros(len(order))
for basis, label, colour in BASES:
    widths = np.array([counts[(p, basis)] for p in order], dtype=float)
    if not widths.any():
        continue
    ax.barh(y, widths, left=left, height=0.6, color=colour, label=label, zorder=3)
    for index, width in enumerate(widths):
        if width >= 45:
            ax.text(left[index] + width / 2, y[index], f"{int(width)}",
                    ha="center", va="center", fontsize=8,
                    color=S.on_color(colour))
    left += widths
ax.set_yticks(y, [f"{P.LABEL.get(p, 'Not placed')}\n{totals[p]}" for p in order])
ax.invert_yaxis()
ax.set_xticks([])
ax.set_ylim(len(order) - 0.35, -1.15)
S.despine(ax, keep=("left",))
ax.legend(loc="upper right", ncol=2, borderaxespad=0.2)

unplaced = totals["unknown"]
unrecorded = sum(1 for r in rows.values() if r["positionality"] == "unknown"
                 and r["birth_context"] == "unrecorded")
tunis_births = sum(1 for r in rows.values() if r["positionality"] == "unknown"
                   and r["birth_context"] == "tunisia")
by_birthplace = counts[("colonist", "birthplace")]
by_institution = counts[("native", "institutional")]
S.titles(
    ax,
    "A third of this elite cannot be placed on either side of the colonial line",
    f"Every person in the volume by the side the record places them on, and by "
    f"the kind of fact that placed them. {unplaced} of {len(rows)} are not "
    f"placed at all: {unrecorded} because their notice prints no birthplace and "
    f"names no communal institution, and {tunis_births} because it prints a "
    f"Tunisian birthplace, which fits a Tunisian family and a settler's son "
    f"equally well. The native count is therefore a floor. Note also that the "
    f"two sides are reached by different evidence — {by_birthplace} of the "
    f"{totals['colonist']} colonists by a birthplace, {by_institution} of the "
    f"{totals['native']} natives by a communal institution — which fig. 55 "
    "shows is not a harmless difference.",
    wrap=104,
)
S.save(fig, "fig54_positionality_coding",
       "Coding rules and their error rates: code/pipeline/code_positionality.py")
