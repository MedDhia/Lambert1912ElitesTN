"""Fig. 40 — How big the associations said they were.

Only some entries state a membership. Where they do, the range is four orders of
magnitude: committees of a few dozen alongside a federation claiming twenty
thousand. The projection in `edges_person_person.csv` excludes the largest of
them for exactly this reason, and this is the figure that shows why.
"""
import _style as S

organisations = S.read("organizations.csv")
stated = sorted(
    (int(o["n_members_stated"]), o["organisation_name"])
    for o in organisations if o["n_members_stated"].isdigit())
sizes = [n for n, _ in stated]

fig, ax = S.figure(7.4, 3.7)
S.grid(ax, axis="x")
# One dot per body on a log axis: with n this small a histogram would invent a
# shape, and the individual bodies are recognisable and worth seeing.
ax.scatter(sizes, [0] * len(sizes), s=44, color=S.BLUE, alpha=0.75,
           linewidths=0.6, edgecolors=S.SURFACE, zorder=3)
ax.axvline(60, color=S.ORANGE, linewidth=1.4, zorder=2)
ax.text(60, 0.34, "  60 — bodies above this line are\n  excluded from the one-mode projection",
        ha="left", va="top", fontsize=8, color=S.ORANGE, linespacing=1.4)

# The three largest are the ones the exclusion rule is aimed at, so they are
# named. Stacked at increasing offsets: on a log axis they sit close enough that
# labels at one height would overlap.
for depth, (value, name) in enumerate(stated[-3:]):
    ax.annotate(S.shorten(name, 30, 2), xy=(value, 0), xytext=(0, -22 - 26 * depth),
                textcoords="offset points", ha="center", va="top",
                fontsize=7.5, color=S.INK_SECONDARY, linespacing=1.35,
                arrowprops=dict(arrowstyle="-", color=S.GRID, linewidth=0.8,
                                shrinkA=2, shrinkB=6))

ax.set_xscale("log")
ax.set_ylim(-1.05, 0.45)
ax.set_yticks([])
ax.set_xlim(min(sizes) * 0.6, max(sizes) * 2.2)
S.despine(ax, keep=("bottom",))

above = sum(1 for n in sizes if n > 60)
S.titles(
    ax,
    "A membership roll and a committee are not the same kind of tie",
    f"Every stated membership in the volume: {len(sizes)} of the "
    f"{len(organisations)} association entries give a number, and they run from "
    f"{min(sizes)} to {max(sizes):,} on a log scale. {above} of the {len(sizes)} sit "
    "above the 60-member line at which the co-membership projection stops treating "
    "shared membership as a tie — being one of twenty thousand is not evidence that "
    "any two names on the list knew each other.",
    xlabel="Members stated (log scale)",
    wrap=100,
)
S.save(fig, "fig40_association_size",
       "Self-reported and undated; the other 94 entries state no membership")
