"""Keeps docs/figures.md honest about what the figures actually say.

The index in `docs/figures.md` lists every figure with its claim. That claim is
supposed to be the title the figure carries when rendered, so a reader scanning
the index sees the findings rather than a list of chart types — and so nobody
has to open 33 PNGs to learn what is in them.

An index like that rots the moment a title is reworded, and silently: nothing
breaks, the document merely starts describing figures that no longer exist in
that form. Several titles were reworded during review in exactly this way, one
of them because the original overstated what its chart showed. This test makes
the index a checked claim rather than a remembered one.

Standard library only, so it runs on CI without the plotting dependencies.
"""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIGURES = ROOT / "code" / "figures"
INDEX = ROOT / "docs" / "figures.md"

# `S.titles(ax, "the claim", ...)` for most figures; fig. 33 draws small
# multiples and sets a suptitle instead.
TITLE_RE = re.compile(r'S\.titles\(\s*\w+,\s*\n?\s*"([^"]+)"')
SUPTITLE_RE = re.compile(r'suptitle\(\s*"([^"]+)"')
ROW_RE = re.compile(r"\|\s*\d+\s*\|\s*`(fig\d+_\w+)`\s*\|\s*([^|]+?)\s*\|")


def rendered_title(source: str) -> str | None:
    match = TITLE_RE.search(source) or SUPTITLE_RE.search(source)
    return match.group(1) if match else None


class TestFigureIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scripts = sorted(FIGURES.glob("fig*.py"))
        cls.titles = {p.stem: rendered_title(p.read_text(encoding="utf-8"))
                      for p in cls.scripts}
        cls.rows = ROW_RE.findall(INDEX.read_text(encoding="utf-8"))
        cls.indexed = dict(cls.rows)

    def test_every_figure_states_a_title(self):
        for name, title in self.titles.items():
            with self.subTest(figure=name):
                self.assertIsNotNone(
                    title, f"{name} has no title this test can find; if it sets "
                    "one another way, teach rendered_title about it")

    def test_every_figure_appears_in_the_index(self):
        for name in self.titles:
            with self.subTest(figure=name):
                self.assertIn(name, self.indexed,
                              f"{name} is not listed in docs/figures.md")

    def test_the_index_lists_no_figure_that_does_not_exist(self):
        for name in self.indexed:
            with self.subTest(figure=name):
                self.assertIn(name, self.titles,
                              f"docs/figures.md lists {name}, which has no script")

    def test_each_figure_is_listed_once(self):
        names = [name for name, _ in self.rows]
        duplicates = {n for n in names if names.count(n) > 1}
        self.assertEqual(duplicates, set(), f"listed more than once: {duplicates}")

    def test_the_index_claim_is_the_figure_s_own_title(self):
        for name, title in self.titles.items():
            if name not in self.indexed:
                continue  # reported by the coverage test above
            with self.subTest(figure=name):
                self.assertEqual(
                    self.indexed[name], title,
                    f"docs/figures.md describes {name} as its claim, but the "
                    "figure renders a different title; reword one to match")


if __name__ == "__main__":
    unittest.main()
