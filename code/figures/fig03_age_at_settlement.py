"""Fig. 3 — How old they were when they came to Tunisia."""
import _style as S

persons = S.read("persons.csv")
ages = [
    int(p["settled_tunisia_year"]) - int(p["birth_year"])
    for p in persons
    if p["birth_year"] and p["settled_tunisia_year"]
]
ages = [a for a in ages if 0 <= a <= 70]
median = sorted(ages)[len(ages) // 2]

fig, ax = S.figure(7.2, 4.0)
S.grid(ax)
ax.hist(ages, bins=range(0, 72, 2), color=S.BLUE, zorder=3, rwidth=0.86)
ax.axvline(median, color=S.ORANGE, linewidth=2, zorder=4)
ax.annotate(
    f"median {median} years",
    xy=(median, ax.get_ylim()[1] * 0.92), xytext=(median + 3, ax.get_ylim()[1] * 0.92),
    color=S.INK_SECONDARY, fontsize=9, va="center",
)
S.despine(ax)
S.titles(
    ax,
    "They arrived young — a career made in the Protectorate, not brought to it",
    f"Years between birth and the date of settlement in Tunisia (n = {len(ages)}). "
    "The settlement date is an interpretation of the bare date Lambert prints "
    "after the address; see the codebook.",
    xlabel="Age on arrival in Tunisia",
    ylabel="Persons",
)
S.save(fig, "fig03_age_at_settlement", "Both dates readable for 40% of notices")
