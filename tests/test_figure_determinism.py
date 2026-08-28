"""Guards against figures whose captions change between rebuilds.

The figure outputs are committed, and the figure captions state facts about
named people. Two bugs of one class got through before this file existed, both
caused by ordering something by a set's iteration order:

- `fig28` drew its edges in hash order, so the PNG never reproduced and every
  rebuild produced a spurious diff;
- `fig32` picked "the broker holding fewest ties" with `min` over a *set*,
  which broke the tie between two four-tie brokers arbitrarily. The subtitle
  named Nestler on some runs and Vendel on others, asserting each as fact.

The second is the one that matters, so it is the one tested here. These tests
need neither matplotlib nor networkx: the ordering rule is deliberately plain
data manipulation over a dict, so it can be checked in the standard-library
test suite that CI already runs.
"""

from __future__ import annotations

import pathlib
import re
import sys
import unittest

FIGURES = pathlib.Path(__file__).resolve().parents[1] / "code" / "figures"
sys.path.insert(0, str(FIGURES))

import _networks as N  # noqa: E402


class TestRankingIsTotal(unittest.TestCase):
    """`ranked` must depend on the input values and nothing else."""

    def test_orders_by_score_descending(self):
        scores = {"b": 0.5, "a": 0.9, "c": 0.1}
        self.assertEqual(N.ranked(scores), ["a", "b", "c"])

    def test_breaks_ties_by_node_id_not_insertion_order(self):
        # The real case: two nodes scoring identically. Whichever order the
        # caller's dict happens to be built in, the answer must be the same.
        forwards = {"vendel": 0.089, "nestler": 0.089, "gounot": 0.161}
        backwards = {"nestler": 0.089, "vendel": 0.089, "gounot": 0.161}
        self.assertEqual(N.ranked(forwards), ["gounot", "nestler", "vendel"])
        self.assertEqual(N.ranked(forwards), N.ranked(backwards))

    def test_truncation_is_stable_across_a_tie_at_the_boundary(self):
        # A tie straddling the cut is the nastiest case: an unstable sort could
        # include a different node in the top N on different runs.
        scores = {"a": 1.0, "b": 0.5, "c": 0.5, "d": 0.5, "e": 0.1}
        self.assertEqual(N.ranked(scores, n=3), ["a", "b", "c"])
        for _ in range(50):
            self.assertEqual(N.ranked(dict(reversed(list(scores.items()))), n=3),
                             ["a", "b", "c"])

    def test_among_restricts_candidates_without_disturbing_the_order(self):
        scores = {"a": 0.9, "b": 0.5, "c": 0.1}
        self.assertEqual(N.ranked(scores, among=["c", "b"]), ["b", "c"])

    def test_accepts_a_set_of_candidates_and_still_orders_deterministically(self):
        # Callers may hand in a set; `ranked` must not inherit its disorder.
        scores = {"a": 0.5, "b": 0.5, "c": 0.5}
        self.assertEqual(N.ranked(scores, among={"c", "a", "b"}), ["a", "b", "c"])


class TestFiguresRouteRankingThroughTheHelper(unittest.TestCase):
    """A figure that re-implements the ordering inline can get it wrong again.

    This is a source check rather than a behavioural one, because the failure it
    prevents is a *new* figure sorting betweenness by hand and reintroducing the
    bug. Keeping the rule in one function is the fix; this keeps it there.
    """

    def figure_sources(self):
        for path in sorted(FIGURES.glob("fig*.py")):
            yield path, path.read_text(encoding="utf-8")

    def test_no_figure_sorts_betweenness_without_the_shared_helper(self):
        # Matches `sorted(..., key=lambda n: -betweenness[n])` and friends: a
        # sort keyed on a bare negated score, with no node id to break ties.
        inline_sort = re.compile(r"key=lambda\s+\w+:\s*-\s*\w*betweenness\w*\[")
        for path, source in self.figure_sources():
            with self.subTest(figure=path.name):
                self.assertIsNone(
                    inline_sort.search(source),
                    f"{path.name} ranks betweenness inline; use _networks.ranked "
                    "so ties break on the node id",
                )

    def test_no_figure_takes_a_min_or_max_over_a_set_literal(self):
        # `min(brokers, ...)` where brokers is a set was the fig. 32 bug.
        over_set = re.compile(r"\b(?:min|max)\(\s*set\(")
        for path, source in self.figure_sources():
            with self.subTest(figure=path.name):
                self.assertIsNone(over_set.search(source),
                                  f"{path.name} reduces over a set literal")

    # Named explicitly rather than detected. Computing betweenness is not the
    # risk -- fig. 25 takes a mean of it and never ranks anything, so it has no
    # ordering to get wrong. The risk is *selecting* nodes by it, which is what
    # these four do. A fifth figure that started ranking betweenness would be
    # caught by the inline-sort test above rather than by this list.
    RANKING_FIGURES = (
        "fig30_broker_affiliation_network.py",
        "fig31_broker_comembership_by_community.py",
        "fig32_degree_vs_betweenness.py",
        "fig33_broker_ego_networks.py",
    )

    def test_the_ranking_figures_use_the_helper(self):
        for name in self.RANKING_FIGURES:
            path = FIGURES / name
            with self.subTest(figure=name):
                self.assertTrue(path.exists(), f"{name} is missing")
                self.assertIn("N.ranked(", path.read_text(encoding="utf-8"),
                              f"{name} selects nodes by betweenness but does not "
                              "order them through _networks.ranked")


if __name__ == "__main__":
    unittest.main()
