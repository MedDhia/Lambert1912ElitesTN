"""Fig. 36 — The credentials the volume thought worth printing.

Fig. 5 counts the institutions attended. This counts the qualifications they
produced, which is a different claim about the same rubric: what the elite
carried, not where they sat.
"""
import collections

import _style as S

LABELS = {
    "baccalaureat": "Baccalauréat",
    "diplome_superieur": "Diplôme supérieur",
    "licence_droit": "Licence en droit",
    "certificat": "Certificat",
    "brevet_superieur": "Brevet supérieur",
    "doctorat_medecine": "Doctorat en médecine",
    "doctorat_droit": "Doctorat en droit",
    "agregation": "Agrégation",
    "licence_lettres": "Licence ès lettres",
    "licence_sciences": "Licence ès sciences",
}
rows = S.read("education.csv")
degrees = collections.Counter(
    d for r in rows if r["degrees"] for d in r["degrees"].split(";"))
named = [(LABELS.get(k, k), v) for k, v in degrees.most_common() if k in LABELS][::-1]
labels = [k for k, _ in named]
counts = [v for _, v in named]

# One number is the story -- the baccalauréat dwarfs the rest -- so everything
# below it recedes to a lighter step rather than taking a hue of its own.
colours = [S.BLUE if count == max(counts) else S.RAMP[200] for count in counts]

fig, ax = S.figure(7.4, 4.8)
S.grid(ax, axis="x")
bars = ax.barh(labels, counts, height=0.66, color=colours, zorder=3)
S.value_labels(ax, bars, counts)
ax.set_xticks([])
ax.set_xlim(0, max(counts) * 1.14)
S.despine(ax, keep=("left",))

with_degree = sum(1 for r in rows if r["degrees"])
doctorates = degrees["doctorat_medecine"] + degrees["doctorat_droit"]
S.titles(
    ax,
    "A secondary certificate, not a doctorate, is what this elite carries",
    f"Qualifications named in the ETUDES rubric: {with_degree:,} of the {len(rows):,} "
    f"institution mentions state one. The baccalauréat alone accounts for "
    f"{degrees['baccalaureat']}, more than every doctorate and the agrégation "
    f"together ({doctorates + degrees['agregation']}). The law degrees are the one "
    "professional credential recorded in bulk, which fits an elite of officials, "
    "magistrates and notaries.",
    xlabel="Times named",
    wrap=100,
)
S.save(fig, "fig36_credentials",
       "A person may hold several; counted per mention, not per person")
