"""Fig. 64 — What the network sorts on, and what it does not.

Fig. 62 showed that colonists and natives shared bodies less often than chance.
This asks the prior question: is that a general tendency of the network — like
associating with like — or is it specific to the colonial line? Six attributes,
one test, and the answer is that five of them do nothing.
"""
import sys

import numpy as np

import _positionality as P
import _style as S

sys.path.insert(0, str(S.ROOT / "code" / "pipeline"))
import homophily as H  # noqa: E402

membership = H.bodies()
results = [r for name, label in H.attributes().items()
           if (r := H.test_attribute(name, label, membership))]
results.sort(key=lambda r: r["observed"])

# The two colonial and communal readings of the same line carry the emphasis;
# the attributes that turn out to do nothing are the comparison, not the point.
COLONIAL = ("Positionality", "Community")
colours = [S.ORANGE if r["name"].startswith(COLONIAL) else S.DE_EMPHASIS
           for r in results]

fig, ax = S.figure(8.0, 4.4)
S.grid(ax, axis="x")
y = np.arange(len(results))
# The null band is what makes the chart readable: r on its own says nothing
# without the spread a random labelling of this same graph would produce.
for index, r in enumerate(results):
    ax.barh(index, 4 * r["null_sd"], left=r["null_mean"] - 2 * r["null_sd"],
            height=0.5, color=S.GRID, zorder=2)
ax.axvline(0, color=S.AXIS, linewidth=0.8, zorder=1)
ax.scatter([r["observed"] for r in results], y, s=74, color=colours,
           edgecolors=S.SURFACE, linewidths=1.2, zorder=4)
for index, r in enumerate(results):
    # Clear of the null band as well as the mark: a label set over grey on the
    # rows that did nothing is exactly where it is hardest to read.
    ax.text(max(r["observed"], r["null_mean"] + 2 * r["null_sd"]) + 0.012, index,
            f"{r['observed']:+.3f}   {P.p_text(r['p'])}", va="center", ha="left",
            fontsize=8, color=S.INK if r["p"] < 0.05 else S.INK_MUTED)
ax.set_yticks(y, [f"{r['name']}\n{r['n']} people · {r['ties']:,} ties"
                  for r in results], fontsize=8)
ax.set_xlim(-0.06, 0.46)
S.despine(ax, keep=("bottom",))

colonial = max(results, key=lambda r: r["observed"])
weak = [r for r in results if r["p"] >= 0.05]
S.titles(
    ax,
    "The network sorts on the colonial line and on almost nothing else",
    f"Newman's nominal assortativity for six attributes on the co-membership "
    f"network. The grey band is the middle of {H.N_PERM:,} relabellings of the same "
    f"graph — the null the projection demands, since every clique it manufactured "
    f"is present in the null too. Positionality reaches {colonial['observed']:+.3f}; "
    f"{' and '.join(r['name'].split(' (')[0].lower() for r in weak)} sit inside "
    f"their own null. This is not a network in which similar people associate: two "
    "men of the same age, or holding the same number of decorations, are no more "
    "likely to share a committee than any two men in the volume.",
    xlabel="Assortativity r  (0 = chance, 1 = complete separation)",
    wrap=104,
)
S.save(fig, "fig64_homophily_by_attribute",
       f"Bodies with 2–{H.MAX_BODY} recorded members; seed {H.SEED}; "
       "full tables in output/tables/homophily.md")
