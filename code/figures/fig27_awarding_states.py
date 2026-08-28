"""Fig. 27 — Which states decorated this elite."""
import collections

import _style as S

decorations = S.read("decorations.csv")
by_state = collections.Counter(d["order_country"] for d in decorations if d["order_country"])
people = len({d["entry_id"] for d in decorations})

# France's colonial orders are printed as their own decorations (Étoile Noire du
# Bénin, Étoile d'Anjouan, Ordre Radama) and coded that way; keeping them apart
# from the metropolitan orders is the point of the row, so they are not merged.
labels = {
    "France": "France", "Tunisia": "Tunisia (the Bey)", "Morocco": "Morocco",
    "Italy": "Italy", "Ottoman Empire": "Ottoman Empire", "Russia": "Russia",
    "Belgium": "Belgium", "France (Benin)": "France — Benin",
    "Austria-Hungary": "Austria-Hungary", "Portugal": "Portugal",
    "France (Comoros)": "France — Comoros", "Greece": "Greece", "Spain": "Spain",
    "international": "Red Cross (international)",
    "France (Madagascar)": "France — Madagascar", "Norway": "Norway",
}
rows = by_state.most_common()
names = [labels.get(state, state) for state, _ in rows][::-1]
values = [count for _, count in rows][::-1]
# One number is the story — the two protecting states against everyone else — so
# the rest recede to grey rather than each taking a hue.
colours = [S.BLUE if state in ("France", "Tunisia") else S.DE_EMPHASIS
           for state, _ in rows][::-1]
foreign = sum(c for s, c in rows if s not in ("France", "Tunisia"))

fig, ax = S.figure(7.4, 5.4)
S.grid(ax, axis="x")
bars = ax.barh(names, values, color=colours, height=0.66, zorder=3)
S.value_labels(ax, bars, values, pad=0.012)
ax.set_xticks([])
ax.set_xlim(0, max(values) * 1.1)
S.despine(ax, keep=("left",))
S.titles(
    ax,
    "Two states did the decorating; sixteen awarding authorities appear in all",
    f"{len(decorations):,} decorations held by {people:,} people. France and the "
    f"Bey account for {100 * (by_state['France'] + by_state['Tunisia']) / len(decorations):.0f}% "
    f"of them; the other fourteen entries share {foreign}. The foreign orders are "
    "not a sideline but a claim: a Tunis notable wearing the Medjidié or the "
    "Crown of Italy is displaying a second patron.",
    xlabel="Decorations recorded",
    wrap=100,
)
S.save(fig, "fig27_awarding_states",
       "Every order named in a notice, at any grade; a person may hold several")
