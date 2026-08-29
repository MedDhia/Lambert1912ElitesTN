"""Fig. 34 — Honours accumulate with time served, not with merit alone.

Fig. 10 shows that decorated people get longer entries. This asks a prior
question: who is decorated at all. The answer is mostly a matter of how long
they have been eligible.
"""
import collections
import statistics

import numpy as np

import _style as S

persons = [p for p in S.read("persons.csv") if p["birth_year"] and p["n_decorations"]]
cohorts = collections.defaultdict(list)
for person in persons:
    decade = (int(person["birth_year"]) // 10) * 10
    cohorts[decade].append(int(person["n_decorations"]))
# Decades with fewer than 20 people are dropped: a mean of a dozen values is
# not a cohort, and the volume's tails are thin at both ends.
decades = [d for d in sorted(cohorts) if len(cohorts[d]) >= 20]
share = [100 * sum(1 for n in cohorts[d] if n) / len(cohorts[d]) for d in decades]
mean = [statistics.fmean(cohorts[d]) for d in decades]

x = np.arange(len(decades))
fig, ax = S.figure(7.4, 4.6)
S.grid(ax)
bars = ax.bar(x, share, width=0.62, color=S.BLUE, zorder=3)
S.value_labels(ax, bars, share, horizontal=False, fmt="{:.0f}%")
for index, (position, value) in enumerate(zip(x, mean)):
    ax.text(position, 4, f"{value:.2f}", ha="center", va="bottom",
            fontsize=8, color=S.on_color(S.BLUE))
ax.text(-0.62, 4, "mean\nhonours", ha="right", va="bottom", fontsize=7.5,
        color=S.INK_SECONDARY, linespacing=1.3)
ax.set_xticks(x, [f"{d}s\n(n={len(cohorts[d])})" for d in decades])
ax.set_yticks([])
ax.set_ylim(0, 100)
S.despine(ax)
S.titles(
    ax,
    "Honours accumulate with time served",
    f"Share of each birth cohort carrying at least one decoration, with the mean "
    f"number of decorations printed inside each bar. Among the "
    f"{sum(len(cohorts[d]) for d in decades):,} people whose birth year the volume "
    f"prints, the 1850s cohort is decorated at {share[1]:.0f}% and the 1880s at "
    f"{share[-1]:.0f}%. Nothing here says the older men were more deserving: by "
    "1912 they had simply been eligible for thirty more years.",
    ylabel="Carrying at least one honour",
    wrap=100,
)
S.save(fig, "fig34_honours_by_cohort",
       f"Birth year is printed for {len(persons):,} of {len(S.read('persons.csv')):,}; "
       f"decades with fewer than 20 "
       f"people are omitted, leaving {sum(len(cohorts[d]) for d in decades):,} plotted")
