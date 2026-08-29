"""Fig. 55 — Why the two sides cannot be compared as they stand.

This figure exists to stop a mistake, and it is a mistake this repository made
before it was caught. Natives are mostly identified through a communal
institution; colonists mostly through a European birthplace. Holding an
institutional tie is also what puts a person in the network. So the coding and
the outcome share a cause, and the raw comparison measures the coding.
"""
import statistics

import numpy as np

import _positionality as P
import _style as S

coding, measured = P.coding(), P.measures()

CELLS = [
    ("colonist", "birthplace", "Colonist, placed by\nwhere he was born"),
    ("colonist", "institutional", "Colonist, placed by\na body he belonged to"),
    ("native", "institutional", "Native, placed by\na body he belonged to"),
]


def cell(side: str, basis: str) -> list[float]:
    out = []
    for person in P.placed(coding):
        if person["positionality"] != side or person["position_basis"] != basis:
            continue
        found = P.in_giant(person, measured)
        if found is not None:
            out.append(float(found["comem_betweenness"]))
    return out


values = [cell(side, basis) for side, basis, _ in CELLS]
means = [statistics.fmean(v) for v in values]
# The two that are actually comparable: same basis, different side.
COMPARABLE = (1, 2)
colours = [S.DE_EMPHASIS if i not in COMPARABLE else P.COLOUR[CELLS[i][0]]
           for i in range(len(CELLS))]

fig, ax = S.figure(7.8, 4.2)
S.grid(ax, axis="x")
y = np.arange(len(CELLS))
bars = ax.barh(y, means, height=0.58, color=colours, zorder=3)
for bar, mean, sample in zip(bars, means, values):
    ax.text(bar.get_width() + max(means) * 0.015, bar.get_y() + bar.get_height() / 2,
            f"{mean:.4f}   (n={len(sample)})", va="center", ha="left",
            fontsize=8.5, color=S.INK_SECONDARY)
ax.set_yticks(y, [label for _, _, label in CELLS], fontsize=8.5)
ax.invert_yaxis()
ax.set_xticks([])
ax.set_xlim(0, max(means) * 1.32)
S.despine(ax, keep=("left",))

within, across = P.permutation_p(values[1], values[0])
matched_diff, matched_p = P.permutation_p(values[1], values[2])
ratio = means[1] / means[0]
S.titles(
    ax,
    "How a person was identified moves this measure more than which side he was on",
    f"Mean betweenness in the co-membership giant component, for people placed "
    f"on the colonial line by different kinds of evidence. Among colonists "
    f"alone — one side of the line, so nothing about the colonial order can "
    f"explain it — those placed by a communal body sit on {ratio:.1f} times as "
    f"many paths as those placed by a birthplace ({P.p_text(across)}). The "
    f"evidence that identifies a person and the ties that give him a network "
    f"position are the same ties. Only the lower two bars hold that constant, "
    f"and between them the gap is {abs(matched_diff):.4f} ({P.p_text(matched_p)}). "
    "Every comparison in figs. 56 to 63 is drawn on the matched basis for this "
    "reason.",
    xlabel="Mean betweenness (giant component only)",
    wrap=104,
)
S.save(fig, "fig55_identification_artefact",
       "Betweenness is computed within each node's own component, so only the giant is comparable")
