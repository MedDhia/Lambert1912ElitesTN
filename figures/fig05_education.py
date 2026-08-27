"""Fig. 5 — Where they were schooled."""
import collections
import _style as S

education = S.read("education.csv")
LABELS = {
    "secondary_lycee": "Lycée", "secondary_college": "Collège",
    "university_faculty": "University faculty", "teacher_training": "École normale",
    "grande_ecole": "Grande école", "institute": "Institute",
    "islamic_institution": "Islamic institution\n(Zitouna, Khaldounia, Sadiki)",
    "other": "Other / unclassified",
}
counts = collections.Counter(r["institution_kind"] for r in education)
items = [(k, v) for k, v in counts.most_common()][::-1]
names = [LABELS.get(k, k) for k, _ in items]
values = [v for _, v in items]

fig, ax = S.figure(7.2, 4.4)
colors = [S.ORANGE if k == "islamic_institution" else S.BLUE for k, _ in items]
bars = ax.barh(names, values, height=0.62, color=colors, zorder=3)
S.value_labels(ax, bars, values)
S.despine(ax, keep=("left",))
ax.set_xticks([])
ax.set_xlim(0, max(values) * 1.12)
S.titles(
    ax,
    "A French secondary education is the common credential",
    f"Institutions named in the ETUDES rubric ({len(education)} mentions by "
    f"{len({r['entry_id'] for r in education})} persons; a person may name several). "
    "Islamic institutions highlighted.",
)
S.save(fig, "fig05_education", "The ETUDES rubric is present in 58% of notices")
