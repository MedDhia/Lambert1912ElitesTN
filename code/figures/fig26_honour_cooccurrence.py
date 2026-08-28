"""Fig. 26 — Which decorations were held together.

A decoration is rarely held alone. Reading the pairs shows how the two honours
systems interlock: the question is whether the Bey's Nichan Iftikhar arrives
with a French order or instead of one.
"""
import collections
import itertools

import numpy as np

import _style as S

LABELS = {
    "nichan_iftikhar": "Nichan Iftikhar\n(Tunisia)",
    "palmes_academiques": "Palmes\nacadémiques",
    "merite_agricole": "Mérite\nagricole",
    "legion_honneur": "Légion\nd'honneur",
    "medaille_coloniale": "Médaille\ncoloniale",
    "ouissam_alaouite": "Ouissam Alaouite\n(Morocco)",
    "couronne_italie": "Couronne d'Italie\n(Italy)",
    "medaille_militaire": "Médaille\nmilitaire",
}
SHORT = {
    "nichan_iftikhar": "Nichan\nIftikhar", "palmes_academiques": "Palmes",
    "merite_agricole": "Mérite\nagricole", "legion_honneur": "Légion",
    "medaille_coloniale": "Méd.\ncoloniale", "ouissam_alaouite": "Ouissam",
    "couronne_italie": "Couronne\nd'Italie", "medaille_militaire": "Méd.\nmilitaire",
}
orders = list(LABELS)

held = collections.defaultdict(set)
for d in S.read("decorations.csv"):
    held[d["entry_id"]].add(d["order"])
totals = collections.Counter(o for s in held.values() for o in s)
pairs = collections.Counter()
for s in held.values():
    for a, b in itertools.combinations(sorted(s), 2):
        pairs[(a, b)] += 1

# Cell = share of the row order's holders who also hold the column order. The
# matrix is deliberately asymmetric: 45% of Légion holders also have the Nichan
# is a different fact from 11% of Nichan holders also having the Légion, and the
# asymmetry is the finding.
n = len(orders)
matrix = np.full((n, n), np.nan)
for i, row in enumerate(orders):
    for j, col in enumerate(orders):
        if i == j:
            continue
        both = pairs[tuple(sorted((row, col)))]
        matrix[i, j] = 100 * both / totals[row]

fig, ax = S.figure(7.6, 6.2)
image = ax.imshow(matrix, cmap="Blues", vmin=0, vmax=np.nanmax(matrix))
# The columns repeat the rows, so they can be labelled short: the full name and
# the awarding state are printed once, down the left.
ax.set_xticks(range(n), [SHORT[o] for o in orders], fontsize=7.5)
ax.set_yticks(range(n), [LABELS[o] for o in orders], fontsize=7.5)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.tick_params(length=0)
# Every cell carries its number: nothing here is reachable by reading a shade.
for i in range(n):
    for j in range(n):
        if i == j:
            ax.text(j, i, "—", ha="center", va="center", fontsize=8, color=S.INK_MUTED)
            continue
        value = matrix[i, j]
        fill = image.cmap(image.norm(value))
        ax.text(j, i, f"{value:.0f}", ha="center", va="center", fontsize=8,
                color=S.on_color(
                    "#{:02x}{:02x}{:02x}".format(*(int(255 * c) for c in fill[:3]))))
# A 2px gap between cells: adjacency is the grid, not a drawn line.
ax.set_xticks(np.arange(n + 1) - 0.5, minor=True)
ax.set_yticks(np.arange(n + 1) - 0.5, minor=True)
ax.grid(which="minor", color=S.SURFACE, linewidth=2)
ax.tick_params(which="minor", length=0)

nichan_of_legion = 100 * pairs[tuple(sorted(("legion_honneur", "nichan_iftikhar")))] / totals["legion_honneur"]
legion_of_nichan = 100 * pairs[tuple(sorted(("legion_honneur", "nichan_iftikhar")))] / totals["nichan_iftikhar"]
S.titles(
    ax,
    "The Bey's order accompanies the French ones; it does not replace them",
    f"Read along a row. {nichan_of_legion:.0f}% of the {totals['legion_honneur']} "
    f"Légion d'honneur holders also wear the Nichan Iftikhar, but only "
    f"{legion_of_nichan:.0f}% of the {totals['nichan_iftikhar']} Nichan holders wear "
    "the Légion — the beylical honour is the wide one, given to almost everyone the "
    "French state had already recognised and to many more besides.",
    xlabel="… also held this one",
    ylabel="Of the people holding this order …",
    wrap=102,
)
S.save(fig, "fig26_honour_cooccurrence",
       "Counted per person, ignoring grade; the diagonal is not a comparison and is left blank")
