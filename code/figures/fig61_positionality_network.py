"""Fig. 61 — The co-membership network, coloured by side of the colonial line.

Figs. 56 and 62 give the numbers; this gives the shape they describe. Natives
are not a rim around a colonist core, which is what a segregated elite would
look like. They are scattered through it in small clumps — inside the network,
but sitting with each other.
"""
import networkx as nx

import _networks as N
import _ordering as O
import _positionality as P
import _style as S

coding = P.coding()
giant = N.giant(N.comembership_graph())
betweenness = nx.betweenness_centrality(giant)
names = N.display_names()

by_entry = {}
for node in giant:
    person = coding.get(node)
    by_entry[node] = person["positionality"] if person else "unknown"

ORDER = [(P.NATIVE, "Native"), (P.COLONIST, "Colonist"), ("unknown", "Not placed")]
FILL = {P.NATIVE: S.ORANGE, P.COLONIST: S.BLUE, "unknown": S.DE_EMPHASIS}

pos = nx.spring_layout(giant, k=0.30, iterations=240, seed=9)
sizes = dict(zip(sorted(giant), S.betweenness_sizes(betweenness, sorted(giant))))

fig, ax = S.network_figure(pos, header=2.0)
nx.draw_networkx_edges(giant, pos, ax=ax, edgelist=sorted(giant.edges()),
                       edge_color=S.GRID, width=0.35, alpha=0.65)
for side, label in ORDER:
    nodes = sorted(n for n in giant if by_entry[n] == side)
    if not nodes:
        continue
    nx.draw_networkx_nodes(
        giant, pos, ax=ax, nodelist=nodes, node_color=FILL[side],
        node_size=[sizes[n] for n in nodes], linewidths=0.4,
        edgecolors=S.SURFACE, label=f"{label} ({len(nodes)})")

natives = sorted(n for n in giant if by_entry[n] == P.NATIVE)
labelled = S.annotate_nodes(
    ax, [(pos[n], N.pretty(n, names, {}), (sizes[n] / 3.1416) ** 0.5)
         for n in O.ranked(betweenness, among=natives, n=6)], width=17)
ax.legend(loc="upper right", scatterpoints=1, labelspacing=0.7)

placed = sum(1 for n in giant if by_entry[n] in (P.COLONIST, P.NATIVE))
S.titles(
    ax,
    "Natives sit inside the network, in clumps rather than on the rim",
    f"The co-membership giant component ({giant.number_of_nodes()} people), coloured by "
    f"side of the colonial line and sized by betweenness. {placed} of these people are "
    f"placed at all; the grey are the ones fig. 54 could not reach, and they are not a "
    f"neutral background — some are natives. Nothing here looks like a native periphery: "
    f"the orange sits among the blue, which is what figs. 56 and 57 measure. What the "
    f"eye does pick up is the clumping that fig. 62 tests — orange tends to appear "
    f"beside orange. The {labelled} natives who broker most are named.",
    wrap=104,
)
S.save(fig, "fig61_positionality_network",
       "Node area is linear in betweenness; generically-named bodies excluded")
