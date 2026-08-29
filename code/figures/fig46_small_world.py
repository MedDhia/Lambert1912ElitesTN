"""Fig. 46 — Short paths, dense neighbourhoods: a small world by construction.

The co-membership network has the two signatures of a small world — almost
everyone within a few steps, and neighbourhoods that close on themselves. The
second is largely built in, and saying so is the point of the figure.
"""
import collections
import random

import networkx as nx
import numpy as np

import _networks as N
import _style as S

giant = N.giant(N.comembership_graph())
nodes = sorted(giant)
# Distances from a seeded sample of sources rather than all pairs: 745 full
# BFS runs would change nothing here and the sample is stated on the face.
rng = random.Random(11)
sources = sorted(rng.sample(nodes, 120))
lengths = collections.Counter()
for source in sources:
    for _, distance in nx.single_source_shortest_path_length(giant, source).items():
        if distance:
            lengths[distance] += 1

total = sum(lengths.values())
distances = sorted(lengths)
share = [100 * lengths[d] / total for d in distances]
cumulative = np.cumsum(share)

fig, ax = S.figure(7.6, 4.6)
S.grid(ax)
bars = ax.bar(np.arange(len(distances)), share, width=0.64, color=S.RAMP[300], zorder=3)
S.value_labels(ax, bars, share, horizontal=False, fmt="{:.0f}%", pad=0.02)
ax.set_xticks(np.arange(len(distances)), [str(d) for d in distances])
ax.set_yticks([])
ax.set_ylim(0, max(share) * 1.18)
S.despine(ax)

mean = sum(d * lengths[d] for d in distances) / total
within_four = cumulative[distances.index(4)]
clustering = nx.average_clustering(giant)
S.titles(
    ax,
    "Any two of these people are four handshakes apart",
    f"Shortest-path lengths from {len(sources)} seeded sources to every other "
    f"person in the co-membership giant component ({giant.number_of_nodes()} "
    f"people). The mean is {mean:.1f} steps and {within_four:.0f}% of pairs lie "
    f"within four. Average clustering is {clustering:.2f}, which with paths this "
    "short is the textbook small-world signature — but the clustering is largely "
    "built in: projecting a committee of n members creates a clique, so closed "
    "triangles are a property of the projection as much as of the elite.",
    xlabel="Steps between two people",
    ylabel="Share of pairs",
    wrap=100,
)
S.save(fig, "fig46_small_world",
       "Sampled sources, seeded for reproducibility; distances within the giant component only")
