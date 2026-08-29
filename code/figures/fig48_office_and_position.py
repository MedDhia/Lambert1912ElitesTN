"""Fig. 48 — Office-holders sit differently in the network from ordinary members.

Fig. 17 shows that the volume mostly records officers. This asks whether that
recording bias also picks out a structural position, or merely a title.
"""
import collections
import statistics

import numpy as np

import _style as S

OFFICE = {"president", "honorary_president", "past_president", "vice_president",
          "honorary_vice_president", "secretary", "secretary_general",
          "deputy_secretary", "treasurer", "deputy_treasurer", "director",
          "founder"}

roles = collections.defaultdict(set)
for tie in S.read("edges_person_organisation.csv"):
    if not tie["resolution"].startswith("ambiguous"):
        roles[tie["person_node"]].add(tie["role"])

measures = {m["node_id"]: m for m in S.read("person_network_measures.csv")}
groups = collections.defaultdict(list)
for node, held in sorted(roles.items()):
    row = measures.get(node)
    if not row or not row["comem_betweenness"]:
        continue
    key = "office" if held & OFFICE else "member"
    groups[key].append((float(row["comem_betweenness"]), int(row["affil_degree"])))

PANELS = [
    ("Mean betweenness", 0, "{:.4f}"),
    ("Mean bodies belonged to", 1, "{:.2f}"),
]
BARS = [("Holds an office", "office", S.BLUE), ("Ordinary member", "member", S.DE_EMPHASIS)]

fig, axes = S.plt.subplots(1, 2, figsize=(8.2, 4.0))
for ax, (heading, index, fmt) in zip(axes, PANELS):
    values = [statistics.fmean(v[index] for v in groups[key]) for _, key, _ in BARS]
    S.grid(ax)
    bars = ax.bar(np.arange(len(BARS)), values, width=0.5,
                  color=[c for _, _, c in BARS], zorder=3)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.02,
                fmt.format(value), ha="center", va="bottom", fontsize=9,
                color=S.INK_SECONDARY)
    ax.set_xticks(np.arange(len(BARS)), [label for label, _, _ in BARS], fontsize=8.5)
    ax.set_yticks([])
    ax.set_ylim(0, max(values) * 1.22)
    S.despine(ax)
    ax.set_title(heading, fontsize=9.5, color=S.INK_SECONDARY, loc="left", pad=8)

# The title block is three wrapped lines of figure-level text sitting above the
# axes; the panel headings need the axes pulled down or the two meet.
fig.subplots_adjust(wspace=0.28, bottom=0.12, top=0.80)
ratio = (statistics.fmean(v[0] for v in groups["office"])
         / statistics.fmean(v[0] for v in groups["member"]))
fig.suptitle("Holding office is a structural position, not just a title",
             x=0.008, y=1.10, ha="left", fontsize=12, fontweight="bold", color=S.INK)
fig.text(0.008, 1.06,
         f"The {len(groups['office'])} people recorded in at least one office against the "
         f"{len(groups['member'])} recorded only as members.\nOffice-holders sit on "
         f"{ratio:.1f} times as many shortest paths and belong to more bodies. The "
         "direction is unsurprising; the size is not,\nand some of it is recording rather "
         "than structure — an officer is named in the body's own entry, a member usually "
         "is not.",
         ha="left", va="top", fontsize=8.5, color=S.INK_SECONDARY, linespacing=1.5)
S.save(fig, "fig48_office_and_position",
       "Anyone holding an office anywhere counts as an office-holder")
