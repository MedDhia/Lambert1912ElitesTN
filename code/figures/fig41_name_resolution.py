"""Fig. 41 — What happens to a name the volume mentions.

Every tie in the network rests on matching a printed name to a notice. This is
the figure that says how often that succeeds, how often it is refused, and how
often the person simply has no notice to match.
"""
import collections

import numpy as np

import _style as S

mentions = S.read("mentions.csv")
counts = collections.Counter(m["resolution"] for m in mentions)
GROUPS = [
    ("resolved", "Matched to a notice", S.BLUE),
    ("resolved_fuzzy", "Matched allowing one\nmistyped character", S.RAMP[250]),
    ("ambiguous", "Refused: the surname fits\nmore than one notice", S.ORANGE),
    ("ambiguous_fuzzy", "Refused, on a fuzzy\nsurname match", S.RAMP[150]),
    ("unmatched", "No notice of their own\nto match", S.DE_EMPHASIS),
]
labels = [label for _, label, _ in GROUPS][::-1]
values = [counts[key] for key, _, _ in GROUPS][::-1]
colours = [colour for _, _, colour in GROUPS][::-1]

fig, ax = S.figure(7.6, 4.6)
S.grid(ax, axis="x")
bars = ax.barh(np.arange(len(labels)), values, height=0.64, color=colours, zorder=3)
for bar, value in zip(bars, values):
    ax.text(bar.get_width() + max(values) * 0.012,
            bar.get_y() + bar.get_height() / 2,
            f"{value}   {100 * value / len(mentions):.0f}%",
            va="center", fontsize=8.5, color=S.INK_SECONDARY)
ax.set_yticks(np.arange(len(labels)), labels, fontsize=8)
ax.set_xticks([])
ax.set_xlim(0, max(values) * 1.2)
S.despine(ax, keep=("left",))

matched = counts["resolved"] + counts["resolved_fuzzy"]
refused = counts["ambiguous"] + counts["ambiguous_fuzzy"]
S.titles(
    ax,
    "Most names the volume drops are people it never gave an entry",
    f"All {len(mentions):,} person-mentions found inside other entries, by how the "
    f"matcher resolved them. {matched} reach a notice and {refused} are refused "
    f"because a surname fits more than one — those become no tie at all rather than "
    f"a guess. The largest group, {counts['unmatched']}, is neither: these are real "
    "members of this elite whom Lambert never wrote up, and they enter the network "
    "as nodes without attributes.",
    xlabel="Mentions",
    wrap=100,
)
S.save(fig, "fig41_name_resolution",
       "Refusals stay in mentions.csv marked ambiguous, for manual disambiguation")
