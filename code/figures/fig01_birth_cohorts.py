"""Fig. 1 — When the elite of 1912 was born."""
import collections
import _style as S

persons = S.read("persons.csv")
years = [int(p["birth_year"]) for p in persons if p["birth_year"]]
counts = collections.Counter(y // 10 * 10 for y in years)
decades = [d for d in sorted(counts) if 1820 <= d <= 1890]
values = [counts[d] for d in decades]

fig, ax = S.figure(7.2, 4.0)
S.grid(ax)
bars = ax.bar([f"{d}s" for d in decades], values, width=0.62, color=S.BLUE, zorder=3)
# Emphasis: the two decades that supply half the volume.
peak = sorted(range(len(values)), key=lambda i: values[i], reverse=True)[:2]
for i, bar in enumerate(bars):
    if i not in peak:
        bar.set_color(S.RAMP[250])
S.value_labels(ax, bars, values, horizontal=False)
S.despine(ax)
ax.set_yticks([])
ax.set_ylim(0, max(values) * 1.16)
S.titles(
    ax,
    "Half the volume was born in the 1860s and 1870s",
    f"Persons with a readable birth year (n = {len(years)} of {len(persons)}); "
    "18 born before 1820 and 8 after 1890 fall outside the range shown",
)
S.save(fig, "fig01_birth_cohorts", "Birth year is printed for 87% of biographical notices")
