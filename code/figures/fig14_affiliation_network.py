"""Fig. 14 — The affiliation network: people and the bodies they belonged to."""
import networkx as nx
import _style as S

edges = S.read("edges_person_organisation.csv")
nodes = {n["node_id"]: n for n in S.read("network_nodes.csv")}

G = nx.Graph()
for e in edges:
    if e["resolution"].startswith("ambiguous"):
        continue  # a surname shared by two people assigns no tie
    G.add_node(e["person_node"], kind="person")
    G.add_node(e["organisation_node"], kind="org", label=e["organisation_name"])
    G.add_edge(e["person_node"], e["organisation_node"])

giant = G.subgraph(max(nx.connected_components(G), key=len)).copy()
pos = nx.spring_layout(giant, k=0.38, iterations=260, seed=11)
degree = dict(giant.degree())
people = [n for n in giant if giant.nodes[n]["kind"] == "person"]
bodies = [n for n in giant if giant.nodes[n]["kind"] == "org"]

fig, ax = S.network_figure(pos)
nx.draw_networkx_edges(giant, pos, ax=ax, edge_color=S.GRID, width=0.7, alpha=0.9)
nx.draw_networkx_nodes(
    giant, pos, nodelist=people, ax=ax, node_color=S.BLUE,
    node_size=[10 + 8 * degree[n] for n in people], linewidths=0.6, edgecolors=S.SURFACE,
)
nx.draw_networkx_nodes(
    giant, pos, nodelist=bodies, ax=ax, node_color=S.ORANGE,
    node_size=[26 + 9 * degree[n] for n in bodies], linewidths=0.8, edgecolors=S.SURFACE,
)
# Direct-label the hubs: identity never rests on colour alone.
hubs = sorted(bodies, key=lambda n: -degree[n])[:10]
labelled = S.annotate_nodes(ax, [
    (pos[n], nodes.get(n, {}).get("label") or giant.nodes[n].get("label", n))
    for n in hubs
])
ax.scatter([], [], s=45, color=S.BLUE, label=f"Person ({len(people)})")
ax.scatter([], [], s=45, color=S.ORANGE, label=f"Association or public body ({len(bodies)})")
ax.legend(loc="upper left", bbox_to_anchor=(-0.02, 1.0))
S.titles(
    ax,
    "One connected elite: two thirds of all affiliation ties form a single component",
    f"Largest connected component of the two-mode affiliation network: "
    f"{giant.number_of_nodes()} of {G.number_of_nodes()} nodes and "
    f"{giant.number_of_edges()} ties. Node size is degree; layout is force-directed. "
    f"The {labelled} largest bodies that could be labelled without overlap are named.",
    wrap=104,
)
S.save(fig, "fig14_affiliation_network", "Ties come from printed officer lists and from memberships stated in a person's own entry")
