"""Fig. 35 — Where they were born against where the volume finds them.

The birthplaces are scattered across France and the Mediterranean; the
residences are Tunis and a short list of coastal towns. That contraction is the
Protectorate's settlement pattern in one picture.
"""
import collections

import numpy as np

import _style as S

ties = S.read("edges_person_place.csv")
births = collections.Counter(t["place_name"] for t in ties if t["relation"] == "birthplace")
homes = collections.Counter(t["place_name"] for t in ties if t["relation"] == "residence")

TOP = 10
origins = births.most_common(TOP)[::-1]
residences = homes.most_common(TOP)[::-1]
total_births = sum(births.values())
total_homes = sum(homes.values())

fig, axes = S.plt.subplots(1, 2, figsize=(8.6, 4.6))
for ax, rows, total, colour, heading in (
    (axes[0], origins, total_births, S.DE_EMPHASIS, "Born at"),
    (axes[1], residences, total_homes, S.BLUE, "Living at"),
):
    names = [name for name, _ in rows]
    counts = [count for _, count in rows]
    S.grid(ax, axis="x")
    bars = ax.barh(np.arange(len(names)), counts, height=0.66, color=colour, zorder=3)
    S.value_labels(ax, bars, counts, pad=0.02)
    ax.set_yticks(np.arange(len(names)), names)
    ax.set_xticks([])
    ax.set_xlim(0, max(counts) * 1.18)
    S.despine(ax, keep=("left",))
    ax.set_title(f"{heading}  ({total:,} people named a place)",
                 fontsize=9.5, color=S.INK_SECONDARY, loc="left", pad=8)

fig.subplots_adjust(wspace=0.42, bottom=0.08)
fig.suptitle("A scattered origin, a single destination",
             x=0.008, y=1.10, ha="left", fontsize=12, fontweight="bold", color=S.INK)
fig.text(0.008, 1.06,
         f"The ten commonest birthplaces and the ten commonest residences, counted over the "
         f"{total_births:,} people whose\nbirthplace the volume prints and the {total_homes:,} "
         f"whose residence it does. Tunis heads both lists, but it holds "
         f"{100 * homes['Tunis'] / total_homes:.0f}% of the\nresidences against "
         f"{100 * births['Tunis'] / total_births:.0f}% of the births: the rest of the elite came "
         "from somewhere else and converged on it.",
         ha="left", va="top", fontsize=8.5, color=S.INK_SECONDARY, linespacing=1.5)
S.save(fig, "fig35_origins_and_residence",
       "A person may be counted in both panels; places are as the volume spells them")
