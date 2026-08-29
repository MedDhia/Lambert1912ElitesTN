"""Shared reading of the colonist/native coding, so ten figures agree on it.

Every restriction this variable needs is in one place here, because each is easy
to forget and each changes the answer:

* **Giant component only, for any centrality.** `network_measures.py` computes
  betweenness and closeness inside each node's own component, and says plainly
  that comparing a score from a three-node component with one from the giant is
  meaningless. It is: the middle node of a three-node path scores 1.0.
* **Matched on `position_basis`.** A native is usually placed by an
  institutional tie and a colonist by a birthplace, and institutional ties are
  also what put a person in the network. Comparing the raw groups measures the
  coding. `matched()` holds the basis constant; fig. 55 shows the difference it
  makes.
* **`unknown` is not a third group.** It is 36% of the volume and is thinner on
  every measure -- fewer decorations, shorter entries, less networked -- so it
  is people the volume said less about, not a population.
"""

from __future__ import annotations

import collections
import itertools
import random
import statistics

import _style as S

COLONIST, NATIVE = "colonist", "native"
# Colonist reads as the volume's own default and takes the de-emphasis grey;
# native carries the emphasis colour. Two slots, all-pairs: validated.
COLOUR = {COLONIST: S.BLUE, NATIVE: S.ORANGE}
LABEL = {COLONIST: "Colonist", NATIVE: "Native"}


def coding() -> dict[str, dict]:
    """The positionality row for every person, keyed by entry_id."""
    return {r["entry_id"]: r for r in S.read("person_positionality.csv")}


def measures() -> dict[str, dict]:
    """Network measures for every person who has a node, keyed by entry_id."""
    return {r["entry_id"]: r for r in S.read("person_network_measures.csv")
            if r["entry_id"]}


def placed(rows: dict[str, dict] | None = None) -> list[dict]:
    """Everyone the coding places on one side or the other, in a stable order."""
    rows = rows if rows is not None else coding()
    return [rows[k] for k in sorted(rows)
            if rows[k]["positionality"] in (COLONIST, NATIVE)]


def in_giant(person: dict, measured: dict[str, dict]) -> dict | None:
    """This person's measures if they sit in the co-membership giant, else None."""
    row = measured.get(person["entry_id"])
    return row if row and row["comem_in_giant"] == "1" else None


def matched(basis: str = "institutional") -> dict[str, list[tuple[dict, dict]]]:
    """(person, measures) per side, in the giant, placed on the same evidence.

    Restricting to one basis is what makes the two sides comparable at all. The
    default is `institutional`, the only basis with enough people on both sides.
    """
    rows, measured = coding(), measures()
    out: dict[str, list[tuple[dict, dict]]] = {COLONIST: [], NATIVE: []}
    for person in placed(rows):
        if person["position_basis"] != basis:
            continue
        found = in_giant(person, measured)
        if found is not None:
            out[person["positionality"]].append((person, found))
    return out


def permutation_p(a: list[float], b: list[float], iterations: int = 20_000,
                  seed: int = 7) -> tuple[float, float]:
    """Two-sided difference in means and its permutation p-value.

    A seeded shuffle rather than a t-test: these are small, heavily
    zero-inflated samples and the normal approximation has no business here.
    """
    observed = statistics.fmean(a) - statistics.fmean(b)
    pool = sorted(a) + sorted(b)
    rng = random.Random(seed)
    split, hits = len(a), 0
    for _ in range(iterations):
        rng.shuffle(pool)
        drawn = statistics.fmean(pool[:split]) - statistics.fmean(pool[split:])
        if abs(drawn) >= abs(observed) - 1e-15:
            hits += 1
    return observed, (hits + 1) / (iterations + 1)


def p_text(p: float) -> str:
    """A p-value written the way it should be read."""
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def bodies_by_person() -> dict[str, set[str]]:
    """Which bodies each person belongs to, on unambiguous ties only."""
    out = collections.defaultdict(set)
    for tie in S.read("edges_person_organisation.csv"):
        if tie["person_entry_id"] and not tie["resolution"].startswith("ambiguous"):
            out[tie["person_entry_id"]].add(tie["organisation_node"])
    return out


def crossing_pairs(side: dict[str, str], cap: int = 60):
    """Co-membership pairs among placed people, split by whether they cross.

    `side` maps entry_id -> positionality. Bodies with more than `cap` members
    are dropped, as everywhere else in this repository: a printed membership
    roll of hundreds is a different kind of tie from a committee.
    """
    members = collections.defaultdict(set)
    for tie in S.read("edges_person_organisation.csv"):
        person = tie["person_entry_id"]
        if person and person in side and not tie["resolution"].startswith("ambiguous"):
            members[tie["organisation_node"]].add(person)
    bodies = [sorted(m) for m in
              (members[k] for k in sorted(members)) if 2 <= len(m) <= cap]
    counts = collections.Counter()
    for body in bodies:
        for a, b in itertools.combinations(body, 2):
            counts["mixed" if side[a] != side[b] else f"both_{side[a]}"] += 1
    return bodies, counts
