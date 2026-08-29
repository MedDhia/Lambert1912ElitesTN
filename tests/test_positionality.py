"""Integrity checks on the colonist/native coding.

Standard library only, so it runs on CI without the plotting dependencies.

Two of these tests exist because of bugs that reached committed figures. A
figure claimed natives brokered twice as much as colonists; the claim came from
two Europeans miscoded as Tunisian Muslims, one of them by a regex matching a
Tunis street name and the other by a merged entry. `test_no_european_birth_is`
`_coded_native_on_a_school_alone` and `test_merged_entries_are_not_placed_on`
`_institutional_evidence` pin both fixes.
"""

from __future__ import annotations

import collections
import csv
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

POSITIONS = {"colonist", "native", "unknown"}
COLONIST_DETAILS = {"metropolitan_colonist", "colony_born_colonist",
                    "colonist_unspecified"}
DETAILS = COLONIST_DETAILS | {
    "native_muslim", "native_jewish", "native_jewish_european_status", "unknown",
}
BASES = {"institutional", "birthplace", "reserved_post", "name", ""}


def read(name: str) -> list[dict]:
    with (PROCESSED / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class TestPositionality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = read("person_positionality.csv")
        cls.communities = {r["entry_id"]: r for r in read("person_communities.csv")}
        cls.persons = {r["entry_id"]: r for r in read("persons.csv")}

    def test_one_row_per_person(self):
        self.assertEqual(len(self.rows), len(self.persons))
        self.assertEqual(len({r["entry_id"] for r in self.rows}), len(self.rows))

    def test_values_are_from_the_documented_vocabularies(self):
        for row in self.rows:
            self.assertIn(row["positionality"], POSITIONS)
            self.assertIn(row["position_detail"], DETAILS)
            self.assertIn(row["position_basis"], BASES)

    def test_detail_agrees_with_positionality(self):
        for row in self.rows:
            with self.subTest(entry=row["entry_id"]):
                if row["positionality"] == "colonist":
                    self.assertIn(row["position_detail"], COLONIST_DETAILS)
                elif row["positionality"] == "native":
                    self.assertTrue(row["position_detail"].startswith("native"))
                else:
                    self.assertEqual(row["position_detail"], "unknown")

    def test_unplaced_rows_carry_no_basis_and_no_confidence(self):
        """A basis is what placed someone; an unplaced row has none.

        `birth_tunisia` is evidence the coder looked and found the birthplace
        uninformative, which is not the same as a basis, and counting it as one
        would overstate how far the coding reaches.
        """
        for row in self.rows:
            if row["positionality"] == "unknown":
                with self.subTest(entry=row["entry_id"]):
                    self.assertEqual(row["position_basis"], "")
                    self.assertEqual(row["confidence"], "")

    def test_placed_rows_all_carry_a_basis(self):
        for row in self.rows:
            if row["positionality"] != "unknown":
                with self.subTest(entry=row["entry_id"]):
                    self.assertNotEqual(row["position_basis"], "")

    def test_it_follows_the_community_coding_except_where_documented(self):
        """Positionality is a mapping of `community_group`, plus two rules.

        The only rows allowed to differ are those the reserved-post rule placed
        and those a merged entry unplaced.
        """
        mapping = {"european": "colonist", "tunisian": "native", "unknown": "unknown"}
        for row in self.rows:
            expected = mapping[self.communities[row["entry_id"]]["community_group"]]
            if row["positionality"] == expected:
                continue
            with self.subTest(entry=row["entry_id"]):
                self.assertTrue(
                    row["position_basis"] == "reserved_post"
                    or "merged_entry" in row["evidence"],
                    f"{row['entry_id']} diverges from the community coding without "
                    "either documented reason")

    def test_merged_entries_are_not_placed_on_institutional_evidence(self):
        """A merged entry carries the next person's institutions into this row."""
        for row in self.rows:
            if "merged_entry" in row["evidence"]:
                with self.subTest(entry=row["entry_id"]):
                    self.assertEqual(row["positionality"], "unknown")

    def test_no_european_birth_is_coded_native_on_a_school_alone(self):
        """A school can be a workplace; a birthplace outranks it.

        A professor born in Lyon who ran a laboratory at Sfax was coded a
        Tunisian Muslim because a school mention outvoted his French birth.
        """
        for row in self.rows:
            evidence = set(row["evidence"].split(";"))
            european_birth = {"birth_france", "birth_italy", "birth_malta"} & evidence
            if row["positionality"] == "native" and european_birth:
                with self.subTest(entry=row["entry_id"]):
                    self.assertTrue(
                        evidence & {"muslim_office", "jewish_institution",
                                    "member_of:muslim_body", "member_of:jewish_body"},
                        f"{row['entry_id']} is native despite a European birthplace, "
                        "on evidence weaker than an office or a communal body")

    def test_the_grana_keep_their_own_detail(self):
        """Jews with a European nationality stay findable rather than absorbed."""
        grana = [r for r in self.rows
                 if r["position_detail"] == "native_jewish_european_status"]
        for row in grana:
            self.assertEqual(row["positionality"], "native")
            self.assertIn(row["birth_context"], ("europe", "algeria"))
        self.assertTrue(grana, "the Grana case should still be reachable")

    def test_both_sides_have_enough_matched_people_to_compare(self):
        """Figs. 56 to 63 need both sides placed on the same kind of evidence."""
        matched = collections.Counter(
            r["positionality"] for r in self.rows
            if r["position_basis"] == "institutional")
        for side in ("colonist", "native"):
            self.assertGreaterEqual(matched[side], 30, f"too few matched {side}s")


if __name__ == "__main__":
    unittest.main()
