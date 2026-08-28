"""Fig. 10 — Does the volume give more space to the decorated?"""
import statistics
import _style as S

persons = S.read("persons.csv")
buckets = [("0", []), ("1", []), ("2", []), ("3", []), ("4 or more", [])]
index = {"0": 0, "1": 1, "2": 2, "3": 3}
for p in persons:
    n = int(p["n_decorations"])
    buckets[index.get(str(n), 4)][1].append(int(p["n_chars"]))

fig, ax = S.figure(7.2, 4.0)
S.grid(ax)
positions = range(len(buckets))
box = ax.boxplot(
    [v for _, v in buckets], positions=list(positions), widths=0.5, showfliers=False,
    patch_artist=True,
    medianprops=dict(color=S.SURFACE, linewidth=2),
    whiskerprops=dict(color=S.AXIS, linewidth=1),
    capprops=dict(color=S.AXIS, linewidth=1),
    boxprops=dict(linewidth=0),
)
ramp = [S.RAMP[150], S.RAMP[250], S.RAMP[400], S.RAMP[500], S.RAMP[650]]
for patch, colour in zip(box["boxes"], ramp):
    patch.set_facecolor(colour)
for i, (_, values) in enumerate(buckets):
    ax.text(i, statistics.median(values) + 60, f"{statistics.median(values):,.0f}",
            ha="center", va="bottom", fontsize=8.5, color=S.INK_SECONDARY)
ax.set_xticks(list(positions), [f"{label}\n(n={len(v)})" for label, v in buckets])
S.despine(ax)
S.titles(
    ax,
    "More honours, more column inches — the volume ranks as the state ranks",
    "Length of the biographical notice by number of distinct honours named in it. "
    "Whiskers span 1.5×IQR; outliers omitted. Median printed above each box.",
    xlabel="Honours named in the entry",
    ylabel="Characters in the entry",
)
S.save(fig, "fig10_attention_and_honours", "Entry length is a measure of the compiler's attention, not of the subject's importance")
