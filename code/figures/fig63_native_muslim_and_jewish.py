"""Fig. 63 — The native side is two populations, not one.

Putting Jews on the native side of the line, as the volume itself does, is a
claim about position and not about sameness. Split the native side and the two
halves turn out to occupy almost disjoint parts of the record: one in the
beylical state, the other in the professions and trade.
"""
import collections
import statistics

import numpy as np

import _positionality as P
import _style as S

rows = collections.defaultdict(list)
for person in P.placed():
    detail = person["position_detail"]
    if detail.startswith("native_jewish"):
        rows["jewish"].append(person)     # the two Grana included: same population
    elif detail == "native_muslim":
        rows["muslim"].append(person)

GROUPS = [("muslim", "Muslim", S.RAMP[600]), ("jewish", "Jewish", S.RAMP[300])]
FIELDS = [
    ("Decorations held\nmean per person", lambda r: int(r["n_decorations"]), "{:.2f}"),
    ("Légion d'honneur\nshare holding it", lambda r: int(r["has_legion_honneur"] == "1"), "{:.0%}"),
]

fig, axes = S.plt.subplots(1, 3, figsize=(10.0, 4.2),
                           gridspec_kw={"width_ratios": [1, 1, 2.4]})
for ax, (heading, read_value, fmt) in zip(axes, FIELDS):
    means = [statistics.fmean([read_value(r) for r in rows[key]]) for key, _, _ in GROUPS]
    S.grid(ax)
    bars = ax.bar(np.arange(len(GROUPS)), means, width=0.52,
                  color=[c for _, _, c in GROUPS], zorder=3)
    for bar, mean in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.03,
                fmt.format(mean), ha="center", va="bottom", fontsize=9,
                color=S.INK_SECONDARY)
    ax.set_xticks(np.arange(len(GROUPS)), [label for _, label, _ in GROUPS], fontsize=8.5)
    ax.set_yticks([])
    ax.set_ylim(0, max(means) * 1.3)
    S.despine(ax)
    ax.set_title(heading, fontsize=8.5, color=S.INK_SECONDARY, loc="left", pad=6)

ax = axes[2]
share = {}
for key, _, _ in GROUPS:
    counted = collections.Counter(r["occupation_primary"] for r in rows[key]
                                  if r["occupation_primary"])
    total = sum(counted.values())
    share[key] = {k: 100 * v / total for k, v in counted.items()}
categories = sorted(set(share["muslim"]) | set(share["jewish"]),
                    key=lambda c: (-(share["muslim"].get(c, 0) - share["jewish"].get(c, 0)), c))
categories = [c for c in categories
              if max(share["muslim"].get(c, 0), share["jewish"].get(c, 0)) >= 8]
S.grid(ax, axis="x")
y = np.arange(len(categories))
height = 0.38
for offset, (key, label, colour) in zip((-0.5, 0.5), GROUPS):
    values = [share[key].get(c, 0) for c in categories]
    ax.barh(y + offset * (height + 0.02), values, height, color=colour, zorder=3,
            label=f"{label} (n={len(rows[key])})")
    for value, position in zip(values, y + offset * (height + 0.02)):
        ax.text(value + 0.7, position, f"{value:.0f}%", va="center", ha="left",
                fontsize=7.5, color=S.INK_SECONDARY)
ax.set_yticks(y, [c.replace("_", " ").replace("politics native admin", "native administration")
                  for c in categories], fontsize=8)
ax.invert_yaxis()
ax.set_xticks([])
ax.set_xlim(0, max(max(share[k].values()) for k, _, _ in GROUPS) * 1.5)
# One extra slot of headroom above the top pair, so the legend has somewhere to
# sit that is neither over a bar nor over the panel title.
ax.set_ylim(len(categories) - 0.45, -1.35)
S.despine(ax, keep=("left",))
ax.legend(loc="upper right", ncol=2, borderaxespad=0.2)
ax.set_title("Primary occupation, share of each group", fontsize=8.5,
             color=S.INK_SECONDARY, loc="left", pad=6)

_, p_decorations = P.permutation_p(
    [int(r["n_decorations"]) for r in rows["muslim"]],
    [int(r["n_decorations"]) for r in rows["jewish"]])
fig.subplots_adjust(wspace=0.52, bottom=0.08, top=0.74)
fig.suptitle("The native side is two populations: one in the state, one in the professions",
             x=0.008, y=1.15, ha="left", fontsize=12, fontweight="bold", color=S.INK)
fig.text(
    0.008, 1.10,
    f"The {len(rows['muslim'])} Muslim and {len(rows['jewish'])} Jewish natives, split. "
    f"Both are natives in the sense this coding means — beylical subjects, not French "
    f"citizens or protected\nforeigners — and on that axis the volume treats them alike. "
    f"Everything else differs. Muslims hold more decorations ({P.p_text(p_decorations)}) "
    f"and nearly three times\nthe share of the Légion d'honneur, and their careers sit in "
    f"the beylical administration; Jewish careers sit in medicine, law and commerce, and "
    f"almost never\nin the native state. Reading 'native' as one interest here would be a "
    "mistake; with groups this small, read the occupational shares as shape, not "
    "quantity.",
    ha="left", va="top", fontsize=8.5, color=S.INK_SECONDARY, linespacing=1.5)
S.save(fig, "fig63_native_muslim_and_jewish",
       "Occupation categories under 8% in both groups are omitted")
