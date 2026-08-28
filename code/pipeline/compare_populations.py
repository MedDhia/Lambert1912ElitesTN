"""Compare the coded populations: community, and gender.

Applies the design of Hammami, "Gendered Informational Inequality in Elite
Networks", to Lambert (1912): code individuals, compute network position on the
giant component, and compare groups on brokerage and on the resources the record
reports.

The comparison is run at two very different sample sizes, and the tests differ
accordingly:

* **Community** (652 European, 173 Tunisian) supports the full apparatus:
  regression on log-transformed betweenness with degree, closeness and
  clustering as controls, plus the zero/positive hurdle decomposition.
* **Gender** does not. The volume contains eleven women, three with any
  affiliation tie and two in the giant component. At that size a zero-inflated
  negative binomial, a quantile regression, an IPTW re-weighting or a
  gender-by-community interaction are not estimable in any meaningful sense --
  a model will return coefficients, and they will be noise. What *is* valid at
  n = 11 is exact and permutation inference, which makes no large-sample
  assumption, so that is what is run.

Writes output/tables/comparison_tables.md and prints the same tables.
"""

from __future__ import annotations

import collections
import csv
import json
import math
import pathlib
import random
import statistics

import networkx as nx

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "output" / "tables"
SEED = 42
N_PERM = 100_000


def read(name: str) -> list[dict]:
    with (PROCESSED / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fisher_exact_2x2(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p for [[a,b],[c,d]]; valid at any cell size."""
    def p_table(x: int) -> float:
        return (
            math.comb(a + b, x) * math.comb(c + d, (a + c) - x)
            / math.comb(a + b + c + d, a + c)
        )
    observed = p_table(a)
    lo = max(0, (a + c) - (c + d))
    hi = min(a + b, a + c)
    return min(1.0, sum(
        p_table(x) for x in range(lo, hi + 1) if p_table(x) <= observed * (1 + 1e-9)
    ))


def permutation_diff(values_a: list[float], values_b: list[float],
                     n_perm: int = N_PERM) -> tuple[float, float]:
    """(observed difference in means, two-sided permutation p)."""
    rng = random.Random(SEED)
    pooled = values_a + values_b
    n_a = len(values_a)
    observed = statistics.fmean(values_a) - statistics.fmean(values_b)
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(pooled)
        diff = statistics.fmean(pooled[:n_a]) - statistics.fmean(pooled[n_a:])
        hits += abs(diff) >= abs(observed) - 1e-12
    return observed, hits / n_perm


def ols(y: list[float], X: list[list[float]]) -> tuple[list[float], list[float]]:
    """Least squares with classical standard errors, via normal equations."""
    n, k = len(y), len(X[0])
    xtx = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    xty = [sum(X[i][a] * y[i] for i in range(n)) for a in range(k)]
    aug = [row[:] + [xty[r]] for r, row in enumerate(xtx)]
    for col in range(k):                                   # Gauss-Jordan
        pivot = max(range(col, k), key=lambda r: abs(aug[r][col]))
        aug[col], aug[pivot] = aug[pivot], aug[col]
        if abs(aug[col][col]) < 1e-12:
            return [float("nan")] * k, [float("nan")] * k
        scale = aug[col][col]
        aug[col] = [v / scale for v in aug[col]]
        for r in range(k):
            if r != col and aug[r][col]:
                factor = aug[r][col]
                aug[r] = [v - factor * w for v, w in zip(aug[r], aug[col])]
    beta = [aug[r][k] for r in range(k)]
    resid = [y[i] - sum(X[i][a] * beta[a] for a in range(k)) for i in range(n)]
    sigma2 = sum(r * r for r in resid) / max(n - k, 1)
    inv = [[aug[r][c] for c in range(k)] for r in range(k)]  # not the true inverse
    # Recompute the inverse properly for the standard errors.
    ident = [[float(r == c) for c in range(k)] for r in range(k)]
    work = [row[:] + ident[r] for r, row in enumerate(xtx)]
    for col in range(k):
        pivot = max(range(col, k), key=lambda r: abs(work[r][col]))
        work[col], work[pivot] = work[pivot], work[col]
        scale = work[col][col]
        work[col] = [v / scale for v in work[col]]
        for r in range(k):
            if r != col and work[r][col]:
                factor = work[r][col]
                work[r] = [v - factor * w for v, w in zip(work[r], work[col])]
    inv = [[work[r][k + c] for c in range(k)] for r in range(k)]
    se = [math.sqrt(max(sigma2 * inv[a][a], 0)) for a in range(k)]
    return beta, se


def zscore(values: list[float]) -> list[float]:
    mean = statistics.fmean(values)
    sd = statistics.pstdev(values) or 1.0
    return [(v - mean) / sd for v in values]


def table(header: list[str], rows: list[list], out: list[str]) -> None:
    out.append("| " + " | ".join(header) + " |")
    out.append("|" + "|".join(["---"] * len(header)) + "|")
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    out.append("")


def main() -> int:
    persons = {p["entry_id"]: p for p in read("persons.csv")}
    gender = {g["entry_id"]: g for g in read("person_gender.csv")}
    community = {c["entry_id"]: c for c in read("person_communities.csv")}

    # --- network position, as in the paper: the giant component ------------
    graph = nx.Graph()
    for e in read("edges_person_person.csv"):
        graph.add_edge(e["source"], e["target"], weight=int(e["weight"]))
    giant = graph.subgraph(max(nx.connected_components(graph), key=len)).copy()
    betweenness = nx.betweenness_centrality(giant)
    closeness = nx.closeness_centrality(giant)
    clustering = nx.clustering(giant)
    degree = dict(giant.degree())

    out: list[str] = ["# Comparison tables\n",
                      "Generated by `code/pipeline/compare_populations.py`.\n"]

    # --- 1. composition -----------------------------------------------------
    out.append("## 1. Who the volume contains\n")
    counts = collections.Counter(c["community"] for c in community.values())
    table(["Community", "n", "% of notices"],
          [[k, v, f"{100 * v / len(persons):.1f}"] for k, v in counts.most_common()], out)
    gcounts = collections.Counter(g["gender"] for g in gender.values())
    table(["Gender", "n", "% of notices"],
          [[k, v, f"{100 * v / len(persons):.2f}"] for k, v in gcounts.most_common()], out)

    # --- 2. resources by community -----------------------------------------
    out.append("## 2. What each community holds\n")
    groups = collections.defaultdict(list)
    for eid, c in community.items():
        if c["community_group"] in ("european", "tunisian"):
            groups[c["community_group"]].append(persons[eid])
    rows = []
    for label, key, fn in [
        ("Holds Légion d'honneur (%)", "has_legion_honneur",
         lambda v: 100 * statistics.fmean([float(x) for x in v])),
        ("Holds Nichan Iftikhar (%)", "has_nichan_iftikhar",
         lambda v: 100 * statistics.fmean([float(x) for x in v])),
        ("Mean honours named", "n_decorations",
         lambda v: statistics.fmean([float(x) for x in v])),
        ("Median entry length (chars)", "n_chars",
         lambda v: statistics.median([float(x) for x in v])),
        ("Carries a portrait (%)", "n_portraits",
         lambda v: 100 * statistics.fmean([float(x) > 0 for x in v])),
    ]:
        eu = fn([p[key] for p in groups["european"]])
        tn = fn([p[key] for p in groups["tunisian"]])
        rows.append([label, f"{eu:.1f}", f"{tn:.1f}", f"{tn - eu:+.1f}"])
    table(["Measure", f"European (n={len(groups['european'])})",
           f"Tunisian (n={len(groups['tunisian'])})", "Difference"], rows, out)

    # Fisher exact on the two honours systems
    for order, label in [("has_legion_honneur", "Légion d'honneur"),
                         ("has_nichan_iftikhar", "Nichan Iftikhar")]:
        a = sum(1 for p in groups["tunisian"] if p[order] == "1")
        b = len(groups["tunisian"]) - a
        c = sum(1 for p in groups["european"] if p[order] == "1")
        d = len(groups["european"]) - c
        out.append(f"- **{label}**: {a}/{a + b} Tunisian vs {c}/{c + d} European, "
                   f"Fisher exact p = {fisher_exact_2x2(a, b, c, d):.4g}")
    out.append("")

    # --- 3. brokerage by community: the paper's models ---------------------
    out.append("## 3. Brokerage by community\n")
    sample = []
    for node in giant:
        c = community.get(node)
        if c and c["community_group"] in ("european", "tunisian"):
            sample.append({
                "tunisian": 1.0 if c["community_group"] == "tunisian" else 0.0,
                "bc": betweenness[node], "deg": float(degree[node]),
                "close": closeness[node], "clust": clustering[node],
            })
    out.append(f"Persons with a notice, a coded community and a place in the giant "
               f"component: **n = {len(sample)}** "
               f"({sum(int(s['tunisian']) for s in sample)} Tunisian).\n")
    if len(sample) >= 40:
        y = [math.log1p(s["bc"] * 1000) for s in sample]
        X = [[1.0, s["tunisian"]] for s in sample]
        beta, se = ols(y, X)
        Xc = [[1.0, s["tunisian"], z1, z2, z3] for s, z1, z2, z3 in zip(
            sample, zscore([s["deg"] for s in sample]),
            zscore([s["close"] for s in sample]),
            zscore([s["clust"] for s in sample]))]
        beta_c, se_c = ols(y, Xc)
        table(["Model", "Tunisian coefficient", "SE", "t"],
              [["log1p(betweenness×1000) ~ community", f"{beta[1]:.3f}", f"{se[1]:.3f}",
                f"{beta[1] / se[1]:.2f}"],
               ["+ degree, closeness, clustering (standardised)", f"{beta_c[1]:.3f}",
                f"{se_c[1]:.3f}", f"{beta_c[1] / se_c[1]:.2f}"]], out)
        zero_tn = [s for s in sample if s["tunisian"]]
        zero_eu = [s for s in sample if not s["tunisian"]]
        out.append(f"- Zero brokerage: {100 * statistics.fmean([s['bc'] == 0 for s in zero_tn]):.1f}% "
                   f"of Tunisians, {100 * statistics.fmean([s['bc'] == 0 for s in zero_eu]):.1f}% "
                   f"of Europeans in the component.")
        obs, p = permutation_diff([math.log1p(s["bc"] * 1000) for s in zero_tn],
                                  [math.log1p(s["bc"] * 1000) for s in zero_eu],
                                  n_perm=20_000)
        out.append(f"- Permutation test on mean log brokerage (20,000 draws): "
                   f"difference {obs:+.3f}, p = {p:.4f}\n")

    # --- 4. gender: what the data will and will not support ----------------
    out.append("## 4. Gender\n")
    women = [eid for eid, g in gender.items() if g["gender"] == "FEMALE"]
    men = [eid for eid, g in gender.items() if g["gender"] == "MALE"]
    affiliated = {e["person_node"] for e in read("edges_person_organisation.csv")}
    w_net = [e for e in women if e in giant]
    m_net = [e for e in men if e in giant]
    table(["Measure", "Women", "Men"],
          [["Notices in the volume", len(women), len(men)],
           ["With any affiliation tie", sum(e in affiliated for e in women),
            sum(e in affiliated for e in men)],
           ["In the co-membership giant component", len(w_net), len(m_net)]], out)

    a, b = sum(e in affiliated for e in women), len(women) - sum(e in affiliated for e in women)
    c = sum(e in affiliated for e in men)
    d = len(men) - c
    out.append(f"Fisher exact test on having any affiliation tie: p = "
               f"{fisher_exact_2x2(a, b, c, d):.4g}. This is the one inference the "
               f"cell sizes support.\n")

    obs, p = permutation_diff(
        [float(persons[e]["n_chars"]) for e in women],
        [float(persons[e]["n_chars"]) for e in men], n_perm=20_000)
    out.append(f"Permutation test on entry length (20,000 draws): women's notices run "
               f"{obs:+.0f} characters against men's, p = {p:.4f}.\n")

    out.append(
        "**Not estimable here.** The paper's zero-inflated negative binomial, its "
        "quantile regressions, its IPTW re-weighting, its mediation analysis and its "
        f"gender-by-community interaction all require variation among women. There are "
        f"{len(w_net)} women in the giant component and {sum(1 for e in women if community[e]['community_group'] == 'tunisian')} "
        "Tunisian woman in the whole volume. Fitting those models would return "
        "coefficients, and the coefficients would be artefacts of two observations. "
        "The absence is the finding: a 1912 who's-who of the Protectorate recorded "
        f"{len(women)} women among {len(persons)} notables, and all but three of them "
        "outside any recorded organisation.\n")

    TABLES.mkdir(parents=True, exist_ok=True)
    (TABLES / "comparison_tables.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
