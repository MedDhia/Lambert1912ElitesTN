"""Fig. 42 — The giant component, and the islands nobody draws.

Figs. 14, 15, 25 and 30–33 all draw the largest component, because that is where
the structure is. This is the figure that shows what those pictures leave out.
"""
import collections

import numpy as np

import _style as S

rows = [r for r in S.read("person_network_measures.csv") if r["comem_component_size"]]
sizes = [int(r["comem_component_size"]) for r in rows]
giant = max(sizes)
# One entry per component, not per person: dividing the head count by the size
# recovers how many components of that size there are.
per_size = collections.Counter(sizes)
components = {size: count // size for size, count in per_size.items()}

small = sorted(size for size in components if size != giant)
# The tick carries the component size and how many components have it; the bar
# height is how many people that accounts for.
labels = [f"{size}\n×{components[size]}" for size in small] + [f"{giant}\n×1"]
people = [size * components[size] for size in small] + [giant]
colours = [S.RAMP[300]] * len(small) + [S.BLUE]

fig, ax = S.figure(7.6, 4.4)
S.grid(ax)
bars = ax.bar(np.arange(len(labels)), people, width=0.64, color=colours, zorder=3)
S.value_labels(ax, bars, people, horizontal=False, pad=0.03)
# Log scale, because the giant is 25 times the largest fragment and a linear
# axis flattens every other bar into the baseline. Ticks are kept: on a log
# axis the reader cannot infer the spacing from the labelled tips alone.
ax.set_yscale("log")
ax.set_ylim(1, giant * 3.4)
ax.set_xticks(np.arange(len(labels)), labels, fontsize=8)
S.despine(ax, keep=("bottom", "left"))

outside = sum(people[:-1])
S.titles(
    ax,
    "Four in five people sit in one component; the rest sit in fragments",
    f"The co-membership projection broken into its connected components: "
    f"{giant} of the {sum(people)} people with any co-membership tie are in the "
    f"giant, and the remaining {outside} are spread over "
    f"{sum(components[s] for s in small)} components of at most {max(small)}. Every "
    "network figure in this set draws the giant alone, which is defensible and "
    f"worth stating: it omits {100 * outside / sum(people):.0f}% of the people who "
    "have a co-membership tie at all. The tick under each bar gives the component "
    "size and how many components are that size.",
    xlabel="Component size × how many components",
    ylabel="People (log scale)",
    wrap=100,
)
S.save(fig, "fig42_network_components",
       "Absent entirely: 751 notices with no affiliation, and 212 people whose only "
       "bodies were too large for the projection")
