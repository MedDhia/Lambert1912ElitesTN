"""Code each person's community from the evidence printed in their entry.

WHAT THIS VARIABLE IS
---------------------
Colonial Tunisia was administered as a set of distinct communities, and Lambert's
volume is organised around them: it carries entries on *Francais*, *Italiens*,
*Maltais*, *Grecs*, *Espagnols*, *Israelites* and *Maures*, and reports the
1906 census by community. This module reconstructs, for each biographical
notice, which of those communities the printed record places the person in.

It is a coding of **evidence in the source**, not an attribution of identity.
Every row carries the rules that fired (`evidence`) and a confidence, and a
person for whom the volume prints nothing diagnostic stays `unknown` rather than
being guessed at. In particular, no one is classified from a surname: surname
lists are the standard way this coding goes wrong, and in Tunisia they go wrong
in a specific way -- Cardoso, Valensi, Lumbroso, Bessis and Castelnuovo are borne
by Tunisian Jewish and by Italian Catholic families alike.

THE CATEGORIES
--------------
Two groups, following the volume's own usage:

* **European** -- `european_french`, `european_italian`, `european_maltese`,
  `european_other` (Greek, Spanish, British, Swiss, German, Maltese-adjacent).
* **Tunisian** -- `tunisian_muslim`, `tunisian_jewish`.

The volume itself puts Jews on the Tunisian side: its *Israelites* entry calls
them "une partie importante de la population indigene", and its *Tunisiens*
entry records that "Tunisiens" was the name the country's Jews used for
themselves. That is the 1912 usage this coding follows; it is not a claim about
nationality, which for many people in this book was a separate and contested
matter.

KNOWN HARD CASES, HANDLED EXPLICITLY
------------------------------------
* **The Grana.** Lambert's own *Italiens* entry opens: "Les premiers Italiens
  fixes en Tunisie etaient des israelites de Livourne." Livornese Jews held
  Italian nationality and a Tunisian communal life. Religious evidence wins over
  birthplace here, so they code `tunisian_jewish`, with `livorno_jewish_note` in
  the evidence column so the case can be pulled out and re-coded.
* **Algeria-born.** Algeria was French territory; its Jews had been French
  citizens since the Cremieux decree of 1870, which Lambert's *Israelites* entry
  mentions. Algeria-born people with no other marker code `european_french` at
  medium confidence, flagged `birth_algeria`.
* **Born in Tunisia, no marker.** A Tunis birth is compatible with all three
  communities, including second-generation settlers. These stay `unknown`,
  flagged `birth_tunisia`, and they are the largest single reason for a
  non-classification.

Output: data/processed/person_communities.csv, one row per person.
"""

from __future__ import annotations

import collections
import csv
import json
import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

# --- gazetteers -------------------------------------------------------------
# The 1912 departements. Birthplace detail is usually the departement, so this
# is the single largest lever for identifying the metropolitan French.
DEPARTEMENTS = """
ain aisne allier basses-alpes hautes-alpes alpes-maritimes ardeche ardennes
ariege aube aude aveyron bouches-du-rhone calvados cantal charente
charente-inferieure cher correze corse cote-d-or cotes-du-nord creuse dordogne
doubs drome eure eure-et-loir finistere gard haute-garonne gers gironde herault
ille-et-vilaine indre indre-et-loire isere jura landes loir-et-cher loire
haute-loire loire-inferieure loiret lot lot-et-garonne lozere maine-et-loire
manche marne haute-marne mayenne meurthe-et-moselle meuse morbihan nievre nord
oise orne pas-de-calais puy-de-dome basses-pyrenees hautes-pyrenees
pyrenees-orientales rhone haute-saone saone-et-loire sarthe savoie haute-savoie
seine seine-inferieure seine-et-marne seine-et-oise deux-sevres somme tarn
tarn-et-garonne var vaucluse vendee vienne haute-vienne vosges yonne belfort
alsace lorraine moselle bas-rhin haut-rhin
""".split()

FRENCH_PLACES = {
    "france", "paris", "lyon", "marseille", "bordeaux", "toulouse", "nantes",
    "lille", "nice", "montpellier", "rouen", "nancy", "grenoble", "rennes",
    "reims", "toulon", "angers", "dijon", "brest", "le havre", "saint-etienne",
    "limoges", "besancon", "amiens", "perpignan", "avignon", "nimes", "bayonne",
    "pau", "poitiers", "orleans", "tours", "caen", "clermont-ferrand", "arles",
    "narbonne", "beziers", "carcassonne", "cahors", "auch", "albi", "foix",
    "tarbes", "agen", "perigueux", "angouleme", "la rochelle", "niort",
    "chartres", "blois", "bourges", "nevers", "moulins", "vichy", "roanne",
    "chambery", "annecy", "valence", "gap", "draguignan", "ajaccio", "bastia",
    "aix-en-provence", "sete", "cette", "versailles", "strasbourg", "metz",
}
ALGERIA_PLACES = {
    "algerie", "alger", "oran", "constantine", "bone", "philippeville", "blida",
    "setif", "tlemcen", "mostaganem", "bougie", "batna", "biskra", "guelma",
    "souk-ahras", "sidi-bel-abbes", "mascara", "medea", "miliana", "cherchell",
    "djidjelli", "collo", "la calle", "tebessa", "tiaret", "orleansville",
    "mesopotamie",
}
ITALY_PLACES = {
    "italie", "italia", "sicile", "sicilia", "sardaigne", "naples", "napoli",
    "livourne", "livorno", "genes", "genova", "rome", "roma", "milan", "turin",
    "florence", "messine", "catane", "girgenti", "trapani", "palerme", "palermo",
    "marsala", "pantelleria", "sciacca", "favignana", "lampedusa", "toscane",
    "piemont", "calabre", "venise", "bologne", "ancone", "bari", "syracuse",
    "caltanisetta", "linosa", "ustica", "elbe", "carloforte",
}
MALTA_PLACES = {"malte", "malta", "la valette", "valette", "gozo", "maltais"}
OTHER_EUROPE = {
    "grece": "Greece", "espagne": "Spain", "angleterre": "United Kingdom",
    "grande-bretagne": "United Kingdom", "ecosse": "United Kingdom",
    "irlande": "Ireland", "suisse": "Switzerland", "allemagne": "Germany",
    "autriche": "Austria-Hungary", "hongrie": "Austria-Hungary",
    "belgique": "Belgium", "hollande": "Netherlands", "pays-bas": "Netherlands",
    "portugal": "Portugal", "russie": "Russia", "pologne": "Poland",
    "roumanie": "Romania", "serbie": "Serbia", "grec": "Greece",
    "danemark": "Denmark", "suede": "Sweden", "norvege": "Norway",
    "turquie": "Ottoman Empire", "constantinople": "Ottoman Empire",
    "smyrne": "Ottoman Empire", "egypte": "Egypt", "alexandrie": "Egypt",
    "malteque": "Malta", "corfou": "Greece", "athenes": "Greece",
    "barcelone": "Spain", "madrid": "Spain", "gibraltar": "United Kingdom",
    "londres": "United Kingdom", "geneve": "Switzerland", "vienne (autriche)": "Austria-Hungary",
}

# --- institutional markers --------------------------------------------------
# Offices and schools that belong to one community's own institutions. These are
# the strongest evidence in the volume, because they are facts about a post held
# or a school attended rather than inferences about a person.
MUSLIM_OFFICE = re.compile(
    r"\boukil\b|\bcadi\b|\bkadi\b|mufti|\bimam\b|\bcheikh\b|\bca[iï]d\b|khalifa|"
    r"mokaddem|bach[\s-]?mamlouk|notaire\s+musulman|tribunal\s+du\s+char[aà]|"
    r"medjless|conseil\s+mixte\s+immobilier.{0,30}musulman",
    re.IGNORECASE,
)
ISLAMIC_SCHOOL = re.compile(
    r"khaldounia|grande\s+mosqu[ée]e|zitouna|djama[\s-]?ez[\s-]?zitouna|medersa|"
    r"coll[èe]ge\s+sadiki|sadiki", re.IGNORECASE,
)
JEWISH_OFFICE = re.compile(
    r"\brabbin|grand[\s-]rabbin|communaut[ée]\s+isra[ée]lite|culte\s+isra[ée]lite|"
    r"caisse\s+de\s+secours\s+isra[ée]lite|h[oô]pital\s+isra[ée]lite|"
    r"alliance\s+isra[ée]lite|[ée]coles?\s+de\s+l[’']alliance|talmud", re.IGNORECASE,
)
DESCRIBED_JEWISH = re.compile(r"\bisra[ée]lite\b", re.IGNORECASE)
DESCRIBED_MUSLIM = re.compile(r"\bmusulman", re.IGNORECASE)
ITALIAN_MARKER = re.compile(
    r"consulat\s+g[ée]n[ée]ral\s+d[’']Italie|consul.{0,20}d[’']Italie|"
    r"societ[aà]\s+italiana|associazione|scuole\s+italiane|[ée]coles?\s+italiennes|"
    r"couronne\s+d[’']Italie|Maurice\s+et\s+Lazare|regio\s+", re.IGNORECASE,
)
MALTESE_MARKER = re.compile(r"\bmaltais|anglo[\s-]maltaise", re.IGNORECASE)

# Community-marked organisations, matched against affiliation ties.
ORG_PATTERNS = [
    ("tunisian_muslim", re.compile(r"musulman|indig[èe]ne", re.IGNORECASE)),
    ("tunisian_jewish", re.compile(r"isra[ée]lite|juive|h[ée]bra", re.IGNORECASE)),
    ("european_italian", re.compile(r"italian|italien|associazione|societ[aà]\b", re.IGNORECASE)),
    ("european_maltese", re.compile(r"maltais", re.IGNORECASE)),
]
# Membership of a French settler body is weak evidence: these bodies had members
# from every community. It is recorded, and used only when nothing else is known.
FRENCH_ORG = re.compile(
    r"colons\s+fran[çc]ais|soci[ée]t[ée]\s+fran[çc]aise\s+de\s+bienfaisance|"
    r"cercle\s+civil\s+fran[çc]ais|travailleurs\s+fran[çc]ais|"
    r"union\s+fran[çc]aise", re.IGNORECASE,
)

NASAB_PARTICLES = {"BEN", "BENT", "BIN", "OULD", "ABD", "ABOU", "ABU", "BOU",
                   "BEL", "EL", "SIDI", "SI", "OU"}
HONORIFIC = re.compile(r"\b(Si|Sidi|Hadj|Hadji|Cheikh|Bey|Pacha)\b", re.IGNORECASE)

GROUP = {
    "european_french": "european", "european_italian": "european",
    "european_maltese": "european", "european_other": "european",
    "tunisian_muslim": "tunisian", "tunisian_jewish": "tunisian",
    "unknown": "unknown",
}


def norm(s: str) -> str:
    s = "".join(
        c for c in unicodedata.normalize("NFD", s or "")
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", s.lower().replace("'", "-").replace("’", "-")).strip()


def read(name: str) -> list[dict]:
    with (PROCESSED / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def birthplace_signal(person: dict, tunisian_places: set[str]) -> tuple[str, str]:
    """(category, evidence) implied by the birthplace, or ('', '')."""
    blob = f"{norm(person['birth_place'])} {norm(person['birth_place_detail'])}".strip()
    if not blob:
        return "", ""
    tokens = set(re.split(r"[ ,()]+", blob)) | {blob}

    def hit(vocab) -> bool:
        return any(v in tokens for v in vocab) or any(
            re.search(rf"\b{re.escape(v)}\b", blob) for v in vocab
        )

    if hit(MALTA_PLACES):
        return "european_maltese", "birth_malta"
    if hit(ITALY_PLACES):
        return "european_italian", "birth_italy"
    if hit(set(DEPARTEMENTS)) or hit(FRENCH_PLACES):
        return "european_french", "birth_france"
    if hit(ALGERIA_PLACES):
        return "european_french", "birth_algeria"
    for key, label in OTHER_EUROPE.items():
        if re.search(rf"\b{re.escape(key)}\b", blob):
            return "european_other", f"birth_{label.lower().replace(' ', '_')}"
    if hit(tunisian_places) or "tunisie" in blob:
        return "", "birth_tunisia"
    return "", ""


def main() -> int:
    persons = read("persons.csv")
    entries = {e["entry_id"]: e["text"] for e in read("entries.csv")}
    edges = read("edges_person_organisation.csv")

    # The volume's own gazetteer supplies the Tunisian place names.
    tunisian_places = {
        norm(p["place_name"]) for p in read("places.csv") if len(p["place_name"]) > 3
    }
    tunisian_places |= {
        "tunis", "sousse", "sfax", "bizerte", "kairouan", "mahdia", "monastir",
        "beja", "gabes", "nabeul", "djerba", "le kef", "kef", "tozeur", "gafsa",
        "zaghouan", "la goulette", "la marsa", "testour", "moknine", "medenine",
        "grombalia", "ariana", "manouba", "carthage", "kelibia", "hammamet",
        "msaken", "tabarka", "nefta", "kebili", "metline", "porto-farina",
    }

    orgs_by_person: dict[str, list[str]] = collections.defaultdict(list)
    for e in edges:
        if e["person_entry_id"]:
            orgs_by_person[e["person_entry_id"]].append(e["organisation_name"])

    rows = []
    for p in persons:
        text = entries[p["entry_id"]]
        evidence: list[str] = []
        votes: list[tuple[str, str]] = []  # (category, confidence)

        # --- tier A: the person's own institutions ------------------------
        if MUSLIM_OFFICE.search(text):
            votes.append(("tunisian_muslim", "high")); evidence.append("muslim_office")
        if ISLAMIC_SCHOOL.search(text):
            votes.append(("tunisian_muslim", "high")); evidence.append("islamic_school")
        if JEWISH_OFFICE.search(text):
            votes.append(("tunisian_jewish", "high")); evidence.append("jewish_institution")
        if DESCRIBED_JEWISH.search(text) and not JEWISH_OFFICE.search(text):
            votes.append(("tunisian_jewish", "medium")); evidence.append("described_israelite")
        if DESCRIBED_MUSLIM.search(text) and not MUSLIM_OFFICE.search(text):
            votes.append(("tunisian_muslim", "medium")); evidence.append("described_muslim")
        if ITALIAN_MARKER.search(text):
            votes.append(("european_italian", "high")); evidence.append("italian_institution")
        if MALTESE_MARKER.search(text):
            votes.append(("european_maltese", "high")); evidence.append("maltese_marker")

        # --- tier A': community-marked bodies they belong to ---------------
        for name in orgs_by_person.get(p["entry_id"], []):
            for category, rx in ORG_PATTERNS:
                if rx.search(name):
                    votes.append((category, "medium"))
                    evidence.append(f"member_of:{category.split('_')[-1]}_body")
            if FRENCH_ORG.search(name):
                evidence.append("member_of:french_settler_body")

        # --- tier B: birthplace -------------------------------------------
        category, note = birthplace_signal(p, tunisian_places)
        if note:
            evidence.append(note)
        if category:
            votes.append((category, "medium" if note == "birth_algeria" else "high"))

        # --- tier C: Arabic patronymic construction in the printed name ----
        tokens = set(re.sub(r"[^A-Z ]", " ", norm(p["surname"]).upper()).split())
        if NASAB_PARTICLES & tokens:
            votes.append(("tunisian_muslim", "medium")); evidence.append("nasab_particle")
        if HONORIFIC.search(f"{p['surname']} {p['forenames']}"):
            votes.append(("tunisian_muslim", "medium")); evidence.append("honorific")

        # --- resolve -------------------------------------------------------
        # Religious and communal institutions outrank birthplace, which is what
        # makes the Livornese Jewish case come out as Jewish rather than Italian.
        community, confidence, conflict = "unknown", "", ""
        if votes:
            weight = {"high": 3, "medium": 2, "low": 1}
            tally: collections.Counter[str] = collections.Counter()
            for cat, conf in votes:
                tally[cat] += weight[conf]
            ranked = tally.most_common()
            community = ranked[0][0]
            best_conf = max(
                (conf for cat, conf in votes if cat == community),
                key=lambda c: weight[c],
            )
            confidence = best_conf
            if len(ranked) > 1 and ranked[1][1] == ranked[0][1]:
                confidence = "low"
                conflict = ";".join(cat for cat, _ in ranked if _ == ranked[0][1])
            elif len(ranked) > 1:
                conflict = ";".join(cat for cat, _ in ranked[1:])
        if community == "unknown" and "member_of:french_settler_body" in evidence:
            community, confidence = "european_french", "low"

        grana = community == "tunisian_jewish" and "birth_italy" in evidence
        if grana:
            evidence.append("livorno_jewish_note")

        rows.append({
            "entry_id": p["entry_id"],
            "surname": p["surname"],
            "forenames": p["forenames"],
            "community": community,
            "community_group": GROUP[community],
            "confidence": confidence,
            "evidence": ";".join(dict.fromkeys(evidence)),
            "competing_categories": conflict,
            "birth_year": p["birth_year"],
            "birth_place": p["birth_place"],
            "occupation_primary": p["occupation_primary"],
            "n_decorations": p["n_decorations"],
            "has_legion_honneur": p["has_legion_honneur"],
            "has_nichan_iftikhar": p["has_nichan_iftikhar"],
            "n_chars": p["n_chars"],
            "n_portraits": p["n_portraits"],
            "page_first": p["page_first"],
        })

    with (PROCESSED / "person_communities.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    counts = collections.Counter(r["community"] for r in rows)
    groups = collections.Counter(r["community_group"] for r in rows)
    print(json.dumps({
        "persons": len(rows),
        "by_community": dict(counts.most_common()),
        "by_group": dict(groups.most_common()),
        "classified": len(rows) - counts["unknown"],
        "by_confidence": dict(collections.Counter(r["confidence"] for r in rows)),
        "with_competing_evidence": sum(1 for r in rows if r["competing_categories"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
