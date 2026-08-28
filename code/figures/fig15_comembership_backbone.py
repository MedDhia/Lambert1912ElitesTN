"""Fig. 15 — Who sits on committees with whom."""
import collections
import networkx as nx
import _style as S

pairs = S.read("edges_person_person.csv")
persons = {p["entry_id"]: p for p in S.read("persons.csv")}
# network_nodes.csv carries a display label for every node, including the people
# who are named only inside someone else's entry and so have no notice.
names = {n["node_id"]: n["label"] for n in S.read("network_nodes.csv")}

G = nx.Graph()
for r in pairs:
    G.add_edge(r["source"], r["target"], weight=int(r["weight"]))
giant = G.subgraph(max(nx.connected_components(G), key=len)).copy()
pos = nx.spring_layout(giant, k=0.30, iterations=240, seed=7)
degree = dict(giant.degree())

# All-pairs colour forms cap at three slots: the three largest sectors are
# named, everything else is the de-emphasis grey.
counts = collections.Counter(
    persons[n]["occupation_primary"] for n in giant
    if n in persons and persons[n]["occupation_primary"]
)
top = [k for k, _ in counts.most_common(3)]
LABELS = {"military": "Military", "administration": "Civil administration",
          "justice_law": "Law and justice", "medicine_health": "Medicine and health",
          "commerce": "Commerce", "education_science": "Education and science"}
palette = dict(zip(top, S.SERIES[:3]))

fig, ax = S.network_figure(pos, header=1.9)
nx.draw_networkx_edges(giant, pos, ax=ax, edge_color=S.GRID, width=0.5, alpha=0.85)
for key in top + [None]:
    members = [
        n for n in giant
        if (persons.get(n, {}).get("occupation_primary") or None) == key
        or (key is None and persons.get(n, {}).get("occupation_primary", "") not in top)
    ]
    if not members:
        continue
    nx.draw_networkx_nodes(
        giant, pos, nodelist=members, ax=ax,
        node_color=palette.get(key, S.DE_EMPHASIS),
        node_size=[14 + 5 * degree[n] for n in members],
        linewidths=0.6, edgecolors=S.SURFACE,
        label=(f"{LABELS.get(key, key)} ({len(members)})" if key
               else f"Other or not coded ({len(members)})"),
    )
labelled = S.annotate_nodes(ax, [
    (pos[n], names.get(n, n).replace("NAME:", "").title())
    for n in sorted(degree, key=lambda n: -degree[n])[:9]
], width=16)
ax.legend(loc="upper left", bbox_to_anchor=(-0.01, 1.0), scatterpoints=1)
S.titles(
    ax,
    "Four in five committee-sharers sit in a single connected core",
    f"Largest component of the co-membership projection: {giant.number_of_nodes()} "
    f"of {G.number_of_nodes()} people who share at least one body, "
    f"{giant.number_of_edges()} ties. Node size is the number of co-members; the "
    f"{labelled} best-connected people are named. Most of this network has no "
    "occupation because most of it has no notice: these are people the volume "
    "names in someone else's entry only.",
    wrap=100,
)
S.save(fig, "fig15_comembership_backbone", "Bodies with more than 60 recorded members are excluded from the projection")
