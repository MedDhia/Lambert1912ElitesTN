"""Fig. 6 — How much space the volume gives each person."""
import statistics
import _style as S

persons = S.read("persons.csv")
with_portrait = [int(p["n_chars"]) for p in persons if int(p["n_portraits"]) > 0]
without = [int(p["n_chars"]) for p in persons if int(p["n_portraits"]) == 0]

fig, ax = S.figure(7.2, 3.6)
S.grid(ax, axis="x")
box = ax.boxplot(
    [without, with_portrait], orientation="horizontal", widths=0.45, showfliers=False,
    patch_artist=True,
    medianprops=dict(color=S.SURFACE, linewidth=2),
    whiskerprops=dict(color=S.AXIS, linewidth=1),
    capprops=dict(color=S.AXIS, linewidth=1),
    boxprops=dict(linewidth=0),
)
for patch, colour in zip(box["boxes"], [S.RAMP[250], S.BLUE]):
    patch.set_facecolor(colour)
ax.set_yticks([1, 2], [
    f"No portrait\n(n = {len(without)})", f"Portrait\n(n = {len(with_portrait)})",
])
for i, values in enumerate([without, with_portrait], start=1):
    med = statistics.median(values)
    ax.text(med, i + 0.32, f"median {med:,.0f}", ha="center", va="bottom",
            fontsize=8.5, color=S.INK_SECONDARY)
S.despine(ax)
S.titles(
    ax,
    "A portrait comes with roughly twice the words",
    "Length of the biographical notice in characters, by whether the entry carries "
    "a photogravure portrait. Whiskers span 1.5×IQR; outliers omitted.",
    xlabel="Characters in the entry",
)
S.save(fig, "fig06_attention", "Portrait placement is inferred from ALTO illustration coordinates")
