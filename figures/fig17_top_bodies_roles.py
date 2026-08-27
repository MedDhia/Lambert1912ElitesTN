"""Fig. 17 — Who holds office in the largest bodies."""
import collections
import _style as S

edges = S.read("edges_person_organisation.csv")
CLASSES = [
    ("Presidency", {"president", "honorary_president", "past_president",
                    "vice_president", "honorary_vice_president"}),
    ("Secretary, treasurer", {"secretary", "secretary_general", "deputy_secretary",
                              "treasurer", "deputy_treasurer", "archivist_librarian"}),
    ("Board, council", {"board_member", "councillor", "assessor", "commissioner",
                        "delegate", "director", "founder", "rapporteur", "auditor"}),
    ("Ordinary member", {"member", "honorary_member", "corresponding_member"}),
]
by_body = collections.defaultdict(collections.Counter)
labels = {}
for e in edges:
    by_body[e["organisation_node"]][e["role"]] += 1
    labels[e["organisation_node"]] = e["organisation_name"]
top = sorted(by_body, key=lambda b: -sum(by_body[b].values()))[:12][::-1]

fig, ax = S.figure(7.6, 5.4)
left = [0] * len(top)
for (name, roles), colour in zip(CLASSES, S.SERIES):
    values = [sum(v for r, v in by_body[b].items() if r in roles) for b in top]
    bars = ax.barh([S.shorten(labels[b], 34, 1) for b in top], values, left=left,
                   height=0.62, color=colour, label=name, zorder=3,
                   edgecolor=S.SURFACE, linewidth=1.6)  # the 2px surface gap
    for bar, value in zip(bars, values):
        # Aqua and yellow sit below 3:1 on this surface: label them for relief.
        if value >= 4:
            ax.text(bar.get_x() + value / 2, bar.get_y() + bar.get_height() / 2,
                    str(value), ha="center", va="center", fontsize=8,
                    color=S.on_color(colour))
    left = [l + v for l, v in zip(left, values)]
for y, total in enumerate(left):
    ax.text(total + 1.5, y, str(total), va="center", fontsize=8.5, color=S.INK_SECONDARY)
S.despine(ax, keep=("left",))
ax.set_xticks([])
ax.set_xlim(0, max(left) * 1.08)
ax.legend(loc="lower right", ncols=2)
S.titles(
    ax,
    "Mostly office-holders — except where the volume prints a membership roll",
    "The twelve bodies with most recorded affiliates, by the office each person "
    "holds. Totals at the bar end. Segments under four are left unlabelled.",
)
S.save(fig, "fig17_top_bodies_roles", "Officer lists are printed in full; ordinary members usually are not")
