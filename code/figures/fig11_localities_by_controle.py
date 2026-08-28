"""Fig. 11 — The gazetteer's coverage of the Regency."""
import collections
import _style as S

places = S.read("places.csv")
counts = collections.Counter(p["controle_civil"] for p in places if p["controle_civil"])
items = counts.most_common(16)[::-1]
names = [k for k, _ in items]
values = [v for _, v in items]

fig, ax = S.figure(7.2, 5.0)
bars = ax.barh(names, values, height=0.62, color=S.BLUE, zorder=3)
S.value_labels(ax, bars, values)
S.despine(ax, keep=("left",))
ax.set_xticks([])
ax.set_xlim(0, max(values) * 1.12)
unnamed = sum(1 for p in places if not p["controle_civil"])
S.titles(
    ax,
    "Coverage follows the colonial administration, and thickens around Tunis",
    f"Localities per contrôle civil, the French civil district ({sum(counts.values())} "
    f"of {len(places)} localities name one; {unnamed} do not). Top 16 districts shown.",
)
S.save(fig, "fig11_localities_by_controle", "Districts are as printed, including the military territories of the south")
