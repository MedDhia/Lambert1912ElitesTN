"""Code each person's gender from the evidence printed in their entry.

Same method as `code_communities.py`: tiered evidence, the rules that fired
recorded on every row, a confidence, and `unknown` where the volume prints
nothing diagnostic. Values are MALE / FEMALE / UNKNOWN, matching the coding used
in Hammami, "Gendered Informational Inequality in Elite Networks".

The evidence, strongest first:

1. **A civil title.** "Mme", "Mlle", "Vve" and their OCR wreckage -- the 1912
   scan renders Mme as ``M"``, ``Al""``, ``M""`` -- and the feminine participle
   "nee X". These are unambiguous.
2. **A grammatically gendered occupation.** French marks the holder's gender in
   the noun: *directrice*, *institutrice*, *sage-femme*, *religieuse* against
   *directeur*, *instituteur*, *pasteur*. This is evidence about the person, not
   an assumption about the job.
3. **The forename.** French, Italian and Arabic forenames are strongly gendered.
   A compound resolves to male if any element is masculine, which is the right
   rule for "Marie-Joseph" and "Jean-Marie".

A caution that matters more here than anywhere else in this dataset: Lambert's
volume is a record of who the colonial elite counted as notable, and it counted
almost no women. The coding below recovers the handful it does contain. That
number is a finding about the source, and it is far too small to support the
regression apparatus the gender-and-networks literature applies to modern elite
data -- see `output/tables/comparison_tables.md`, which states which models are
estimable here and which are not.

Output: data/processed/person_gender.csv, one row per person.
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

# --- tier 1: civil titles and feminine participles ---------------------------
# The OCR mangles "Mme" badly, so the pattern has to admit its variants while
# staying anchored to the position a title occupies: immediately after the
# headword, before the forename.
# The title must sit inside the headword's *own* parenthesis. Loose matching
# fails in a specific way here: the OCR renders both "Mme" and "Maitre" as M
# plus punctuation, and "Secretaire de M" Gueydan, avocat" is a man working for
# another man. Anchoring to the subject's parenthesis removes that whole class.
TITLE_IN_HEADWORD = re.compile(
    r"^\s*\(\s*(?:M|Al|AI|A1|Mm|Mme|Mlle|Mile|Mll)[\"'’\.]{1,3}\s*(?=[A-ZÉÈ]|\))"
    r"|^\s*\(\s*(?:Mme|Madame|Mlle|Mademoiselle|V(?:eu)?ve)\b",
)
# "nee" is feminine agreement, but only when it introduces a maiden name or a
# birthplace. "Nee. en mater." is the OCR's version of "Negt. en mater.".
NEE_FEMALE = re.compile(r"\bn[ée]e\b[\s.,]*(?=(?:[àa]\b|[A-ZÉÈ][a-zà-ÿ]{2}))", re.IGNORECASE)

# --- tier 2: grammatically gendered occupations ------------------------------
# Deliberately excludes "superieure": in "ecole primaire superieure" the
# feminine agreement is with the school, not with the person, and that single
# word accounted for seventeen of the twenty-nine false positives in the first
# pass. Also excluded: "presidente" and "maitresse", which in this volume attach
# to a body or to another person more often than to the subject.
OCCUPATION_FEMALE = re.compile(
    r"\bdirectrice\b|\binstitutrice\b|\bsage[\s-]femme\b|\breligieuse\b|"
    r"\binfirmi[èe]re\b|\bsurveillante\b|\bfondatrice\b|\bcollaboratrice\b|"
    r"\bs[oœ]ur\b|\bveuve\b|\bla\s+m[èe]re\b",
    re.IGNORECASE,
)
OCCUPATION_MALE = re.compile(
    r"\binstituteur\b|\bdirecteur\b|\bpasteur\b|\bcur[ée]\b|\bpr[êe]tre\b|"
    r"\brabbin\b|\bimam\b|\bcolonel\b|\bcapitaine\b|\bg[ée]n[ée]ral\b|"
    r"\bcommandant\b|\bpr[ée]sident\b|\bconsul\b|\bavocat\b|\bing[ée]nieur\b|"
    r"\boukil\b|\bca[iï]d\b|\bcheikh\b|\bn[ée]\s+[àa]\b",
    re.IGNORECASE,
)

# --- tier 3: forenames -------------------------------------------------------
FEMALE_NAMES = {
    "marie", "anne", "charlotte", "mathilde", "marguerite", "lea", "emilie",
    "adelaide", "gertrude", "jeanne", "louise", "berthe", "blanche", "rose",
    "julie", "helene", "adele", "cecile", "clotilde", "eugenie", "henriette",
    "josephine", "madeleine", "pauline", "suzanne", "therese", "valentine",
    "victorine", "yvonne", "alice", "amelie", "antoinette", "augustine",
    "caroline", "celestine", "claire", "clemence", "delphine", "elisa", "emma",
    "ernestine", "fanny", "felicie", "gabrielle", "genevieve", "germaine",
    "jacqueline", "juliette", "laure", "leonie", "lucie", "marcelle",
    "marthe", "noemie", "olga", "sarah", "sara", "esther", "rachel", "rebecca",
    "messaouda", "hanna", "aicha", "fatma", "khadija", "zohra", "emma",
    "angele", "angelina", "carmela", "giuseppina", "rosa", "teresa", "anna",
    "elena", "lucia", "concetta", "salvatrice",
}
MALE_NAMES = {
    "louis", "joseph", "jean", "pierre", "paul", "henri", "charles", "francois",
    "jules", "albert", "emile", "victor", "antoine", "auguste", "ernest",
    "eugene", "georges", "leon", "andre", "jacques", "alexandre", "lucien",
    "maurice", "alfred", "mohamed", "rene", "felix", "philippe", "adolphe",
    "alphonse", "gustave", "camille", "etienne", "baptiste", "edmond", "henry",
    "cesar", "emmanuel", "gabriel", "gaston", "bernard", "clement", "frederic",
    "marcel", "armand", "dominique", "ferdinand", "julien", "pascal", "raymond",
    "ahmed", "daniel", "edouard", "elie", "guillaume", "isaac", "michel",
    "raoul", "thomas", "aime", "alexis", "antonin", "david", "fernand",
    "giuseppe", "marc", "marius", "moise", "robert", "rodolphe", "salah",
    "sauveur", "simon", "seraphin", "theodore", "adrien", "ali", "amedee",
    "aristide", "augustin", "benjamin", "bechir", "felicien", "giacomo",
    "hubert", "isidore", "justin", "mario", "martial", "martin", "nicolas",
    "raphael", "samuel", "william", "xavier", "abraham", "alcide", "ange",
    "barthelemy", "benoit", "calixte", "carlo", "claude", "celestin", "desire",
    "elisee", "emilien", "fortune", "germain", "gerard", "hassen", "hippolyte",
    "honore", "horace", "jacob", "laurent", "leonce", "leopold", "mathieu",
    "maxime", "mohammed", "mustapha", "norbert", "paolo", "philibert",
    "prosper", "richard", "roger", "sadok", "salvator", "stephane", "sebastien",
    "toussaint", "ugo", "valere", "wilfrid", "abdelaziz", "abdeljelil",
    "abderrahmane", "abdulhamid", "achille", "albin", "alberic", "arthur",
    "arnold", "aron", "arsene", "basile", "bonaventure", "bruno", "casimir",
    "carmelo", "chadli", "cherif", "cyprien", "cyrille", "damase", "dante",
    "dario", "darius", "eloi", "emilio", "enrico", "fabien", "firmin",
    "francesco", "francis", "gino", "gioacchino", "giulio", "godefroy",
    "guglielmo", "hector", "hermann", "hilaire", "ignace", "israel", "james",
    "joachim", "jerome", "lazare", "lorenzo", "ludovic", "leonard", "leonidas",
    "manoubi", "mariano", "marino", "mehmed", "meyer", "napoleon", "narcisse",
    "nessim", "nicolo", "nissim", "noel", "octave", "omar", "oscar", "paulin",
    "placide", "rachid", "regis", "romain", "said", "scipion", "sellam",
    "simeon", "spiridion", "sylvain", "tahar", "taieb", "theophile", "tolomeo",
    "umberto", "urbain", "valentin", "victorien", "victorin", "vincent",
    "virgile", "vital", "youcef", "younes", "housseïn", "housseine", "moslefa",
    "moustapha", "abou", "chadly", "dehmani", "khlil", "kilien", "mohsen",
    "carmel", "candide", "clodomir", "edgard", "hamadi", "salvatore",
}


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s or "")
        if unicodedata.category(c) != "Mn"
    )


def read(name: str) -> list[dict]:
    with (PROCESSED / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def name_tokens(*fields: str) -> set[str]:
    joined = " ".join(fields)
    return {
        strip_accents(t).lower()
        for t in re.split(r"[-\s\.\(\),]+", joined)
        if len(t) > 2
    }


def code(person: dict, text: str) -> tuple[str, str, list[str]]:
    """Return (gender, confidence, evidence)."""
    head = text[: len(person["surname"]) + 200]
    evidence: list[str] = []
    votes: list[tuple[str, str]] = []

    after_headword = text[len(person["surname"]):][:80]
    if TITLE_IN_HEADWORD.search(after_headword):
        votes.append(("FEMALE", "high")); evidence.append("civil_title")
    if NEE_FEMALE.search(head):
        votes.append(("FEMALE", "high")); evidence.append("nee_participle")
    if OCCUPATION_FEMALE.search(head):
        votes.append(("FEMALE", "high")); evidence.append("feminine_occupation")
    if OCCUPATION_MALE.search(head):
        votes.append(("MALE", "medium")); evidence.append("masculine_occupation")

    tokens = name_tokens(person["forenames"])
    if tokens & MALE_NAMES:
        votes.append(("MALE", "medium")); evidence.append("masculine_forename")
    elif tokens & FEMALE_NAMES:
        votes.append(("FEMALE", "medium")); evidence.append("feminine_forename")

    if not votes:
        return "UNKNOWN", "", evidence

    weight = {"high": 3, "medium": 2}
    tally: collections.Counter[str] = collections.Counter()
    for value, conf in votes:
        tally[value] += weight[conf]
    # A civil title or "nee" outranks everything: a woman's entry can name a
    # masculine occupation (her late husband's) or carry a compound forename.
    if any(e in evidence for e in ("civil_title", "nee_participle", "feminine_occupation")):
        return "FEMALE", "high", evidence
    ranked = tally.most_common()
    gender = ranked[0][0]
    confidence = max(
        (c for v, c in votes if v == gender), key=lambda c: weight[c]
    )
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        confidence = "low"
    return gender, confidence, evidence


def main() -> int:
    persons = read("persons.csv")
    entries = {e["entry_id"]: e["text"] for e in read("entries.csv")}
    communities = {c["entry_id"]: c for c in read("person_communities.csv")}

    rows = []
    for p in persons:
        gender, confidence, evidence = code(p, entries[p["entry_id"]])
        community = communities.get(p["entry_id"], {})
        rows.append({
            "entry_id": p["entry_id"],
            "surname": p["surname"],
            "forenames": p["forenames"],
            "gender": gender,
            "gender_confidence": confidence,
            "gender_evidence": ";".join(dict.fromkeys(evidence)),
            "community": community.get("community", "unknown"),
            "community_group": community.get("community_group", "unknown"),
            "birth_year": p["birth_year"],
            "occupation_primary": p["occupation_primary"],
            "n_decorations": p["n_decorations"],
            "n_chars": p["n_chars"],
            "n_portraits": p["n_portraits"],
            "page_first": p["page_first"],
        })

    with (PROCESSED / "person_gender.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    counts = collections.Counter(r["gender"] for r in rows)
    print(json.dumps({
        "persons": len(rows),
        "by_gender": dict(counts.most_common()),
        "female_share_pct": round(100 * counts["FEMALE"] / len(rows), 2),
        "by_confidence": dict(collections.Counter(r["gender_confidence"] for r in rows)),
    }, indent=2))
    print("\nEvery person coded FEMALE, for inspection against the page:")
    for r in rows:
        if r["gender"] == "FEMALE":
            print(f"  {r['entry_id']}  p.{r['page_first']:>4}  "
                  f"{r['surname'][:24]:24} ({r['forenames'][:20]:20})  {r['gender_evidence']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
