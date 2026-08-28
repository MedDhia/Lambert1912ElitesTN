"""Descriptive tables and network summaries over the processed dataset.

Standard library only, so it runs anywhere Python does. Everything here is meant
to be read as much as run: it shows which columns answer which kind of question.

    python3 code/examples/quickstart.py
"""

from __future__ import annotations

import collections
import csv
import itertools
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "processed"


def load(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def rule(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


def bar(n: int, total: int, width: int = 32) -> str:
    return "#" * max(1, round(width * n / total)) if n else ""


def main() -> None:
    persons = load("persons.csv")
    orgs = load("organizations.csv")
    places = load("places.csv")
    decs = load("decorations.csv")
    edges = load("edges_person_organisation.csv")
    careers = load("career_positions.csv")

    rule("1. Birth cohorts of the 1,307 biographical notices")
    cohorts = collections.Counter(
        int(p["birth_year"]) // 10 * 10 for p in persons if p["birth_year"]
    )
    peak = max(cohorts.values())
    for decade in sorted(cohorts):
        if decade >= 1820:
            print(f"  {decade}s  {cohorts[decade]:4}  {bar(cohorts[decade], peak)}")
    print(f"  (birth year readable for {sum(cohorts.values())} of {len(persons)})")

    rule("2. Sector, by primary occupational category")
    occ = collections.Counter(p["occupation_primary"] or "(not coded)" for p in persons)
    for k, v in occ.most_common():
        print(f"  {k:28} {v:4}")

    rule("3. Two honours systems side by side")
    # The French state and the Bey both distribute status; who gets which, and in
    # what grade, is one of the more directly usable measures in the volume.
    fr = sum(1 for p in persons if p["has_legion_honneur"] == "1")
    tn = sum(1 for p in persons if p["has_nichan_iftikhar"] == "1")
    both = sum(
        1 for p in persons
        if p["has_legion_honneur"] == "1" and p["has_nichan_iftikhar"] == "1"
    )
    none = sum(1 for p in persons if p["n_decorations"] == "0")
    print(f"  Legion d'honneur              {fr:4}")
    print(f"  Nichan Iftikhar (beylical)    {tn:4}")
    print(f"  both                          {both:4}")
    print(f"  no honour named               {none:4}")
    print("\n  Grades of the Nichan Iftikhar:")
    grades = collections.Counter(
        d["grade"] or "(not stated)" for d in decs if d["order"] == "nichan_iftikhar"
    )
    for k, v in grades.most_common():
        print(f"    {k:20} {v:4}")

    rule("4. Honours by sector (share holding a French honour)")
    by_sector: dict[str, list[int]] = collections.defaultdict(list)
    for p in persons:
        if p["occupation_primary"]:
            by_sector[p["occupation_primary"]].append(p["has_legion_honneur"] == "1")
    rows = [(k, len(v), 100 * sum(v) / len(v)) for k, v in by_sector.items() if len(v) >= 25]
    for k, n, pct in sorted(rows, key=lambda r: -r[2]):
        print(f"  {k:28} n={n:4}  {pct:5.1f}%")

    rule("5. The associational field")
    kinds = collections.Counter(o["organisation_kind_primary"] or "(not coded)" for o in orgs)
    for k, v in kinds.most_common():
        print(f"  {k:28} {v:4}")

    rule("6. Best-connected bodies in the affiliation network")
    deg = collections.Counter(e["organisation_node"] for e in edges)
    label = {e["organisation_node"]: e["organisation_name"] for e in edges}
    for node, n in deg.most_common(12):
        print(f"  {n:4}  {label[node][:60]}")

    rule("7. Best-connected people (affiliations held)")
    pdeg = collections.Counter(
        e["person_node"] for e in edges if e["resolution"] != "ambiguous"
    )
    plabel = {p["entry_id"]: f"{p['surname']} ({p['forenames']})" for p in persons}
    for node, n in pdeg.most_common(12):
        print(f"  {n:4}  {plabel.get(node, node)[:60]}")

    rule("8. Career sequences: what follows military service")
    # position_order preserves Lambert's printed order, which is chronological.
    seqs: dict[str, list[tuple[int, str]]] = collections.defaultdict(list)
    for c in careers:
        if c["occupation_categories"]:
            seqs[c["entry_id"]].append(
                (int(c["position_order"]), c["occupation_categories"].split(";")[0])
            )
    transitions: collections.Counter[tuple[str, str]] = collections.Counter()
    for steps in seqs.values():
        ordered = [cat for _, cat in sorted(steps)]
        for a, b in itertools.pairwise(ordered):
            if a != b:
                transitions[(a, b)] += 1
    for (a, b), n in transitions.most_common(10):
        print(f"  {n:4}  {a} -> {b}")

    rule("9. Colonial geography: localities per contrôle civil")
    cc = collections.Counter(p["controle_civil"] for p in places if p["controle_civil"])
    for k, v in cc.most_common(12):
        print(f"  {k:24} {v:4}")

    rule("10. Verifying any of the above")
    p = next(x for x in persons if x["has_legion_honneur"] == "1" and x["career_raw"])
    print(f"  {p['surname']} ({p['forenames']}), b. {p['birth_year']} {p['birth_place']}")
    print(f"  honours : {p['decoration_orders']}")
    print(f"  career  : {p['career_raw'][:150]}...")
    entries = {e["entry_id"]: e for e in load("entries.csv")}
    print(f"  page    : {entries[p['entry_id']]['page_url']}")


if __name__ == "__main__":
    main()
