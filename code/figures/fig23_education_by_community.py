"""Fig. 23 — Two educational systems, side by side."""
import collections
import _style as S

comm = {r["entry_id"]: r["community_group"] for r in S.read("person_communities.csv")}
education = S.read("education.csv")
LABELS = {
    "secondary_lycee": "Lycée", "secondary_college": "Collège",
    "university_faculty": "University faculty", "teacher_training": "École normale",
    "grande_ecole": "Grande école", "institute": "Institute",
    "islamic_institution": "Islamic institution\n(Zitouna, Khaldounia, Sadiki)",
    "technical_school": "Technical school", "other": "Other",
}
people = collections.defaultdict(set)
counts = collections.defaultdict(collections.Counter)
for r in education:
    group = comm.get(r["entry_id"])
    if group in ("european", "tunisian"):
        counts[group][r["institution_kind"]] += 1
        people[group].add(r["entry_id"])
totals = {g: sum(c.values()) for g, c in counts.items()}
keys = ["secondary_lycee", "secondary_college", "university_faculty",
        "teacher_training", "grande_ecole", "islamic_institution"][::-1]
eu = [100 * counts["european"][k] / totals["european"] for k in keys]
tn = [100 * counts["tunisian"][k] / totals["tunisian"] for k in keys]

fig, ax = S.figure(7.4, 4.2)
S.grid(ax, axis="x")
for i, (a, b) in enumerate(zip(eu, tn)):
    ax.plot([a, b], [i, i], color=S.AXIS, linewidth=1.5, zorder=2)
    # Where the two shares coincide one dot hides the other, which reads as a
    # missing series; separate them just enough to show both.
    nudge = 0.09 if abs(a - b) < 0.5 else 0.0
    ax.scatter([a], [i + nudge], s=80, color=S.BLUE, zorder=3,
               edgecolor=S.SURFACE, linewidth=1.5)
    ax.scatter([b], [i - nudge], s=80, color=S.ORANGE, zorder=3,
               edgecolor=S.SURFACE, linewidth=1.5)
ax.set_yticks(range(len(keys)), [LABELS[k] for k in keys])
ax.set_xlim(-1, max(eu + tn) * 1.15)
ax.set_ylim(-0.6, len(keys) - 0.4)
S.despine(ax)
ax.scatter([], [], s=80, color=S.BLUE,
           label=f"European ({len(people['european'])} people)")
ax.scatter([], [], s=80, color=S.ORANGE,
           label=f"Tunisian ({len(people['tunisian'])} people)")
ax.legend(loc="lower right")
islamic = 100 * counts["tunisian"]["islamic_institution"] / totals["tunisian"]
closest = min(keys, key=lambda k: (
    abs(100 * counts["european"][k] / totals["european"]
        - 100 * counts["tunisian"][k] / totals["tunisian"]), k))
S.titles(
    ax,
    "The Islamic institutions educate Tunisians only — the French ones educate both",
    f"Share of each community's institution mentions, by kind. Zitouna, the Khaldounia "
    f"and the Collège Sadiki account for {islamic:.0f}% of the "
    f"{totals['tunisian']} Tunisian mentions and for none at all of the "
    f"{totals['european']} European ones, while every French institution on the chart "
    f"carries both communities. The nearest thing to a shared credential is the "
    f"{LABELS[closest].lower()}, where the two shares are within half a point — close "
    "enough that the dots are nudged apart to stay visible.",
    xlabel="Share of the community's institution mentions (%)",
    wrap=100,
)
S.save(fig, "fig23_education_by_community", "Institutions named in the ETUDES rubric; a person may name several")
