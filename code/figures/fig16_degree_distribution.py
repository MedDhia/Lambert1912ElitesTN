"""Fig. 16 — How unequally affiliations are distributed."""
import collections
import _style as S

edges = [e for e in S.read("edges_person_organisation.csv")
         if not e["resolution"].startswith("ambiguous")]
people = collections.Counter(e["person_node"] for e in edges)
bodies = collections.Counter(e["organisation_node"] for e in edges)

fig, ax = S.figure(7.2, 4.4)
S.grid(ax)
for counts, colour, label in (
    (people, S.BLUE, f"Persons ({len(people)})"),
    (bodies, S.ORANGE, f"Associations and public bodies ({len(bodies)})"),
):
    ranked = sorted(counts.values(), reverse=True)
    ax.plot(range(1, len(ranked) + 1), ranked, color=colour, label=label)
    ax.scatter([1], [ranked[0]], s=60, color=colour, zorder=4,
               edgecolor=S.SURFACE, linewidth=1.5)
ax.set_xscale("log")
ax.set_yscale("log")
ax.annotate(
    f"the busiest body has {max(bodies.values())} recorded members",
    xy=(1, max(bodies.values())), xytext=(1.35, max(bodies.values()) * 0.62),
    fontsize=8.5, color=S.INK_SECONDARY, va="center",
)
ax.legend(loc="lower left")
S.despine(ax, keep=("bottom", "left"))
S.titles(
    ax,
    "A few bodies carry the network; almost everyone belongs to one thing",
    "Rank-size plot of degree in the two-mode affiliation network, log-log. "
    "Ambiguous name matches are excluded.",
    xlabel="Rank (log)",
    ylabel="Affiliations recorded (log)",
)
S.save(fig, "fig16_degree_distribution", "Degree here is what the volume records, not what a person actually joined")
