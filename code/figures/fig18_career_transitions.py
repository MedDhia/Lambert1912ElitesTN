"""Fig. 18 — What follows what in a colonial career."""
import collections
import itertools
import numpy as np
import _style as S

career = S.read("career_positions.csv")
LABELS = {
    "military": "Military", "administration": "Civil admin.",
    "justice_law": "Law", "medicine_health": "Medicine",
    "education_science": "Education", "commerce": "Commerce",
    "industry_crafts": "Industry", "engineering_architecture": "Engineering",
    "agriculture": "Agriculture", "diplomacy": "Consular",
    "politics_native_admin": "Office-holding", "press_letters_arts": "Press, arts",
    "finance_banking": "Finance", "transport_maritime": "Transport",
    "religion": "Religion", "mining": "Mining",
}
sequences = collections.defaultdict(list)
for row in career:
    if row["occupation_categories"]:
        sequences[row["entry_id"]].append(
            (int(row["position_order"]), row["occupation_categories"].split(";")[0])
        )
transitions = collections.Counter()
n_persons = sum(1 for steps in sequences.values() if len(steps) >= 2)
for steps in sequences.values():
    ordered = [c for _, c in sorted(steps)]
    for a, b in itertools.pairwise(ordered):
        if a != b:  # a move inside a sector is not a transition between sectors
            transitions[(a, b)] += 1

totals = collections.Counter()
for (a, b), n in transitions.items():
    totals[a] += n
    totals[b] += n
keys = [k for k, _ in totals.most_common(8)]
matrix = np.array([[transitions.get((a, b), 0) for b in keys] for a in keys], float)

fig, ax = S.figure(6.8, 5.6)
im = ax.imshow(matrix, cmap="Blues", vmin=0, vmax=matrix.max())
ax.set_xticks(range(len(keys)), [LABELS.get(k, k) for k in keys],
              rotation=40, ha="right")
ax.set_yticks(range(len(keys)), [LABELS.get(k, k) for k in keys])
for i in range(len(keys)):
    for j in range(len(keys)):
        if matrix[i, j]:
            ax.text(j, i, int(matrix[i, j]), ha="center", va="center", fontsize=8,
                    color=S.SURFACE if matrix[i, j] > matrix.max() * 0.55 else S.INK)
ax.set_xlabel("Sector of the next post")
ax.set_ylabel("Sector of the previous post")
S.despine(ax, keep=())
ax.tick_params(length=0)
bar = fig.colorbar(im, ax=ax, shrink=0.62, pad=0.03)
bar.outline.set_visible(False)
bar.set_label("Transitions recorded", color=S.INK_SECONDARY, fontsize=8.5)
S.titles(
    ax,
    "Careers move between the army, the administration and the courts",
    f"Consecutive posts in the SUCCESS' rubric, for the {n_persons} persons whose "
    "career sequence carries at least two coded posts. Moves within a sector are "
    "excluded, so the diagonal is empty by construction.",
    wrap=88,
)
S.save(fig, "fig18_career_transitions", "Sequence is Lambert's printed order, which normally but not always runs chronologically")
