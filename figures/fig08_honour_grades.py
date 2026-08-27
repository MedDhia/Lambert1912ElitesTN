"""Fig. 8 — The grade structure of each honours system."""
import collections
import numpy as np
import _style as S

decs = S.read("decorations.csv")
ORDER = ["chevalier", "officier", "commandeur", "grand_officier",
         "grand_cordon", "grand_croix"]
LABELS = {
    "chevalier": "Chevalier", "officier": "Officier", "commandeur": "Commandeur",
    "grand_officier": "Grand officier", "grand_cordon": "Grand cordon",
    "grand_croix": "Grand-croix",
}
series = {
    "Légion d'honneur (France)": collections.Counter(
        d["grade"] for d in decs if d["order"] == "legion_honneur"),
    "Nichan Iftikhar (Bey of Tunis)": collections.Counter(
        d["grade"] for d in decs if d["order"] == "nichan_iftikhar"),
}
y = np.arange(len(ORDER))
height = 0.36

fig, ax = S.figure(7.4, 4.2)
S.grid(ax, axis="x")
for i, ((name, counts), colour) in enumerate(zip(series.items(), (S.BLUE, S.ORANGE))):
    values = [counts.get(g, 0) for g in ORDER]
    offset = (0.5 - i) * (height + 0.03)  # the 2px surface gap between neighbours
    bars = ax.barh(y + offset, values, height=height, color=colour, label=name, zorder=3)
    for bar, value in zip(bars, values):
        if value:
            ax.text(bar.get_width() + 6, bar.get_y() + bar.get_height() / 2, f"{value}",
                    va="center", fontsize=8, color=S.INK_SECONDARY)
ax.set_yticks(y, [LABELS[g] for g in ORDER])
ax.invert_yaxis()
ax.set_xticks([])
ax.set_xlim(0, 500)
S.despine(ax, keep=("left",))
ax.legend(loc="lower right", ncols=1)
S.titles(
    ax,
    "The beylical order is granted freely at the middle grades",
    "Persons by grade within each order. Grades with no holder in either order are "
    "omitted. A person may hold both orders at different grades.",
)
S.save(fig, "fig08_honour_grades", "Grade is unstated for 16% of honours")
