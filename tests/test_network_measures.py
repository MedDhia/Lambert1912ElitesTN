"""Integrity checks on the exported network measures.

`person_network_measures.csv` states each person's position in the two networks.
Every value in it is derived, so the checks below are about the derivation being
faithful to the edge lists it came from rather than about the volume: the rows
must be exactly the person nodes those edge lists contain, the degrees must be
the degrees, and the giant-component flags must agree with the component sizes.

The one distinction worth guarding deliberately is blank versus zero. A person
with no co-membership tie has no betweenness; that is not the same claim as a
betweenness of zero, and the file must not collapse the two.
"""

from __future__ import annotations

import collections
import csv
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"


def load(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class NetworkMeasuresTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load("person_network_measures.csv")
        cls.by_node = {r["node_id"]: r for r in cls.rows}
        cls.affiliation = load("edges_person_organisation.csv")
        cls.comembership = load("edges_person_person.csv")
        cls.persons = {p["entry_id"] for p in load("persons.csv")}


class TestCoverage(NetworkMeasuresTestCase):
    def test_one_row_per_person_node_in_either_network(self):
        expected = ({t["person_node"] for t in self.affiliation}
                    | {n for t in self.comembership for n in (t["source"], t["target"])})
        self.assertEqual(set(self.by_node), expected)

    def test_node_ids_are_unique(self):
        counts = collections.Counter(r["node_id"] for r in self.rows)
        self.assertEqual([n for n, c in counts.items() if c > 1], [])

    def test_entry_id_is_present_exactly_when_the_person_has_a_notice(self):
        for row in self.rows:
            with self.subTest(node=row["node_id"]):
                if row["has_notice"] == "1":
                    self.assertIn(row["entry_id"], self.persons)
                else:
                    self.assertEqual(row["entry_id"], "")

    def test_every_entry_id_joins_to_persons(self):
        for row in self.rows:
            if row["entry_id"]:
                self.assertIn(row["entry_id"], self.persons)


class TestDegreesMatchTheEdgeLists(NetworkMeasuresTestCase):
    def test_affiliation_degree_is_the_number_of_distinct_bodies(self):
        bodies = collections.defaultdict(set)
        for tie in self.affiliation:
            bodies[tie["person_node"]].add(tie["organisation_node"])
        for node, expected in bodies.items():
            with self.subTest(node=node):
                self.assertEqual(int(self.by_node[node]["affil_degree"]), len(expected))

    def test_comembership_degree_is_the_number_of_distinct_partners(self):
        partners = collections.defaultdict(set)
        for tie in self.comembership:
            partners[tie["source"]].add(tie["target"])
            partners[tie["target"]].add(tie["source"])
        for node, expected in partners.items():
            with self.subTest(node=node):
                self.assertEqual(int(self.by_node[node]["comem_degree"]), len(expected))


class TestValuesAreInRange(NetworkMeasuresTestCase):
    BOUNDED = ("affil_betweenness", "affil_closeness",
               "comem_betweenness", "comem_closeness", "comem_clustering")

    def test_normalised_measures_lie_between_zero_and_one(self):
        for row in self.rows:
            for column in self.BOUNDED:
                if row[column] == "":
                    continue
                with self.subTest(node=row["node_id"], column=column):
                    self.assertGreaterEqual(float(row[column]), 0.0)
                    self.assertLessEqual(float(row[column]), 1.0)

    def test_degree_is_below_its_component_size(self):
        for row in self.rows:
            for prefix in ("affil", "comem"):
                if row[f"{prefix}_degree"] == "":
                    continue
                with self.subTest(node=row["node_id"], network=prefix):
                    self.assertLess(int(row[f"{prefix}_degree"]),
                                    int(row[f"{prefix}_component_size"]))


class TestComponents(NetworkMeasuresTestCase):
    def test_the_giant_flag_marks_exactly_the_largest_component(self):
        for prefix in ("affil", "comem"):
            sizes = [int(r[f"{prefix}_component_size"]) for r in self.rows
                     if r[f"{prefix}_component_size"] != ""]
            largest = max(sizes)
            for row in self.rows:
                if row[f"{prefix}_component_size"] == "":
                    continue
                with self.subTest(node=row["node_id"], network=prefix):
                    self.assertEqual(
                        row[f"{prefix}_in_giant"] == "1",
                        int(row[f"{prefix}_component_size"]) == largest)

    def test_a_node_alone_with_one_partner_brokers_nothing(self):
        # A two-node component has no paths to sit on; the value must be a real
        # zero rather than a blank, because the node *is* in the network.
        pairs = [r for r in self.rows if r["comem_component_size"] == "2"]
        for row in pairs:
            with self.subTest(node=row["node_id"]):
                self.assertEqual(float(row["comem_betweenness"]), 0.0)


class TestAbsenceIsBlankNotZero(NetworkMeasuresTestCase):
    """A person absent from a network has no score, which is not a score of 0."""

    def test_rows_absent_from_co_membership_are_blank_across_every_column(self):
        in_projection = {n for t in self.comembership for n in (t["source"], t["target"])}
        absent = [r for r in self.rows if r["node_id"] not in in_projection]
        self.assertTrue(absent, "expected some people to have no co-membership tie")
        for row in absent:
            with self.subTest(node=row["node_id"]):
                for column in ("comem_degree", "comem_component_size", "comem_in_giant",
                               "comem_betweenness", "comem_closeness", "comem_clustering"):
                    self.assertEqual(row[column], "")

    def test_a_present_node_never_has_a_blank_measure(self):
        for row in self.rows:
            for prefix in ("affil", "comem"):
                if row[f"{prefix}_degree"] == "":
                    continue
                with self.subTest(node=row["node_id"], network=prefix):
                    self.assertNotEqual(row[f"{prefix}_betweenness"], "")
                    self.assertNotEqual(row[f"{prefix}_closeness"], "")


if __name__ == "__main__":
    unittest.main()
