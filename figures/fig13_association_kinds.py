"""Fig. 13 — What kind of associations they were."""
import collections
import _style as S

orgs = S.read("organizations.csv")
LABELS = {
    "chamber_public_body": "Chamber / public body",
    "mutual_aid": "Mutual aid, benevolence",
    "professional_union": "Professional, occupational",
    "learned_society": "Learned society",
    "sport_leisure": "Sport and leisure",
    "agricultural_economic": "Agricultural, economic",
    "national_community": "National community",
    "religious": "Religious",
    "music_arts": "Music and arts",
    "alumni": "Alumni",
    "masonic": "Masonic",
}
counts = collections.Counter(
    o["organisation_kind_primary"] for o in orgs if o["organisation_kind_primary"]
)
items = counts.most_common()[::-1]
names = [LABELS.get(k, k) for k, _ in items]
values = [v for _, v in items]

fig, ax = S.figure(7.2, 4.4)
bars = ax.barh(names, values, height=0.62, color=S.BLUE, zorder=3)
S.value_labels(ax, bars, values)
S.despine(ax, keep=("left",))
ax.set_xticks([])
ax.set_xlim(0, max(values) * 1.14)
uncoded = len(orgs) - sum(values)
S.titles(
    ax,
    "Chambers, mutual aid and professional bodies dominate the associational field",
    f"Primary kind, associations with one coded (n = {sum(values)} of {len(orgs)}; "
    f"{uncoded} carry no keyword the classifier recognises). Kinds are multi-label.",
)
S.save(fig, "fig13_association_kinds", "Lambert's preface claims more than 175 societies; 159 were recovered")
