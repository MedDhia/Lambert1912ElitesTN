"""Export each person's position in the two networks as dataset columns.

The pipeline computed centrality and threw it away: `compare_populations.py`
needed betweenness, closeness and clustering for its brokerage models and
discarded them, and every figure that sizes a node recomputed them. Anyone
wanting to model on network position had to rebuild the graph themselves. This
writes them out once.

Two networks, kept separate because they answer different questions:

- **affiliation** — the two-mode people x bodies graph from
  `edges_person_organisation.csv`. Degree is the number of bodies a person is
  recorded in. Paths run person -> body -> person, so betweenness here measures
  brokerage *between organisations*.
- **co-membership** — the one-mode projection from `edges_person_person.csv`,
  an edge wherever two people share a body. This is the graph the comparison
  tables model, and the values below for its giant component are identical to
  the ones that stage computes.

Both are taken exactly as published, with no filtering beyond what
`build_networks.py` already applied (which excludes bodies with more than 60
recorded members from the projection, as a membership roll is not a committee).
In particular the ties resolved only ambiguously are *included*, as they are in
the published edge lists and in the comparison tables. The betweenness figures
additionally drop generically-named organisation nodes -- see
`code/figures/_networks.py` for why -- and that filter is deliberately not
applied here, so this file stays a faithful function of its published inputs.

Centrality is only meaningful within a component, so every measure is computed
inside the node's own component and `*_component_size` is exported alongside.
Comparing a betweenness score from a three-node component with one from the
giant is meaningless; the column is there so that mistake is visible.

There is no clustering column for the affiliation network: a two-mode graph has
no triangles, so it would be zero for everyone.

Output: data/processed/person_network_measures.csv, one row per person node
appearing in either network. A person whose notice records no affiliation has no
row -- 556 of the 1,307 notices are represented, plus the people who appear only
inside someone else's entry.
"""

from __future__ import annotations

import csv
import pathlib

import graph_metrics as gm

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"


def read(name: str) -> list[dict]:
    with (PROCESSED / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def measure(graph: dict[str, set[str]]) -> dict[str, dict[str, float]]:
    """Every measure for every node, computed within its own component."""
    result: dict[str, dict[str, float]] = {}
    for component in gm.components(graph):
        block = {node: graph[node] & component for node in component}
        betweenness = gm.betweenness(block)
        closeness = gm.closeness(block)
        clustering = gm.clustering(block)
        for node in component:
            result[node] = {
                "degree": float(len(block[node])),
                "component_size": float(len(component)),
                "betweenness": betweenness[node],
                "closeness": closeness[node],
                "clustering": clustering[node],
            }
    return result


def number(value: float) -> str:
    """Ten significant figures: enough to round-trip, short enough to read."""
    return f"{value:.10g}"


def main() -> int:
    affiliation_ties = read("edges_person_organisation.csv")
    affiliation = gm.adjacency(
        (tie["person_node"], tie["organisation_node"]) for tie in affiliation_ties)
    people_in_affiliation = {tie["person_node"] for tie in affiliation_ties}

    comembership = gm.adjacency(
        (tie["source"], tie["target"]) for tie in read("edges_person_person.csv"))

    affiliation_scores = measure(affiliation)
    comembership_scores = measure(comembership)

    labels = {n["node_id"]: n["label"] for n in read("network_nodes.csv")}
    entry_ids = {tie["person_node"]: tie["person_entry_id"]
                 for tie in affiliation_ties if tie["person_entry_id"]}
    with_notice = {p["entry_id"] for p in read("persons.csv")}

    affiliation_giant = max((s["component_size"] for s in affiliation_scores.values()),
                            default=0.0)
    comembership_giant = max((s["component_size"] for s in comembership_scores.values()),
                             default=0.0)

    nodes = sorted((people_in_affiliation | set(comembership_scores))
                   & (set(affiliation_scores) | set(comembership_scores)))
    rows = []
    for node in nodes:
        entry_id = entry_ids.get(node, "")
        row = {
            "node_id": node,
            "label": labels.get(node, ""),
            "entry_id": entry_id if entry_id in with_notice else "",
            "has_notice": int(entry_id in with_notice),
        }
        for prefix, scores, giant in (
            ("affil", affiliation_scores, affiliation_giant),
            ("comem", comembership_scores, comembership_giant),
        ):
            found = scores.get(node)
            if found is None:
                # Absent from this network: blank, not zero. A person with no
                # co-membership tie has no betweenness, which is not the same
                # claim as a betweenness of zero.
                row[f"{prefix}_degree"] = ""
                row[f"{prefix}_component_size"] = ""
                row[f"{prefix}_in_giant"] = ""
                row[f"{prefix}_betweenness"] = ""
                row[f"{prefix}_closeness"] = ""
            else:
                row[f"{prefix}_degree"] = int(found["degree"])
                row[f"{prefix}_component_size"] = int(found["component_size"])
                row[f"{prefix}_in_giant"] = int(found["component_size"] == giant)
                row[f"{prefix}_betweenness"] = number(found["betweenness"])
                row[f"{prefix}_closeness"] = number(found["closeness"])
            if prefix == "comem":
                row["comem_clustering"] = (
                    "" if found is None else number(found["clustering"]))
        rows.append(row)

    path = PROCESSED / "person_network_measures.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"  wrote {path.relative_to(ROOT)}: {len(rows)} person nodes "
          f"({sum(r['has_notice'] for r in rows)} with a notice); "
          f"affiliation giant {int(affiliation_giant)} nodes, "
          f"co-membership giant {int(comembership_giant)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
