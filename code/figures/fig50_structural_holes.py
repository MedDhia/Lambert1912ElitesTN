"""Fig. 50 — Why Burt's constraint does not do much work on this record.

Constraint is meant to separate people whose contacts know each other from
people who span structural holes. On this network it does something else: it
tracks how few contacts a person has. The figure exists to show that, because
constraint is otherwise a tempting column to reach for.
"""
import collections
import math
import statistics

import networkx as nx

import _networks as N
import _style as S

giant = N.giant(N.comembership_graph())
# Constraint is O(degree^2) per node and the hubs here reach several hundred
# neighbours; the cap keeps it tractable and is stated on the face.
CAP = 40
block = giant.subgraph(sorted(n for n in giant if giant.degree(n) <= CAP))
constraint = {n: v for n, v in nx.constraint(block).items() if v == v}
degree = {n: block.degree(n) for n in constraint}

nodes = sorted(constraint)
xs = [degree[n] for n in nodes]
ys = [constraint[n] for n in nodes]
mean_x, mean_y = statistics.fmean(xs), statistics.fmean(ys)
correlation = sum((a - mean_x) * (b - mean_y) for a, b in zip(xs, ys)) / math.sqrt(
    sum((a - mean_x) ** 2 for a in xs) * sum((b - mean_y) ** 2 for b in ys))

by_degree = collections.defaultdict(list)
for node in nodes:
    by_degree[degree[node]].append(constraint[node])
line = sorted((d, statistics.median(v)) for d, v in by_degree.items() if len(v) >= 5)

alone = [n for n in nodes if degree[n] == 1]
rest = [n for n in nodes if degree[n] > 1]

fig, ax = S.figure(7.6, 4.6)
S.grid(ax, axis="both")
ax.scatter([degree[n] for n in rest], [constraint[n] for n in rest],
           s=20, color=S.RAMP[250], linewidths=0, alpha=0.8, zorder=3,
           label=f"Two or more co-members ({len(rest)})")
ax.scatter([degree[n] for n in alone], [constraint[n] for n in alone],
           s=34, color=S.ORANGE, linewidths=0.5, edgecolors=S.SURFACE, zorder=5,
           label=f"A single co-member ({len(alone)})")
ax.plot([d for d, _ in line], [m for _, m in line], color=S.INK_MUTED,
        linewidth=1.6, zorder=4, label="Median at each degree")
ax.set_xlim(0, CAP + 1)
ax.set_ylim(0, 1.1)
S.despine(ax, keep=("bottom", "left"))
ax.legend(loc="upper right", scatterpoints=1)

S.titles(
    ax,
    "Constraint here measures how few people you know, not how closed they are",
    f"Burt's constraint against the number of co-members, for the "
    f"{len(constraint)} people in the co-membership giant component with {CAP} or "
    f"fewer. The two move together almost mechanically (r = {correlation:.2f}): "
    f"the {len(alone)} people at the top of the chart are simply those with a "
    f"single contact, for whom constraint is 1 by definition. Median constraint is "
    f"{statistics.median(ys):.2f}, roughly what three unconnected contacts would "
    "give. Reach for constraint here and you will mostly re-measure degree — the "
    "record rarely gives an ego network rich enough for the measure to bite.",
    xlabel="Co-members (degree, capped at 40)",
    ylabel="Burt's constraint",
    wrap=100,
)
S.save(fig, "fig50_structural_holes",
       "Constraint is undefined for isolates and is computed within the capped subgraph")
