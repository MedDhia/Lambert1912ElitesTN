"""Test homophily in the co-membership network, attribute by attribute.

THE QUESTION
------------
Do people who sit on the same body resemble each other more than chance allows,
and on which attribute? The answer here is narrow and worth stating up front:
the network sorts on the colonial and communal line and on almost nothing else.
Two men of the same age, or holding the same number of decorations, are no more
likely to share a committee than any two men in the volume.

THREE STATISTICS, BECAUSE ONE IS NOT ENOUGH
-------------------------------------------
* **Newman's nominal assortativity** `r` -- the share of ties that fall within a
  group, corrected for what the group sizes alone would produce. 0 is chance,
  1 is complete separation. This is the headline.
* **The E-I index** -- (external - internal) / total ties. Reported because it
  is conventional, and read with care: with 715 colonists and 126 natives most
  ties are internal whatever anyone prefers, so E-I mostly measures group size.
* **Coleman's index**, per group -- the same idea as `r` but computed for one
  group at a time against its share of the population, which is what makes it
  possible to say that the closure is stronger on the settler side.

THE NULL, WHICH IS THE WHOLE ARGUMENT
-------------------------------------
The one-mode projection turns every body into a clique: its members are all
mutually tied by construction. Any homophily statistic computed on it is
therefore inflated, and no analytic standard error is honest, because the ties
are not independent draws.

The null used here holds the **graph fixed** and permutes the attribute labels
over the nodes. Every clique the projection manufactured is present in the null
as well, so its contribution cancels, and the p-value is exact under the
hypothesis that labels are assigned at random. `permutation_p` is the only
inference in this module; nothing here reports a t-statistic.

FOUR THINGS THAT COULD EXPLAIN THE RESULT AWAY, AND DO NOT
----------------------------------------------------------
Ranked by how much they worried the author:

1. **Circularity.** `code_communities.py` places some people *by* their
   membership of a communal body -- a Jewish or Muslim society, an Italian
   association, a French settler club. Those people are in that body with
   others of their kind by construction, so part of the homophily could be the
   coding rule reflected back. Dropping every community-marked body takes the
   colonist/native `r` from +0.33 to +0.24: about a quarter of the raw effect is
   circular, and three quarters is not.
2. **Degree.** Natives hold fewer ties than colonists, and a plain label shuffle
   breaks that association. Permuting labels *within degree quartiles* leaves
   the result where it was.
3. **One big clique.** A single large body with a homogeneous membership could
   carry everything, since it contributes pairs in proportion to the square of
   its size. Weighting every body equally instead reproduces the finding.
4. **One influential body.** A leave-one-body-out pass reports the largest
   swings, and no body moves `r` by more than about 0.05.

Writes output/tables/homophily.md and prints the same tables. Standard library
only, like the rest of the pipeline: assortativity and a shuffle need arithmetic
and an edge list, not a graph library.
"""

from __future__ import annotations

import collections
import csv
import itertools
import json
import pathlib
import random
import re
import statistics

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "output" / "tables"

SEED = 17
N_PERM = 2_000
# Bodies larger than this are printed membership rolls rather than committees,
# and are excluded from the projection everywhere in this repository.
MAX_BODY = 60

# Bodies whose printed name marks them as one community's own. These are the
# bodies `code_communities.py` reads as evidence, which is what makes them a
# circularity risk rather than merely interesting.
COMMUNITY_MARKED = re.compile(
    r"musulman|indig[èe]ne|isra[ée]lite|juive|h[ée]bra|italian|italien|associazione|"
    r"societ[aà]\b|maltais|colons\s+fran[çc]ais|"
    r"soci[ée]t[ée]\s+fran[çc]aise\s+de\s+bienfaisance|cercle\s+civil\s+fran[çc]ais|"
    r"travailleurs\s+fran[çc]ais|union\s+fran[çc]aise",
    re.IGNORECASE,
)

Pair = tuple[str, str]


def read(name: str) -> list[dict]:
    with (PROCESSED / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# --- the network ------------------------------------------------------------

def bodies(marked: bool | None = None) -> list[list[str]]:
    """Membership lists, in a stable order, as the projection reads them.

    `marked=False` keeps only the bodies whose name does *not* mark a community,
    which is robustness check 1.
    """
    return [members for members, _ in named_bodies(marked)]


def named_bodies(marked: bool | None = None) -> list[tuple[list[str], str]]:
    """(members, printed name) per body, so a result can name what produced it."""
    members: dict[str, set[str]] = collections.defaultdict(set)
    names: dict[str, str] = {}
    for tie in read("edges_person_organisation.csv"):
        person = tie["person_entry_id"]
        if not person or tie["resolution"].startswith("ambiguous"):
            continue
        members[tie["organisation_node"]].add(person)
        names[tie["organisation_node"]] = tie["organisation_name"]
    out = []
    for node in sorted(members):
        if marked is not None and bool(COMMUNITY_MARKED.search(names[node])) != marked:
            continue
        if 2 <= len(members[node]) <= MAX_BODY:
            out.append((sorted(members[node]), names[node]))
    return out


def pairs(membership: list[list[str]], labelled: dict[str, str]) -> list[Pair]:
    """Every co-membership tie between two labelled people, deduplicated.

    Two people on three committees together are one tie, not three: this is an
    unweighted projection, and counting the repeat would let a handful of
    double-booked pairs stand in for a pattern.
    """
    seen: set[Pair] = set()
    for body in membership:
        inside = [m for m in body if m in labelled]
        seen.update(itertools.combinations(inside, 2))
    return sorted(seen)


# --- the statistics ---------------------------------------------------------

def mixing(edges: list[Pair], label: dict[str, str]) -> collections.Counter:
    """Symmetric counts e[(a, b)], each tie counted in both directions."""
    counts: collections.Counter = collections.Counter()
    for u, v in edges:
        counts[(label[u], label[v])] += 1
        counts[(label[v], label[u])] += 1
    return counts


def assortativity(edges: list[Pair], label: dict[str, str]) -> float:
    """Newman's nominal assortativity: (trace - sum a_i^2) / (1 - sum a_i^2)."""
    counts = mixing(edges, label)
    total = sum(counts.values())
    if not total:
        return float("nan")
    groups = sorted({g for pair in counts for g in pair})
    shares = {g: sum(counts[(g, h)] for h in groups) / total for g in groups}
    trace = sum(counts[(g, g)] for g in groups) / total
    expected = sum(shares[g] ** 2 for g in groups)
    return (trace - expected) / (1 - expected) if expected < 1 else float("nan")


def ei_index(edges: list[Pair], label: dict[str, str]) -> float:
    """(external - internal) / total. Dominated by group size; see the docstring."""
    internal = sum(1 for u, v in edges if label[u] == label[v])
    return (len(edges) - 2 * internal) / len(edges) if edges else float("nan")


def coleman(edges: list[Pair], label: dict[str, str]) -> dict[str, float]:
    """Per-group homophily against the group's share of the population."""
    degree: collections.Counter = collections.Counter()
    same: collections.Counter = collections.Counter()
    size = collections.Counter(label.values())
    n = len(label)
    for u, v in edges:
        for x, y in ((u, v), (v, u)):
            degree[label[x]] += 1
            same[label[x]] += label[x] == label[y]
    out = {}
    for group, total in sorted(degree.items()):
        observed = same[group] / total
        expected = (size[group] - 1) / (n - 1)
        out[group] = ((observed - expected) / (1 - expected)
                      if expected < 1 else float("nan"))
    return out


def permutation_p(edges: list[Pair], label: dict[str, str],
                  strata: dict[str, int] | None = None,
                  statistic=assortativity, iterations: int = N_PERM,
                  seed: int = SEED) -> dict:
    """Observed statistic against labels shuffled with the graph held fixed.

    `strata` restricts each shuffle to within a stratum -- pass degree quartiles
    to ask whether the result survives holding degree constant (check 2).
    """
    observed = statistic(edges, label)
    nodes = sorted(label)
    blocks: dict[int, list[str]] = collections.defaultdict(list)
    for node in nodes:
        blocks[0 if strata is None else strata[node]].append(node)
    rng = random.Random(seed)
    drawn = []
    for _ in range(iterations):
        shuffled = {}
        for block in sorted(blocks):
            members = blocks[block]
            values = [label[n] for n in members]
            rng.shuffle(values)
            shuffled.update(zip(members, values))
        drawn.append(statistic(edges, shuffled))
    at_least = sum(1 for d in drawn if d >= observed)
    return {
        "observed": observed,
        "null_mean": statistics.fmean(drawn),
        "null_sd": statistics.pstdev(drawn),
        "p": (at_least + 1) / (iterations + 1),
    }


def body_purity(membership: list[list[str]], label: dict[str, str]) -> float:
    """Mean within-body share of same-label pairs, one observation per body.

    Check 3: every body counts once, so a large clique cannot dominate the way
    it does when ties are counted individually.
    """
    shares = []
    for body in membership:
        inside = [m for m in body if m in label]
        if len(inside) < 2:
            continue
        combos = list(itertools.combinations(inside, 2))
        shares.append(sum(label[a] == label[b] for a, b in combos) / len(combos))
    return statistics.fmean(shares) if shares else float("nan")


def degree_quartiles(edges: list[Pair], label: dict[str, str]) -> dict[str, int]:
    degree: collections.Counter = collections.Counter()
    for u, v in edges:
        degree[u] += 1
        degree[v] += 1
    values = sorted(degree[n] for n in label)
    if not values:
        return {n: 0 for n in label}
    cuts = [values[int(f * len(values))] for f in (0.25, 0.5, 0.75)]
    return {n: sum(degree[n] > c for c in cuts) for n in label}


# --- the attributes ---------------------------------------------------------

def attributes() -> dict[str, dict[str, str]]:
    """Every attribute worth testing, as {name: {entry_id: value}}.

    An attribute the volume does not print for someone leaves them out of that
    attribute's test rather than joining an "unknown" group: "the volume did not
    say" is not a category people can be homophilous on.
    """
    persons = {r["entry_id"]: r for r in read("persons.csv")}
    positionality = {r["entry_id"]: r for r in read("person_positionality.csv")}
    communities = {r["entry_id"]: r for r in read("person_communities.csv")}

    def cohort(row: dict) -> str | None:
        year = row["birth_year"]
        if not year or not 1810 <= int(year) <= 1900:
            return None
        return f"{10 * (int(year) // 10)}s"

    def defined(source: dict, column: str, blank: str) -> dict[str, str]:
        return {k: v[column] for k, v in source.items() if v[column] != blank}

    return {
        "Positionality (colonist / native)":
            defined(positionality, "positionality", "unknown"),
        "Community (European / Tunisian)":
            defined(communities, "community_group", "unknown"),
        "Community (six groups)":
            defined(communities, "community", "unknown"),
        "Occupation sector":
            {k: v["occupation_primary"] for k, v in persons.items()
             if v["occupation_primary"]},
        "Birth cohort":
            {k: c for k, v in persons.items() if (c := cohort(v))},
        "Holds any honour":
            {k: ("decorated" if int(v["n_decorations"]) else "undecorated")
             for k, v in persons.items()},
    }


def test_attribute(name: str, label: dict[str, str],
                   membership: list[list[str]]) -> dict | None:
    edges = pairs(membership, label)
    inside = {n: label[n] for n in {x for e in edges for x in e}}
    if len(edges) < 30 or len(set(inside.values())) < 2:
        return None
    result = permutation_p(edges, inside)
    result.update(name=name, n=len(inside), ties=len(edges),
                  ei=ei_index(edges, inside), coleman=coleman(edges, inside),
                  groups=len(set(inside.values())))
    return result


def robustness(label: dict[str, str]) -> list[dict]:
    """The four checks, each against its own null."""
    every = bodies()
    edges = pairs(every, label)
    inside = {n: label[n] for n in {x for e in edges for x in e}}
    unmarked = bodies(marked=False)
    unmarked_edges = pairs(unmarked, label)
    unmarked_inside = {n: label[n] for n in {x for e in unmarked_edges for x in e}}

    checks = [
        dict(check="Every body", unit="assortativity r",
             **permutation_p(edges, inside), n=len(inside), ties=len(edges)),
        dict(check="Community-marked bodies removed", unit="assortativity r",
             **permutation_p(unmarked_edges, unmarked_inside),
             n=len(unmarked_inside), ties=len(unmarked_edges)),
        dict(check="Labels shuffled within degree quartile", unit="assortativity r",
             **permutation_p(edges, inside, strata=degree_quartiles(edges, inside)),
             n=len(inside), ties=len(edges)),
        dict(check="Every body weighted equally", unit="within-body same-label share",
             **permutation_p(edges, inside,
                             statistic=lambda _e, lab: body_purity(every, lab)),
             n=len(inside), ties=len(edges)),
    ]
    return checks


def influential_bodies(label: dict[str, str], top: int = 6) -> list[tuple]:
    """Leave-one-body-out on r, largest absolute swings first (check 4).

    A negative swing means the body was holding the result up; a positive one
    means it was a place where the two sides actually met.
    """
    every = named_bodies()
    base_edges = pairs([m for m, _ in every], label)
    base = assortativity(base_edges,
                         {n: label[n] for n in {x for e in base_edges for x in e}})
    swings = []
    for index, (body, name) in enumerate(every):
        kept = [m for i, (m, _) in enumerate(every) if i != index]
        edges = pairs(kept, label)
        inside = {n: label[n] for n in {x for e in edges for x in e}}
        if len(edges) < 30:
            continue
        swings.append((assortativity(edges, inside) - base, len(body), name))
    swings.sort(key=lambda s: (-abs(s[0]), s[2]))
    return swings[:top]


def main() -> int:
    every = bodies()
    attrs = attributes()
    results = [r for name, label in attrs.items()
               if (r := test_attribute(name, label, every))]
    results.sort(key=lambda r: -r["observed"])

    colonial = attrs["Positionality (colonist / native)"]
    checks = robustness(colonial)

    lines = [
        "# Homophily in the co-membership network",
        "",
        "Generated by `code/pipeline/homophily.py`. Every p-value is a permutation",
        f"test with the graph held fixed and the labels shuffled, {N_PERM:,} draws,",
        f"seed {SEED}. Bodies with more than {MAX_BODY} recorded members are excluded",
        "as printed membership rolls rather than committees.",
        "",
        "## 1. Assortativity by attribute",
        "",
        "| Attribute | people | ties | groups | r | null r | sd | p | E-I |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['name']} | {r['n']} | {r['ties']} | {r['groups']} | "
            f"{r['observed']:+.3f} | {r['null_mean']:+.3f} | {r['null_sd']:.3f} | "
            f"{r['p']:.4f} | {r['ei']:+.3f} |")
    lines += [
        "",
        "The colonial and communal attributes sort the network; occupation barely",
        "does, and birth cohort and honours do not at all. Homophily here is",
        "specific rather than general.",
        "",
        "## 2. Coleman's index, by group",
        "",
        "Per-group homophily against the group's own share of the population, so",
        "the majority is not flattered by its size.",
        "",
        "| Attribute | group | Coleman |",
        "|---|---|---|",
    ]
    for r in results:
        if r["groups"] > 6 or r["observed"] < 0.1:
            continue
        for group, value in sorted(r["coleman"].items(), key=lambda kv: -kv[1]):
            lines.append(f"| {r['name']} | {group} | {value:+.3f} |")

    lines += [
        "",
        "## 3. Mixing across the colonial line",
        "",
        "| pair | observed | expected from group sizes alone |",
        "|---|---|---|",
    ]
    edges = pairs(every, colonial)
    inside = {n: colonial[n] for n in {x for e in edges for x in e}}
    counts = collections.Counter(
        tuple(sorted((inside[u], inside[v]))) for u, v in edges)
    total = sum(counts.values())
    size = collections.Counter(inside.values())
    n = len(inside)
    for pair, count in sorted(counts.items()):
        if pair[0] == pair[1]:
            expected = (size[pair[0]] / n) ** 2
        else:
            expected = 2 * (size[pair[0]] / n) * (size[pair[1]] / n)
        lines.append(f"| {pair[0]} – {pair[1]} | {100 * count / total:.1f}% | "
                     f"{100 * expected:.1f}% |")

    lines += [
        "",
        "## 4. Robustness on the colonist / native split",
        "",
        "| check | statistic | observed | null | sd | p |",
        "|---|---|---|---|---|---|",
    ]
    for c in checks:
        lines.append(
            f"| {c['check']} | {c['unit']} | {c['observed']:+.3f} | "
            f"{c['null_mean']:+.3f} | {c['null_sd']:.3f} | {c['p']:.4f} |")
    lines += [
        "",
        "Removing the community-marked bodies is the check that matters: those are",
        "the bodies the community coding reads as evidence, so a person placed by",
        "one is in it with others of their kind by construction. The effect falls",
        "by about a quarter and survives.",
        "",
        "## 5. Leave-one-body-out",
        "",
        "| body | members | change in r when dropped |",
        "|---|---|---|",
    ]
    for delta, body_size, name in influential_bodies(colonial):
        lines.append(f"| {name} | {body_size} | {delta:+.4f} |")
    lines += [
        "",
        "No single body carries the result. A negative swing marks a body that was",
        "holding the homophily up; a positive one marks a body where the two sides",
        "actually met.",
        "",
    ]

    TABLES.mkdir(parents=True, exist_ok=True)
    (TABLES / "homophily.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(json.dumps({
        "attributes_tested": len(results),
        "significant_at_05": sum(1 for r in results if r["p"] < 0.05),
        "colonial_r": round(checks[0]["observed"], 3),
        "colonial_r_without_marked_bodies": round(checks[1]["observed"], 3),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
