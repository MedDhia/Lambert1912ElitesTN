"""Fig. 20 — Honours across the two communities."""
import collections
import statistics
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
S.titles(
    ax,
    "Recognition does not divide along the colonial line",
    "Share of each community holding each marker. Neither honour differs "
    "significantly between the two: Fisher exact p = 0.12 for the Légion d'honneur "
    "and p = 0.93 for the Nichan Iftikhar.",
    xlabel="Share of the community (%)",
)
S.save(fig, "fig20_honours_by_community", "Among the 825 notices whose community the entry's own evidence settles")
