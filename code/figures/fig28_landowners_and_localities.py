"""Fig. 28 — The named landowners of the localities, and who they are not.

Locality entries often close with a list of the proprietors of the domains in
the commune. Those names are the volume's only systematic record of rural
property — and they are mostly names the dictionary never biographises.

Each cluster below is one connected group of localities and the owners they
share. The graph is drawn cluster by cluster rather than in one layout because
that is the finding: it does not connect up.
"""
import collections

import numpy as np

import _style as S

owners = [t for t in S.read("edges_person_place.csv") if t["relation"] == "property_owner"]
has_notice = {p["entry_id"] for p in S.read("persons.csv")}

adjacency = collections.defaultdict(set)
label = {}
for tie in owners:
    person = ("person", tie["person_node"])
    place = ("place", tie["place_node"])
    label[person] = tie["person_name"]
    label[place] = tie["place_name"]
    adjacency[person].add(place)
    adjacency[place].add(person)

components = []
seen = set()
for start in adjacency:
    if start in seen:
        continue
    stack, component = [start], set()
    while stack:
        node = stack.pop()
        if node in component:
            continue
        component.add(node)
        stack.extend(adjacency[node] - component)
    seen |= component
    components.append(component)
components.sort(key=len, reverse=True)

# Each component is drawn as its places on a short vertical spine with their
# owners on a ring around them, then packed into a grid: a single force-directed
# layout of 50 disconnected pieces says nothing a grid does not say better.
COLUMNS = 10
X_STEP, Y_STEP = 2.2, 2.1
# The four largest clusters take a row of their own, four across the same width
# the others use ten across. They are the only ones named, and a quarter of the
# row is room enough for a locality name; it also keeps the size difference
# legible instead of burying the 15-owner cluster among the pairs.
NAMED = 4


def cell(index: int) -> tuple[float, float]:
    if index < NAMED:
        return (index * (COLUMNS - 1) * X_STEP / (NAMED - 1), Y_STEP)
    rank = index - NAMED
    return ((rank % COLUMNS) * X_STEP, -(rank // COLUMNS) * Y_STEP)


cell_positions = {}
for index, component in enumerate(components):
    cx, cy = cell(index)
    places = sorted(n for n in component if n[0] == "place")
    people = sorted(n for n in component if n[0] == "person")
    for k, place in enumerate(places):
        cell_positions[place] = (cx, cy + 0.16 * (k - (len(places) - 1) / 2))
    radius = 0.34 + 0.03 * len(people)
    for k, person in enumerate(people):
        angle = 2 * np.pi * k / len(people) + 0.4
        cell_positions[person] = (cx + radius * np.cos(angle),
                                  cy + radius * np.sin(angle))

fig, ax = S.figure(8.4, 5.2)
ax.set_aspect("equal")
ax.set_axis_off()
for node, neighbours in adjacency.items():
    x0, y0 = cell_positions[node]
    # sorted(), not the raw set: set order over string tuples varies with the
    # interpreter's hash seed, so the segments would be drawn in a different
    # order on every run and the PNG would never reproduce byte for byte.
    for other in sorted(neighbours):
        x1, y1 = cell_positions[other]
        ax.plot([x0, x1], [y0, y1], color=S.GRID, linewidth=0.7, zorder=1)

groups = [
    ([n for n in cell_positions if n[0] == "person" and n[1] not in has_notice],
     S.DE_EMPHASIS, 14, "Owner with no notice of their own"),
    ([n for n in cell_positions if n[0] == "person" and n[1] in has_notice],
     S.BLUE, 22, "Owner who also has a biographical notice"),
    ([n for n in cell_positions if n[0] == "place"], S.ORANGE, 30, "Locality"),
]
for members, colour, size, name in groups:
    ax.scatter([cell_positions[n][0] for n in members],
               [cell_positions[n][1] for n in members],
               s=size, color=colour, linewidths=0.5, edgecolors=S.SURFACE,
               zorder=3, label=f"{name} ({len(members)})")
for index, component in enumerate(components[:NAMED]):
    place = max((n for n in component if n[0] == "place"),
                key=lambda n: len(adjacency[n]))
    cx, cy = cell(index)
    # Below the cluster, in data units, so the gap clears its widest owner ring
    # rather than a fixed number of points that a taller cluster grows past.
    ax.text(cx, cy - 0.45 - 0.03 * sum(1 for n in component if n[0] == "person"),
            f"{label[place]} — {len(adjacency[place])} owners",
            ha="center", va="top", fontsize=7, color=S.INK)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.16), ncol=3)

with_notice = len({t["person_node"] for t in owners} & has_notice)
all_owners = len({t["person_node"] for t in owners})
S.titles(
    ax,
    "The named owners of the land are mostly not the people in the book",
    f"{len(owners)} property ties: {all_owners} named owners across "
    f"{len({t['place_node'] for t in owners})} localities, in "
    f"{len(components)} clusters that never join up — "
    f"{sum(1 for c in components if len(c) == 2)} of them a single owner with a "
    f"single estate. Only {with_notice} of the {all_owners} owners have a "
    "biographical notice: the volume records rural property without recording the "
    "proprietors as persons.",
    wrap=100,
)
S.save(fig, "fig28_landowners_and_localities",
       "Owners as printed in the locality entries; positions are a packing, not a layout")
