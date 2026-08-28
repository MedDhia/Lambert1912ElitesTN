"""Fig. 19 — The communities the volume records."""
import collections
import _style as S

rows = S.read("person_communities.csv")
LABELS = {
    "european_french": "European — French", "european_italian": "European — Italian",
    "european_maltese": "European — Maltese", "european_other": "European — other",
    "tunisian_muslim": "Tunisian — Muslim", "tunisian_jewish": "Tunisian — Jewish",
    "unknown": "Not classifiable",
}
counts = collections.Counter(r["community"] for r in rows)
order = ["european_french", "european_italian", "european_other", "european_maltese",
         "tunisian_muslim", "tunisian_jewish", "unknown"]
names = [LABELS[k] for k in order][::-1]
values = [counts[k] for k in order][::-1]
colors = [S.DE_EMPHASIS if k == "unknown" else
          (S.BLUE if k.startswith("european") else S.ORANGE) for k in order][::-1]

fig, ax = S.figure(7.4, 4.4)
bars = ax.barh(names, values, height=0.62, color=colors, zorder=3)
S.value_labels(ax, bars, values)
S.despine(ax, keep=("left",))
ax.set_xticks([])
ax.set_xlim(0, max(values) * 1.14)
ax.scatter([], [], s=45, color=S.BLUE, label="European")
ax.scatter([], [], s=45, color=S.ORANGE, label="Tunisian")
ax.scatter([], [], s=45, color=S.DE_EMPHASIS, label="Evidence insufficient")
ax.legend(loc="lower right")
eu = sum(counts[k] for k in order if k.startswith("european"))
tn = sum(counts[k] for k in order if k.startswith("tunisian"))
S.titles(
    ax,
    "Four Europeans recorded for every Tunisian",
    f"Community coded from institutional, educational and birthplace evidence in "
    f"each entry ({eu} European, {tn} Tunisian, {counts['unknown']} not classifiable "
    f"of {len(rows)}). Nobody is classified from a surname.",
)
S.save(fig, "fig19_community_composition", "Coding rules and the evidence behind each row are in person_communities.csv")
