"""Fig. 60 — The two sides are not the same age, and only one of them arrived.

A colonist's notice records when he came to Tunisia; a native's usually cannot,
because there is nothing to record. That asymmetry is the clearest thing the
biographical fields say about the colonial relation.
"""
import collections

import numpy as np

import _positionality as P
import _style as S

# Six birth years in the volume fall outside any human range (1600, 1700, 1750
# and so on) -- OCR reading a date off a neighbouring line. They are dropped and
# counted rather than winsorised.
EARLIEST, LATEST = 1810, 1900

people = collections.defaultdict(list)
for person in P.placed():
    people[person["positionality"]].append(person)

sides = (P.COLONIST, P.NATIVE)
DECADES = list(range(1830, 1891, 10))


def cohorts(rows):
    years = [int(r["birth_year"]) for r in rows if r["birth_year"]]
    kept = [y for y in years if EARLIEST <= y <= LATEST]
    counted = collections.Counter(min(max(10 * (y // 10), DECADES[0]), DECADES[-1])
                                  for y in kept)
    return [100 * counted[d] / len(kept) for d in DECADES], kept, len(years) - len(kept)


profiles, kept, dropped = {}, {}, 0
for side in sides:
    profiles[side], kept[side], lost = cohorts(people[side])
    dropped += lost

fig, (ax_cohort, ax_settled) = S.plt.subplots(
    1, 2, figsize=(8.4, 4.0), gridspec_kw={"width_ratios": [1.7, 1]})

S.grid(ax_cohort)
x = np.arange(len(DECADES))
for side in sides:
    ax_cohort.plot(x, profiles[side], color=P.COLOUR[side], linewidth=2.2, zorder=4,
                   marker="o", markersize=4, markeredgewidth=0,
                   label=f"{P.LABEL[side]} (n={len(kept[side])})")
ax_cohort.set_xticks(x, [f"{d}s" for d in DECADES], fontsize=8)
# A line chart carries no direct labels, so this is the one panel in the set
# that keeps its value axis rather than dropping it.
top = max(max(profiles[s]) for s in sides)
ax_cohort.set_yticks(range(0, int(top) + 10, 10),
                     [f"{v}%" for v in range(0, int(top) + 10, 10)], fontsize=8)
ax_cohort.set_ylim(0, top * 1.25)
S.despine(ax_cohort)
ax_cohort.legend(loc="upper left")
ax_cohort.set_title("Birth decade, as a share of each side", fontsize=8.5,
                    color=S.INK_SECONDARY, loc="left", pad=6)

S.grid(ax_settled)
shares = [100 * sum(1 for r in people[side] if r["settled_tunisia_year"]) / len(people[side])
          for side in sides]
bars = ax_settled.bar(np.arange(2), shares, width=0.5,
                      color=[P.COLOUR[s] for s in sides], zorder=3)
for bar, share, side in zip(bars, shares, sides):
    n = sum(1 for r in people[side] if r["settled_tunisia_year"])
    ax_settled.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.4,
                    f"{share:.0f}%\n{n} of {len(people[side])}", ha="center",
                    va="bottom", fontsize=8.5, color=S.INK_SECONDARY)
ax_settled.set_xticks(np.arange(2), [P.LABEL[s] for s in sides], fontsize=8.5)
ax_settled.set_yticks([])
ax_settled.set_ylim(0, max(shares) * 1.42)
S.despine(ax_settled)
ax_settled.set_title("Has a year of settling in Tunisia", fontsize=8.5,
                     color=S.INK_SECONDARY, loc="left", pad=6)

median_gap = (sorted(kept[P.COLONIST])[len(kept[P.COLONIST]) // 2]
              - sorted(kept[P.NATIVE])[len(kept[P.NATIVE]) // 2])
fig.subplots_adjust(wspace=0.22, bottom=0.1, top=0.74)
fig.suptitle("Only one side of this elite has a date of arrival",
             x=0.008, y=1.15, ha="left", fontsize=12, fontweight="bold", color=S.INK)
fig.text(
    0.008, 1.10,
    f"Left: birth decade. The colonist side peaks in the 1860s and the native side a "
    f"decade later — a median gap of {abs(median_gap):.0f} years, so the natives the\n"
    f"volume records are a slightly younger set, which fits an elite recruited through "
    f"French-language schooling that only opened later. Right: the field that\ndoes not "
    f"translate. {shares[0]:.0f}% of colonists have a year they settled in Tunisia and "
    f"{shares[1]:.0f}% of natives do, because for a native there is usually no such "
    f"year to\nprint. Any model using settlement date is a model of one side of this "
    "population only.",
    ha="left", va="top", fontsize=8.5, color=S.INK_SECONDARY, linespacing=1.5)
S.save(fig, f"fig60_position_and_cohort",
       f"{dropped} birth years outside {EARLIEST}–{LATEST} dropped as OCR errors")
