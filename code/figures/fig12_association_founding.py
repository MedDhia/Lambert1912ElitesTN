"""Fig. 12 — When the Regency's associations were founded."""
import _style as S

orgs = S.read("organizations.csv")
years = sorted(int(o["founded_year"]) for o in orgs if o["founded_year"])
years = [y for y in years if 1860 <= y <= 1912]
cumulative = list(range(1, len(years) + 1))

fig, ax = S.figure(7.4, 4.2)
S.grid(ax)
ax.step(years, cumulative, where="post", color=S.BLUE, zorder=3)
ax.fill_between(years, cumulative, step="post", color=S.BLUE, alpha=0.10, zorder=2)
ax.axvline(1881, color=S.ORANGE, linewidth=2, zorder=4)
ax.annotate("Treaty of Bardo, 1881", xy=(1881, len(years) * 0.55),
            xytext=(1883, len(years) * 0.55), fontsize=9, color=S.INK_SECONDARY,
            va="center")
ax.annotate(f"{cumulative[-1]} associations\nwith a founding date",
            xy=(years[-1], cumulative[-1]), xytext=(years[-1] - 2, cumulative[-1] - 7),
            fontsize=8.5, color=S.INK_SECONDARY, ha="right", va="top")
ax.scatter([years[-1]], [cumulative[-1]], s=60, color=S.BLUE, zorder=5,
           edgecolor=S.SURFACE, linewidth=1.5)
S.despine(ax)
ax.set_xlim(1860, 1915)
S.titles(
    ax,
    "Associational life is a creation of the Protectorate's second generation",
    f"Cumulative count of associations by founding year (n = {len(years)} of "
    f"{len(orgs)} with a readable date). Societies founded before 1860 are omitted.",
    ylabel="Associations founded, cumulative",
)
S.save(fig, "fig12_association_founding", "Founding dates as printed in the notice")
