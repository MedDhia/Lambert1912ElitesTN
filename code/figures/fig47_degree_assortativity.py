"""Fig. 47 — Do the well-connected attach to the well-connected?

The two graphs give opposite answers, and the disagreement is instructive: one
of them is measuring the projection rather than the elite.
"""
import networkx as nx
import numpy as np

import _networks as N
import _style as S

affiliation = N.giant(N.affiliation_graph()[0])
comembership = N.giant(N.comembership_graph())

GRAPHS = [
    ("Two-mode\npeople × bodies", affiliation, S.BLUE),
    ("One-mode\nco-membership", comembership, S.ORANGE),
]
values = [nx.degree_assortativity_coefficient(g) for _, g, _ in GRAPHS]

fig, ax = S.figure(7.4, 4.2)
S.grid(ax)
x = np.arange(len(GRAPHS))
bars = ax.bar(x, values, width=0.5, color=[c for _, _, c in GRAPHS], zorder=3)
for bar, value in zip(bars, values):
    offset = 0.028 if value > 0 else -0.028
    ax.text(bar.get_x() + bar.get_width() / 2, value + offset, f"{value:+.2f}",
            ha="center", va="bottom" if value > 0 else "top",
            fontsize=10, color=S.INK_SECONDARY)
ax.axhline(0, color=S.AXIS, linewidth=1.0, zorder=4)
ax.set_xticks(x, [label for label, _, _ in GRAPHS])
ax.set_yticks([])
ax.set_ylim(min(values) * 1.5, max(values) * 1.35)
S.despine(ax, keep=())
ax.text(0.5, max(values) * 1.2, "hubs attach to hubs", ha="center", fontsize=8,
        color=S.INK_MUTED)
ax.text(0.5, min(values) * 1.3, "hubs attach to the sparsely connected",
        ha="center", fontsize=8, color=S.INK_MUTED)

S.titles(
    ax,
    "The projection says hubs cluster together; the raw graph says the opposite",
    f"Degree assortativity in each network. In the two-mode graph it is "
    f"{values[0]:+.2f}: a body with many members is mostly joined by people who "
    f"belong to little else, which is what a membership list looks like. In the "
    f"projection it is {values[1]:+.2f}, but that is largely the projection "
    "talking — turning one body of n members into a clique gives all n the same "
    "high degree and makes them each other's neighbours. Prefer the two-mode "
    "figure; the projection's number is about the method.",
    ylabel="Degree assortativity",
    wrap=100,
)
S.save(fig, "fig47_degree_assortativity",
       "Largest connected component of each graph; Newman's degree correlation coefficient")
