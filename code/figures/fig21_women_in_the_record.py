"""Fig. 21 — The eleven women.

The story here is a single number, so the form is emphasis on a unit grid rather
than a chart of series: every notice in the volume is one mark, and the eleven
women are the only ones that carry colour.
"""
import _style as S

rows = S.read("person_gender.csv")
women = [r for r in rows if r["gender"] == "FEMALE"]
affiliated = {e["person_node"] for e in S.read("edges_person_organisation.csv")}
total = len(rows)

COLS = 44
fig, ax = S.figure(7.4, 5.0)
female_positions = {i for i, r in enumerate(rows) if r["gender"] == "FEMALE"}
xs_o, ys_o, xs_w, ys_w = [], [], [], []
for i in range(total):
    x, y = i % COLS, i // COLS
    (xs_w if i in female_positions else xs_o).append(x)
    (ys_w if i in female_positions else ys_o).append(-y)
ax.scatter(xs_o, ys_o, s=9, color=S.GRID, linewidths=0)
ax.scatter(xs_w, ys_w, s=26, color=S.ORANGE, linewidths=0.6, edgecolors=S.SURFACE)
ax.set_axis_off()
ax.set_aspect("equal")
ax.annotate(
    f"{len(women)} women", xy=(COLS + 0.6, -total / COLS / 2),
    fontsize=11, color=S.INK, va="center", fontweight="bold",
)
ax.annotate(
    f"{total - len(women):,} other notices\n(1,115 men, 181 not codeable)",
    xy=(COLS + 0.6, -total / COLS / 2 - 3.2), fontsize=8.5, color=S.INK_SECONDARY,
    va="top",
)
S.titles(
    ax,
    "Eleven women in a volume of 1,307 notables",
    "Every biographical notice in the volume, one mark each, in printed order. "
    "Gender is coded from civil titles, feminine occupational nouns and forenames; "
    f"only {sum(1 for w in women if w['entry_id'] in affiliated)} of the eleven "
    "women are recorded in any organisation at all.",
    wrap=92,
)
S.save(fig, "fig21_women_in_the_record", "0.84% of notices; all eleven verified against the page image")
