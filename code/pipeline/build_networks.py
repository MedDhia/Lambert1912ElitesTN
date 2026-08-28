"""Build the relational layer: who belongs to what, and who appears with whom.

Three kinds of tie are recoverable from the volume, and they differ in how much
they can be trusted:

1. **Officer and member lists inside association entries** ("Pres., M. Marcille;
   v.-pres., M. Brou; ... membres du bureau, MM. Courtade, L. Blanc, Girod").
   These are explicit, role-bearing, and dated by the entry -- the strongest tie.
2. **Memberships stated inside a person's own entry** ("membre de la Chambre de
   Commerce de Tunis de 1898 a 1902; secretaire elu de cette compagnie").
3. **Property lists inside place entries** ("Propr.: MM. Robert, Julien,
   Vernay"), which tie people to localities as landowners.

Names are matched back to the volume's own biographical entries by surname.
Where a surname is carried by more than one person with an entry, the mention is
recorded as ambiguous rather than assigned: `resolution` is a column, not a
hidden decision. People named only in someone else's entry become nodes too --
they are real members of the elite, just without a notice of their own.

Outputs (data/processed): mentions.csv, edges_person_organisation.csv,
edges_person_person.csv, edges_person_place.csv, network_nodes.csv,
network_edges.csv.
"""

from __future__ import annotations

import csv
import itertools
import json
import pathlib
import re
import unicodedata
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
ARK = "bpt6k5505300s"
PAGE_URL = "https://gallica.bnf.fr/ark:/12148/" + ARK + "/f{view}.item"

# --- roles ------------------------------------------------------------------
# Order matters: the longer, more specific label has to win over its own prefix
# ("vice-president" before "president", "president d'honneur" before both).
ROLE_PATTERNS: list[tuple[str, str]] = [
    ("honorary_president", r"pr[ée]s(?:ident)?s?\.?,?\s*d[’'\s]*honn?(?:eur)?"),
    ("honorary_vice_president", r"v(?:ice)?[\.\s-]*pr[ée]s(?:ident)?s?\.?,?\s*d[’'\s]*honn?"),
    ("past_president", r"anc(?:ien|\.)\s*s?\.?\s*pr[ée]s(?:ident)?s?"),
    ("vice_president", r"v(?:ice)?[\.\s-]*pr[ée]s(?:ident)?s?\.?"),
    ("president", r"pr[ée]s(?:ident)?s?\.?"),
    ("secretary_general", r"secr[ée]?t?a?i?r?e?\.?[\s-]*g[ée]n(?:[ée]ral)?\.?"),
    ("deputy_secretary", r"secr[ée]?t?a?i?r?e?\.?[\s-]*adj(?:oint)?\.?"),
    ("secretary", r"secr[ée]?t?a?i?r?e?\.?"),
    ("deputy_treasurer", r"tr[ée][ss]?\.?[\s-]*adj(?:oint)?\.?|tr[ée]sorier[\s-]*adj"),
    ("treasurer", r"tr[ée][ss]?(?:orier)?\.?"),
    ("archivist_librarian", r"archiviste|biblioth[ée]caire"),
    ("assessor", r"assess(?:eur)?s?\.?"),
    ("board_member", r"membres?\s+du\s+bureau|conseil\s+d[’'\s]*administration|comit[ée]\s+directeur"),
    ("councillor", r"conseillers?"),
    ("commissioner", r"commiss(?:aire)?s?\.?"),
    ("delegate", r"d[ée]l[ée]gu[ée]s?"),
    ("director", r"directeur|g[ée]rant"),
    ("founder", r"fondateur|fondatrice|membres?\s+fondateurs?"),
    ("honorary_member", r"membres?\s+d[’'\s]*honn(?:eur)?|membres?\s+honor(?:aires?)?"),
    ("member", r"membres?\s+actifs?|membres?|soci[ée]taires?|adh[ée]rents?"),
]
ROLE_RE = re.compile(
    "|".join(f"(?P<{k}>{p})" for k, p in ROLE_PATTERNS), re.IGNORECASE
)

# Titles that precede a name and are not part of it.
TITLE_RE = re.compile(
    r"^(?:MM\.?|M\.|MAI\.?|A[I1]A[I1]\.?|Mme\.?|Mlle\.?|D[Rr]\.?|D['’]|docteur|"
    r"prof(?:esseur)?\.?|av(?:ocat)?\.?|cav\.|comm(?:andant)?\.?|cap(?:itaine)?\.?|"
    r"col(?:onel)?\.?|g[ée]n(?:[ée]ral)?\.?|ing(?:[ée]nieur)?\.?|abb[ée]|R\.\s*P\.|"
    r"S\.\s*A\.|Mgr|baron|comte|marquis|R[ée]sident\s+G[ée]n[ée]ral|Si|Sidi|Hadj|"
    r"cheikh|ca[iï]d|le|la|les|de)\s+",
    re.IGNORECASE,
)
# Section headings that introduce an officer list and must not be read as names.
SECTION_WORDS = {
    "BUREAU", "COMMISSION", "COMITE", "CONSEIL", "MEMBRES", "MEMBRE", "ADMINISTRATION",
    "PERMANENTE", "DIRECTEUR", "DIRECTION", "PRESIDENT", "SECRETAIRE", "TRESORIER",
    "ANCIENS", "ANCIEN", "ACTUEL", "SIEGE", "TRAVAUX", "BUT", "ETUDES", "SUCCESS",
    "MM", "M", "MAI", "ET", "LE", "LA", "LES", "DE", "DU", "DES",
}
# An affiliation target must actually name a body, not a country or a fragment.
ORG_NOUN_RE = re.compile(
    r"\b(soci[ée]t[ée]|societ[àa]|associazione|association|cercle|club|chambre|comit[ée]|"
    r"ligue|syndicat|loge|conseil|conf[ée]rence|institut|acad[ée]mie|banque|compagnie|"
    r"caisse|f[ée]d[ée]ration|union|amicale|mutuelle|orph[ée]linat|[ée]cole|coll[èe]ge|"
    r"h[oô]pital|croix|alliance|oeuvre|fondation|patronage|harmonie|chorale|commission|"
    r"tribunal|municipalit[ée]|conservatoire|mus[ée]e|barreau)\b",
    re.IGNORECASE,
)
NAME_TOKEN_RE = re.compile(r"^[A-ZÉÈÊÀÇÎÔÜ][\wà-ÿ'’\-]{1,}$", re.UNICODE)
# Institutions get named where a person is expected ("la Municipalite designe
# deux membres"). They are capitalised and pass every shape test, so they have
# to be excluded by name.
NON_PERSON_WORDS = {
    "MUNICIPALITE", "GOUVERNEMENT", "CONFERENCE", "CONSULTATIVE", "COUR",
    "TRIBUNAL", "CHAMBRE", "SOCIETE", "ASSOCIATION", "COMITE", "DIRECTION",
    "ADMINISTRATION", "MINISTERE", "RESIDENCE", "PREFECTURE", "ETAT",
    "PROTECTORAT", "REPUBLIQUE", "PRES", "SECR", "TRES", "VICE", "HONNEUR",
    "BANQUE", "COMPAGNIE", "SYNDICAT", "CONSEIL", "REGENCE", "FRANCE", "TUNISIE",
}

# Membership claims inside a person's own entry. The role half is
# case-insensitive; the organisation half deliberately is NOT, because the
# capital is what separates a named body ("membre de la Chambre de Commerce")
# from an ordinary job description ("commissaire de police a Monastir").
AFFIL_RE = re.compile(
    r"(?P<role>(?i:membre\s+correspondant|membre\s+fondateur|membre\s+d[’'\s]*honneur|"
    r"membre|pr[ée]sident\s+d[’'\s]*honneur|pr[ée]sident|vice[\s-]pr[ée]sident|v\.-pr[ée]s\.|"
    r"secr[ée]taire\s+g[ée]n[ée]ral|secr[ée]taire|tr[ée]sorier|administrateur|fondateur|"
    r"conseiller|assesseur|d[ée]l[ée]gu[ée]|censeur|commissaire|rapporteur|directeur))"
    r"\s+(?:[ée]lu\s+)?(?:de\s+la|de\s+l[’']|du|des|de|d[’'])\s*"
    r"(?P<org>(?:l[’']|La\s|Le\s|Les\s)?[A-ZÉÈÊÀÇÎÔ][^.;:,()«»]{3,70})"
)
# Trailing clauses that the greedy capture sweeps up ("... de Tunis de 1898 a 1902").
ORG_TAIL_RE = re.compile(
    r"\s+(?:depuis|jusqu|pendant|en\s+1\d{3}|de\s+1\d{3}|du\s+1\d{3}|d[èe]s\s+1\d{3}).*$"
)

STOP_ORG_WORDS = {
    "tunisie", "tunis", "france", "regence", "la regence", "protectorat", "ville",
    "region", "pays", "commission", "meme", "cette", "celle", "cette societe",
    "cette compagnie", "cette association", "meme societe", "police",
}


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def name_key(s: str) -> str:
    """Normalised comparison key for a personal name."""
    s = strip_accents(s).upper()
    s = re.sub(r"\b(FILS|PERE|AINE|JEUNE|FRERES?)\b", " ", s)
    s = re.sub(r"[^A-Z ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def org_key(s: str) -> str:
    s = strip_accents(s).lower()
    s = re.sub(r"^(l'|la |le |les |de |du |des )+", "", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def clean_name(fragment: str) -> str:
    """Pull a personal name off the front of a list fragment."""
    frag = re.sub(r"\s+", " ", fragment)
    if ":" in frag:  # "BUREAU : MM. Florian Ducurtil, pres."
        frag = frag.rsplit(":", 1)[1]
    frag = frag.split("(")[0]  # "Waldispul (Grand-Hotel)": drop the business name
    frag = frag.strip(" .,;:'\"«»()")
    for _ in range(3):  # "MM. le D' Untel"
        new = TITLE_RE.sub("", frag)
        if new == frag:
            break
        frag = new
    tokens = frag.split(" ")
    out: list[str] = []
    for tok in tokens:
        bare = tok.strip(".,;:'\"()")
        if not bare:
            continue
        if strip_accents(bare).upper() in SECTION_WORDS:
            if out:
                break
            continue
        if NAME_TOKEN_RE.match(bare) or re.match(r"^[A-Z]\.?(-[A-Z]\.?)*$", bare):
            out.append(bare)
            if len(out) >= 4:
                break
        elif out:
            break
        else:
            break
    name = " ".join(out).strip(" .,-")
    key = name_key(name)
    if len(key) < 3:
        return ""
    if set(key.split(" ")) <= NON_PERSON_WORDS or key.split(" ")[0] in NON_PERSON_WORDS:
        return ""
    return name


def split_names(fragment: str) -> list[str]:
    """A plural role lists several people: 'MM. Courtade, L. Blanc, Girod et Verry'."""
    parts = re.split(r",| et | e | & |;", fragment)
    names = [clean_name(p) for p in parts]
    return [n for n in names if n]


ORG_STOPWORDS = {
    "de", "du", "des", "la", "le", "les", "et", "en", "aux", "au", "pour", "sur",
    "dans", "tunisie", "tunisienne", "tunisien", "tunis", "francaise", "francais",
    "generale", "general", "section", "comite", "societe", "association", "cercle",
    "club", "union", "ligue", "chambre", "amicale", "syndicat", "conseil",
}


def canonicalise_orgs(keys: list[str]) -> dict[str, str]:
    """Collapse organisation-name variants onto one canonical key.

    The same body is written several ways across the volume, and the OCR adds
    its own ("Comite permanent des fetes de M'unis"). Two names are merged only
    when one's distinctive tokens are a subset of the other's and at least two
    such tokens are shared -- enough to join "Institut de Carthage" to "Institut
    de Carthage, section scientifique" without merging every "Societe" into one
    node. Names carrying a single distinctive token ("Comite des Fetes") are
    left alone: one shared word is not evidence of the same body.
    """
    content = {
        k: {t for t in k.split(" ") if len(t) >= 4 and t not in ORG_STOPWORDS}
        for k in keys
    }
    order = sorted(keys, key=lambda k: (-len(content[k]), -len(k)))
    canon: dict[str, str] = {}
    for k in order:
        toks = content[k]
        if len(toks) < 2:
            canon[k] = k
            continue
        for other in order:
            if other == k or other not in canon or canon[other] != other:
                continue
            if toks and toks <= content[other] and len(toks & content[other]) >= 2:
                canon[k] = other
                break
        else:
            canon[k] = k
    return canon


def edit_distance_at_most_one(a: str, b: str) -> bool:
    """True when `a` and `b` differ by at most one insertion/deletion/substitution."""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        return sum(x != y for x, y in zip(a, b)) == 1
    if la > lb:
        a, b, la, lb = b, a, lb, la
    i = j = diff = 0
    while i < la and j < lb:
        if a[i] != b[j]:
            diff += 1
            if diff > 1:
                return False
            j += 1
        else:
            i += 1
            j += 1
    return True


def read_csv(path: pathlib.Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: pathlib.Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# --------------------------------------------------------------------------
def officer_mentions(text: str) -> list[tuple[str, str, str]]:
    """(role, name, evidence) triples from an association's officer list."""
    out: list[tuple[str, str, str]] = []
    # Officer lists are semicolon-delimited; sentence breaks also separate them.
    for seg in re.split(r"[;]|(?<=[a-z)])\.\s+(?=[A-ZÉÈ])", text):
        seg = seg.strip()
        if len(seg) < 4 or len(seg) > 400:
            continue
        m = ROLE_RE.search(seg)
        if not m:
            continue
        role = m.lastgroup
        before, after = seg[: m.start()], seg[m.end() :]
        # Both orders occur: "Pres., M. Marcille" and "Vilatte L.-E., pres."
        target = after if len(after.strip(" .,:;")) > 2 else before
        plural = bool(re.search(r"s\s*$", m.group(0).strip(" .,"))) or role in {
            "board_member", "councillor", "member", "honorary_member", "assessor",
            "commissioner", "delegate", "founder", "past_president",
        }
        names = split_names(target) if plural else [clean_name(target)]
        for name in names[: 12 if plural else 1]:
            if name:
                out.append((role, name, seg[:180]))
    return out


def main() -> int:
    entries = {r["entry_id"]: r for r in read_csv(PROCESSED / "entries.csv")}
    persons = read_csv(PROCESSED / "persons.csv")
    orgs = read_csv(PROCESSED / "organizations.csv")
    places = read_csv(PROCESSED / "places.csv")

    # --- index of people who have their own entry --------------------------
    by_surname: dict[str, list[dict]] = defaultdict(list)
    for p in persons:
        key = name_key(p["surname"])
        if key:
            by_surname[key].append(p)
            first = key.split(" ")[0]
            if first != key and len(first) >= 4:
                by_surname[first].append(p)

    surname_keys = sorted(by_surname)

    def resolve(name: str) -> tuple[str, str, int]:
        """Return (person_entry_id, resolution, n_candidates) for a mention."""
        key = name_key(name)
        cands: list[dict] = []
        for tok in [key] + key.split(" "):
            if len(tok) < 3:
                continue
            if by_surname.get(tok):
                cands = by_surname[tok]
                break
        uniq = {c["entry_id"]: c for c in cands}
        if len(uniq) == 1:
            return next(iter(uniq)), "resolved", 1
        if len(uniq) > 1:
            return "", "ambiguous", len(uniq)
        # Fall back to a one-character tolerance, which recovers the OCR's own
        # substitutions ("Maziere" for "Mazieres"). Flagged separately so that
        # an analysis can drop these ties if it wants only exact matches.
        for tok in key.split(" "):
            if len(tok) < 5:
                continue
            near = {
                pid["entry_id"]
                for sk in surname_keys
                if len(sk) >= 5 and edit_distance_at_most_one(tok, sk)
                for pid in by_surname[sk]
            }
            if len(near) == 1:
                return next(iter(near)), "resolved_fuzzy", 1
            if len(near) > 1:
                return "", "ambiguous_fuzzy", len(near)
        return "", "unmatched", 0

    mentions: list[dict] = []
    person_org: list[dict] = []
    person_place: list[dict] = []

    # --- 1. officer and member lists in association entries ----------------
    org_by_id = {o["entry_id"]: o for o in orgs}
    for o in orgs:
        entry = entries[o["entry_id"]]
        own_key = org_key(o["organisation_name"])
        for role, name, evidence in officer_mentions(entry["text"]):
            if org_key(name) and org_key(name) in own_key:
                continue  # the association's own name, not one of its officers
            pid, resolution, ncand = resolve(name)
            mentions.append(
                {
                    "mention_id": f"M{len(mentions) + 1:06d}",
                    "source_entry_id": o["entry_id"],
                    "source_entry_type": "organisation",
                    "name_raw": name,
                    "name_key": name_key(name),
                    "role": role,
                    "person_entry_id": pid,
                    "resolution": resolution,
                    "n_candidates": ncand,
                    "page": entry["page_first"],
                    "page_url": entry["page_url"],
                    "evidence": evidence,
                }
            )
            person_org.append(
                {
                    "person_node": pid or f"NAME:{name_key(name)}",
                    "person_name": name,
                    "person_entry_id": pid,
                    "resolution": resolution,
                    "organisation_node": o["entry_id"],
                    "organisation_name": o["organisation_name"],
                    "role": role,
                    "tie_source": "organisation_entry_officer_list",
                    "organisation_founded_year": o["founded_year"],
                    "page": entry["page_first"],
                    "page_url": entry["page_url"],
                    "evidence": evidence,
                }
            )

    # --- 2. memberships stated inside a person's own entry -----------------
    org_index = {org_key(o["organisation_name"]): o["entry_id"] for o in orgs}
    for p in persons:
        entry = entries[p["entry_id"]]
        for m in AFFIL_RE.finditer(entry["text"]):
            org_name = re.sub(r"\s+", " ", m.group("org")).strip(" .,;:'’")
            org_name = ORG_TAIL_RE.sub("", org_name)
            # Trailing connectives get swept in by the greedy name pattern.
            org_name = re.sub(
                r"\s+(?:de|du|des|d[’']|la|le|l[’']|et|aux?|en|pour|dit)$", "", org_name
            ).strip(" .,;:'’")
            key = org_key(org_name)
            if not key or key in STOP_ORG_WORDS or len(key) < 6:
                continue
            if not ORG_NOUN_RE.search(org_name) and len(key.split(" ")) < 3:
                continue  # too thin to be a named body
            role = name_key(m.group("role")).lower().replace(" ", "_")
            role = {
                "membre": "member", "membre_correspondant": "corresponding_member",
                "membre_fondateur": "founder", "membre_d_honneur": "honorary_member",
                "membre_dhonneur": "honorary_member",
                "president_d_honneur": "honorary_president",
                "president_dhonneur": "honorary_president",
                "president": "president", "vicepresident": "vice_president",
                "vpres": "vice_president", "v_pres": "vice_president",
                "vice_president": "vice_president", "secretaire": "secretary",
                "secretaire_general": "secretary_general", "tresorier": "treasurer",
                "administrateur": "director", "fondateur": "founder",
                "conseiller": "councillor", "assesseur": "assessor",
                "delegue": "delegate", "censeur": "auditor",
                "commissaire": "commissioner", "rapporteur": "rapporteur",
                "directeur": "director",
            }.get(role, role)
            matched = org_index.get(key, "")
            person_org.append(
                {
                    "person_node": p["entry_id"],
                    "person_name": f"{p['surname']} {p['forenames']}".strip(),
                    "person_entry_id": p["entry_id"],
                    "resolution": "resolved",
                    "organisation_node": matched or f"ORG:{key}",
                    "organisation_name": org_name,
                    "role": role,
                    "tie_source": "person_entry_statement",
                    "organisation_founded_year": org_by_id.get(matched, {}).get("founded_year", ""),
                    "page": entry["page_first"],
                    "page_url": entry["page_url"],
                    "evidence": entry["text"][max(0, m.start() - 40) : m.end() + 40],
                }
            )

    # --- 2b. collapse organisation-name variants ---------------------------
    named_keys = sorted(
        {r["organisation_node"][4:] for r in person_org if r["organisation_node"].startswith("ORG:")}
    )
    canon = canonicalise_orgs(named_keys)
    label_for: dict[str, str] = {}
    for r in person_org:
        if r["organisation_node"].startswith("ORG:"):
            key = canon.get(r["organisation_node"][4:], r["organisation_node"][4:])
            # An entry of its own always wins over a bare mention.
            r["organisation_name_raw"] = r["organisation_name"]
            if key in org_index:
                r["organisation_node"] = org_index[key]
                r["organisation_name"] = next(
                    o["organisation_name"] for o in orgs if o["entry_id"] == org_index[key]
                )
            else:
                r["organisation_node"] = f"ORG:{key}"
                best = label_for.get(key, "")
                if len(r["organisation_name"]) > len(best):
                    label_for[key] = r["organisation_name"]
        else:
            r["organisation_name_raw"] = r["organisation_name"]
    for r in person_org:
        if r["organisation_node"].startswith("ORG:"):
            r["organisation_name"] = label_for.get(r["organisation_node"][4:], r["organisation_name"])

    # --- 3. landowners named in place entries ------------------------------
    for pl in places:
        if not pl["owners_raw"]:
            continue
        entry = entries[pl["entry_id"]]
        for name in split_names(pl["owners_raw"])[:25]:
            pid, resolution, ncand = resolve(name)
            mentions.append(
                {
                    "mention_id": f"M{len(mentions) + 1:06d}",
                    "source_entry_id": pl["entry_id"],
                    "source_entry_type": "place",
                    "name_raw": name,
                    "name_key": name_key(name),
                    "role": "property_owner",
                    "person_entry_id": pid,
                    "resolution": resolution,
                    "n_candidates": ncand,
                    "page": entry["page_first"],
                    "page_url": entry["page_url"],
                    "evidence": pl["owners_raw"][:180],
                }
            )
            person_place.append(
                {
                    "person_node": pid or f"NAME:{name_key(name)}",
                    "person_name": name,
                    "person_entry_id": pid,
                    "resolution": resolution,
                    "place_node": pl["entry_id"],
                    "place_name": pl["place_name"],
                    "relation": "property_owner",
                    "controle_civil": pl["controle_civil"],
                    "page": entry["page_first"],
                    "page_url": entry["page_url"],
                    "evidence": pl["owners_raw"][:180],
                }
            )

    # --- 4. residence and birthplace ties ----------------------------------
    place_by_key = {org_key(pl["place_name"]): pl["entry_id"] for pl in places}
    for p in persons:
        for field, relation in (("city", "residence"), ("birth_place", "birthplace")):
            val = p[field].strip()
            if not val:
                continue
            person_place.append(
                {
                    "person_node": p["entry_id"],
                    "person_name": f"{p['surname']} {p['forenames']}".strip(),
                    "person_entry_id": p["entry_id"],
                    "resolution": "resolved",
                    "place_node": place_by_key.get(org_key(val), f"PLACE:{org_key(val)}"),
                    "place_name": val,
                    "relation": relation,
                    "controle_civil": "",
                    "page": p["page_first"],
                    "page_url": entries[p["entry_id"]]["page_url"],
                    "evidence": p["address_raw"] if relation == "residence" else p["birth_date_raw"],
                }
            )

    # --- 5. one-mode projection: co-membership -----------------------------
    members_by_org: dict[str, list[dict]] = defaultdict(list)
    for row in person_org:
        members_by_org[row["organisation_node"]].append(row)

    pair_counts: Counter[tuple[str, str]] = Counter()
    pair_orgs: dict[tuple[str, str], set[str]] = defaultdict(set)
    for org_node, rows in members_by_org.items():
        seen = {r["person_node"]: r for r in rows}
        if len(seen) > 60:
            continue  # a membership roll, not a committee: not a meaningful tie
        for a, b in itertools.combinations(sorted(seen), 2):
            pair_counts[(a, b)] += 1
            pair_orgs[(a, b)].add(org_node)

    person_person = [
        {
            "source": a,
            "target": b,
            "weight": n,
            "edge_type": "co_membership",
            "shared_organisations": ";".join(sorted(pair_orgs[(a, b)])),
        }
        for (a, b), n in pair_counts.items()
    ]

    # --- 6. node table -----------------------------------------------------
    nodes: dict[str, dict] = {}
    person_by_id = {p["entry_id"]: p for p in persons}
    for p in persons:
        nodes[p["entry_id"]] = {
            "node_id": p["entry_id"],
            "label": f"{p['surname']} ({p['forenames']})".strip(),
            "node_type": "person_with_entry",
            "subtype": p["occupation_primary"],
            "birth_year": p["birth_year"],
            "n_decorations": p["n_decorations"],
            "has_portrait": int(int(p["n_portraits"]) > 0),
            "entry_length_chars": p["n_chars"],
            "page": p["page_first"],
            "page_url": entries[p["entry_id"]]["page_url"],
        }
    for row in person_org + person_place:
        nid = row["person_node"]
        if nid.startswith("NAME:") and nid not in nodes:
            nodes[nid] = {
                "node_id": nid,
                "label": row["person_name"],
                "node_type": "person_named_only",
                "subtype": "",
                "birth_year": "",
                "n_decorations": "",
                "has_portrait": 0,
                "entry_length_chars": "",
                "page": row["page"],
                "page_url": row["page_url"],
            }
    for o in orgs:
        nodes[o["entry_id"]] = {
            "node_id": o["entry_id"],
            "label": o["organisation_name"],
            "node_type": "organisation_with_entry",
            "subtype": o["organisation_kind_primary"],
            "birth_year": o["founded_year"],
            "n_decorations": "",
            "has_portrait": 0,
            "entry_length_chars": o["n_chars"],
            "page": o["page_first"],
            "page_url": entries[o["entry_id"]]["page_url"],
        }
    for row in person_org:
        nid = row["organisation_node"]
        if nid.startswith("ORG:") and nid not in nodes:
            nodes[nid] = {
                "node_id": nid,
                "label": row["organisation_name"],
                "node_type": "organisation_named_only",
                "subtype": "",
                "birth_year": "",
                "n_decorations": "",
                "has_portrait": 0,
                "entry_length_chars": "",
                "page": row["page"],
                "page_url": row["page_url"],
            }
    for pl in places:
        nodes[pl["entry_id"]] = {
            "node_id": pl["entry_id"],
            "label": pl["place_name"],
            "node_type": "place_with_entry",
            "subtype": pl["controle_civil"],
            "birth_year": "",
            "n_decorations": "",
            "has_portrait": 0,
            "entry_length_chars": pl["n_chars"],
            "page": pl["page_first"],
            "page_url": entries[pl["entry_id"]]["page_url"],
        }
    for row in person_place:
        nid = row["place_node"]
        if nid.startswith("PLACE:") and nid not in nodes:
            nodes[nid] = {
                "node_id": nid,
                "label": row["place_name"],
                "node_type": "place_named_only",
                "subtype": "",
                "birth_year": "",
                "n_decorations": "",
                "has_portrait": 0,
                "entry_length_chars": "",
                "page": row["page"],
                "page_url": row["page_url"],
            }

    # --- 7. a single two-mode edge list for Gephi / igraph ------------------
    combined = [
        {
            "source": r["person_node"],
            "target": r["organisation_node"],
            "edge_type": "affiliation",
            "role": r["role"],
            "weight": 1,
            "tie_source": r["tie_source"],
            "resolution": r["resolution"],
            "page": r["page"],
            "page_url": r["page_url"],
        }
        for r in person_org
    ] + [
        {
            "source": r["person_node"],
            "target": r["place_node"],
            "edge_type": r["relation"],
            "role": r["relation"],
            "weight": 1,
            "tie_source": "place_entry" if r["relation"] == "property_owner" else "person_entry",
            "resolution": r["resolution"],
            "page": r["page"],
            "page_url": r["page_url"],
        }
        for r in person_place
    ]

    write_csv(PROCESSED / "mentions.csv", mentions)
    write_csv(PROCESSED / "edges_person_organisation.csv", person_org)
    write_csv(PROCESSED / "edges_person_person.csv", person_person)
    write_csv(PROCESSED / "edges_person_place.csv", person_place)
    write_csv(PROCESSED / "network_nodes.csv", list(nodes.values()))
    write_csv(PROCESSED / "network_edges.csv", combined)

    res = Counter(m["resolution"] for m in mentions)
    print(
        json.dumps(
            {
                "mentions": len(mentions),
                "mention_resolution": dict(res),
                "person_organisation_edges": len(person_org),
                "person_place_edges": len(person_place),
                "co_membership_edges": len(person_person),
                "nodes": len(nodes),
                "nodes_by_type": dict(Counter(n["node_type"] for n in nodes.values())),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
