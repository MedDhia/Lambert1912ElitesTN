"""Fig. 53 — How much of this network rests on a few people.

Remove people at random and the network barely notices. Remove them in order of
betweenness and it comes apart. That gap is the sharpest statement available of
how concentrated brokerage is here — fig. 30 shows the concentration, this shows
what it costs.
"""
import random

import networkx as nx

import _networks as N
import _ordering as O
import _style as S

giant = N.giant(N.comembership_graph())
start = giant.number_of_nodes()
betweenness = nx.betweenness_centrality(giant)
by_betweenness = O.ranked(betweenness)

rng = random.Random(42)
at_random = sorted(giant)
rng.shuffle(at_random)

STEPS = list(range(0, 221, 10))


def collapse(order):
    remaining = giant.copy()
    curve = []
    for removed in STEPS:
        for node in order[:removed]:
            if node in remaining:
                remaining.remove_node(node)
        largest = max((len(c) for c in nx.connected_components(remaining)), default=0)
        curve.append(100 * largest / start)
    return curve


targeted = collapse(by_betweenness)
random_curve = collapse(at_random)

fig, ax = S.figure(7.6, 4.6)
S.grid(ax)
ax.plot(STEPS, random_curve, color=S.DE_EMPHASIS, linewidth=2.2, zorder=3)
ax.plot(STEPS, targeted, color=S.ORANGE, linewidth=2.2, zorder=4)
ax.annotate("removed at random", xy=(STEPS[-1], random_curve[-1]), xytext=(-6, 12),
            textcoords="offset points", ha="right", fontsize=9, color=S.INK_SECONDARY)
ax.annotate("removed in order of betweenness", xy=(STEPS[-1], targeted[-1]),
            xytext=(-6, 14), textcoords="offset points", ha="right", fontsize=9,
            color=S.ORANGE)
ax.set_xlim(0, STEPS[-1])
ax.set_ylim(0, 104)
S.despine(ax, keep=("bottom", "left"))

index = STEPS.index(80)
S.titles(
    ax,
    "Eighty people hold four fifths of this network together",
    f"The largest surviving component as people are removed from the co-membership "
    f"giant ({start} people), by two orders. Taken at random, {STEPS[index]} "
    f"removals leave {random_curve[index]:.0f}% of the network intact. Taken in "
    f"order of betweenness, the same number leaves {targeted[index]:.0f}%. This is "
    "the ordinary fragility of a network with hubs rather than anything peculiar "
    "to 1912 — but it does mean that conclusions about this elite's cohesion rest "
    "on how a few dozen notices were read.",
    xlabel="People removed",
    ylabel="Largest component (% of the original)",
    wrap=100,
)
S.save(fig, "fig53_attack_tolerance",
       "Random order is seeded; betweenness is computed once, on the intact network")
