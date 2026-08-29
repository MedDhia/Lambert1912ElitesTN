"""Fig. 43 — Who among this elite is recorded as having published.

The OEUVRES rubric names books, papers and pamphlets. Which trades it attaches
to says something about where intellectual authority sat in the Protectorate —
and it is not where a colonial administration's own hierarchy would put it.
"""
import collections

import numpy as np

import _style as S

LABELS = {
    "medicine_health": "Medicine and health", "military": "Military",
    "justice_law": "Law and justice", "industry_crafts": "Industry and crafts",
    "education_science": "Education and science",
    "engineering_architecture": "Engineering, architecture",
    "administration": "Civil administration", "commerce": "Commerce",
    "press_letters_arts": "Press, letters, arts", "agriculture": "Agriculture",
}
persons = S.read("persons.csv")
total = collections.Counter(p["occupation_primary"] for p in persons if p["occupation_primary"])
authors = collections.Counter(
    p["occupation_primary"] for p in persons
    if p["has_works"] == "1" and p["occupation_primary"])

# Sectors with fewer than 25 people are dropped: a share computed on a dozen
# notices swings by eight points on a single author.
rows = [(LABELS[k], 100 * authors[k] / total[k], authors[k], total[k])
        for k in LABELS if total[k] >= 25]
rows.sort(key=lambda r: r[1])
labels = [r[0] for r in rows]
shares = [r[1] for r in rows]
best = max(shares)
colours = [S.BLUE if s == best else S.RAMP[200] for s in shares]

fig, ax = S.figure(7.4, 4.8)
S.grid(ax, axis="x")
bars = ax.barh(np.arange(len(labels)), shares, height=0.64, color=colours, zorder=3)
for bar, (_, share, n, denom) in zip(bars, rows):
    ax.text(bar.get_width() + best * 0.025, bar.get_y() + bar.get_height() / 2,
            f"{share:.0f}%   ({n} of {denom})", va="center", fontsize=8,
            color=S.INK_SECONDARY)
ax.set_yticks(np.arange(len(labels)), labels)
ax.set_xticks([])
ax.set_xlim(0, best * 1.5)
S.despine(ax, keep=("left",))

all_authors = sum(1 for p in persons if p["has_works"] == "1")
S.titles(
    ax,
    "Medicine publishes four times as often as the administration",
    f"Share of each sector's notices whose OEUVRES rubric names a publication. "
    f"{all_authors} of {len(persons):,} notices name one. Medicine leads at "
    f"{best:.0f}%, while civil administration — the largest sector in the volume and "
    f"the one nearest the Protectorate's own authority — reaches "
    f"{100 * authors['administration'] / total['administration']:.0f}%, and commerce "
    "less still. Sectors with fewer than 25 notices are omitted, since one author "
    "would move them several points.",
    xlabel="Notices naming a publication (%)",
    wrap=100,
)
S.save(fig, "fig43_who_writes",
       "Records that the volume printed a work, not whether one was written")
