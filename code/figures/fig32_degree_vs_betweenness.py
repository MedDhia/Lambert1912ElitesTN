"""Fig. 32 — What sizing by betweenness adds to sizing by degree.

A fair question to put to figs. 30 and 31: if the brokers are just the
best-connected nodes, betweenness is decoration. The answer is not a clean no.
The two measures correlate strongly. What betweenness adds is the spread: at any
given number of ties, some people sit on many times more paths than their peers,
and a ranking by degree cannot see them.
"""
import collections
import math
import statistics

import networkx as nx

import _networks as N
import _style as S

graph, labels, _ = N.affiliation_graph()
giant = N.giant(graph)
names = N.display_names()

betweenness = nx.betweenness_centrality(giant)
degree = dict(giant.degree())
brokers = set(sorted(betweenness, key=lambda n: -betweenness[n])[:20])
rest = [n for n in giant if n not in brokers]

# The median at each degree is the "typical" node with that many ties. Degrees
# with fewer than five nodes are dropped: a median of two points is not one.
by_degree = collections.defaultdict(list)
for node in giant:
    by_degree[degree[node]].append(betweenness[node])
typical = sorted((d, statistics.median(v)) for d, v in by_degree.items() if len(v) >= 5)

fig, ax = S.figure(7.6, 5.0)
S.grid(ax, axis="both")
ax.scatter([degree[n] for n in rest], [betweenness[n] for n in rest],
           s=20, color=S.DE_EMPHASIS, linewidths=0, zorder=3, alpha=0.8,
           label=f"Everyone else ({len(rest)})")
ax.plot([d for d, _ in typical], [m for _, m in typical],
        color=S.INK_MUTED, linewidth=1.4, zorder=4,
        label="Median at each number of ties")
ax.scatter([degree[n] for n in brokers], [betweenness[n] for n in brokers],
           s=52, color=S.BLUE, linewidths=0.6, edgecolors=S.SURFACE, zorder=5,
           label=f"The {len(brokers)} highest-betweenness nodes")

# Name the brokers holding fewest ties -- the ones a degree ranking would miss.
fewest = sorted(brokers, key=lambda n: degree[n])[:8]
placed = S.annotate_nodes(
    ax, [((degree[n], betweenness[n]), N.pretty(n, names, labels)) for n in fewest],
    fontsize=7, width=17)

ax.set_xscale("log")
ax.set_xlim(0.85, max(degree.values()) * 1.6)
ax.set_ylim(-0.012, max(betweenness.values()) * 1.1)
S.despine(ax, keep=("bottom", "left"))
ax.legend(loc="upper left", scatterpoints=1)

xs = [degree[n] for n in giant]
ys = [betweenness[n] for n in giant]
mx, my = statistics.mean(xs), statistics.mean(ys)
correlation = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / math.sqrt(
    sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
small = sum(1 for n in brokers if degree[n] < 10)
# The example has to be one of the marked nodes, or the reader cannot find it.
leanest = min(brokers, key=lambda n: degree[n])
typical_at = statistics.median(by_degree[degree[leanest]])

S.titles(
    ax,
    "Degree mostly predicts brokerage — and misses the people who matter most",
    f"Every node in the affiliation network's largest component. Degree and "
    f"betweenness correlate strongly (r = {correlation:.2f}), so sizing by "
    f"betweenness is not a different ranking so much as a sharper one: "
    f"{small} of the {len(brokers)} highest-betweenness nodes hold fewer than ten "
    f"ties, and their scores run far above the median for their degree. "
    f"{N.pretty(leanest, names, labels)} holds {degree[leanest]} and still sits "
    f"on {betweenness[leanest] / (typical_at or 1):.0f} times as many paths as "
    f"the typical {degree[leanest]}-tie node.",
    xlabel="Ties held (degree, log scale)",
    ylabel="Betweenness centrality",
    wrap=100,
)
S.save(fig, "fig32_degree_vs_betweenness",
       "A node well above the line is the only route between parts of the network")
