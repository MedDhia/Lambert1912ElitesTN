"""Fig. 24 — Do the two communities meet in the associations?

The co-membership projection gives a tie whenever two people are recorded in the
same body. Counting those ties by the community of each end, and comparing them
with what the same people would produce if they joined at random, measures how
far associational life was shared.

The benchmark is the configuration expectation: hold every person's number of
ties fixed and rewire at random, so a group's share of ties comes out as its
share of tie-ends. That is the right null here because Europeans are the large
majority -- most ties would be European-European whatever the mixing.
"""
import collections

import numpy as np

import _style as S

comm = {r["entry_id"]: r["community_group"] for r in S.read("person_communities.csv")}
person_entry = {
    e["person_node"]: e["person_entry_id"]
    for e in S.read("edges_person_organisation.csv") if e["person_entry_id"]
}


def group(node: str) -> str:
    return comm.get(person_entry.get(node, ""), "")


observed = collections.Counter()
ends = collections.Counter()
tied_people = set()
for edge in S.read("edges_person_person.csv"):
    a, b = group(edge["source"]), group(edge["target"])
    if a in ("european", "tunisian") and b in ("european", "tunisian"):
        observed[tuple(sorted((a, b)))] += 1
        ends[a] += 1
        ends[b] += 1
        tied_people.update((edge["source"], edge["target"]))

n_ties = sum(observed.values())
p_eu = ends["european"] / (2 * n_ties)
p_tn = ends["tunisian"] / (2 * n_ties)
expected = {
    ("european", "european"): p_eu ** 2,
    ("european", "tunisian"): 2 * p_eu * p_tn,
    ("tunisian", "tunisian"): p_tn ** 2,
}
# Newman's assortativity: the excess of same-group ties over the null, scaled by
# the room the null leaves for any excess at all.
same = (observed[("european", "european")] + observed[("tunisian", "tunisian")]) / n_ties
null_same = expected[("european", "european")] + expected[("tunisian", "tunisian")]
r = (same - null_same) / (1 - null_same)

kinds = [
    (("european", "european"), "European\nwith European"),
    (("european", "tunisian"), "Across the two\ncommunities"),
    (("tunisian", "tunisian"), "Tunisian\nwith Tunisian"),
]
obs = [100 * observed[k] / n_ties for k, _ in kinds]
exp = [100 * expected[k] for k, _ in kinds]

x = np.arange(len(kinds))
width = 0.34
fig, ax = S.figure(7.4, 4.6)
S.grid(ax)
bars = ax.bar(x - width / 2 - 0.015, obs, width, color=S.BLUE, label="Observed", zorder=3)
nulls = ax.bar(x + width / 2 + 0.015, exp, width, color=S.DE_EMPHASIS,
               label="Expected if the same people joined at random", zorder=3)
for group_of_bars, values in ((bars, obs), (nulls, exp)):
    for bar, value in zip(group_of_bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.1,
                f"{value:.1f}%", ha="center", va="bottom",
                fontsize=8.5, color=S.INK_SECONDARY)
ax.set_xticks(x, [label for _, label in kinds])
ax.set_yticks([])
ax.set_ylim(0, max(obs + exp) * 1.16)
S.despine(ax)
ax.legend(loc="upper right")
S.titles(
    ax,
    "Europeans and Tunisians belonged to the same bodies less often than chance",
    f"Co-membership ties among the {len(tied_people)} people whose community the "
    f"entry settles and who share a body with another such person: {n_ties:,} ties. "
    f"Cross-community ties run {100 * (1 - obs[1] / exp[1]):.0f}% below the random "
    f"benchmark, and Tunisian-Tunisian ties at {obs[2] / exp[2]:.1f} times it. "
    f"Assortativity r = {r:.2f} — mild segregation, not separation. Fig. 62 puts the "
    "same question to the colonist/native coding, against a null that shuffles labels "
    "rather than assuming independence, and finds the gap wider.",
    ylabel="Share of coded co-membership ties",
    wrap=100,
)
S.save(fig, "fig24_community_mixing",
       "Ties from the one-mode projection; large membership rolls are excluded upstream")
