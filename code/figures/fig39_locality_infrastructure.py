"""Fig. 39 — What the volume records about a locality, and how often nothing.

The locality entries carry infrastructure flags — a station, a market, a school,
Roman remains. Reading them as a description of Tunisia would be a mistake: the
commonest state of a locality entry is that it names none of them.
"""
import collections

import numpy as np

import _style as S

FLAGS = [
    ("has_market", "Market"),
    ("has_railway_station", "Railway station"),
    ("has_school", "School"),
    ("has_roman_ruins", "Roman remains"),
    ("has_post_office", "Post office"),
]
places = S.read("places.csv")
named = collections.Counter()
for place in places:
    hits = tuple(label for key, label in FLAGS if place[key] == "1")
    named[hits] += 1

singles = [(label, sum(1 for p in places if p[key] == "1")) for key, label in FLAGS]
singles.sort(key=lambda row: row[1])
none_at_all = named[()]

fig, ax = S.figure(7.4, 4.4)
S.grid(ax, axis="x")
labels = [label for label, _ in singles] + ["— nothing named —"]
counts = [count for _, count in singles] + [none_at_all]
colours = [S.RAMP[300]] * len(singles) + [S.ORANGE]
bars = ax.barh(np.arange(len(labels)), counts, height=0.62, color=colours, zorder=3)
S.value_labels(ax, bars, counts)
ax.set_yticks(np.arange(len(labels)), labels)
ax.set_xticks([])
ax.set_xlim(0, max(counts) * 1.14)
S.despine(ax, keep=("left",))

several = sum(n for hits, n in named.items() if len(hits) >= 2)
S.titles(
    ax,
    "For half the localities the volume records no amenity at all",
    f"Infrastructure named across the {len(places)} locality entries. Flags are not "
    f"exclusive — {several} entries carry two or more — and the highlighted bar "
    f"counts the entries carrying none, which is {100 * none_at_all / len(places):.0f}% of "
    "them. These columns record what Lambert chose to print about a place, not "
    "what stood there; the post office is rare here because he rarely mentioned "
    "one, not because Tunisia had six.",
    xlabel="Locality entries",
    wrap=100,
)
S.save(fig, "fig39_locality_infrastructure",
       "Flags are set from phrases in the entry text; absence is silence, not a survey")
