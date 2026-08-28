"""Fig. 29 — Is the OCR what limits the dataset?

The obvious worry about a dataset built from 1912 OCR is that the blank cells
are the scanner's fault. This tests it: split the biographical notices into
quartiles by the per-word confidence the ALTO gives them, and see whether the
fields come out less often in the bad ones.

They do not. Recovery is flat across the first three quartiles, and the drop in
the cleanest quartile runs the wrong way for a legibility story — those entries
are the longest in the volume, not the hardest to read. What is missing from the
dataset is, overwhelmingly, missing from the book.
"""
import statistics

import numpy as np

import _style as S

persons = [p for p in S.read("persons.csv") if p["ocr_confidence"]]
persons.sort(key=lambda p: float(p["ocr_confidence"]))
size = len(persons) // 4
quartiles = [persons[i * size:(i + 1) * size if i < 3 else None] for i in range(4)]

FIELDS = [
    ("Birth year", lambda p: bool(p["birth_year"])),
    ("Occupation", lambda p: bool(p["occupation_primary"])),
    ("Education", lambda p: bool(p["education_raw"])),
    ("Career posts", lambda p: bool(p["career_raw"])),
]
x = np.arange(len(FIELDS))
width = 0.2

fig, ax = S.figure(7.6, 4.6)
S.grid(ax)
for index, (bucket, colour) in enumerate(zip(quartiles, S.ORDINAL_4)):
    values = [100 * sum(1 for p in bucket if test(p)) / len(bucket)
              for _, test in FIELDS]
    low = float(bucket[0]["ocr_confidence"])
    high = float(bucket[-1]["ocr_confidence"])
    offset = (index - 1.5) * (width + 0.012)
    bars = ax.bar(x + offset, values, width, color=colour, zorder=3,
                  label=f"{low:.2f}–{high:.2f}")
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.4,
                f"{value:.0f}", ha="center", va="bottom", fontsize=7.5,
                color=S.INK_SECONDARY)
ax.set_xticks(x, [name for name, _ in FIELDS])
ax.set_yticks([])
ax.set_ylim(0, 100)
S.despine(ax)
legend = ax.legend(loc="upper right", ncol=2, title="OCR confidence quartile")
legend.get_title().set_fontsize(8.5)
legend.get_title().set_color(S.INK_SECONDARY)

confidences = [float(p["ocr_confidence"]) for p in persons]
lengths = {i: statistics.median(int(p["n_chars"]) for p in q)
           for i, q in enumerate(quartiles)}
S.titles(
    ax,
    "OCR quality is not what limits the dataset",
    f"Share of the {len(persons):,} biographical notices from which each field "
    f"could be read, by quartile of the notice's mean per-word OCR confidence "
    f"(median {statistics.median(confidences):.3f}, range "
    f"{min(confidences):.3f}–{max(confidences):.3f}). Recovery barely moves. The "
    f"cleanest quartile records a birth year least often, which is a composition "
    f"effect and not a legibility one — those notices are the longest in the "
    f"volume ({lengths[3]:,.0f} characters at the median against {lengths[0]:,.0f} "
    "in the worst quartile); they simply do not print a date.",
    ylabel="Notices with the field present (%)",
    wrap=100,
)
S.save(fig, "fig29_ocr_and_recovery",
       "Confidence is the mean of the ALTO per-word WC scores over the entry")
