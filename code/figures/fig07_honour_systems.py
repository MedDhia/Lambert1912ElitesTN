"""Fig. 7 — Two states, two honours systems."""
import _style as S

persons = S.read("persons.csv")
fr = {p["entry_id"] for p in persons if p["has_legion_honneur"] == "1"}
tn = {p["entry_id"] for p in persons if p["has_nichan_iftikhar"] == "1"}
none = {p["entry_id"] for p in persons if p["n_decorations"] == "0"}
ids = {p["entry_id"] for p in persons}
groups = [
    ("No honour named", len(none)),
    ("Other honours only", len(ids - none - fr - tn)),
    ("Beylical only\n(Nichan Iftikhar)", len(tn - fr)),
    ("French only\n(Légion d'honneur)", len(fr - tn)),
    ("Both", len(fr & tn)),
]
names = [n for n, _ in groups]
values = [v for _, v in groups]
# Ordered categories -> the ordinal blue ramp (validated with --ordinal).
colors = [S.RAMP[150], S.RAMP[250], S.RAMP[400], S.RAMP[500], S.RAMP[650]]

fig, ax = S.figure(7.2, 4.0)
bars = ax.barh(names, values, height=0.6, color=colors, zorder=3)
S.value_labels(ax, bars, values)
for bar, value, fill in zip(bars, values, colors):
    ax.text(bar.get_width() * 0.5, bar.get_y() + bar.get_height() / 2,
            f"{100 * value / len(persons):.0f}%", ha="center", va="center",
            fontsize=8.5, color=S.on_color(fill))
S.despine(ax, keep=("left",))
ax.set_xticks([])
ax.set_xlim(0, max(values) * 1.12)
S.titles(
    ax,
    "The Bey's order reaches four times as many people as the Légion d'honneur",
    f"All {len(persons)} biographical notices, in mutually exclusive groups. "
    "The Nichan Iftikhar is the beylical order; the Légion d'honneur is French.",
)
S.save(fig, "fig07_honour_systems", "Honours are read from the entry text, so silence is not proof of absence")
