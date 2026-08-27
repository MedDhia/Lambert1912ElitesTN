"""Segment the OCR line stream into dictionary entries.

Lambert sets every paragraph with a first-line indent, so an indent marks a
*paragraph*, not necessarily an entry: long entries on associations run to
several paragraphs. Distinguishing the two cases is what this stage does, using
the one structural property a dictionary guarantees -- alphabetical order:

1. **Anchors.** Personal-name headwords are set in capitals (``BOURGADE
   (Francois)``), which makes them recognisable without typography. Their sort
   keys must increase down the volume, so a longest non-decreasing subsequence
   over the candidate anchors yields a scaffold that is monotone by
   construction; garbled or spurious candidates fall out of it.
2. **Windows.** Every other indented paragraph is accepted as an entry only if
   its sort key falls between the last accepted headword and the next scaffold
   anchor. Organisation and place headwords ("Association sportive...",
   "Ateliers (Les)") sit inside that window; continuation paragraphs
   ("En 1900, elle a distribue...", "Tunis, rue d'Allemagne") do not, and are
   merged back into the entry above.
3. **Rubrics.** The volume's own in-entry labels -- ETUDES, SUCCESS',
   TRAVAUX, BUT -- are capitalised like surnames and are excluded explicitly.

Every decision is written to disk with the rule that produced it
(``accept_reason``), so segmentation can be audited rather than trusted.

Output: ``data/interim/entries.jsonl``.
"""

from __future__ import annotations

import json
import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"

# The dictionary proper: printed pages 1-468 == IIIF views 25-492. Views 1-24
# are front matter (advertisements and the preface) and 493-494 the endpapers.
BODY_FIRST_VIEW, BODY_LAST_VIEW = 25, 492
INDENT_THRESHOLD = 15

# Words that open a continuation paragraph but never a headword.
CONTINUATION_OPENERS = {
    "a", "au", "aux", "apres", "avant", "avec", "c", "ce", "ces", "cet", "cette",
    "ceux", "chaque", "comme", "d", "dans", "de", "depuis", "des", "du", "elle",
    "elles", "en", "enfin", "ensuite", "est", "et", "il", "ils", "j", "l", "la",
    "le", "les", "leur", "leurs", "lors", "lorsque", "mais", "me", "meme", "n",
    "ne", "nombreuses", "nombreux", "nos", "notre", "on", "or", "ou", "par",
    "pendant", "plus", "pour", "puis", "qu", "quand", "que", "qui", "quoique",
    "sa", "sans", "se", "selon", "ses", "si", "sous", "sur", "tous", "tout",
    "toute", "toutes", "un", "une", "voici", "voila", "y",
}

ROMAN_NUM_RE = re.compile(r"^[IVXLCDM]+$")

# In-entry rubric labels. Lambert prints these in capitals inside an entry, so
# they mimic a surname headword; the OCR variants are frequent enough to matter.
RUBRICS = {
    "ETUDES", "ETUDE", "TRAVAUX", "TIUVAUX", "TBAVAUX", "TEAVAUX", "IRAVAUX",
    "SUCCESSIVEMENT", "SUCCESSIVEM", "SUCCESS", "SUCCES", "SUCCESSIVE", "CESS",
    "BUT", "RUT", "HUT", "BUREAU", "OEUVRES", "OIUVKES", "OUVRAGES",
    "PUBLICATIONS", "HISTORIQUE", "CONSEIL", "MEMBRES", "DECORATIONS",
    "ARCH", "POPUL", "ENVIRONS", "ARMES", "ETRANGER", "COMMERCE",
}


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def sort_key(headword: str) -> str:
    """Normalise a headword to something comparable with `<`.

    Mirrors the volume's own filing practice: accents ignored, case ignored,
    punctuation dropped. OCR confusions between visually similar characters are
    *not* repaired here; the tolerance in `accept_start` absorbs them.
    """
    key = strip_accents(headword).upper()
    key = re.sub(r"[^A-Z ]+", "", key)
    return re.sub(r"\s+", " ", key).strip()


def split_headword(text: str) -> str:
    """Take the headword off the front of an entry's first paragraph.

    Person entries read ``BOURGADE (Francois). Pretre...`` and organisational or
    topical ones ``Association des Anciens Eleves..., 12 mai 1904``, so the
    headword ends at the first comma, sentence period, or opening parenthesis.
    """
    cut = len(text)
    for m in re.finditer(r"\s*\(|[,;:]|\.(?:\s|$)", text):
        if m.start() > 0:
            cut = m.start()
            break
    head = text[:cut].strip(" .,:;-—")
    return head


def is_plausible_headword(head: str) -> bool:
    if not head or len(head) > 90:
        return False
    letters = [c for c in head if c.isalpha()]
    if len(letters) < 2:
        return False
    if not head[0].isupper():
        return False
    first_token = re.split(r"[\s'’]", strip_accents(head).lower(), maxsplit=1)[0]
    if first_token in CONTINUATION_OPENERS:
        return False
    return True


def caps_ratio(head: str) -> float:
    letters = [c for c in strip_accents(head) if c.isalpha()]
    if not letters:
        return 0.0
    return sum(c.isupper() for c in letters) / len(letters)


def is_caps_surname(head: str, key: str) -> bool:
    """A capitalised personal-name headword: the anchor candidates."""
    first = key.split(" ")[0]
    return (
        caps_ratio(head) > 0.85
        and len(first) >= 3
        and first not in RUBRICS
        and not ROMAN_NUM_RE.match(first)
    )


def longest_nondecreasing(keys: list[str]) -> list[int]:
    """Indices of a longest non-decreasing subsequence (patience algorithm)."""
    import bisect

    tails: list[str] = []
    tails_idx: list[int] = []
    back: list[int | None] = [None] * len(keys)
    for i, k in enumerate(keys):
        j = bisect.bisect_right(tails, k)
        if j == len(tails):
            tails.append(k)
            tails_idx.append(i)
        else:
            tails[j] = k
            tails_idx[j] = i
        back[i] = tails_idx[j - 1] if j else None
    out: list[int] = []
    cur: int | None = tails_idx[-1] if tails_idx else None
    while cur is not None:
        out.append(cur)
        cur = back[cur]
    return out[::-1]


def cmp_key(key: str, width: int = 6) -> str:
    """Truncated sort key: absorbs OCR noise deep inside a long headword."""
    return key.replace(" ", "")[:width]


# Fallback headword shapes, for the few entry openings whose indent is lost to
# OCR noise: a capitalised surname followed by parenthesised forenames, and the
# place-entry opening "EL-HAFFEY. C. c. et caidat de Gafsa" (contro^le civil).
HEADWORD_SHAPES = (
    re.compile(r"^[.,;: ]*[A-ZÉÈÊÀÇÔÛ][A-ZÉÈÊÀÇÔÛ'’\- ]{2,40}\s*\([A-ZÉÈ]"),
    re.compile(r"^[.,;: ]*[A-ZÉÈÊÀÇÔÛ][A-ZÉÈÊÀÇÔÛ'’\- ]{2,40}\.\s*C\.\s*c\."),
)


def paragraphs(lines: list[dict]) -> list[list[dict]]:
    out: list[list[dict]] = []
    prev_text = ""
    for rec in lines:
        starts = rec["indent"] >= INDENT_THRESHOLD
        if not starts and prev_text.endswith((".", "!", "»")):
            starts = any(shape.match(rec["text"]) for shape in HEADWORD_SHAPES)
        if starts or not out:
            out.append([rec])
        else:
            out[-1].append(rec)
        prev_text = rec["text"]
    return out


def join_lines(lines: list[dict]) -> str:
    text = " ".join(rec["text"] for rec in lines)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def attach_illustrations(entries: list[dict]) -> None:
    """Attach each illustration to the entry whose text surrounds it.

    The volume advertises 420 photogravure portraits, and 436 of the 532
    illustrations in the dictionary proper have portrait proportions. Carrying
    one is a visible marker of standing, so it is worth recording per entry.
    """
    path = INTERIM / "illustrations.jsonl"
    if not path.exists():
        return
    plates = [json.loads(l) for l in path.open(encoding="utf-8")]
    by_col: dict[tuple[int, int], list[tuple[int, int, dict]]] = {}
    for e in entries:
        e["n_illustrations"] = 0
        e["n_portraits"] = 0
        for view, col, vmin, vmax in e["spans"]:
            by_col.setdefault((view, col), []).append((vmin, vmax, e))

    for pl in plates:
        if not (BODY_FIRST_VIEW <= pl["view"] <= BODY_LAST_VIEW):
            continue
        top, bottom = pl["vpos"], pl["vpos"] + pl["height"]
        cands = by_col.get((pl["view"], pl["column"]), [])
        if not cands:
            continue
        best = max(
            cands,
            key=lambda c: (min(c[1], bottom) - max(c[0], top), -abs(c[0] - top)),
        )
        entry = best[2]
        entry["n_illustrations"] += 1
        ratio = pl["width"] / max(pl["height"], 1)
        if 0.55 < ratio < 1.05 and pl["width"] < 600:
            entry["n_portraits"] += 1


def main() -> int:
    lines = [json.loads(l) for l in (INTERIM / "lines.jsonl").open(encoding="utf-8")]
    body = [r for r in lines if BODY_FIRST_VIEW <= r["view"] <= BODY_LAST_VIEW]

    paras = paragraphs(body)
    cand = []
    for para in paras:
        text = join_lines(para)
        head = split_headword(text)
        cand.append({"para": para, "text": text, "head": head, "key": sort_key(head)})

    # --- scaffold: monotone capitalised surname headwords -------------------
    anchor_idx = [
        i for i, c in enumerate(cand) if is_caps_surname(c["head"], c["key"])
    ]
    keep = longest_nondecreasing([cmp_key(cand[i]["key"]) for i in anchor_idx])
    scaffold = sorted(anchor_idx[k] for k in keep)
    is_anchor = set(scaffold)
    # next_anchor_key[i] = sort key of the first scaffold anchor at or after i
    next_key: list[str] = [""] * len(cand)
    nxt = "￿"
    for i in range(len(cand) - 1, -1, -1):
        next_key[i] = nxt
        if i in is_anchor:
            nxt = cmp_key(cand[i]["key"])

    entries: list[dict] = []
    rejects: dict[str, int] = {}
    rejected_examples: dict[str, list[str]] = {}
    last_key = ""
    for i, c in enumerate(cand):
        para, text, head, key = c["para"], c["text"], c["head"], c["key"]
        if i in is_anchor:
            accepted, reason = True, "anchor_surname"
        elif not is_plausible_headword(head) or key.split(" ")[0] in RUBRICS:
            accepted, reason = False, "implausible_headword"
        elif last_key <= cmp_key(key) and cmp_key(key, 4) <= cmp_key(next_key[i], 4):
            accepted, reason = True, "alphabetical_window"
        else:
            accepted, reason = False, "outside_alphabetical_window"
        if accepted or not entries:
            entries.append(
                {
                    "entry_id": f"L1912-{len(entries) + 1:05d}",
                    "headword_raw": head,
                    "sort_key": key,
                    "accept_reason": reason if accepted else "first_paragraph",
                    "view_first": para[0]["view"],
                    "page_first": para[0]["page_label"],
                    "view_last": para[-1]["view"],
                    "page_last": para[-1]["page_label"],
                    "spans": [
                        [
                            para[0]["view"],
                            para[0]["column"],
                            min(r["vpos"] for r in para),
                            max(r["vpos"] for r in para),
                        ]
                    ],
                    "n_paragraphs": 1,
                    "n_lines": len(para),
                    "ocr_confidences": [r["wc"] for r in para if r["wc"] is not None],
                    "text": text,
                }
            )
            if accepted:
                last_key = max(last_key, cmp_key(key))
        else:
            rejects[reason] = rejects.get(reason, 0) + 1
            rejected_examples.setdefault(reason, []).append(head[:60])
            prev = entries[-1]
            prev["text"] = f"{prev['text']} {text}".strip()
            prev["n_paragraphs"] += 1
            prev["n_lines"] += len(para)
            prev["ocr_confidences"] += [r["wc"] for r in para if r["wc"] is not None]
            prev["view_last"] = para[-1]["view"]
            prev["page_last"] = para[-1]["page_label"]
            prev["spans"].append(
                [
                    para[0]["view"],
                    para[0]["column"],
                    min(r["vpos"] for r in para),
                    max(r["vpos"] for r in para),
                ]
            )

    attach_illustrations(entries)

    for e in entries:
        confs = e.pop("ocr_confidences")
        e["ocr_confidence"] = round(sum(confs) / len(confs), 4) if confs else None
        e["n_chars"] = len(e["text"])

    with (INTERIM / "entries.jsonl").open("w", encoding="utf-8") as fh:
        for e in entries:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")

    reasons: dict[str, int] = {}
    for e in entries:
        reasons[e["accept_reason"]] = reasons.get(e["accept_reason"], 0) + 1
    print(
        json.dumps(
            {
                "paragraphs": len(cand),
                "entries": len(entries),
                "accept_reasons": reasons,
                "reject_reasons": rejects,
            },
            indent=2,
        )
    )
    (INTERIM / "segmentation_rejects.json").write_text(
        json.dumps(rejected_examples, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
