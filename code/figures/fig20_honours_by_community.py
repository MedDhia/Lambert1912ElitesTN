"""Fig. 20 — Honours across the two communities."""
import collections
import statistics

from scipy.stats import fisher_exact

import _style as S

rows = [r for r in S.read("person_communities.csv")
        if r["community_group"] in ("european", "tunisian")]
groups = collections.defaultdict(list)
for r in rows:
    groups[r["community_group"]].append(r)

MEASURES = [
    ("Légion d'honneur", lambda g: 100 * statistics.fmean(
        [r["has_legion_honneur"] == "1" for r in g])),
    ("Nichan Iftikhar", lambda g: 100 * statistics.fmean(
        [r["has_nichan_iftikhar"] == "1" for r in g])),
    ("Any honour named", lambda g: 100 * statistics.fmean(
        [int(r["n_decorations"]) > 0 for r in g])),
    ("Carries a portrait", lambda g: 100 * statistics.fmean(
        [int(r["n_portraits"]) > 0 for r in g])),
]
labels = [m[0] for m in MEASURES][::-1]
eu = [m[1](groups["european"]) for m in MEASURES][::-1]
tn = [m[1](groups["tunisian"]) for m in MEASURES][::-1]

fig, ax = S.figure(7.4, 3.8)
S.grid(ax, axis="x")
for i, (a, b) in enumerate(zip(eu, tn)):
    ax.plot([a, b], [i, i], color=S.AXIS, linewidth=1.5, zorder=2)
    ax.scatter([a], [i], s=80, color=S.BLUE, zorder=3, edgecolor=S.SURFACE, linewidth=1.5)
    ax.scatter([b], [i], s=80, color=S.ORANGE, zorder=3, edgecolor=S.SURFACE, linewidth=1.5)
    ax.text(max(a, b) + 2, i, f"{b - a:+.0f} pts", va="center", fontsize=8.5,
            color=S.INK_SECONDARY)
ax.set_yticks(range(len(labels)), labels)
ax.set_xlim(0, 80)
ax.set_ylim(-0.6, len(labels) - 0.4)
S.despine(ax)
ax.scatter([], [], s=80, color=S.BLUE, label=f"European (n={len(groups['european'])})")
ax.scatter([], [], s=80, color=S.ORANGE, label=f"Tunisian (n={len(groups['tunisian'])})")
ax.legend(loc="lower right")


def fisher_p(column: str) -> float:
    """Recomputed rather than quoted: this caption was stale once already."""
    table = [[sum(1 for r in groups[g] if r[column] != "1"),
              sum(1 for r in groups[g] if r[column] == "1")]
             for g in ("european", "tunisian")]
    return fisher_exact(table)[1]


legion_p, nichan_p = fisher_p("has_legion_honneur"), fisher_p("has_nichan_iftikhar")
any_honour_table = [[sum(1 for r in groups[g] if int(r["n_decorations"]) == 0),
                     sum(1 for r in groups[g] if int(r["n_decorations"]) > 0)]
                    for g in ("european", "tunisian")]
any_honour_p = fisher_exact(any_honour_table)[1]
legion_eu = 100 * statistics.fmean([r["has_legion_honneur"] == "1"
                                    for r in groups["european"]])
legion_tn = 100 * statistics.fmean([r["has_legion_honneur"] == "1"
                                    for r in groups["tunisian"]])
S.titles(
    ax,
    "Where recognition divides, it favours the Tunisians",
    f"Share of each community holding each marker. The beylical order and the portrait "
    f"do not separate the two (the Nichan Iftikhar at Fisher exact p = {nichan_p:.2f}); "
    f"holding any honour at all does not quite, at p = {any_honour_p:.2f}, and favours "
    f"the Europeans. The French Légion d'honneur does, and in the direction "
    f"a colonial hierarchy would not predict: {legion_tn:.0f}% of coded Tunisians hold "
    f"it against {legion_eu:.0f}% of Europeans (p = {legion_p:.3f}). Read it as a "
    "statement about whom the volume printed — a Tunisian had to be more distinguished "
    "to be in it — rather than about who was decorated in Tunisia.",
    xlabel="Share of the community (%)",
    wrap=100,
)
S.save(fig, "fig20_honours_by_community",
       f"Among the {len(rows)} notices whose community the entry's own evidence settles")
