"""Fig. 22 — Occupational profile of each community."""
import collections
import numpy as np
import _style as S

comm = {r["entry_id"]: r["community_group"] for r in S.read("person_communities.csv")}
persons = S.read("persons.csv")
LABELS = {
    "administration": "Civil administration", "military": "Military",
    "justice_law": "Law and justice", "medicine_health": "Medicine and health",
    "education_science": "Education and science", "commerce": "Commerce",
    "industry_crafts": "Industry and crafts",
    "engineering_architecture": "Engineering, architecture",
    "agriculture": "Agriculture", "press_letters_arts": "Press, letters, arts",
    "politics_native_admin": "Office-holding", "diplomacy": "Consular service",
}
counts = collections.defaultdict(collections.Counter)
for p in persons:
    group = comm.get(p["entry_id"])
    if group in ("european", "tunisian") and p["occupation_primary"]:
        counts[group][p["occupation_primary"]] += 1
totals = {g: sum(c.values()) for g, c in counts.items()}
keys = [k for k, _ in counts["european"].most_common() if k in LABELS][:10][::-1]
eu = [100 * counts["european"][k] / totals["european"] for k in keys]
tn = [100 * counts["tunisian"][k] / totals["tunisian"] for k in keys]

y = np.arange(len(keys))
height = 0.36
fig, ax = S.figure(7.4, 5.0)
S.grid(ax, axis="x")
for values, colour, name, offset in (
    (eu, S.BLUE, f"European (n={totals['european']})", 0.5),
    (tn, S.ORANGE, f"Tunisian (n={totals['tunisian']})", -0.5),
):
    bars = ax.barh(y + offset * (height + 0.03), values, height=height,
                   color=colour, label=name, zorder=3)
    for bar, v in zip(bars, values):
        ax.text(bar.get_width() + 0.35, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}", va="center", fontsize=7.5, color=S.INK_SECONDARY)
ax.set_yticks(y, [LABELS[k] for k in keys])
ax.set_xticks([])
ax.set_xlim(0, max(eu + tn) * 1.18)
S.despine(ax, keep=("left",))
ax.legend(loc="lower right")

# Named from the data rather than remembered: an earlier caption called out
# engineering "at more than twice the Tunisian rate" and the coding has since
# moved the ratio to seven.
widest_key, widest_ratio = max(
    ((k, e / t) for k, e, t in zip(keys, eu, tn) if t > 0),
    key=lambda pair: (pair[1], pair[0]))
widest_label = LABELS[widest_key]
S.titles(
    ax,
    "The two communities are recorded in much the same trades",
    f"Share of each community's coded notices, by primary occupational category. Ten "
    f"largest categories. Law, medicine, commerce and the crafts sit within a couple of "
    f"points of each other. The gaps that do open are in the categories tied to one "
    f"state or the other: {widest_label.lower()} is {widest_ratio:.0f} times heavier on "
    f"the European side, and office-holding in the beylical administration — the "
    "Tunisian side's own ladder — barely appears among Europeans at all. See fig. 59 "
    "for the same split drawn on the colonist/native axis.",
    xlabel="Share of the community's notices (%)",
    wrap=100,
)
S.save(fig, "fig22_occupations_by_community",
       f"Among the {totals['european'] + totals['tunisian']} coded notices that name an occupation")
