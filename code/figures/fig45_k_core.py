"""Fig. 45 — How deep the core of this elite goes.

The k-core is the largest subgraph in which everyone still has k neighbours
inside it. Peeling k upward strips the periphery away layer by layer and leaves
whatever survives: here, a group of people every one of whom shares a body with
forty of the others.
"""
import collections

import networkx as nx
import numpy as np

import _networks as N
import _style as S

giant = N.giant(N.comembership_graph())
core = nx.core_number(giant)
sizes = collections.Counter(core.values())
levels = sorted(sizes)
# Cumulative: how many people survive a peel to depth k.
surviving = [sum(count for k, count in sizes.items() if k >= level) for level in levels]

fig, ax = S.figure(7.6, 4.6)
S.grid(ax)
colours = [S.BLUE if level == max(levels) else S.RAMP[250] for level in levels]
bars = ax.bar(np.arange(len(levels)), surviving, width=0.66, color=colours, zorder=3)
S.value_labels(ax, bars, surviving, horizontal=False, pad=0.02)
ax.set_xticks(np.arange(len(levels)), [str(level) for level in levels], fontsize=8)
ax.set_yticks([])
ax.set_ylim(0, max(surviving) * 1.16)
S.despine(ax)

deepest = max(levels)
S.titles(
    ax,
    "Forty-one people each share a body with forty of the others",
    f"People surviving a peel to each depth in the co-membership giant component "
    f"({giant.number_of_nodes()} people). At k the chart counts everyone still "
    f"holding k neighbours once all shallower nodes are stripped away, so the bars "
    f"fall as the requirement tightens. The {deepest}-core — the deepest layer that "
    f"survives at all — holds {sizes[deepest]} people. A group that dense is partly "
    "an artefact of projection, since one committee of forty-one makes every pair "
    "of its members adjacent at a stroke.",
    xlabel="k (neighbours required inside the layer)",
    ylabel="People in the k-core",
    wrap=100,
)
S.save(fig, "fig45_k_core",
       "Bodies with more than 60 recorded members are already excluded from the projection")
