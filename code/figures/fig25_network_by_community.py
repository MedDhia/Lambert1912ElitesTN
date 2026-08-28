"""Fig. 25 — The affiliation network, with each person coloured by community.

Fig. 14 draws the same component to show its shape. This one asks where in that
shape the Tunisian notables sit: at the edge, in their own quarter, or mixed
through it.
"""
import networkx as nx

import _style as S

comm = {r["entry_id"]: r["community_group"] for r in S.read("person_communities.csv")}
nodes = {n["node_id"]: n for n in S.read("network_nodes.csv")}

G = nx.Graph()
for e in S.read("edges_person_organisation.csv"):
    if e["resolution"].startswith("ambiguous"):
        continue  # a surname shared by two people assigns no tie
    G.add_node(e["person_node"], kind="person",
               group=comm.get(e["person_entry_id"], "unknown") or "unknown")
    G.add_node(e["organisation_node"], kind="org", label=e["organisation_name"])
    G.add_edge(e["person_node"], e["organisation_node"])

giant = G.subgraph(max(nx.connected_components(G), key=len)).copy()
pos = nx.spring_layout(giant, k=0.38, iterations=260, seed=11)
degree = dict(giant.degree())
betweenness = nx.betweenness_centrality(giant)
classes = {
    "european": (S.BLUE, "European"),
    "tunisian": (S.ORANGE, "Tunisian"),
    "unknown": (S.DE_EMPHASIS, "Community not settled by the entry"),
}
members = {
    key: [n for n in giant
          if giant.nodes[n]["kind"] == "person" and giant.nodes[n]["group"] == key]
    for key in classes
}
bodies = [n for n in giant if giant.nodes[n]["kind"] == "org"]

fig, ax = S.network_figure(pos)
nx.draw_networkx_edges(giant, pos, ax=ax, edge_color=S.GRID, width=0.7, alpha=0.9)
# Bodies are the scaffold here, not a class of their own: hollow rings, so the
# three person colours are the only fills in the plot.
nx.draw_networkx_nodes(
    giant, pos, nodelist=bodies, ax=ax, node_color=S.SURFACE,
    node_size=[26 + 9 * degree[n] for n in bodies],
    linewidths=1.1, edgecolors=S.INK_MUTED,
)
# Grey first, so an uncoded person never hides a coded one.
for key in ("unknown", "european", "tunisian"):
    colour, name = classes[key]
    nx.draw_networkx_nodes(
        giant, pos, nodelist=members[key], ax=ax, node_color=colour,
        node_size=[12 + 8 * degree[n] for n in members[key]],
        linewidths=0.6, edgecolors=S.SURFACE,
    )
    ax.scatter([], [], s=45, color=colour, label=f"{name} ({len(members[key])})")
ax.scatter([], [], s=55, facecolor=S.SURFACE, edgecolor=S.INK_MUTED, linewidth=1.1,
           label=f"Association or public body ({len(bodies)})")

# The bodies with the most Tunisian members are the point of the figure, so those
# are the ones named rather than the largest bodies overall.
tunisian_share = sorted(
    bodies,
    key=lambda b: -sum(1 for n in giant[b] if giant.nodes[n].get("group") == "tunisian"),
)[:8]
labelled = S.annotate_nodes(ax, [
    (pos[n], nodes.get(n, {}).get("label") or giant.nodes[n].get("label", n))
    for n in tunisian_share
])
ax.legend(loc="upper left", bbox_to_anchor=(-0.02, 1.0))

def mean_betweenness(key: str) -> float:
    return sum(betweenness[n] for n in members[key]) / len(members[key])


S.titles(
    ax,
    "Tunisian notables sit inside the network, not on its rim",
    f"The same largest component as fig. 14 ({giant.number_of_nodes()} nodes, "
    f"{giant.number_of_edges()} ties). Colour is the community the entry's own "
    f"evidence settles — {len(members['european'])} European, "
    f"{len(members['tunisian'])} Tunisian, {len(members['unknown'])} uncoded. The "
    f"{len(members['tunisian'])} Tunisians are not peripheral: their mean "
    f"betweenness ({mean_betweenness('tunisian'):.3f}) exceeds the Europeans' "
    f"({mean_betweenness('european'):.3f}), and they too sit in the community's own "
    f"bodies — the {labelled} with the most Tunisian members are named.",
    wrap=104,
)
S.save(fig, "fig25_network_by_community",
       "Node size is degree; layout is force-directed and identical to fig. 14")
