"""Unit tests for the standard-library centrality measures.

`graph_metrics.py` replaced networkx in the comparison stage, which had silently
broken the pipeline's no-dependencies promise. Replacing a well-tested library
with sixty lines of our own is only defensible if the replacements are checked,
so every expected value below is one that can be worked out by hand on a graph
small enough to draw, and each was confirmed against networkx before being
pinned here.

The tests themselves import nothing outside the standard library, so they run in
CI, which is the whole point of the rewrite.
"""

from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "code" / "pipeline"))

import graph_metrics as gm  # noqa: E402

PATH = [("A", "B"), ("B", "C")]
STAR = [("X", "a"), ("X", "b"), ("X", "c"), ("X", "d")]
TRIANGLE = [("A", "B"), ("B", "C"), ("C", "A")]
# Two triangles sharing the node C -- the classic cut vertex.
BOWTIE = [("A", "B"), ("B", "C"), ("C", "A"), ("C", "D"), ("D", "E"), ("E", "C")]
SQUARE_DIAGONAL = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"), ("A", "C")]


class TestAdjacency(unittest.TestCase):
    def test_builds_both_directions(self):
        graph = gm.adjacency(PATH)
        self.assertEqual(graph["A"], {"B"})
        self.assertEqual(graph["B"], {"A", "C"})

    def test_drops_self_loops(self):
        graph = gm.adjacency([("A", "A"), ("A", "B")])
        self.assertEqual(graph["A"], {"B"})

    def test_ignores_a_repeated_edge(self):
        self.assertEqual(gm.adjacency([("A", "B"), ("B", "A")])["A"], {"B"})


class TestComponents(unittest.TestCase):
    def test_splits_a_disconnected_graph(self):
        graph = gm.adjacency([("A", "B"), ("C", "D"), ("D", "E")])
        self.assertEqual(gm.components(graph), [{"C", "D", "E"}, {"A", "B"}])

    def test_giant_component_keeps_only_internal_edges(self):
        graph = gm.adjacency([("A", "B"), ("C", "D"), ("D", "E")])
        giant = gm.giant_component(graph)
        self.assertEqual(set(giant), {"C", "D", "E"})
        self.assertEqual(giant["D"], {"C", "E"})

    def test_equal_sized_components_break_ties_on_their_least_member(self):
        # Two components of size two: the order must not depend on set order.
        graph = gm.adjacency([("Y", "Z"), ("A", "B")])
        self.assertEqual(gm.components(graph), [{"A", "B"}, {"Y", "Z"}])

    def test_empty_graph(self):
        self.assertEqual(gm.giant_component({}), {})


class TestBetweenness(unittest.TestCase):
    """Normalised as networkx does: scaled by 1/((n-1)(n-2))."""

    def test_middle_of_a_path_carries_every_route(self):
        result = gm.betweenness(gm.adjacency(PATH))
        self.assertAlmostEqual(result["B"], 1.0)
        self.assertAlmostEqual(result["A"], 0.0)
        self.assertAlmostEqual(result["C"], 0.0)

    def test_star_centre_carries_every_route(self):
        result = gm.betweenness(gm.adjacency(STAR))
        self.assertAlmostEqual(result["X"], 1.0)
        self.assertAlmostEqual(result["a"], 0.0)

    def test_a_clique_has_no_brokers(self):
        for value in gm.betweenness(gm.adjacency(TRIANGLE)).values():
            self.assertAlmostEqual(value, 0.0)

    def test_cut_vertex_of_a_bowtie(self):
        result = gm.betweenness(gm.adjacency(BOWTIE))
        self.assertAlmostEqual(result["C"], 2 / 3)
        for node in ("A", "B", "D", "E"):
            self.assertAlmostEqual(result[node], 0.0)

    def test_ties_are_split_between_equal_paths(self):
        # A and C each lie on one of the two shortest B-D routes.
        result = gm.betweenness(gm.adjacency(SQUARE_DIAGONAL))
        self.assertAlmostEqual(result["A"], 1 / 6)
        self.assertAlmostEqual(result["C"], 1 / 6)
        self.assertAlmostEqual(result["B"], 0.0)

    def test_graphs_too_small_to_broker(self):
        self.assertEqual(gm.betweenness(gm.adjacency([("A", "B")])),
                         {"A": 0.0, "B": 0.0})


class TestCloseness(unittest.TestCase):
    def test_path(self):
        result = gm.closeness(gm.adjacency(PATH))
        self.assertAlmostEqual(result["B"], 1.0)
        self.assertAlmostEqual(result["A"], 2 / 3)

    def test_star(self):
        result = gm.closeness(gm.adjacency(STAR))
        self.assertAlmostEqual(result["X"], 1.0)
        self.assertAlmostEqual(result["a"], 4 / 7)

    def test_clique_is_maximally_close(self):
        for value in gm.closeness(gm.adjacency(TRIANGLE)).values():
            self.assertAlmostEqual(value, 1.0)

    def test_square_with_a_diagonal(self):
        result = gm.closeness(gm.adjacency(SQUARE_DIAGONAL))
        self.assertAlmostEqual(result["A"], 1.0)
        self.assertAlmostEqual(result["B"], 0.75)


class TestClustering(unittest.TestCase):
    def test_a_triangle_is_fully_clustered(self):
        for value in gm.clustering(gm.adjacency(TRIANGLE)).values():
            self.assertAlmostEqual(value, 1.0)

    def test_a_path_has_none(self):
        for value in gm.clustering(gm.adjacency(PATH)).values():
            self.assertAlmostEqual(value, 0.0)

    def test_bowtie_centre_sees_one_of_its_six_pairs_tied(self):
        result = gm.clustering(gm.adjacency(BOWTIE))
        self.assertAlmostEqual(result["C"], 1 / 3)
        self.assertAlmostEqual(result["A"], 1.0)

    def test_square_with_a_diagonal(self):
        result = gm.clustering(gm.adjacency(SQUARE_DIAGONAL))
        self.assertAlmostEqual(result["A"], 2 / 3)
        self.assertAlmostEqual(result["B"], 1.0)

    def test_a_node_with_one_neighbour_is_undefined_and_reported_as_zero(self):
        self.assertEqual(gm.clustering(gm.adjacency([("A", "B")])),
                         {"A": 0.0, "B": 0.0})


class TestOrderIndependence(unittest.TestCase):
    """Results must not depend on the order the edges arrived in."""

    def test_same_scores_however_the_graph_was_built(self):
        forwards = gm.adjacency(BOWTIE)
        backwards = gm.adjacency(list(reversed([(b, a) for a, b in BOWTIE])))
        for measure in (gm.betweenness, gm.closeness, gm.clustering):
            with self.subTest(measure=measure.__name__):
                self.assertEqual(measure(forwards), measure(backwards))


if __name__ == "__main__":
    unittest.main()
