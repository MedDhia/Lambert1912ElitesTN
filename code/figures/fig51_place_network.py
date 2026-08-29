"""Fig. 51 — Places tied by the people who moved between them.

The person → place ties carry birthplaces, residences and properties. Turning
them the other way gives a network of places joined by anyone attached to both,
which traces the routes this elite actually travelled.
"""
import collections
import itertools

import networkx as nx

import _networks as N
import _ordering as O
import _style as S

ties = S.read("edges_person_place.csv")
places_of = collections.defaultdict(set)
labels = {}
for tie in ties:
    places_of[tie["person_node"]].add(tie["place_node"])
    labels[tie["place_node"]] = tie["place_name"]

shared = collections.Counter()
for places in places_of.values():
    for a, b in itertools.combinations(sorted(places), 2):
        shared[(a, b)] += 1

graph = nx.Graph()
for (a, b), weight in sorted(shared.items()):
    graph.add_edge(a, b, weight=weight)
giant = graph.subgraph(max(nx.connected_components(graph), key=len)).copy()
pos = nx.spring_layout(giant, k=0.5, iterations=240, seed=3)
degree = dict(giant.degree())

fig, ax = S.network_figure(pos, header=1.9)
weights = [giant[a][b]["weight"] for a, b in sorted(giant.edges())]
nx.draw_networkx_edges(
    giant, pos, ax=ax, edgelist=sorted(giant.edges()), edge_color=S.GRID,
    width=[0.5 + 0.35 * w for w in weights], alpha=0.9)
nx.draw_networkx_nodes(
    giant, pos, ax=ax, nodelist=sorted(giant), node_color=S.AQUA,
    node_size=[12 + 6 * degree[n] for n in sorted(giant)],
    linewidths=0.6, edgecolors=S.SURFACE)
sizes = {n: 12 + 6 * degree[n] for n in giant}
labelled = S.annotate_nodes(
    ax, [(pos[n], labels.get(n, n), (sizes[n] / 3.1416) ** 0.5)
         for n in O.ranked(degree, n=10)], width=16)

strongest = max(shared.items(), key=lambda kv: (kv[1], kv[0]))
S.titles(
    ax,
    "Every route runs through Tunis",
    f"Places tied when at least one person is attached to both — by birth, "
    f"residence or property. {graph.number_of_nodes()} places carry "
    f"{graph.number_of_edges()} ties, and the largest component holds "
    f"{giant.number_of_nodes()}. Edge width is the number of people on the route; "
    f"the heaviest is {labels[strongest[0][0]]}–{labels[strongest[0][1]]} with "
    f"{strongest[1]}. The {labelled} places with the most connections are named. "
    "The star shape is the Protectorate's own geography: careers ran to the "
    "capital, not between the provinces.",
    wrap=104,
)
S.save(fig, "fig51_place_network",
       "Node size is the number of places connected to; a tie is undated and undirected")
