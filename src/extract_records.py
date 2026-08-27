"""Code each dictionary entry into structured variables.

Lambert writes to a house template, and the template is what makes the volume
codeable:

  SURNAME (Forenames), <birth date>, <birthplace>, <decorations>. <occupation>,
  <address>. <date of arrival in Tunisia>. ETUDES : ... SUCCESS' : ... TRAVAUX : ...

Places follow a second template ("C. c. de Sousse, caidat de Mahdia, a 14 k. de
Mahdia ... POPUL. : 4.500 hab.") and associations a third ("15 nov. 1906. Tunis.
Siege social : ... BUT : ... 104 membres. Pres., M. Marcille; v.-pres., ...").

This stage writes one row per entry plus type-specific tables. Every field keeps
its verbatim source string alongside the coded value, so a researcher can check
any cell against the page image, and nothing is silently imputed: a field that
could not be read is empty, not guessed.

Outputs (data/processed): entries.csv, persons.csv, places.csv,
organizations.csv, decorations.csv, career_positions.csv, education.csv.
"""

from __future__ import annotations

import csv
import json
import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"

ARK = "bpt6k5505300s"
PAGE_URL = "https://gallica.bnf.fr/ark:/12148/" + ARK + "/f{view}.item"
IIIF_URL = "https://gallica.bnf.fr/iiif/ark:/12148/" + ARK + "/f{view}/full/full/0/native.jpg"

MONTHS = {
    "janv": 1, "jan": 1, "fev": 2, "fevr": 2, "mars": 3, "avril": 4, "avr": 4,
    "mai": 5, "juin": 6, "juil": 7, "juill": 7, "aout": 8, "sept": 9, "oct": 10,
    "nov": 11, "dec": 12, "decemb": 12,
}
MONTH_RE = r"(?:janv|jan|f[ée]vr?|mars|avril|avr|mai|juin|juill?|ao[uû]t|sept|oct|nov|d[ée]c)[a-zà-ÿ]*\.?"
YEAR_RE = r"1[6-9]\d{2}"
# The OCR routinely reads 8 as S, 0 as O, 1 as l/I and 6 as G inside dates
# ("1S76", "1SS2", "18(52", "1.870"), which would otherwise cost roughly one
# birth year in six -- and worse, let the *next* date in the entry (arrival in
# Tunisia) be picked up as the birth year instead.
YEAR_LOOSE_RE = (
    r"1[\.\s]?[\dSsOolIiGgCcBZzT][\.\s(]?[\dSsOolIiGgCcBZzT][\.\s(]?[\dSsOolIiGgCcBZzT]"
)
DIGIT_FIXES = str.maketrans({"S": "8", "s": "8", "B": "8", "O": "0", "o": "0",
                             "l": "1", "I": "1", "i": "1", "G": "6", "g": "6",
                             "C": "6", "c": "6", "Z": "2", "z": "2", "T": "7"})
DATE_RE = re.compile(
    rf"(?:(\d{{1,2}})\s*(?:er|ER|\"|°|')?\s*)?({MONTH_RE})?\s*({YEAR_LOOSE_RE})", re.IGNORECASE
)


def clean_year(raw: str) -> str:
    """Return a four-digit year, repairing OCR digit confusions, or ''.

    A stray "(" inside the digits is not repairable: it stands where the OCR
    dropped or mangled a character, and closing the gap silently yields a
    plausible but wrong year -- "9 avril 1.8(i6" (1866) would read as 1816.
    Seven dates in the volume look like this; all are left empty.
    """
    if "(" in raw:
        return ""
    digits = re.sub(r"[^\dSsOolIiGgCcBZzT]", "", raw).translate(DIGIT_FIXES)
    if len(digits) != 4 or not digits.isdigit():
        return ""
    return digits if 1600 <= int(digits) <= 1915 else ""

# --- in-entry rubric labels, with the OCR variants that actually occur -------
RUBRIC_PATTERNS = {
    "etudes": r"[EÉ]TUDES?\s*:",
    "carriere": r"SUCCESS(?:IVEMENT|IVEM|[’'\"1I])?\s*[.:]",
    "travaux": r"(?:T[RIEB]{1,2}[AI]VAUX|OEUVRES|O[IÎ]UVKES|OUVRAGES\s+PUBLI[EÉ]S|PUBLICATIONS)\s*:",
    "but": r"[BRH]\s?UT\s*:",
    "population": r"POPUL[A-Z]*\.?\s*:",
    "archeologie": r"ARCH[EÉ]?[A-Z]*\.?\s*:",
}
RUBRIC_RE = re.compile(
    "|".join(f"(?P<{k}>{v})" for k, v in RUBRIC_PATTERNS.items())
)

# --- honours ----------------------------------------------------------------
# Grades run chevalier < officier < commandeur < grand officier < grand-croix.
GRADES = [
    ("grand_maitre", r"gr(?:and)?\.?\s*ma[iî]tre"),
    ("grand_croix", r"gr(?:and)?[\.\s-]*croix"),
    ("grand_cordon", r"gr(?:and)?[\.\s-]*cordon"),
    ("grand_officier", r"gr(?:and)?\.?\s*off(?:icier)?\.?"),
    ("commandeur", r"comm(?:andeur)?\.?"),
    ("officier", r"off(?:icier)?\.?"),
    ("chevalier", r"chev(?:alier)?\.?"),
    ("medaille", r"m[ée]daille"),
    ("titulaire", r"titulaire|d[ée]cor[ée]"),
]
GRADE_RE = re.compile("|".join(f"(?P<{k}>{v})" for k, v in GRADES), re.IGNORECASE)

# Honours are matched on *fuzzy tokens*, not on literal strings. The 1912 OCR
# renders "Nichan-Iftikhar" as "Nichan-lftikhar", "Nichan-Iflikliar" and even
# "iNielian-Jllikbar", and "Legion d'honneur" as "Lesion d'honn-". Since these
# are among the most analytically useful variables in the volume -- state
# recognition of an individual -- recall matters more here than elsewhere, and
# an edit-distance tolerance on a small closed vocabulary is safe.
ORDER_ANCHORS: list[tuple[str, list[tuple[str, int]], int, str]] = [
    # (order key, [(word, max edit distance)], token window, awarding state)
    ("legion_honneur", [("legion", 2), ("honneur", 3)], 3, "France"),
    ("palmes_academiques", [("academie", 2)], 1, "France"),
    ("palmes_academiques", [("instruction", 3), ("publique", 3)], 2, "France"),
    ("merite_agricole", [("merite", 2), ("agricole", 2)], 3, "France"),
    ("ouissam_alaouite", [("ouissam", 2)], 1, "Morocco"),
    ("ouissam_alaouite", [("alaouite", 2)], 1, "Morocco"),
    ("couronne_italie", [("couronne", 2), ("italie", 2)], 3, "Italy"),
    ("saints_maurice_lazare", [("maurice", 2), ("lazare", 2)], 3, "Italy"),
    ("etoile_noire_benin", [("etoile", 1), ("noire", 1)], 2, "France (Benin)"),
    ("etoile_anjouan", [("etoile", 2), ("anjouan", 2)], 3, "France (Comoros)"),
    ("ordre_radama", [("radama", 0)], 1, "France (Madagascar)"),
    ("medjidie", [("medjidie", 2)], 1, "Ottoman Empire"),
    ("osmanie", [("osmanie", 2)], 1, "Ottoman Empire"),
    ("isabelle_catholique", [("isabelle", 2), ("catholique", 3)], 3, "Spain"),
    ("charles_iii", [("charles", 1), ("iii", 0)], 2, "Spain"),
    ("christ_portugal", [("christ", 1), ("portugal", 2)], 3, "Portugal"),
    ("saint_olaf", [("olaf", 0)], 1, "Norway"),  # 0: "olf." is OCR for "off."
    ("saint_stanislas", [("stanislas", 2)], 1, "Russia"),
    ("saint_sauveur_grece", [("sauveur", 2), ("grece", 2)], 3, "Greece"),
    ("francois_joseph", [("francois", 2), ("joseph", 2)], 2, "Austria-Hungary"),
    ("leopold_belgique", [("leopold", 2)], 1, "Belgium"),
    ("dannebrog", [("dannebrog", 2)], 1, "Denmark"),
    ("medaille_militaire", [("medaille", 2), ("militaire", 2)], 3, "France"),
    ("medaille_coloniale", [("medaille", 2), ("coloniale", 2)], 3, "France"),
    ("croix_rouge", [("croix", 0), ("rouge", 0)], 2, "international"),
]
# The three beylical orders share a stem; the qualifier that follows tells them
# apart ("Nichan el-Abed", "Nichan ed-Dem", otherwise the Nichan Iftikhar).
NICHAN_STEM = ("nichan", 2)
NICHAN_VARIANTS = {"el_abed": ("abed", 1), "ed_dem": ("dem", 1)}
# Apostrophes are dropped from tokens on purpose: "d'honn-" has to reduce to
# "honn" before it can be matched against "honneur", and keeping the elision
# would otherwise make "ol'f." (OCR for "off.") look like "Olaf".
TOKEN_RE = re.compile(r"[A-Za-zÀ-ÿ]{2,}")


def within_distance(a: str, b: str, limit: int) -> bool:
    """Bounded Levenshtein test, cheap because the vocabulary is tiny."""
    if abs(len(a) - len(b)) > limit:
        return False
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        best = cur[0]
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            best = min(best, cur[j])
        if best > limit:
            return False
        prev = cur
    return prev[-1] <= limit


# --- occupational coding ----------------------------------------------------
# Keyword sets applied to the occupation clause first, then to the whole entry.
# Multi-label by design: a "docteur en medecine, conseiller municipal" is both.
OCCUPATIONS: list[tuple[str, str]] = [
    ("justice_law", r"avocat|avou[ée]|notaire|huissier|greffier|magistrat|\bjuge\b|procureur|substitut|oukil|cadi|ca[iï]d[ıi]?\s+de\s+justice|conseiller\s+[àa]\s+la\s+cour|pr[ée]sident\s+du\s+tribunal|d[ée]fenseur"),
    ("medicine_health", r"m[ée]decin|docteur\s+en\s+m[ée]decine|chirurgien|pharmacien|dentiste|v[ée]t[ée]rinaire|sage[\s\-]femme|interne\s+des\s+h[oô]pitaux"),
    ("military", r"g[ée]n[ée]ral|colonel|lieutenant[\s\-]colonel|commandant|capitaine|lieutenant|sous[\s\-]officier|adjudant|gendarme|officier\s+d[’'\s]*artillerie|chef\s+de\s+bataillon|mar[ée]chal"),
    ("education_science", r"professeur|instituteur|institutrice|directeur\s+d[’'\s]*[ée]cole|proviseur|censeur|inspecteur\s+de\s+l[’'\s]*enseignement|ma[iî]tre\s+d[’'\s]*[ée]tudes|savant|arch[ée]ologue|naturaliste"),
    ("religion", r"cur[ée]|pr[êe]tre|abb[ée]|pasteur|rabbin|imam|aum[oô]nier|[ée]v[êe]que|mufti|mokaddem|p[èe]re\s+blanc|chanoine"),
    ("engineering_architecture", r"ing[ée]nieur|architecte|g[ée]om[èe]tre|conducteur\s+des\s+ponts|dessinateur[\s\-]projeteur"),
    ("administration", r"fonctionnaire|contr[oô]leur|v[ée]rificateur|conservateur|"
     r"tr[ée]sorier[\s-]payeur|chef\s+de\s+section|chef\s+de\s+bureau|chef\s+de\s+service|sous[\s\-]directeur|directeur\s+g[ée]n[ée]ral|secr[ée]taire\s+g[ée]n[ée]ral|r[ée]dacteur\s+[àa]\s+la\s+direction|\bcommis\b|receveur|percepteur|inspecteur|administrateur|attach[ée]\s+au\s+cabinet|interpr[èe]te|drogman"),
    ("politics_native_admin", r"d[ée]put[ée]|conseiller\s+municipal|\bmaire\b|adjoint\s+au\s+maire|conf[ée]rence\s+consultative|ca[iï]d\b|khalifa|gouverneur|cheikh\s+de|premier\s+ministre|ministre\s+de\s+la\s+plume"),
    ("diplomacy", r"consul|vice[\s\-]consul|charg[ée]\s+d[’'\s]*affaires|agent\s+consulaire"),
    ("commerce", r"n[ée]gociant|commer[çc]ant|marchand|[ée]picier|importateur|exportateur|courtier|repr[ée]sentant\s+de\s+commerce|magasin|quincaillier|libraire"),
    ("industry_crafts", r"industriel|entrepreneur|fabricant|minotier|imprimeur|constructeur|manufactur|usine|tanneur|boulanger|serrurier|menuisier|coiffeur|tailleur"),
    ("agriculture", r"\bcolon\b|agriculteur|viticulteur|[ée]leveur|exploitant\s+agricole|propri[ée]taire\s+agricole|fermier|ol[ée]iculteur|horticulteur"),
    ("finance_banking", r"banquier|banque|agent\s+de\s+change|assureur|assurances|comptable|changeur|courtier\s+d[’'\s]*assurance"),
    ("press_letters_arts", r"journaliste|publiciste|r[ée]dacteur\s+en\s+chef|directeur\s+du\s+journal|homme\s+de\s+lettres|[ée]crivain|po[èe]te|peintre|sculpteur|musicien|artiste|photographe"),
    ("mining", r"\bmine[sr]?\b|minier|phosphate"),
    ("transport_maritime", r"armateur|capitaine\s+au\s+long\s+cours|chef\s+de\s+gare|agent\s+maritime|transitaire|compagnie\s+de\s+navigation|chemins?\s+de\s+fer"),
    ("hospitality_services", r"h[oô]telier|restaurateur|caf[ée]tier|propri[ée]taire\s+d[’'\s]*h[oô]tel"),
]
OCCUPATION_RES = [(k, re.compile(p, re.IGNORECASE)) for k, p in OCCUPATIONS]

DEGREE_PATTERNS = [
    ("licence_droit", r"licenci[ée]\s+en\s+droit"),
    ("doctorat_droit", r"docteur\s+en\s+droit"),
    ("doctorat_medecine", r"docteur\s+en\s+m[ée]decine"),
    ("baccalaureat", r"bachelier|baccalaur[ée]at"),
    ("brevet_superieur", r"brevet\s+sup[ée]rieur"),
    ("agregation", r"agr[ée]g[ée]"),
    ("diplome_superieur", r"dipl[oô]m[ée]"),
    ("certificat", r"certificat"),
]
DEGREE_RES = [(k, re.compile(p, re.IGNORECASE)) for k, p in DEGREE_PATTERNS]

SCHOOL_RE = re.compile(
    r"(?:Facult[ée]s?\s+(?:de\s+)?(?:droit|m[ée]decine|des\s+sciences|des\s+lettres|de\s+th[ée]ologie)[^.;:]{0,40}"
    r"|[EÉ]cole\s+(?:normale|polytechnique|centrale|coloniale|des\s+[A-Za-zà-ÿ\-]+|sup[ée]rieure[^.;:]{0,30}|de\s+[A-Za-zà-ÿ\-]+)"
    r"|lyc[ée]e\s+(?:de\s+|d[’']\s*|cle\s+)?[A-Za-zà-ÿ'\-]+"
    r"|coll[èe]ge\s+(?:de\s+|d[’']\s*|cle\s+)?(?:Sadiki|Alaoui|[A-Za-zà-ÿ'\-]+)"
    r"|Khaldounia|Grande\s+Mosqu[ée]e|Zitouna"
    r"|Institut\s+(?:national\s+)?[A-Za-zà-ÿ'\-]+)",
    re.IGNORECASE,
)

CITY_RE = re.compile(
    r"\b(Tunis|Sousse|Sfax|Bizerte|Kairouan|B[ée]ja|Gab[èe]s|Le\s+Kef|Mahdia|Monastir|"
    r"Nabeul|Zaghouan|Ferryville|La\s+Goulette|La\s+Marsa|Menzel[\s\-]Bourguiba|Djerba|"
    r"Gafsa|Tozeur|Medenine|Souk[\s\-]el[\s\-]Arba|Teboursouk|Grombalia|Tebourba|Carthage)\b"
)
ADDRESS_RE = re.compile(
    r"(\d{1,3}\s*(?:bis|ter)?\s*,\s*(?:rue|avenue|av\.|boulevard|bd|place|quai|impasse|passage|route)"
    r"[^.;]{2,60})",
    re.IGNORECASE,
)

PLACE_MARKERS = re.compile(
    r"\bC\.\s*c\.|contr[oô]le\s+civil|ca[iï]dat|Territoire\s+militaire|"
    r"POPUL|\bannexe\s+et\s+ca[iï]dat", re.IGNORECASE
)
# Localities that Lambert describes without the administrative formula still
# carry a settlement noun and a distance or a population figure.
PLACE_SOFT_RE = re.compile(
    r"(?:village|douar|henchir|oasis|djebel|ha[oe]uch|bourgade|hameau|centre\s+de\s+colonisation"
    r"|localit[ée]|ferme|ruines\s+de|[iî]le\b)", re.IGNORECASE
)
PLACE_MEASURE_RE = re.compile(
    r"[àa]\s*\d{1,3}\s*(?:k|kil|kilom|km)[a-z.]*\s*(?:de|du|d[’'])|\bhab\.|habitants", re.IGNORECASE
)
ORG_HEAD_RE = re.compile(
    r"^(Association|Soci[ée]t[ée]|Societ[àa]|Associazione|Cercle|Club|Comit[ée]|Syndicat|"
    r"Chambre|Union|Ligue|Loge|Conf[ée]rence|Conseil|Compagnie|Banque|Caisse|F[ée]d[ée]ration|"
    r"Orph[ée]linat|Amicale|Mutuelle|Chorale|Harmonie|Croix|H[oô]pital|Institut|Dispensaire|"
    r"Mus[ée]e|Th[ée][âa]tre|Cr[ée]dit|Patronage|Fanfare|Alliance|Oeuvre|Fondation)\b",
    re.IGNORECASE,
)
ORG_BODY_RE = re.compile(
    r"BUT\s*:|Si[èe]ge\s+social|membres?\s+actifs?|adh[ée]rents|Pr[ée]s\.|pr[ée]sident", re.IGNORECASE
)
CROSSREF_RE = re.compile(r"\(\s*V\.\s|\(\s*Voir\s", re.IGNORECASE)
# A locality's description opens with the administrative formula, immediately
# after the headword: "MELLITA. C. c. de Gabes, ann. de Djerba, caidat de
# l'Arad." Anchoring on that position keeps a person whose *job* is "Secretaire
# de Controle civil" out of the place table.
ADMIN_FORMULA_RE = re.compile(
    r"[\s.,;:'’\-]*(?:\([^)]{0,30}\))?[\s.,;:'’\-]*"
    r"(?:C[.,]\s*c\.|Contr[oô]le\s+civil|Ca[iï]dat|Terr\.\s*mil\.|Territoire\s+militaire|"
    r"Annexe\s+et\s+ca[iï]dat|Ann\.\s*(?:et|de)\s)",
    re.IGNORECASE,
)


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", strip_accents(s or "").lower()).strip()


# --------------------------------------------------------------------------
# classification
# --------------------------------------------------------------------------
def caps_ratio(s: str) -> float:
    letters = [c for c in strip_accents(s) if c.isalpha()]
    return sum(c.isupper() for c in letters) / len(letters) if letters else 0.0


def forenames_of(entry: dict) -> str:
    """The parenthesised forenames that follow a personal headword."""
    head = re.escape(entry["headword_raw"][:40])
    m = re.match(rf"\s*{head}[^(]{{0,4}}\(([^)]{{1,60}})\)", entry["text"])
    if not m:
        return ""
    inner = m.group(1).strip()
    # "MANOUBA (LA)", "LOUZA (El-)", "SIDI-TABET (Domaine de)", "ABBAS (ou
    # ABBES)": the parenthesis after a headword is not always forenames.
    if re.match(
        r"^(?:LA|LE|LES|L[’']|EL|El|Le|La|Les|les|la|le|ou|OU|dit|voir|V\.|Domaine|"
        r"Henchir|Oued|Djebel|Bordj|Dar|A[iï]n|Ville|Cap|[ÎIl]le|Les?\b)\b|^[’'\-]",
        inner,
    ):
        return ""
    # Forenames are capitalised words or initials. Anything with a lower-case
    # word in it is a qualifier, not a name: "(methode Prevost-Delaunay)",
    # "(Domaine de)", "(section de Bizerte)".
    parts = [t for t in re.split(r"[\s\-]+", inner) if t]
    if not parts or len(parts) > 6:
        return ""
    if not all(re.match(r"^[A-ZÉÈÊÀÇÎÔÜ][\wà-ÿ'’.]*$", t) for t in parts):
        return ""
    # Forenames are often reduced to initials -- "MUSCAT fils (C.)" -- so a
    # single letter still counts, but a bare number or symbol does not.
    return inner if re.search(r"[A-Za-zà-ÿ]", inner) else ""


def classify(entry: dict) -> tuple[str, str]:
    """Return (entry_type, rule) for one entry."""
    text, head = entry["text"], entry["headword_raw"]
    opening = text[: len(head) + 220]
    forenames = forenames_of(entry)

    if CROSSREF_RE.search(text) and entry["n_chars"] < 140:
        return "cross_reference", "see_also_only"
    # "C. c." (controle civil) and "caidat" name the administrative units a
    # locality belongs to. Nothing else in the volume uses them, so they settle
    # the type even when the headword carries a parenthesis that looks like
    # forenames ("SIDI-TABET (Domaine de). C. c. de Tunis...").
    post = text[len(head) :]
    if ADMIN_FORMULA_RE.match(post):
        return "place", "administrative_unit"
    if PLACE_MARKERS.search(opening) and not forenames:
        return "place", "administrative_markers"
    if not forenames and PLACE_SOFT_RE.search(opening) and PLACE_MEASURE_RE.search(text[:500]):
        return "place", "settlement_noun_and_measure"
    if forenames and re.search(rf"{YEAR_RE}|d[ée]c[ée]d[ée]|n[ée]\s+[àa]", opening):
        return "person", "forenames_and_life_dates"
    if forenames and caps_ratio(head) > 0.6:
        return "person", "caps_headword_with_forenames"
    if (ORG_HEAD_RE.match(head) and len(head.split()) > 1) or (
        ORG_BODY_RE.search(opening) and not forenames
    ):
        return "organisation", "organisational_template"
    if PLACE_MARKERS.search(text[:400]):
        return "place", "administrative_markers_late"
    # A capitalised headword with a life date, an honour, or a stated occupation
    # is a person even when the forenames were lost to OCR ("AZEDINE BEY. 1SS2,
    # La Marsa. Grand cordon de l'Ordre du Sang...").
    if caps_ratio(head) > 0.6 and re.match(r"[A-ZÉÈÊÀÇ]{3}", strip_accents(head)):
        if re.search(rf"{YEAR_RE}", opening):
            return "person", "caps_headword_with_date"
        if find_decorations(opening):
            return "person", "caps_headword_with_honour"
        if occupation_labels(opening):
            return "person", "caps_headword_with_occupation"
    return "topic", "residual"


# --------------------------------------------------------------------------
# shared field extractors
# --------------------------------------------------------------------------
def parse_date(fragment: str) -> tuple[str, str]:
    """Return (verbatim date, year) for the first date-like string."""
    for m in DATE_RE.finditer(fragment):
        year = clean_year(m.group(3))
        if year:
            return m.group(0).strip(" ,."), year
    return "", ""


def rubric_sections(text: str) -> dict[str, str]:
    """Split an entry on its own rubric labels (ETUDES:, SUCCESS':, TRAVAUX:)."""
    marks = [(m.start(), m.end(), m.lastgroup) for m in RUBRIC_RE.finditer(text)]
    out: dict[str, str] = {"_head": text[: marks[0][0]].strip() if marks else text.strip()}
    for i, (_, end, name) in enumerate(marks):
        stop = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out[name] = (out.get(name, "") + " " + text[end:stop].strip()).strip()
    return out


def find_decorations(text: str) -> list[dict]:
    """Every honour named in an entry, with its grade where one is stated."""
    toks = [(m.group(0).lower(), m.start()) for m in TOKEN_RE.finditer(strip_accents(text))]
    words = [t for t, _ in toks]
    found: dict[str, dict] = {}

    def record(key: str, pos: int, country: str) -> None:  # noqa: D401
        if key in found:
            return
        window = text[max(0, pos - 45) : pos]
        grades = list(GRADE_RE.finditer(window))
        found[key] = {
            "order": key,
            "order_country": country,
            "grade": grades[-1].lastgroup if grades else "",
            "position": pos,
            "context": re.sub(r"\s+", " ", text[max(0, pos - 45) : pos + 25]).strip(),
        }

    for i, (tok, pos) in enumerate(toks):
        for key, anchors, window, country in ORDER_ANCHORS:
            head, dist = anchors[0]
            if not within_distance(tok, head, dist):
                continue
            if all(
                any(
                    within_distance(w, target, d)
                    for w in words[i + 1 : i + 1 + window + 1]
                )
                for target, d in anchors[1:]
            ):
                record(key, pos, country)
        if within_distance(tok, NICHAN_STEM[0], NICHAN_STEM[1]):
            variant = "iftikhar"
            for name, (target, d) in NICHAN_VARIANTS.items():
                if any(within_distance(w, target, d) for w in words[i + 1 : i + 3]):
                    variant = name
            record(f"nichan_{variant}", pos, "Tunisia")
    return list(found.values())


def occupation_labels(text: str) -> list[str]:
    return [k for k, rx in OCCUPATION_RES if rx.search(text)]


# --------------------------------------------------------------------------
# person records
# --------------------------------------------------------------------------
# A purely *typographic* feature of the printed headword: does the name use the
# Arabic patronymic construction, with the particle set as a separate word
# ("AHMED BEN OTHMAN", "ABD UL WAHAB", "BEL KHODJA")? This is not an ethnic or
# religious classification and must not be used as one. It under-counts names
# written solid ("ABDELLI", "BOUHAGEB") and says nothing about anyone whose name
# does not take this form. See the codebook before using it.
NASAB_PARTICLES = {
    "BEN", "BENT", "BIN", "OULD", "ABD", "ABOU", "ABU", "BOU", "BEL", "EL",
    "SIDI", "SI", "OU",
}
HONORIFIC_RE = re.compile(r"\b(Si|Sidi|Hadj|Hadji|Cheikh|Bey|Pacha)\b", re.IGNORECASE)


def extract_person(entry: dict) -> dict:
    text = entry["text"]
    head = entry["headword_raw"]
    sections = rubric_sections(text)
    body = sections["_head"]

    forenames = forenames_of(entry)
    after = body
    if forenames:
        idx = body.find(forenames)
        after = body[idx + len(forenames) + 1 :] if idx >= 0 else body
    else:
        after = body[len(head) :]

    # The birth date sits immediately after the forenames throughout the volume
    # ("ABADIE (Jean), 4 sept. 1862, Blaye"). Looking further ahead would pick up
    # the arrival-in-Tunisia date instead whenever the birth date is absent.
    birth_raw, birth_year = parse_date(after[:45])
    birth_place = birth_place_detail = ""
    if birth_raw:
        rest = after[after.find(birth_raw) + len(birth_raw) :]
        m = re.match(
            r"[\s,.;]*([A-ZÉÈÊÀÇÎÔ][^,.;()]{1,40}?)\s*(?:\(([^)]{2,30})\))?\s*[,.;]", rest
        )
        if m and not GRADE_RE.match(m.group(1).strip()):
            birth_place = m.group(1).strip()
            birth_place_detail = (m.group(2) or "").strip()

    decorations = find_decorations(text)
    address = ADDRESS_RE.search(body)
    city = CITY_RE.search(body[address.end():address.end() + 40]) if address else None
    if city is None:
        city = CITY_RE.search(body)

    # The bare date printed after the occupation and address is, throughout the
    # volume, the year the person settled in Tunisia. Coded as inferred.
    settled_raw = settled_year = ""
    tail = body[address.end():] if address else body[len(head) + 60 :]
    m = re.search(rf"(?:^|[.;]\s*)((?:\d{{1,2}}\s*)?(?:{MONTH_RE}\s*)?({YEAR_RE}))\s*[.;]", tail)
    if m:
        settled_raw, settled_year = m.group(1).strip(), m.group(2)

    # The occupation clause runs from the end of the identification block --
    # headword, forenames, birth, honours -- to the address or the settlement
    # date, whichever comes first.
    start = len(head)
    if birth_place and birth_place in body:
        start = max(start, body.find(birth_place) + len(birth_place))
    # Honours are printed between the birth clause and the occupation, so the
    # occupation begins after the last one -- but only honours in the opening
    # half of the entry count, since later text can name an order again.
    for d in decorations:
        pos = d["position"]
        if start < pos < len(body) * 0.6:
            start = pos
    while start < len(body) and body[start] not in " .,;":
        start += 1  # step off the middle of the honour's own name
    while start < len(body) and body[start] in " .,;":
        start += 1
    end = len(body)
    if address and address.start() > start:
        end = address.start()
    elif settled_raw and body.find(settled_raw, start) > start:
        end = body.find(settled_raw, start)
    occupation_raw = re.sub(r"^[\s,.;)]+", "", body[start:end])
    # A stray period inside the honour's name ("Nicha.n-Iflikbar.") can leave a
    # fragment at the head of the clause; drop it when it is not a word.
    occupation_raw = re.sub(r"^[^\s]{0,14}[.,;]\s+(?=[A-ZÉÈÀ])", "", occupation_raw)[:300]

    labels = occupation_labels(occupation_raw) or occupation_labels(body)
    schools = []
    for m in SCHOOL_RE.finditer(sections.get("etudes", "") + " " + body):
        s = re.sub(r"\s+", " ", m.group(0)).strip(" .,;")
        if s.lower() not in {x.lower() for x in schools}:
            schools.append(s)
    degrees = [k for k, rx in DEGREE_RES if rx.search(sections.get("etudes", "") + " " + body)]

    career = sections.get("carriere", "")
    return {
        "entry_id": entry["entry_id"],
        "surname": head,
        "forenames": forenames,
        "name_has_nasab_particle": int(
            bool(NASAB_PARTICLES & set(strip_accents(head).upper().replace("-", " ").split()))
        ),
        "name_honorific": (
            HONORIFIC_RE.search(f"{head} {forenames}").group(1).capitalize()
            if HONORIFIC_RE.search(f"{head} {forenames}")
            else ""
        ),
        "birth_date_raw": birth_raw,
        "birth_year": birth_year,
        "birth_place": birth_place,
        "birth_place_detail": birth_place_detail,
        "occupation_raw": occupation_raw,
        "occupation_categories": ";".join(labels),
        "occupation_primary": labels[0] if labels else "",
        "address_raw": address.group(1).strip() if address else "",
        "city": city.group(1) if city else "",
        "settled_tunisia_raw": settled_raw,
        "settled_tunisia_year": settled_year,
        "n_decorations": len(decorations),
        "decoration_orders": ";".join(d["order"] for d in decorations),
        "has_legion_honneur": int(any(d["order"] == "legion_honneur" for d in decorations)),
        "has_nichan_iftikhar": int(any(d["order"] == "nichan_iftikhar" for d in decorations)),
        "education_raw": sections.get("etudes", ""),
        "education_institutions": ";".join(schools),
        "degrees": ";".join(degrees),
        "career_raw": career,
        "n_career_positions": len([s for s in re.split(r"[;.]", career) if len(s.strip()) > 8]),
        "works_raw": sections.get("travaux", ""),
        "has_works": int(bool(sections.get("travaux", "").strip())),
        "deceased_mentioned": int(bool(re.search(r"d[ée]c[ée]d[ée]|mort\s+le|\+\s*1[89]\d\d", text))),
        "n_portraits": entry["n_portraits"],
        "n_chars": entry["n_chars"],
        "page_first": entry["page_first"],
        "ocr_confidence": entry["ocr_confidence"],
    }


# --------------------------------------------------------------------------
# place records
# --------------------------------------------------------------------------
def extract_place(entry: dict) -> dict:
    text = entry["text"]
    sections = rubric_sections(text)

    cc = re.search(r"C\.\s*c\.\s*(?:et\s+ca[iï]dat\s+)?(?:de\s+|du\s+|d[’'])?([A-ZÉÈ][^,.;]{1,30})", text)
    caidat = re.search(r"ca[iï]dat\s+(?:de\s+|du\s+|des\s+|d[’'])?([A-ZÉÈla][^,.;]{1,30})", text)
    annexe = re.search(r"annexe\s+(?:et\s+ca[iï]dat\s+)?(?:de\s+|du\s+|d[’'])?([A-ZÉÈ][^,.;]{1,30})", text, re.I)
    dist = re.search(r"[àa]\s*(\d{1,3})\s*(?:k|kil|kilom|km)[a-z.]*\s*(?:de\s+|du\s+|d[’'])\s*([A-ZÉÈ][^,.;]{1,30})", text)
    pop = re.search(rf"(?:POPUL[A-Z]*\.?\s*:\s*|\b)([\d]{{1,3}}(?:[.\s]\d{{3}})*|\d+)\s*(?:hab\.|habitants)", text)
    alt = re.search(r"[Aa]ltit[a-z.]*\s*:?\s*(\d{1,4})", text)
    owners = re.search(r"(?:Propr[a-zé]*\.?|Propri[ée]taires?)\s*:?\s*((?:MM\.|M\.)?[^.]{3,300})", text)
    tribe = re.search(r"tribu\s+(?:des\s+|du\s+|de\s+la\s+|de\s+)?([A-ZÉÈ][^,.;]{2,30})", text)

    def num(s: str | None) -> str:
        return re.sub(r"[.\s]", "", s) if s else ""

    return {
        "entry_id": entry["entry_id"],
        "place_name": entry["headword_raw"],
        "controle_civil": cc.group(1).strip() if cc else "",
        "caidat": caidat.group(1).strip() if caidat else "",
        "annexe": annexe.group(1).strip() if annexe else "",
        "distance_km": dist.group(1) if dist else "",
        "distance_from": dist.group(2).strip() if dist else "",
        "population": num(pop.group(1)) if pop else "",
        "altitude_m": alt.group(1) if alt else "",
        "tribe_mentioned": tribe.group(1).strip() if tribe else "",
        "owners_raw": re.sub(r"\s+", " ", owners.group(1)).strip()[:300] if owners else "",
        "has_railway_station": int(bool(re.search(r"sur\s+la\s+ligne|gare|chemin\s+de\s+fer|B\.-G\.", text))),
        "has_school": int(bool(re.search(r"[ée]cole", text, re.I))),
        "has_post_office": int(bool(re.search(r"bureau\s+de\s+poste|t[ée]l[ée]graph|postal", text, re.I))),
        "has_market": int(bool(re.search(r"march[ée]|souk", text, re.I))),
        "has_roman_ruins": int(bool(re.search(r"ruines|romain|byzantin|antique", text, re.I))),
        "archaeology_raw": sections.get("archeologie", ""),
        "n_chars": entry["n_chars"],
        "page_first": entry["page_first"],
        "ocr_confidence": entry["ocr_confidence"],
    }


# --------------------------------------------------------------------------
# organisation records
# --------------------------------------------------------------------------
ORG_KINDS = [
    ("mutual_aid", r"secours\s+mutuels?|mutuelle|bienfaisance|philanthropi|orph[ée]linat"),
    ("professional_union", r"syndicat|amicale\s+des\s+fonctionnaires|association\s+amicale\s+des|corporation|chambre\s+syndicale"),
    ("chamber_public_body", r"chambre\s+de\s+commerce|chambre\s+d[’'\s]*agriculture|conf[ée]rence\s+consultative|conseil\s+"),
    ("learned_society", r"soci[ée]t[ée]\s+de\s+g[ée]ographie|institut|arch[ée]ologi|savante|scientifique|litt[ée]raire|[ée]tudes"),
    ("sport_leisure", r"sportive?|sports|nautique|gymnastique|cycliste|courses|chasse|v[ée]lo|foot"),
    ("alumni", r"anciens\s+[ée]l[èe]ves|anciens\s+combattants"),
    ("masonic", r"loge|ma[çc]onni|grand\s+orient"),
    ("religious", r"catholique|isra[ée]lite|protestant|paroisse|confr[ée]rie|charit[ée]\s+chr[ée]tienne"),
    ("music_arts", r"chorale|harmonie|musique|orph[ée]on|th[ée][âa]tre|beaux[\s\-]arts"),
    ("national_community", r"italiana|italienne|maltais|grecque|anglaise|espagnole|su[ié]sse|allemande|tunisina"),
    ("agricultural_economic", r"agricole|coop[ée]rative|colons|viticole|[ée]conomique"),
]
ORG_KIND_RES = [(k, re.compile(p, re.IGNORECASE)) for k, p in ORG_KINDS]


def extract_organisation(entry: dict) -> dict:
    text = entry["text"]
    sections = rubric_sections(text)
    body = sections["_head"]

    founded_raw, founded_year = parse_date(body[len(entry["headword_raw"]) : len(entry["headword_raw"]) + 160])
    seat = re.search(r"Si[èe]ge\s+social\s*:?\s*([^.]{3,120})", text)
    members = re.search(r"([\d]{1,3}(?:[.\s]\d{3})*|\d+)\s*(?:membres|adh[ée]rents|soci[ée]taires)", text)
    kinds = [k for k, rx in ORG_KIND_RES if rx.search(text)]
    city = CITY_RE.search(seat.group(1)) if seat else CITY_RE.search(body)

    return {
        "entry_id": entry["entry_id"],
        "organisation_name": entry["headword_raw"],
        "founded_raw": founded_raw,
        "founded_year": founded_year,
        "seat_raw": re.sub(r"\s+", " ", seat.group(1)).strip() if seat else "",
        "city": city.group(1) if city else "",
        "n_members_stated": re.sub(r"[.\s]", "", members.group(1)) if members else "",
        "purpose_raw": sections.get("but", "")[:600],
        "activities_raw": sections.get("travaux", "")[:600],
        "organisation_kinds": ";".join(kinds),
        "organisation_kind_primary": kinds[0] if kinds else "",
        "n_chars": entry["n_chars"],
        "page_first": entry["page_first"],
        "ocr_confidence": entry["ocr_confidence"],
    }


PLACE_IN_POSITION_RE = re.compile(r"\b[àa]\s+([A-ZÉÈÊÀÇÎÔ][\wà-ÿ'’\-]+(?:[\- ][A-ZÉÈÊÀÇÎÔ][\wà-ÿ'’\-]+){0,2})")


def career_rows(person: dict) -> list[dict]:
    """One row per post in the SUCCESS' rubric, in the order Lambert prints them.

    The rubric is a career sequence -- "secretaire a l'administration du college
    Sadiki, du 8 mars 1898 au 31 janv. 1907; administrateur du college Sadiki a
    partir du 1er fev. 1907" -- so the order carries information even when the
    dates do not parse.
    """
    raw = person["career_raw"]
    rows = []
    for i, chunk in enumerate(s.strip() for s in re.split(r";", raw)):
        if len(chunk) < 6:
            continue
        year = re.search(YEAR_RE, chunk)
        place = PLACE_IN_POSITION_RE.search(chunk)
        rows.append(
            {
                "entry_id": person["entry_id"],
                "surname": person["surname"],
                "position_order": i + 1,
                "position_raw": chunk[:300],
                "year_first_mentioned": year.group(0) if year else "",
                "place_mentioned": place.group(1) if place else "",
                "occupation_categories": ";".join(occupation_labels(chunk)),
            }
        )
    return rows


INSTITUTION_KINDS = [
    ("university_faculty", r"facult[ée]|universit[ée]"),
    ("grande_ecole", r"[ée]cole\s+(?:normale\s+sup|polytechnique|centrale|coloniale|des\s+mines|"
                     r"des\s+ponts|sup[ée]rieure|nationale)"),
    ("teacher_training", r"[ée]cole\s+normale"),
    ("secondary_lycee", r"lyc[ée]e"),
    ("secondary_college", r"coll[èe]ge"),
    ("islamic_institution", r"khaldounia|grande\s+mosqu[ée]e|zitouna|sadiki"),
    ("technical_school", r"[ée]cole\s+(?:d[’']agriculture|professionnelle|pratique|d[’']arts)"),
    ("institute", r"institut"),
]
INSTITUTION_RES = [(k, re.compile(p, re.IGNORECASE)) for k, p in INSTITUTION_KINDS]


def education_rows(person: dict) -> list[dict]:
    rows = []
    for inst in filter(None, person["education_institutions"].split(";")):
        kind = next((k for k, rx in INSTITUTION_RES if rx.search(inst)), "other")
        rows.append(
            {
                "entry_id": person["entry_id"],
                "surname": person["surname"],
                "institution": inst,
                "institution_kind": kind,
                "degrees": person["degrees"],
            }
        )
    return rows


# --------------------------------------------------------------------------
def write_csv(path: pathlib.Path, rows: list[dict], fields: list[str] | None = None) -> None:
    fields = fields or (list(rows[0].keys()) if rows else [])
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    entries = [json.loads(l) for l in (INTERIM / "entries.jsonl").open(encoding="utf-8")]

    rows, persons, places, orgs, decs = [], [], [], [], []
    for e in entries:
        etype, rule = classify(e)
        rows.append(
            {
                "entry_id": e["entry_id"],
                "headword": e["headword_raw"],
                "sort_key": e["sort_key"],
                "entry_type": etype,
                "classification_rule": rule,
                "segmentation_rule": e["accept_reason"],
                "page_first": e["page_first"],
                "page_last": e["page_last"],
                "view_first": e["view_first"],
                "view_last": e["view_last"],
                "n_chars": e["n_chars"],
                "n_paragraphs": e["n_paragraphs"],
                "n_portraits": e["n_portraits"],
                "ocr_confidence": e["ocr_confidence"],
                "page_url": PAGE_URL.format(view=e["view_first"]),
                "image_url": IIIF_URL.format(view=e["view_first"]),
                "text": e["text"],
            }
        )
        if etype == "person":
            persons.append(extract_person(e))
            for d in find_decorations(e["text"]):
                decs.append({"entry_id": e["entry_id"], "person": e["headword_raw"], **d})
        elif etype == "place":
            places.append(extract_place(e))
        elif etype == "organisation":
            orgs.append(extract_organisation(e))

    write_csv(PROCESSED / "entries.csv", rows)
    write_csv(PROCESSED / "persons.csv", persons)
    write_csv(PROCESSED / "places.csv", places)
    write_csv(PROCESSED / "organizations.csv", orgs)
    write_csv(PROCESSED / "decorations.csv", decs)
    careers = [r for p in persons for r in career_rows(p)]
    education = [r for p in persons for r in education_rows(p)]
    write_csv(PROCESSED / "career_positions.csv", careers)
    write_csv(PROCESSED / "education.csv", education)

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["entry_type"]] = counts.get(r["entry_type"], 0) + 1
    print(
        json.dumps(
            {
                "entries": len(rows),
                "by_type": counts,
                "decorations": len(decs),
                "career_positions": len(careers),
                "education_records": len(education),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
