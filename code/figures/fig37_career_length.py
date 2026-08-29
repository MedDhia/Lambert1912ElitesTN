"""Fig. 37 — How much of a career the volume actually prints.

`career_positions.csv` looks like a sequence dataset and is often used as one.
This is the figure that says how far it goes: for three quarters of the notices
the answer is that the volume prints no sequence at all.

Counted from the rows of `career_positions.csv`, which is the table an analysis
would use. Note that `persons.csv` also carries `n_career_positions`, and the
two do not agree: that column counts *text segments* in the rubric, splitting on
semicolons and full stops, and comes to 2,634 against 1,449 parsed rows. It runs
higher for 272 of these 328 people, because a segment that could not be read as
a post still counts there. Bin by the looser column and every bar moves right.
"""
import collections

import numpy as np

import _style as S

persons = S.read("persons.csv")
posts = collections.Counter(row["entry_id"] for row in S.read("career_positions.csv"))
counts = [posts.get(p["entry_id"], 0) for p in persons]
BINS = [(0, 0, "none"), (1, 2, "1–2"), (3, 5, "3–5"), (6, 9, "6–9"),
        (10, 19, "10–19"), (20, 10_000, "20 or more")]
sizes = [sum(1 for c in counts if low <= c <= high) for low, high, _ in BINS]
labels = [label for _, _, label in BINS]

# The first bar is the finding, so it keeps the hue and the rest recede.
colours = [S.ORANGE] + [S.RAMP[250]] * (len(BINS) - 1)

fig, ax = S.figure(7.4, 4.4)
S.grid(ax)
bars = ax.bar(np.arange(len(labels)), sizes, width=0.64, color=colours, zorder=3)
S.value_labels(ax, bars, sizes, horizontal=False)
ax.set_xticks(np.arange(len(labels)), labels)
ax.set_yticks([])
ax.set_ylim(0, max(sizes) * 1.16)
S.despine(ax)

with_any = len(counts) - sizes[0]
nonzero = sorted(c for c in counts if c)
median = nonzero[len(nonzero) // 2]
S.titles(
    ax,
    "Three quarters of the notices print no career sequence at all",
    f"Biographical notices by the number of posts parsed from the CARRIÈRE rubric. "
    f"{sizes[0]:,} of {len(counts):,} have none, and the {with_any} that do carry "
    f"{sum(counts):,} posts between them — a median of {median} and a maximum of "
    f"{max(counts)}. Career sequences here are therefore a rich sample of a "
    "minority, not a property of the elite as a whole, and modelling them as the "
    "latter would select on the volume's own generosity.",
    ylabel="Notices",
    wrap=100,
)
S.save(fig, "fig37_career_length",
       "Counted from career_positions.csv; persons.csv's n_career_positions is a "
       "looser segment count and runs higher")
