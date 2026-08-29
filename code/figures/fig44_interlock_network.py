"""Fig. 44 — The bodies, linked by the people they share.

Every other network figure here projects onto people. This projects the other
way: two associations are tied when someone belongs to both. It is the
interlocking-directorate object, and it asks a different question — not who the
elite are, but which institutions their memberships bind together.
"""
import collections
import itertools

import networkx as nx

import _networks as N
import _ordering as O
import _style as S

graph, labels, _ = N.affiliation_graph()
people = [n for n in graph if any(True for _ in graph[n])
          and not n.startswith("ORG:") and n in graph]
bodies_of = collections.defaultdict(set)
for tie in S.read("edges_person_organisation.csv"):
    if tie["resolution"].startswith("ambiguous"):
        continue
    if N.is_unidentifiable(tie["organisation_node"], tie["organisation_name"]):
        continue
    bodies_of[tie["person_node"]].add(tie["organisation_node"])

shared = collections.Counter()
for bodies in bodies_of.values():
    for a, b in itertools.combinations(sorted(bodies), 2):
        shared[(a, b)] += 1

interlock = nx.Graph()
for (a, b), weight in sorted(shared.items()):
    interlock.add_edge(a, b, weight=weight)
giant = interlock.subgraph(max(nx.connected_components(interlock), key=len)).copy()
pos = nx.spring_layout(giant, k=0.42, iterations=240, seed=5)
degree = dict(giant.degree())
names = N.display_names()

fig, ax = S.network_figure(pos, header=1.9)
nx.draw_networkx_edges(giant, pos, ax=ax, edge_color=S.GRID, width=0.7, alpha=0.9)
nx.draw_networkx_nodes(
    giant, pos, ax=ax, node_color=S.ORANGE,
    node_size=[14 + 7 * degree[n] for n in sorted(giant)],
    nodelist=sorted(giant), linewidths=0.6, edgecolors=S.SURFACE)
sizes = {n: 14 + 7 * degree[n] for n in giant}
labelled = S.annotate_nodes(
    ax, [(pos[n], N.pretty(n, names, labels), (sizes[n] / 3.1416) ** 0.5)
         for n in O.ranked(degree, n=7)], width=18)

multi = sum(1 for w in shared.values() if w > 1)
S.titles(
    ax,
    "The associations interlock through one shared member at a time",
    f"Two bodies are tied when at least one person belongs to both. "
    f"{interlock.number_of_nodes()} bodies carry {interlock.number_of_edges()} such "
    f"ties, and the largest component holds {giant.number_of_nodes()} of them. Only "
    f"{multi} of those ties rest on more than a single shared person, and none on "
    f"more than three — this is an elite joined by individuals holding two posts, "
    f"not by institutions with overlapping benches. The {labelled} bodies with the "
    "most interlocks are named.",
    wrap=104,
)
S.save(fig, "fig44_interlock_network",
       "Node size is the number of bodies interlocked with; generically-named bodies excluded")
