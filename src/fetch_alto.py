"""Download the BnF/Gallica ALTO OCR for Lambert (1912) and the IIIF manifest.

Source document
---------------
Paul Lambert, *Dictionnaire illustre de la Tunisie: choses et gens de Tunisie*
(Tunis: C. Saliba aine, 1912). Digitised by the Bibliotheque nationale de
France, ark:/12148/bpt6k5505300s, 494 views. Public domain.

The script uses two documented, openly reachable Gallica services:

  * ``/iiif/ark:/12148/<ark>/manifest.json``  -> view list and printed-page labels
  * ``/RequestDigitalElement?O=<ark>&E=ALTO&Deb=<view>`` -> per-view ALTO XML OCR

Downloads are cached on disk, so re-running is cheap and only fetches views that
are missing or that previously came back malformed.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

ARK = "bpt6k5505300s"
MANIFEST_URL = f"https://gallica.bnf.fr/iiif/ark:/12148/{ARK}/manifest.json"
ALTO_URL = "https://gallica.bnf.fr/RequestDigitalElement?O={ark}&E=ALTO&Deb={view}"
USER_AGENT = (
    "Lambert1912ElitesTN/1.0 (academic text-mining of a public-domain BnF volume; "
    "https://github.com/MedDhia/Lambert1912ElitesTN)"
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
ALTO_DIR = RAW / "alto"
# Committed, because it is a fact about the source rather than about whoever
# ran the download: the ALTO cache itself is git-ignored, so nothing downstream
# may infer coverage from whether it happens to be on disk.
MANIFEST_RECORD = ROOT / "data" / "processed" / "source_manifest.json"


def get(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def get_with_retries(url: str, attempts: int = 5) -> bytes:
    last: Exception | None = None
    for i in range(attempts):
        try:
            return get(url)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:  # noqa: PERF203
            last = exc
            time.sleep(2**i)
    raise RuntimeError(f"failed after {attempts} attempts: {url}") from last


def fetch_manifest() -> dict:
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / "manifest.json"
    if not path.exists():
        path.write_bytes(get_with_retries(MANIFEST_URL))
    return json.loads(path.read_text(encoding="utf-8"))


def view_labels(manifest: dict) -> list[dict]:
    """Return [{view: 1, label: '1'}, ...] mapping IIIF view number to page label."""
    out = []
    for canvas in manifest["sequences"][0]["canvases"]:
        view = int(canvas["@id"].rsplit("/f", 1)[1])
        out.append({"view": view, "label": canvas.get("label", "")})
    return sorted(out, key=lambda d: d["view"])


def looks_like_alto(blob: bytes) -> bool:
    head = blob[:2000].lower()
    return b"<alto" in head or b"<?xml" in head and b"alto" in head


def fetch_view(view: int, force: bool = False) -> tuple[int, str]:
    dest = ALTO_DIR / f"f{view:04d}.xml"
    if dest.exists() and not force and dest.stat().st_size > 0:
        if looks_like_alto(dest.read_bytes()):
            return view, "cached"
    blob = get_with_retries(ALTO_URL.format(ark=ARK, view=view))
    if not looks_like_alto(blob):
        # Gallica answers 404-as-HTML for views without an OCR layer (plates,
        # blank leaves). Record the gap rather than silently dropping it.
        (ALTO_DIR / f"f{view:04d}.missing").write_bytes(blob[:400])
        return view, "no-ocr"
    dest.write_bytes(blob)
    return view, "fetched"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workers", type=int, default=3, help="parallel downloads")
    ap.add_argument("--force", action="store_true", help="ignore the disk cache")
    ap.add_argument("--limit", type=int, default=0, help="stop after N views (testing)")
    args = ap.parse_args()

    ALTO_DIR.mkdir(parents=True, exist_ok=True)
    manifest = fetch_manifest()
    views = view_labels(manifest)
    (RAW / "views.json").write_text(json.dumps(views, indent=2), encoding="utf-8")
    todo = [v["view"] for v in views]
    if args.limit:
        todo = todo[: args.limit]

    counts = {"cached": 0, "fetched": 0, "no-ocr": 0, "failed": 0}
    failures: list[int] = []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch_view, v, args.force): v for v in todo}
        for done, fut in enumerate(cf.as_completed(futures), 1):
            try:
                view, status = fut.result()
            except RuntimeError as exc:
                # One unreachable view must not cost the other 493; the run is
                # resumable, so record it and let a later pass pick it up.
                counts["failed"] += 1
                failures.append(futures[fut])
                print(f"  ! {exc}", file=sys.stderr)
                continue
            counts[status] += 1
            if done % 25 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)} views  {counts}", file=sys.stderr, flush=True)

    with_ocr = len(list(ALTO_DIR.glob("f*.xml")))
    MANIFEST_RECORD.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_RECORD.write_text(
        json.dumps(
            {
                "ark": ARK,
                "source": f"https://gallica.bnf.fr/ark:/12148/{ARK}",
                "repository": "Bibliotheque nationale de France",
                "views_in_manifest": len(views),
                "views_with_alto_ocr": with_ocr,
                "views_without_alto_ocr": len(views) - with_ocr,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"views": len(todo), **counts, "failed_views": failures}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
