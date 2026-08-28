"""Fig. 4 — Arrivals in Tunisia, before and after the Protectorate."""
import collections
import _style as S

persons = S.read("persons.csv")
years = [int(p["settled_tunisia_year"]) for p in persons if p["settled_tunisia_year"]]
years = [y for y in years if 1855 <= y <= 1912]
bins = list(range(1855, 1915, 5))
counts = collections.Counter(min(b for b in reversed(bins) if b <= y) for y in years)
values = [counts.get(b, 0) for b in bins]

fig, ax = S.figure(7.4, 4.2)
S.grid(ax)
# Emphasis: the decade after the Treaty of Bardo, when the flow begins.
colors = [S.RAMP[250] if b < 1880 else S.BLUE for b in bins]
ax.bar([b + 2.5 for b in bins], values, width=4.1, color=colors, zorder=3)
ax.axvline(1881, color=S.ORANGE, linewidth=2, zorder=4)
ax.annotate(
    "Treaty of Bardo, 1881",
    xy=(1881, max(values) * 0.95), xytext=(1883, max(values) * 0.95),
    color=S.INK_SECONDARY, fontsize=9, va="center",
)
S.despine(ax)
ax.set_xticks(range(1860, 1915, 10))
ax.set_xlim(1853, 1915)
S.titles(
    ax,
    "Arrivals track the Protectorate, not the conquest",
    f"Persons by five-year period of settlement in Tunisia (n = {len(years)}). "
    "Bars before 1880 shown lighter; 10 earlier arrivals fall outside the range.",
    ylabel="Persons",
)
S.save(fig, "fig04_settlement_timeline", "Settlement year readable for 44% of notices")
