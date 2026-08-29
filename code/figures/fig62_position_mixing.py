"""Fig. 62 — The one place the colonial line is unmistakable: who sat with whom.

Honours, page space and brokerage do not separate the two sides. Shared
membership does, and by a wide margin against a null that holds the bodies and
their sizes fixed and shuffles only the labels.
"""
import collections
import itertools
import random
import statistics

import _positionality as P
import _style as S

ITERATIONS = 2000
SEED = 11

side = {r["entry_id"]: r["positionality"] for r in P.placed()}
bodies, counts = P.crossing_pairs(side)
total = sum(counts.values())
observed = 100 * counts["mixed"] / total

# The null keeps every body and every body's size, and shuffles which placed
# person carries which label. It therefore asks only one question: given this
# many colonists and this many natives spread over these bodies, how much
# crossing would chance produce.
population = sorted({person for body in bodies for person in body})
labels = [side[p] for p in population]
rng = random.Random(SEED)
simulated = []
for _ in range(ITERATIONS):
    rng.shuffle(labels)
    assigned = dict(zip(population, labels))
    mixed = 0
    for body in bodies:
        for a, b in itertools.combinations(body, 2):
            mixed += assigned[a] != assigned[b]
    simulated.append(100 * mixed / total)

null_mean = statistics.fmean(simulated)
p = (sum(1 for s in simulated if s <= observed) + 1) / (ITERATIONS + 1)

fig, ax = S.figure(7.6, 4.2)
S.grid(ax)
ax.hist(simulated, bins=28, color=S.DE_EMPHASIS, zorder=3)
ax.axvline(observed, color=S.ORANGE, linewidth=2.4, zorder=5)
top = ax.get_ylim()[1]
ax.annotate(f"observed\n{observed:.1f}%", xy=(observed, top * 0.92),
            xytext=(8, 0), textcoords="offset points", ha="left", va="top",
            fontsize=9, color=S.ORANGE)
ax.annotate(f"chance\n{null_mean:.1f}%", xy=(null_mean, top * 0.92),
            xytext=(8, 0), textcoords="offset points", ha="left", va="top",
            fontsize=9, color=S.INK_SECONDARY)
ax.set_yticks([])
S.despine(ax)

S.titles(
    ax,
    "Colonists and natives belonged to the same bodies far less often than chance",
    f"Every pair of placed people who share a body, by whether the pair crosses the "
    f"colonial line: {counts['mixed']:,} of {total:,} pairs do, {observed:.1f}%. The "
    f"grey distribution is {ITERATIONS:,} relabellings that keep every body and every "
    f"body's size and shuffle only who is a colonist and who is a native; it centres on "
    f"{null_mean:.1f}%. The observed share falls below all but a handful of them "
    f"({P.p_text(p)}). This is the finding the rest of this group does not make: the "
    "line is not in what the volume awarded or printed, and barely in where people sit "
    "in the network — it is in association itself.",
    xlabel="Share of co-membership pairs that cross the line",
    ylabel="Relabellings",
    wrap=104,
)
S.save(fig, "fig62_position_mixing",
       f"Bodies with 2–60 members; unambiguous ties only; seed {SEED}")
