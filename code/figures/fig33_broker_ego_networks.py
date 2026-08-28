"""Fig. 33 — Why these four are brokers: the bodies they alone hold together.

Each panel takes one high-betweenness person and draws the bodies they belong
to. A grey arc joins two bodies that share some *other* member — a connection
that would survive if this person were removed. Their scarcity is the point: a
body sitting on the ring with no arc is one this person alone reaches.
"""
import itertools

import networkx as nx
import numpy as np

import _networks as N
import _style as S

graph, labels, _ = N.affiliation_graph()
giant = N.giant(graph)
names = N.display_names()
betweenness = nx.betweenness_centrality(giant)

people = [n for n in giant if giant.nodes[n]["kind"] == "person"]
brokers = N.ranked(betweenness, among=people, n=4)

fig, axes = S.plt.subplots(1, 4, figsize=(9.6, 3.8))
# Room at the foot for the legend, which otherwise lands below the source line.
fig.subplots_adjust(bottom=0.16)
for ax, broker in zip(axes, brokers):
    bodies = sorted(giant[broker])
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_xlim(-1.55, 1.55)
    ax.set_ylim(-1.55, 1.55)

    ring = {}
    for index, body in enumerate(bodies):
        angle = 2 * np.pi * index / len(bodies) - np.pi / 2
        ring[body] = (np.cos(angle), np.sin(angle))

    # Spokes: this person's own ties.
    for body, (x, y) in ring.items():
        ax.plot([0, x], [0, y], color=S.RAMP[200], linewidth=0.8, zorder=1)
    # Arcs: a link between two bodies that does not run through this person.
    shared = 0
    for a, b in itertools.combinations(bodies, 2):
        if (set(giant[a]) & set(giant[b])) - {broker}:
            shared += 1
            ax.plot([ring[a][0], ring[b][0]], [ring[a][1], ring[b][1]],
                    color=S.INK_MUTED, linewidth=0.9, zorder=2)
    ax.scatter([p[0] for p in ring.values()], [p[1] for p in ring.values()],
               s=42, color=S.ORANGE, linewidths=0.6, edgecolors=S.SURFACE, zorder=3)
    ax.scatter([0], [0], s=110, color=S.BLUE, linewidths=0.8,
               edgecolors=S.SURFACE, zorder=4)

    pairs = len(bodies) * (len(bodies) - 1) // 2
    ax.set_title(S.shorten(N.pretty(broker, names, labels), 18, 2),
                 fontsize=8.5, color=S.INK, pad=6)
    ax.text(0, -1.5, f"{len(bodies)} bodies · {shared} of {pairs} pairs\nlinked "
            f"without them", ha="center", va="top", fontsize=7,
            color=S.INK_SECONDARY, linespacing=1.45)

axes[0].scatter([], [], s=60, color=S.BLUE, label="The broker")
axes[0].scatter([], [], s=42, color=S.ORANGE, label="A body they belong to")
axes[0].plot([], [], color=S.INK_MUTED, linewidth=0.9,
             label="Two bodies sharing another member")
fig.legend(loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.005), scatterpoints=1)

fig.suptitle("Take one person out and these bodies stop touching",
             x=0.008, y=1.14, ha="left", fontsize=12, fontweight="bold", color=S.INK)
fig.text(0.008, 1.10,
         "The four highest-betweenness people in the affiliation network, each "
         "with the bodies they belong to arranged\naround them. A grey chord "
         "joins two bodies that share a member other than this person — a tie "
         "that would outlive their\nremoval. Most pairs have none: Zuretti's "
         "25 bodies share no other member at all, so all 300 pairs run through him.",
         ha="left", va="top", fontsize=8.5, color=S.INK_SECONDARY, linespacing=1.5)
S.save(fig, "fig33_broker_ego_networks",
       "Bodies with no dictionary entry and a generic printed name are excluded")
