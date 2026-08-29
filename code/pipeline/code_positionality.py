"""Code each person's position in the colonial order: colonist or native.

WHAT THIS VARIABLE IS -- AND HOW IT DIFFERS FROM `community`
-----------------------------------------------------------
`code_communities.py` answers a *communal* question: which of the volume's own
groups -- Francais, Italiens, Maltais, Israelites, Maures -- does the printed
record place this person in. This module answers a *positional* one: on which
side of the colonial relation does the record place them. The Protectorate was
organised around that relation, and it is the axis most questions about elite
formation, brokerage and survival actually turn on.

    colonist   European-origin: metropolitan officials, settlers, and the
               children of settlers born in Tunisia or Algeria.
    native     Tunisian-origin: Muslims and Jews alike.
    unknown    The record prints nothing that places the person.

**Jews are natives here.** This follows the volume's own usage -- its
*Israelites* entry calls them "une partie importante de la population indigene",
and its *Tunisiens* entry records "Tunisiens" as the name the country's Jews
used for themselves -- and it is the position the Protectorate's institutions
assigned them: beylical subjects under beylical jurisdiction, unlike the
French-citizen and consular-protected populations. Two groups of exceptions are
carried explicitly rather than smoothed over, in `position_detail`:

* the **Grana**, Livornese Jews with Italian nationality and consular
  protection, and
* **Algeria-born Jews**, French citizens since the Cremieux decree of 1870.

Both are Tunisian-Jewish in community and European in legal standing, and both
code `native` with `position_detail = native_jewish_european_status`: the
intermediary position is the interesting one, and collapsing it into either side
destroys it. In this volume only the first case actually arises -- two people.
The five Algeria-born natives here are all Muslim, who were French *subjects*
rather than citizens; the Cremieux rule is kept because it is the right rule,
not because it fires. Anyone Algeria-born is findable through `birth_context`
whatever their community.

THIS IS A RE-READING, NOT NEW EVIDENCE
--------------------------------------
For 798 of the 841 people it places, this module is a documented mapping of
`person_communities.csv`, not an independent coding. It adds one rule of its
own: a small set of posts the colonial order reserved to French citizens (the
colonial regiments, the French magistracy, the controle civil and the
Residence). Against the community coding those rules run 96% precise -- they
agree on 70 people and disagree on 3 -- so the 43 they place on their own are
recorded at medium confidence and marked `reserved_post` in `position_basis`,
so that any analysis of office-holding can drop them and avoid arguing in a
circle. The mirror-image rule -- caid, cadi, khalifa, oukil, adel, imam -- is
100% precise (18 agreements, 0 disagreements) but adds nobody the community
coding had not already placed; it is kept as a check. Both rates are recomputed
and printed on every run rather than quoted from here.

THE COVERAGE PROBLEM, WHICH IS NOT SYMMETRIC
--------------------------------------------
Some 37% of the volume stays `unknown`, and they are not a random 37%. The
largest single reason is a Tunis birth with no other marker, which is
compatible with a native family and with a second-generation settler alike; 16
more are people whose entry is merged with a neighbour's (see below). Two
consequences run through every comparison built on this variable:

1. The native count is a floor, and more of the missing are likely native than
   colonist.
2. A native is usually identified *through an institutional tie* -- a post in
   the beylical administration, a communal school, a seat on a Jewish or Muslim
   body -- and holding such ties is also what puts a person in the network.
   Colonists are mostly identified by birthplace, which carries no such
   implication. Comparing the two groups' network positions without holding the
   identification basis constant therefore measures the coding, not the elite.
   `position_basis` exists to make that restriction possible, and fig. 55 shows
   what happens if it is ignored.

Output: data/processed/person_positionality.csv, one row per person.
"""

from __future__ import annotations

import collections
import csv
import json
import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

# --- posts the colonial order reserved to French citizens -------------------
# Matched against posts the person is recorded as *holding* (the occupation
# field and the parsed career sequence), never against the entry text: a
# Tunisian caid's notice names the controleur civil of his region, and a
# decoration is conferred by the Residence, so the whole-text match picks up
# the institution rather than the post.
FRENCH_RESERVED_POST = re.compile(
    # colonial regiments -- native units, but French officer corps
    r"\b(zouaves|tirailleurs|spahis|chasseurs\s+d.afrique|legion\s+etrangere|"
    r"infanterie\s+coloniale|artillerie\s+coloniale|troupes\s+coloniales)\b|"
    # the French magistracy of the Protectorate
    r"procureur|substitut|juge\s+de\s+paix|juge\s+au\s+tribunal|"
    r"president\s+du\s+tribunal|conseiller\s+a\s+la\s+cour|greffier|"
    # the Protectorate's own administration
    r"controleur\s+civil|residence\s+generale|"
    r"secretaire\s+general\s+du\s+gouvernement"
)

# The mirror image: posts reserved to Tunisian subjects. Kept as a check on the
# community coding rather than as a source of new codings -- see the docstring.
NATIVE_RESERVED_POST = re.compile(
    r"\bcaid\b|\bcadi\b|\bkadi\b|khalifa|\boukil\b|mufti|\bimam\b|\badel\b|"
    r"cheikh\s+(el|de)\b|notaire\s+musulman"
)

# Evidence tokens from person_communities.csv, by what kind of fact they are.
INSTITUTIONAL_EVIDENCE = {
    "muslim_office", "islamic_school", "jewish_institution", "italian_institution",
    "maltese_marker", "member_of:muslim_body", "member_of:jewish_body",
    "member_of:italian_body", "member_of:maltese_body",
    "member_of:french_settler_body",
}
NAME_EVIDENCE = {"nasab_particle", "honorific"}

# The volume is set in two columns and the OCR occasionally runs one notice into
# the next, so a handful of entries carry two or three people's text under the
# first one's name. A notice header is `SURNAME (Forenames),` -- more than one of
# them in a single entry means the entry is merged. 34 of 2,779 entries are, and
# the effect on this variable is specific: the trailing text brings the *next*
# person's institutions with it, so a French printer inherits a chair at the
# college Sadiki and codes as a Tunisian Muslim at high confidence. Birthplace
# and name evidence come from the opening line and are unaffected; institutional
# evidence from a merged entry is not trusted here.
NOTICE_HEADER = re.compile(
    r"\b[A-ZÀ-ÜŒ][A-ZÀ-ÜŒ'’\-]{3,}(?:[ \-][A-ZÀ-ÜŒ'’\-]{2,}){0,2}"
    r"\s*\([A-ZÀ-Ü][a-zà-üA-ZÀ-Ü'’\-.]{2,}[^)]{0,30}\)\s*[,.]"
)

POSITION = {
    "european": "colonist",
    "tunisian": "native",
    "unknown": "unknown",
}

FIELDS = [
    "entry_id", "surname", "forenames", "positionality", "position_detail",
    "position_basis", "confidence", "birth_context", "community",
    "evidence", "birth_year", "settled_tunisia_year", "occupation_primary",
    "n_decorations", "has_legion_honneur", "has_nichan_iftikhar",
    "n_chars", "n_portraits",
]


def norm(s: str) -> str:
    s = "".join(
        c for c in unicodedata.normalize("NFD", s or "")
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", s.lower().replace("'", "-").replace("’", "-")).strip()


def read(name: str) -> list[dict]:
    with (PROCESSED / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def birth_context(evidence: set[str]) -> str:
    """Where the record says the person was born, at the granularity that matters.

    Only three answers change the position: Europe (came out), the colonies
    (born into the colonial order), and Tunisia itself.
    """
    if "birth_tunisia" in evidence:
        return "tunisia"
    if "birth_algeria" in evidence:
        return "algeria"
    if any(e.startswith("birth_") for e in evidence):
        return "europe"
    return "unrecorded"


def detail_for(position: str, community: str, where: str) -> str:
    """The sub-position, which is where the interesting cases live."""
    if position == "colonist":
        if where == "europe":
            return "metropolitan_colonist"
        if where in ("tunisia", "algeria"):
            return "colony_born_colonist"
        return "colonist_unspecified"
    if position == "native":
        if community == "tunisian_muslim":
            return "native_muslim"
        # The Grana (Italian nationality) and the Algeria-born (French
        # citizenship under Cremieux): Tunisian in community, European in law.
        if where in ("europe", "algeria"):
            return "native_jewish_european_status"
        return "native_jewish"
    return "unknown"


def basis_for(position: str, evidence: set[str], from_reserved_post: bool) -> str:
    """Which kind of fact placed this person -- the column fig. 55 turns on.

    Blank when nothing placed them: a `birth_tunisia` note is evidence the
    coder looked and found the birthplace uninformative, not a basis.
    """
    if position == "unknown":
        return ""
    if evidence & INSTITUTIONAL_EVIDENCE:
        return "institutional"
    if from_reserved_post:
        return "reserved_post"
    if any(e.startswith("birth_") for e in evidence):
        return "birthplace"
    if evidence & NAME_EVIDENCE:
        return "name"
    return ""


def main() -> int:
    communities = {r["entry_id"]: r for r in read("person_communities.csv")}
    persons = read("persons.csv")

    merged_entry = {
        r["entry_id"]: len(NOTICE_HEADER.findall(" ".join(r["text"].split()))) > 1
        for r in read("entries.csv")
    }

    positions_held = collections.defaultdict(list)
    for row in read("career_positions.csv"):
        positions_held[row["entry_id"]].append(row["position_raw"])

    rows, checks = [], collections.Counter()
    for person in persons:
        entry_id = person["entry_id"]
        coded = communities[entry_id]
        community = coded["community"]
        evidence = {e for e in coded["evidence"].split(";") if e}

        held = norm(
            person["occupation_raw"] + " ; " + " ; ".join(positions_held.get(entry_id, []))
        )
        french_post = bool(FRENCH_RESERVED_POST.search(held))
        native_post = bool(NATIVE_RESERVED_POST.search(held))

        position = POSITION[coded["community_group"]]
        confidence = coded["confidence"]
        from_reserved_post = False
        if position == "unknown" and french_post:
            position, confidence = "colonist", "medium"
            from_reserved_post = True
            evidence.add("french_reserved_post")

        # The reserved-post rules are also run on people the community coding
        # already placed, and disagreements are counted rather than acted on:
        # that count is the rules' error rate, and it is printed below. Rows the
        # rule itself placed are excluded, or the rule would be scoring its own
        # output and the precision would come out flattering.
        if not from_reserved_post:
            if french_post:
                checks["french_post_agrees" if position == "colonist"
                       else "french_post_disagrees"] += 1
            if native_post:
                checks["native_post_agrees" if position == "native"
                       else "native_post_disagrees"] += 1

        where = birth_context(evidence)
        basis = basis_for(position, evidence, from_reserved_post)
        if merged_entry.get(entry_id) and basis in ("institutional", "reserved_post"):
            checks["unplaced_by_merged_entry"] += 1
            position, basis, confidence = "unknown", "", ""
            evidence.add("merged_entry")

        rows.append({
            "entry_id": entry_id,
            "surname": person["surname"],
            "forenames": person["forenames"],
            "positionality": position,
            "position_detail": detail_for(position, community, where),
            "position_basis": basis,
            "confidence": confidence,
            "birth_context": where,
            "community": community,
            "evidence": ";".join(sorted(evidence)),
            "birth_year": person["birth_year"],
            "settled_tunisia_year": person["settled_tunisia_year"],
            "occupation_primary": person["occupation_primary"],
            "n_decorations": person["n_decorations"],
            "has_legion_honneur": person["has_legion_honneur"],
            "has_nichan_iftikhar": person["has_nichan_iftikhar"],
            "n_chars": person["n_chars"],
            "n_portraits": person["n_portraits"],
        })

    out = PROCESSED / "person_positionality.csv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    by_position = collections.Counter(r["positionality"] for r in rows)

    def precision(rule: str) -> float | None:
        agree, disagree = checks[f"{rule}_agrees"], checks[f"{rule}_disagrees"]
        return round(agree / (agree + disagree), 3) if agree + disagree else None

    print(json.dumps({
        "persons": len(rows),
        "by_positionality": dict(by_position.most_common()),
        "by_detail": dict(collections.Counter(r["position_detail"] for r in rows).most_common()),
        "by_basis": dict(collections.Counter(r["position_basis"] for r in rows).most_common()),
        "added_by_reserved_post": sum(
            1 for r in rows if r["position_basis"] == "reserved_post"),
        "reserved_post_rule_check": {
            "french_post_precision": precision("french_post"),
            "native_post_precision": precision("native_post"),
            **dict(checks.most_common()),
        },
        "merged_entries": sum(1 for v in merged_entry.values() if v),
        "unplaced_share": round(by_position["unknown"] / len(rows), 3),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
