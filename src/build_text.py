"""Turn the cached ALTO OCR into an ordered, column-aware text stream.

Lambert's dictionary is set in two columns with a hanging *first-line indent*:
the first line of every headword entry sits a few points to the right of the
column's left margin. ALTO preserves those coordinates, so this stage keeps the
geometry (HPOS/VPOS, column id) that ``segment_entries.py`` needs, rather than
flattening everything to a plain string.

Also handled here:

* the ALTO files declare ``ISO-8859-1`` but are actually UTF-8;
* end-of-line hyphenation, where BnF's OCR stores the reconstructed word in
  ``SUBS_CONTENT`` on the first fragment and repeats it on the second;
* running heads (the page number and the three-letter alphabetical guide word).

Output: ``data/interim/lines.jsonl`` (one record per OCR line) and
``data/interim/reading_order.txt`` for eyeballing.
"""

from __future__ import annotations

import json
import pathlib
import re
import statistics
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
ALTO_DIR = ROOT / "data" / "raw" / "alto"
INTERIM = ROOT / "data" / "interim"

RUNNING_HEAD_MAX_VPOS = 360
# Running heads read "40 ATT — AUG" or "BRI — BRU 77": a folio number and the
# two alphabetical guide words for the page. The OCR mangles both the letters
# and the dash often enough that the pattern has to be generous.
GUIDE_PAIR_RE = re.compile(
    r"^\W{0,3}\d{0,3}\W{0,3}"
    r"([A-ZÉÈÊÀÇÔÏÎÛËÜÄÖ][A-Za-zÉÈÊÀÇÔÏÎÛËÜÄÖ.'’\-]{0,5})"
    r"\s*[—–\-■;:.,]{1,3}\s*"
    r"([A-ZÉÈÊÀÇÔÏÎÛËÜÄÖ][A-Za-zÉÈÊÀÇÔÏÎÛËÜÄÖ.'’\-]{0,5})"
    r"\W{0,3}\d{0,3}\W{0,2}$"
)
GUIDE_WORD_RE = re.compile(
    r"^\W{0,3}\d{0,3}\W{0,3}[A-ZÉÈÊÀÇÔÏÎÛËÜÄÖ][A-ZÉÈÊÀÇÔÏÎÛËÜÄÖ'’.\-]{1,5}\W{0,3}\d{0,3}\W{0,2}$"
)
PAGE_NO_RE = re.compile(r"^[0-9IVXLCivxlc\-—.' ]{1,8}$")


def running_head(text: str) -> str | None:
    """Return the guide word(s) if `text` is a running head, else None."""
    if PAGE_NO_RE.match(text):
        return ""
    m = GUIDE_PAIR_RE.match(text)
    if m:
        return f"{m.group(1)} — {m.group(2)}"
    if GUIDE_WORD_RE.match(text) and len(text) <= 12:
        return text.strip(" .0123456789'")
    return None


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def load_alto(path: pathlib.Path) -> ET.Element:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r'encoding="[^"]*"', 'encoding="utf-8"', text, count=1)
    return ET.fromstring(text)


def line_text(line: ET.Element) -> tuple[str, float]:
    """Reassemble a TextLine, resolving OCR hyphenation. Returns (text, mean WC)."""
    words: list[str] = []
    confs: list[float] = []
    for el in line:
        if local(el.tag) != "String":
            continue
        subs_type = el.get("SUBS_TYPE")
        if subs_type == "HypPart2":
            continue  # the full word was already emitted with HypPart1
        content = el.get("SUBS_CONTENT") if subs_type == "HypPart1" else el.get("CONTENT")
        if not content:
            continue
        words.append(content)
        try:
            confs.append(float(el.get("WC", "")))
        except ValueError:
            pass
    return " ".join(words), (sum(confs) / len(confs) if confs else float("nan"))


def gutter(blocks: list[dict], min_gap: int = 150) -> int | None:
    """Locate the gutter between the two text columns.

    Neither the page centre nor the widest gap between line starts is reliable.
    The scans are cropped unevenly, and illustrated entries wrap their text
    around a portrait in a *narrow inset* measure, which adds a third and fourth
    left edge to the page. So the columns are located from full-measure blocks
    only, and the narrow insets are then attached to whichever column contains
    them. Pages with a single measure (advertisements, the preface, plates) get
    ``None``.
    """
    if not blocks:
        return None
    widest = max(b["width"] for b in blocks)
    full = sorted(b["hpos"] for b in blocks if b["width"] >= 0.8 * widest)
    if len(full) < 2:
        return None
    gap, at = 0, None
    for a, b in zip(full, full[1:]):
        if b - a > gap:
            gap, at = b - a, (a + b) // 2
    return at if gap >= min_gap else None


def order_blocks(blocks: list[dict]) -> list[dict]:
    """Reading order inside one column.

    Sorting by vertical position handles the common case, including a narrow
    inset that continues below a portrait. Where two blocks genuinely sit side by
    side (text either side of an illustration) they overlap vertically, and the
    left-hand one is read first.
    """
    ordered = sorted(blocks, key=lambda b: (b["vpos"], b["hpos"]))
    out: list[dict] = []
    i = 0
    while i < len(ordered):
        cluster = [ordered[i]]
        i += 1
        while i < len(ordered):
            cand = ordered[i]
            bottom = min(b["vpos"] + b["height"] for b in cluster)
            overlap = bottom - cand["vpos"]
            shortest = min(min(b["height"] for b in cluster), cand["height"])
            if overlap > 0.4 * shortest:
                cluster.append(cand)
                i += 1
            else:
                break
        out.extend(sorted(cluster, key=lambda b: b["hpos"]))
    return out


def assign_columns(blocks: list[dict], split: int | None) -> None:
    """Attach every block to a column, insets included.

    A narrow inset does not belong to the side of the gutter its left edge falls
    on: an inset in the right half of the left column sits past a gutter
    estimated from full-measure blocks alone. It belongs to the column that
    physically contains it, so it is assigned by horizontal overlap instead.
    """
    if not blocks:
        return
    widest = max(b["width"] for b in blocks)
    for b in blocks:
        b["narrow"] = b["width"] < 0.6 * widest
        b["column"] = 0 if split is None or b["hpos"] < split else 1

    spans = {}
    for col in (0, 1):
        full = [b for b in blocks if b["column"] == col and not b["narrow"]]
        if full:
            spans[col] = (
                min(b["hpos"] for b in full),
                max(b["hpos"] + b["width"] for b in full),
            )
    if len(spans) != 2:
        return
    for b in (x for x in blocks if x["narrow"]):
        lo, hi = b["hpos"], b["hpos"] + b["width"]
        overlaps = {
            col: max(0, min(hi, s1) - max(lo, s0)) for col, (s0, s1) in spans.items()
        }
        best = max(overlaps, key=overlaps.get)
        if overlaps[best] > 0:
            b["column"] = best


def page_lines(root: ET.Element, view: int, heads: list[dict], illus: list[dict]) -> list[dict]:
    blocks: list[dict] = []
    plates = [
        {
            "view": view,
            "hpos": int(e.get("HPOS", 0)),
            "vpos": int(e.get("VPOS", 0)),
            "width": int(e.get("WIDTH", 0)),
            "height": int(e.get("HEIGHT", 0)),
        }
        for e in root.iter()
        if local(e.tag) == "Illustration"
    ]
    for block in root.iter():
        if local(block.tag) != "TextBlock":
            continue
        rows: list[dict] = []
        for line in block:
            if local(line.tag) != "TextLine":
                continue
            text, conf = line_text(line)
            text = text.strip()
            if not text:
                continue
            hpos, vpos = int(line.get("HPOS", 0)), int(line.get("VPOS", 0))
            rows.append(
                {
                    "view": view,
                    "hpos": hpos,
                    "vpos": vpos,
                    "wc": None if conf != conf else round(conf, 3),
                    "text": text,
                }
            )
        if rows:
            blocks.append(
                {
                    "hpos": int(block.get("HPOS", 0)),
                    "vpos": int(block.get("VPOS", 0)),
                    "width": int(block.get("WIDTH", 0)),
                    "height": int(block.get("HEIGHT", 0)),
                    "lines": rows,
                }
            )

    # Strip running heads: the folio number and the two alphabetical guide
    # words. Body text can sit as high as VPOS 287 on some views, so height
    # alone is not enough -- a head must also be among the topmost lines of the
    # page and match the head shape. The guide words are kept as page metadata
    # because they bound which headwords may legitimately appear on the page.
    all_lines = [r for b in blocks for r in b["lines"]]
    if all_lines:
        top = min(r["vpos"] for r in all_lines)
        for b in blocks:
            keep = []
            for r in b["lines"]:
                head = (
                    running_head(r["text"])
                    if r["vpos"] <= min(top + 45, RUNNING_HEAD_MAX_VPOS)
                    else None
                )
                if head is None:
                    keep.append(r)
                elif head:
                    heads.append({"view": view, "hpos": r["hpos"], "text": head})
            b["lines"] = keep
        blocks = [b for b in blocks if b["lines"]]

    split = gutter(blocks)
    assign_columns(blocks, split)

    # Portraits: the volume carries 420 photogravure portraits, and which entry
    # carries one is a usable measure of prominence. Assign each illustration to
    # a column now; `segment_entries.py` attaches it to the entry it sits in.
    for pl in plates:
        pl["column"] = 0 if split is None or pl["hpos"] < split else 1
        illus.append(pl)

    out: list[dict] = []
    for col in (0, 1):
        for b in order_blocks([x for x in blocks if x["column"] == col]):
            for rec in sorted(b["lines"], key=lambda r: r["vpos"]):
                rec["column"] = col
                rec["measure"] = "inset" if b["narrow"] else "main"
                out.append(rec)

    # First-line indent, measured against a *local* baseline. A single column
    # margin is unusable: the scans are skewed, so the left margin drifts by
    # 10-20 units down a column -- the same order as the indent itself. The
    # median of the nine surrounding lines in the same measure tracks the drift.
    for key in {(r["column"], r["measure"]) for r in out}:
        group = [r for r in out if (r["column"], r["measure"]) == key]
        for i, rec in enumerate(group):
            window = [
                x["hpos"] for j, x in enumerate(group) if j != i and abs(j - i) <= 4
            ]
            rec["indent"] = rec["hpos"] - (
                statistics.median(window) if window else rec["hpos"]
            )
    return out


def main() -> int:
    INTERIM.mkdir(parents=True, exist_ok=True)
    views = {
        v["view"]: v["label"]
        for v in json.loads((ROOT / "data" / "raw" / "views.json").read_text("utf-8"))
    }

    records: list[dict] = []
    heads: list[dict] = []
    illus: list[dict] = []
    for path in sorted(ALTO_DIR.glob("f*.xml")):
        view = int(path.stem.lstrip("f"))
        try:
            root = load_alto(path)
        except ET.ParseError as exc:
            print(f"  ! unparseable ALTO for view {view}: {exc}")
            continue
        for rec in page_lines(root, view, heads, illus):
            rec["page_label"] = views.get(view, "")
            records.append(rec)
    with (INTERIM / "illustrations.jsonl").open("w", encoding="utf-8") as fh:
        for rec in illus:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    (INTERIM / "guide_words.json").write_text(
        json.dumps(heads, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    with (INTERIM / "lines.jsonl").open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    with (INTERIM / "reading_order.txt").open("w", encoding="utf-8") as fh:
        last = None
        for rec in records:
            key = (rec["view"], rec["column"])
            if key != last:
                fh.write(f"\n===== view f{rec['view']} (p. {rec['page_label']}) col {rec['column']} =====\n")
                last = key
            fh.write(rec["text"] + "\n")

    print(json.dumps({"views_parsed": len({r['view'] for r in records}), "lines": len(records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
