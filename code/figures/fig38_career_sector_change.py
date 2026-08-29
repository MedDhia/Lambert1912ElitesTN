"""Fig. 38 — How many careers cross a sector line at all.

Fig. 18 shows which moves happen. It cannot show how common moving is, because
a chart of transitions counts only the people who made one. This counts people,
including the ones who stayed put.
"""
import collections

import _style as S

sequences = collections.defaultdict(list)
for row in S.read("career_positions.csv"):
    if row["occupation_categories"]:
        sequences[row["entry_id"]].append(
            (int(row["position_order"]), row["occupation_categories"].split(";")[0]))

careers = {entry: sorted(posts) for entry, posts in sequences.items() if len(posts) >= 2}
sectors = {entry: [sector for _, sector in posts] for entry, posts in careers.items()}
never_left = sum(1 for s in sectors.values() if len(set(s)) == 1)
returned = sum(1 for s in sectors.values() if len(set(s)) > 1 and s[0] == s[-1])
ended_elsewhere = len(careers) - never_left - returned

WEDGES = [
    ("Never left one sector", never_left, S.BLUE),
    ("Moved, but ended where they began", returned, S.RAMP[250]),
    ("Ended in a different sector", ended_elsewhere, S.ORANGE),
]

fig, ax = S.figure(7.4, 2.7)
left = 0.0
total = len(careers)
for label, value, colour in WEDGES:
    ax.barh([0], [value], left=left, height=0.5, color=colour, zorder=3)
    # Direct labels inside each segment: nothing here is reachable by colour.
    ax.text(left + value / 2, 0, f"{value}\n{100 * value / total:.0f}%",
            ha="center", va="center", fontsize=9, linespacing=1.35,
            color=S.on_color(colour))
    ax.text(left + value / 2, -0.42, S.shorten(label, 22, 2), ha="center", va="top",
            fontsize=8, color=S.INK_SECONDARY, linespacing=1.35)
    left += value
ax.set_xlim(0, total)
ax.set_ylim(-1.15, 0.5)
ax.set_axis_off()

S.titles(
    ax,
    "Most careers cross a sector line; half still end where they began",
    f"The {total} people with two or more posts whose sector could be coded, by "
    f"whether their recorded career stays inside one sector. "
    f"{100 * (returned + ended_elsewhere) / total:.0f}% leave at least once, yet "
    f"{100 * (never_left + returned) / total:.0f}% finish in the sector they "
    f"started in — of the {returned + ended_elsewhere} who moved, only {returned} "
    "came back. Fig. 18 shows which lines get crossed; this shows how many people "
    "cross one, which a transition count cannot.",
    wrap=100,
)
S.save(fig, "fig38_career_sector_change",
       "Only posts whose sector the occupation coder could read; order is as printed")
