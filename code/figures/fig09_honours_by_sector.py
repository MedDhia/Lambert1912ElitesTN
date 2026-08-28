"""Fig. 9 — Which occupations each state chose to decorate."""
import collections
import _style as S

persons = S.read("persons.csv")
LABELS = {
    "military": "Military", "politics_native_admin": "Office-holding",
    "administration": "Civil administration", "justice_law": "Law and justice",
    "medicine_health": "Medicine and health", "engineering_architecture": "Engineering",
    "education_science": "Education and science", "commerce": "Commerce",
    "industry_crafts": "Industry and crafts", "agriculture": "Agriculture",
    "diplomacy": "Consular service", "press_letters_arts": "Press, letters, arts",
}
by_sector = collections.defaultdict(list)
for p in persons:
    if p["occupation_primary"]:
        by_sector[p["occupation_primary"]].append(p)
rows = []
for key, people in by_sector.items():
    if len(people) < 25:
        continue
    fr = 100 * sum(1 for p in people if p["has_legion_honneur"] == "1") / len(people)
    tn = 100 * sum(1 for p in people if p["has_nichan_iftikhar"] == "1") / len(people)
    rows.append((LABELS.get(key, key), len(people), fr, tn))
rows.sort(key=lambda r: r[3])

fig, ax = S.figure(7.4, 5.0)
S.grid(ax, axis="x")
for i, (name, n, fr, tn) in enumerate(rows):
    ax.plot([fr, tn], [i, i], color=S.AXIS, linewidth=1.5, zorder=2)
    ax.scatter([fr], [i], s=70, color=S.BLUE, zorder=3,
               edgecolor=S.SURFACE, linewidth=1.5)   # 2px surface ring
    ax.scatter([tn], [i], s=70, color=S.ORANGE, zorder=3,
               edgecolor=S.SURFACE, linewidth=1.5)
ax.set_yticks(range(len(rows)), [f"{name}  (n={n})" for name, n, _, _ in rows])
ax.set_xlim(-3, 100)
ax.set_ylim(-0.8, len(rows) - 0.2)
S.despine(ax)
ax.scatter([], [], s=70, color=S.BLUE, label="Légion d'honneur (France)")
ax.scatter([], [], s=70, color=S.ORANGE, label="Nichan Iftikhar (Bey of Tunis)")
ax.legend(loc="lower right")
S.titles(
    ax,
    "Both states decorate office-holders and soldiers; only the Bey decorates traders",
    "Occupational categories with at least 25 persons. Each pair of dots is one "
    "sector; the gap between them is the difference between the two systems.",
    xlabel="Share of the sector holding the honour (%)",
)
S.save(fig, "fig09_honours_by_sector", "Primary occupational category; multi-label coding in the codebook")
