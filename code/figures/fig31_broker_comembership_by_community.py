"""Fig. 31 — Who brokers in the co-membership network, and from which community.

`docs/comparison_tables.md` reports that Tunisian notables sit on more shortest
paths than Europeans once degree, closeness and clustering are controlled
(b = 0.35 SD, t = 2.31). That is a coefficient. This is the picture behind it.
"""
import collections

import networkx as nx

import _networks as N
import _style as S

giant = N.giant(N.comembership_graph())
names = N.display_names()
community = N.person_communities()

betweenness = nx.betweenness_centrality(giant)
degree = dict(giant.degree())
pos = nx.spring_layout(giant, k=0.30, iterations=240, seed=7)

CLASSES = {
    "european": (S.BLUE, "European"),
    "tunisian": (S.ORANGE, "Tunisian"),
    "unknown": (S.DE_EMPHASIS, "Community not settled by the entry"),
}
members = collections.defaultdict(list)
for node in giant:
    members[community.get(node, "unknown") if community.get(node) in CLASSES
            else "unknown"].append(node)

fig, ax = S.network_figure(pos, header=2.0)
nx.draw_networkx_edges(giant, pos, ax=ax, edge_color=S.GRID, width=0.5, alpha=0.85)
# Grey first, so an uncoded person never covers a coded one.
for key in ("unknown", "european", "tunisian"):
    colour, name = CLASSES[key]
    nx.draw_networkx_nodes(
        giant, pos, nodelist=members[key], ax=ax, node_color=colour,
        node_size=S.betweenness_sizes(betweenness, members[key]),
        linewidths=0.6, edgecolors=S.SURFACE,
    )
    ax.scatter([], [], s=45, color=colour, label=f"{name} ({len(members[key])})")

sizes = dict(zip(list(giant), S.betweenness_sizes(betweenness, list(giant))))
labelled = S.annotate_nodes(
    ax, [(pos[n], N.pretty(n, names), (sizes[n] / 3.1416) ** 0.5)
         for n in N.ranked(betweenness, n=10)], width=16)
ax.legend(loc="upper left", bbox_to_anchor=(-0.01, 1.0), scatterpoints=1)


def mean_betweenness(key: str) -> float:
    return sum(betweenness[n] for n in members[key]) / max(len(members[key]), 1)


coded = len(members["european"]) + len(members["tunisian"])
S.titles(
    ax,
    "The brokers are not all Europeans",
    f"Largest component of the co-membership projection: {giant.number_of_nodes()} "
    f"people, {giant.number_of_edges()} ties, area linear in betweenness. Colour "
    f"is the community the entry's own evidence settles, which it does for "
    f"{coded} of these {giant.number_of_nodes()} people "
    f"({100 * coded / giant.number_of_nodes():.0f}%) — the grey majority are named "
    f"only inside someone else's entry and have no notice to code. Among those "
    f"coded, mean betweenness is {mean_betweenness('tunisian'):.4f} for Tunisians "
    f"against {mean_betweenness('european'):.4f} for Europeans. The {labelled} "
    "highest that could be labelled clear are named.",
    wrap=104,
)
S.save(fig, "fig31_broker_comembership_by_community",
       "Bodies with more than 60 recorded members are excluded from the projection")
