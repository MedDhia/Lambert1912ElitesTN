"""Integrity checks on the committed dataset in `data/processed/`.

These run without network access and without the ALTO cache, so CI can verify
what a user actually downloads. They check three things: that the tables join,
that coded values stay inside their documented domains, and that the volume's
own preface counts are still met.
"""

from __future__ import annotations

import csv
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"

ENTRY_TYPES = {"person", "place", "organisation", "topic", "cross_reference"}
RESOLUTIONS = {"resolved", "resolved_fuzzy", "ambiguous", "ambiguous_fuzzy", "unmatched"}
ROLES = {
    "president", "honorary_president", "past_president", "vice_president",
    "honorary_vice_president", "secretary", "secretary_general", "deputy_secretary",
    "treasurer", "deputy_treasurer", "assessor", "board_member", "councillor",
    "commissioner", "delegate", "director", "founder", "archivist_librarian",
    "honorary_member", "member", "corresponding_member", "auditor", "rapporteur",
}
TIE_SOURCES = {"organisation_entry_officer_list", "person_entry_statement"}
EDGE_TYPES = {"affiliation", "property_owner", "residence", "birthplace"}
NODE_TYPES = {
    "person_with_entry", "person_named_only", "organisation_with_entry",
    "organisation_named_only", "place_with_entry", "place_named_only",
}
PAGE_URL_RE = re.compile(r"^https://gallica\.bnf\.fr/ark:/12148/bpt6k5505300s/f\d+\.item$")


def load(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class DatasetTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = load("entries.csv")
        cls.persons = load("persons.csv")
        cls.places = load("places.csv")
        cls.orgs = load("organizations.csv")
        cls.entry_ids = {r["entry_id"] for r in cls.entries}


class TestEntries(DatasetTestCase):
    def test_entry_ids_are_unique(self):
        self.assertEqual(len(self.entry_ids), len(self.entries))

    def test_entry_types_are_in_the_documented_domain(self):
        self.assertLessEqual({r["entry_type"] for r in self.entries}, ENTRY_TYPES)

    def test_every_entry_is_locatable_on_the_source_page(self):
        for r in self.entries[:: max(1, len(self.entries) // 200)]:
            with self.subTest(entry=r["entry_id"]):
                self.assertRegex(r["page_url"], PAGE_URL_RE)
                self.assertIn(f"/f{r['view_first']}.item", r["page_url"])

    def test_entries_come_from_the_dictionary_proper(self):
        views = [int(r["view_first"]) for r in self.entries]
        self.assertGreaterEqual(min(views), 25)   # views 1-24 are front matter
        self.assertLessEqual(max(views), 492)     # 493-494 are endpapers

    def test_n_chars_matches_the_text(self):
        for r in self.entries[:: max(1, len(self.entries) // 200)]:
            with self.subTest(entry=r["entry_id"]):
                self.assertEqual(int(r["n_chars"]), len(r["text"]))

    def test_ocr_confidence_is_a_probability(self):
        for r in self.entries:
            if r["ocr_confidence"]:
                self.assertTrue(0.0 <= float(r["ocr_confidence"]) <= 1.0)


class TestPrefaceBenchmarks(DatasetTestCase):
    """Lambert states his own totals on pp. III-IV; they are the external check.

    Thresholds sit a little below the stated figures for places and societies,
    which the pipeline does not fully recover -- see the validation report. They
    are here to catch a regression, not to certify completeness.
    """

    def counts(self):
        out: dict[str, int] = {}
        for r in self.entries:
            out[r["entry_type"]] = out.get(r["entry_type"], 0) + 1
        return out

    def test_biographical_notices_meet_the_stated_minimum(self):
        self.assertGreaterEqual(self.counts().get("person", 0), 1300)

    def test_localities_within_ten_percent_of_the_stated_count(self):
        self.assertGreaterEqual(self.counts().get("place", 0), 675)

    def test_societies_within_fifteen_percent_of_the_stated_count(self):
        self.assertGreaterEqual(self.counts().get("organisation", 0), 148)

    def test_portrait_count_matches_the_stated_420(self):
        found = sum(int(r["n_portraits"]) for r in self.entries)
        self.assertTrue(400 <= found <= 445, f"{found} portraits located, expected ~420")


class TestTypedTables(DatasetTestCase):
    def test_typed_tables_join_to_entries_and_match_their_type(self):
        by_type = {r["entry_id"]: r["entry_type"] for r in self.entries}
        for rows, expected in (
            (self.persons, "person"), (self.places, "place"), (self.orgs, "organisation")
        ):
            for r in rows:
                with self.subTest(entry=r["entry_id"]):
                    self.assertEqual(by_type.get(r["entry_id"]), expected)

    def test_birth_years_are_plausible_or_absent(self):
        for r in self.persons:
            if r["birth_year"]:
                with self.subTest(entry=r["entry_id"]):
                    self.assertTrue(1600 <= int(r["birth_year"]) <= 1915)

    def test_flags_are_binary(self):
        for r in self.persons:
            for field in ("has_legion_honneur", "has_nichan_iftikhar",
                          "name_has_nasab_particle"):
                with self.subTest(entry=r["entry_id"], field=field):
                    self.assertIn(r[field], {"0", "1"})

    def test_honour_flags_agree_with_the_decoration_list(self):
        for r in self.persons:
            orders = set(filter(None, r["decoration_orders"].split(";")))
            with self.subTest(entry=r["entry_id"]):
                self.assertEqual(r["has_legion_honneur"] == "1", "legion_honneur" in orders)
                self.assertEqual(len(orders), int(r["n_decorations"]))

    def test_long_tables_join_to_persons(self):
        person_ids = {r["entry_id"] for r in self.persons}
        for name in ("decorations.csv", "career_positions.csv", "education.csv"):
            for r in load(name):
                with self.subTest(table=name, entry=r["entry_id"]):
                    self.assertIn(r["entry_id"], person_ids)

    def test_place_populations_are_numeric(self):
        for r in self.places:
            if r["population"]:
                with self.subTest(entry=r["entry_id"]):
                    self.assertTrue(r["population"].isdigit())


class TestNetwork(DatasetTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.nodes = load("network_nodes.csv")
        cls.edges = load("network_edges.csv")
        cls.node_ids = {r["node_id"] for r in cls.nodes}

    def test_node_ids_are_unique(self):
        self.assertEqual(len(self.node_ids), len(self.nodes))

    def test_node_types_are_in_the_documented_domain(self):
        self.assertLessEqual({r["node_type"] for r in self.nodes}, NODE_TYPES)

    def test_every_edge_endpoint_exists_in_the_node_table(self):
        for e in self.edges:
            with self.subTest(edge=(e["source"], e["target"])):
                self.assertIn(e["source"], self.node_ids)
                self.assertIn(e["target"], self.node_ids)

    def test_edge_types_and_roles_are_in_the_documented_domain(self):
        self.assertLessEqual({e["edge_type"] for e in self.edges}, EDGE_TYPES)
        affiliations = load("edges_person_organisation.csv")
        self.assertLessEqual({e["role"] for e in affiliations}, ROLES)
        self.assertLessEqual({e["tie_source"] for e in affiliations}, TIE_SOURCES)

    def test_resolution_is_recorded_and_never_silently_assigned(self):
        for r in load("mentions.csv"):
            with self.subTest(mention=r["mention_id"]):
                self.assertIn(r["resolution"], RESOLUTIONS)
                resolved = r["resolution"] in {"resolved", "resolved_fuzzy"}
                self.assertEqual(bool(r["person_entry_id"]), resolved)
                if r["resolution"].startswith("ambiguous"):
                    self.assertGreater(int(r["n_candidates"]), 1)

    def test_ties_carry_their_evidence(self):
        for name in ("edges_person_organisation.csv", "edges_person_place.csv"):
            for r in load(name):
                with self.subTest(table=name, person=r["person_node"]):
                    self.assertRegex(r["page_url"], PAGE_URL_RE)

    def test_co_membership_projection_is_a_simple_undirected_graph(self):
        seen: set[tuple[str, str]] = set()
        for e in load("edges_person_person.csv"):
            pair = (e["source"], e["target"])
            with self.subTest(pair=pair):
                self.assertNotEqual(e["source"], e["target"], "self-loop")
                self.assertLess(e["source"], e["target"], "pair not canonically ordered")
                self.assertNotIn(pair, seen, "duplicate edge")
                self.assertGreaterEqual(int(e["weight"]), 1)
                seen.add(pair)

    def test_people_with_a_notice_are_all_nodes(self):
        # Isolates included: non-membership has to be observable, not missing.
        for r in self.persons:
            with self.subTest(entry=r["entry_id"]):
                self.assertIn(r["entry_id"], self.node_ids)


if __name__ == "__main__":
    unittest.main()
