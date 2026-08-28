"""Fig. 2 — What the elite of 1912 did for a living."""
import collections
import _style as S

persons = S.read("persons.csv")
LABELS = {
    "military": "Military", "administration": "Civil administration",
    "justice_law": "Law and justice", "medicine_health": "Medicine and health",
    "education_science": "Education and science", "commerce": "Commerce",
    "industry_crafts": "Industry and crafts",
    "engineering_architecture": "Engineering, architecture",
    "agriculture": "Agriculture", "diplomacy": "Consular service",
    "politics_native_admin": "Office-holding (elective, beylical)",
    "press_letters_arts": "Press, letters, arts", "religion": "Religion",
    "finance_banking": "Finance and banking", "transport_maritime": "Transport, shipping",
    "mining": "Mining", "hospitality_services": "Hotels and services",
}
counts = collections.Counter(
    p["occupation_primary"] for p in persons if p["occupation_primary"]
)
items = counts.most_common()
names = [LABELS.get(k, k) for k, _ in items][::-1]
values = [v for _, v in items][::-1]

fig, ax = S.figure(7.2, 5.6)
bars = ax.barh(names, values, height=0.62, color=S.BLUE, zorder=3)
S.value_labels(ax, bars, values)
S.despine(ax, keep=("left",))
ax.set_xticks([])
ax.set_xlim(0, max(values) * 1.12)
S.titles(
    ax,
    "A service elite: soldiers, officials, lawyers and doctors first",
    f"Primary occupational category, persons with one coded (n = {sum(values)} of "
    f"{len(persons)}). Categories are multi-label; the primary is the first match "
    "in a fixed priority order.",
)
S.save(fig, "fig02_occupations", "19% of notices carry no readable occupation clause")
