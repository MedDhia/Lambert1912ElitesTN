"""Fig. 30 — The affiliation network, with nodes sized by betweenness.

Fig. 14 draws this graph sized by degree, which shows the big bodies. Sizing the
same graph by betweenness shows something else: who the network would fall apart
without.
"""
import networkx as nx

import _networks as N
import _style as S

graph, labels, dropped = N.affiliation_graph()
giant = N.giant(graph)
names = N.display_names()

betweenness = nx.betweenness_centrality(giant)
degree = dict(giant.degree())
pos = nx.spring_layout(giant, k=0.38, iterations=260, seed=11)

people = [n for n in giant if giant.nodes[n]["kind"] == "person"]
bodies = [n for n in giant if giant.nodes[n]["kind"] == "org"]

fig, ax = S.network_figure(pos, header=2.0)
nx.draw_networkx_edges(giant, pos, ax=ax, edge_color=S.GRID, width=0.7, alpha=0.9)
for members, colour, name in (
    (people, S.BLUE, "Person"),
    (bodies, S.ORANGE, "Association or public body"),
):
    nx.draw_networkx_nodes(
        giant, pos, nodelist=members, ax=ax, node_color=colour,
        node_size=S.betweenness_sizes(betweenness, members),
        linewidths=0.6, edgecolors=S.SURFACE,
    )
    ax.scatter([], [], s=45, color=colour, label=f"{name} ({len(members)})")

# Label the brokers, not the hubs: that is the whole difference from fig. 14.
# Each label carries its node's radius so the label's backing patch clears the
# mark instead of covering the biggest ones.
sizes = dict(zip(list(giant), S.betweenness_sizes(betweenness, list(giant))))
top = sorted(betweenness, key=lambda n: -betweenness[n])[:12]
labelled = S.annotate_nodes(
    ax, [(pos[n], N.pretty(n, names, labels), (sizes[n] / 3.1416) ** 0.5)
         for n in top], width=18)
ax.legend(loc="upper left", bbox_to_anchor=(-0.02, 1.0), scatterpoints=1)

zero = sum(1 for n in giant if betweenness[n] == 0)
brokers = sorted(people, key=lambda n: -betweenness[n])[:3]
S.titles(
    ax,
    "Brokerage is far more concentrated than membership",
    f"Largest component of the two-mode affiliation network: "
    f"{giant.number_of_nodes()} nodes, {giant.number_of_edges()} ties. "
    f"Area is betweenness, on a linear scale, so it reads as share of shortest "
    f"paths brokered. {zero} of the {giant.number_of_nodes()} nodes "
    f"({100 * zero / giant.number_of_nodes():.0f}%) sit on no shortest path at "
    f"all and are drawn at the floor size. The {labelled} highest that could be "
    f"labelled clear are named — note {N.pretty(brokers[0], names, labels)}, the "
    f"highest-scoring person in the network, on only {degree[brokers[0]]} ties.",
    wrap=104,
)
S.save(fig, "fig30_broker_affiliation_network",
       f"{dropped} ties on generically-named bodies excluded — see _networks.py")
