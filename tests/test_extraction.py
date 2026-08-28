"""Unit tests for the parsing rules, pinned to cases the OCR actually produces.

Each case below is a real string from the volume that broke an earlier version
of the pipeline. They are here so the fix cannot be undone silently.
"""

from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "code" / "pipeline"))

import build_networks as bn  # noqa: E402
import build_text as bt  # noqa: E402
import extract_records as er  # noqa: E402
import segment_entries as se  # noqa: E402


class TestYearRepair(unittest.TestCase):
    """The OCR reads 8 as S, 0 as O, 6 as C/G, and sprinkles stray periods."""

    def test_repairs_digit_confusions(self):
        self.assertEqual(er.clean_year("1S76"), "1876")
        self.assertEqual(er.clean_year("1SS2"), "1882")
        self.assertEqual(er.clean_year("1.870"), "1870")
        self.assertEqual(er.clean_year("1SC0"), "1860")

    def test_rejects_years_with_a_dropped_character(self):
        # "9 avril 1.8(i6" is 1866; closing the gap would silently yield 1816.
        self.assertEqual(er.clean_year("1.8(i6"), "")
        self.assertEqual(er.clean_year("18(34"), "")

    def test_rejects_impossible_years(self):
        self.assertEqual(er.clean_year("1999"), "")   # after publication
        self.assertEqual(er.clean_year("1200"), "")   # before the range
        self.assertEqual(er.clean_year("187"), "")    # too short

    def test_birth_date_is_taken_from_beside_the_forenames(self):
        # AUBERT has no birth date; "1899" is the year he settled in Tunisia and
        # must not be read as a birth year.
        entry = {
            "entry_id": "L1912-00000",
            "headword_raw": "AUBERT",
            "text": (
                "AUBERT (Godefroy), Paris, Médaille militaire; Croix de Guadalupe "
                "(Mexique). Rentier, 8, rue de Hollande, Tunis. 1899. Ancien..."
            ),
            "n_chars": 150,
            "n_portraits": 0,
            "page_first": "40",
            "ocr_confidence": 0.9,
        }
        self.assertEqual(er.extract_person(entry)["birth_year"], "")


class TestHonours(unittest.TestCase):
    def test_matches_mangled_order_names(self):
        cases = {
            "chev. de la Légion d'honn-, Médaille coloniale": "legion_honneur",
            "comm. do la. Lésion d'honneur": "legion_honneur",
            "off. du Nichan-Iflikliar": "nichan_iftikhar",
            "off. du Nichan-lftikhar": "nichan_iftikhar",
            "chev. du Mérite agricole": "merite_agricole",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                orders = {d["order"] for d in er.find_decorations(text)}
                self.assertIn(expected, orders)

    def test_does_not_read_the_abbreviation_off_as_the_order_of_saint_olaf(self):
        for text in ("olf. du Nichan-Iftikhar", "ol'f. d'Académie", "off. d'Académie"):
            with self.subTest(text=text):
                orders = {d["order"] for d in er.find_decorations(text)}
                self.assertNotIn("saint_olaf", orders)

    def test_distinguishes_the_three_beylical_orders(self):
        self.assertIn(
            "nichan_el_abed",
            {d["order"] for d in er.find_decorations("grand cordon du Nichan el-Abed")},
        )
        self.assertIn(
            "nichan_iftikhar",
            {d["order"] for d in er.find_decorations("off. du Nichan-Iftikhar")},
        )

    def test_reads_the_grade_that_precedes_the_order(self):
        found = {d["order"]: d["grade"] for d in er.find_decorations(
            "gr. off. du Nichan-Iftikhar, chev. de la Légion d'honneur"
        )}
        self.assertEqual(found["nichan_iftikhar"], "grand_officier")
        self.assertEqual(found["legion_honneur"], "chevalier")


class TestClassification(unittest.TestCase):
    def entry(self, text, head, chars=200):
        return {
            "headword_raw": head, "text": text, "n_chars": chars,
            "n_portraits": 0, "page_first": "1", "ocr_confidence": 0.9,
        }

    def test_administrative_formula_marks_a_place(self):
        e = self.entry("MELLITA. C. c. de Gabès, ann. de Djerba, caïdat de l'Arad.", "MELLITA")
        self.assertEqual(er.classify(e)[0], "place")

    def test_a_place_qualifier_in_parentheses_is_not_forenames(self):
        e = self.entry(
            "SIDI-TABET (Domaine cle). C. c. de Tunis, caïdat cle la banlieue. Haras.",
            "SIDI-TABET",
        )
        self.assertEqual(er.classify(e)[0], "place")

    def test_working_for_the_controle_civil_does_not_make_a_person_a_place(self):
        e = self.entry(
            "BREIEAN (Paul-Auguste-René). 26 avril 1884, Paris. Secrétaire cle "
            "Contrôle civil, 44 (bis), avenue de Paris, Tunis.",
            "BREIEAN",
        )
        self.assertEqual(er.classify(e)[0], "person")

    def test_a_parenthesised_qualifier_does_not_make_a_society_a_person(self):
        e = self.entry(
            "Association sténo graphique unitaire (méthode Prévost-Delaunay). "
            "20 octobre 1897. Groupe de Tunis. BUT : vulgariser la sténographie. "
            "19 membres.",
            "Association sténo graphique unitaire",
        )
        self.assertEqual(er.classify(e)[0], "organisation")

    def test_initials_count_as_forenames(self):
        e = self.entry(
            "MUSCAT fils (C), mai 1866, Tunis. Entrepreneur de charpente.",
            "MUSCAT fils",
        )
        self.assertEqual(er.classify(e)[0], "person")


class TestSegmentation(unittest.TestCase):
    def test_longest_nondecreasing_keeps_the_monotone_run(self):
        keys = ["ABADIE", "ABBAS", "ZZZZ", "ABDELLI", "ABEASIS"]
        kept = [keys[i] for i in se.longest_nondecreasing(keys)]
        self.assertEqual(kept, ["ABADIE", "ABBAS", "ABDELLI", "ABEASIS"])

    def test_sort_key_ignores_accents_case_and_punctuation(self):
        self.assertEqual(se.sort_key("Béja-el-Kébir"), "BEJAELKEBIR")

    def test_headword_stops_at_the_first_delimiter(self):
        self.assertEqual(
            se.split_headword("ASTOIN-SIELGE (Joseph-Charles). Vice-consul de France"),
            "ASTOIN-SIELGE",
        )
        self.assertEqual(
            se.split_headword("Association générale des Etudiants de Tunisie, 21 janv. 1907."),
            "Association générale des Etudiants de Tunisie",
        )

    def test_rubric_labels_are_not_headwords(self):
        for rubric in ("ETUDES", "TRAVAUX", "SUCCESS", "BUT"):
            with self.subTest(rubric=rubric):
                self.assertTrue(se.is_caps_surname(rubric, rubric) is False)

    def test_continuation_openers_are_rejected(self):
        self.assertFalse(se.is_plausible_headword("En 1900, elle a distribué"))
        self.assertTrue(se.is_plausible_headword("Association Amicale"))


class TestLayout(unittest.TestCase):
    def page(self):
        """A page with columns at 250 and 957 and an inset wrapping a portrait
        in the right half of the *left* column -- the layout of view f25."""
        return [
            {"hpos": 250, "width": 653}, {"hpos": 262, "width": 657},
            {"hpos": 660, "width": 243},  # the inset
            {"hpos": 957, "width": 661}, {"hpos": 968, "width": 653},
        ]

    def test_gutter_ignores_narrow_insets(self):
        self.assertIsNotNone(bt.gutter(self.page()))

    def test_inset_is_assigned_to_the_column_that_contains_it(self):
        blocks = self.page()
        bt.assign_columns(blocks, bt.gutter(blocks))
        by_hpos = {b["hpos"]: b["column"] for b in blocks}
        self.assertEqual(by_hpos[660], 0, "inset must join the left column")
        self.assertEqual(by_hpos[250], 0)
        self.assertEqual(by_hpos[957], 1)

    def test_single_measure_pages_are_one_column(self):
        self.assertIsNone(bt.gutter([{"hpos": 250, "width": 1400}] * 8))

    def test_side_by_side_blocks_are_read_left_to_right(self):
        blocks = [
            {"hpos": 900, "vpos": 500, "height": 300},
            {"hpos": 250, "vpos": 505, "height": 300},
            {"hpos": 250, "vpos": 900, "height": 200},
        ]
        order = [(b["hpos"], b["vpos"]) for b in bt.order_blocks(blocks)]
        self.assertEqual(order, [(250, 505), (900, 500), (250, 900)])

    def test_running_heads_are_recognised_including_ocr_damage(self):
        for head in ("40 ATT — AUG", "BRI — BRU 77", "EL-H — ELL", "GAZ- — GËR"):
            with self.subTest(head=head):
                self.assertIsNotNone(bt.running_head(head))
        self.assertIsNone(bt.running_head("Association générale des Etudiants de"))


class TestNameParsing(unittest.TestCase):
    def test_strips_titles_and_business_names(self):
        self.assertEqual(bn.clean_name("M. Gustave Rolland"), "Gustave Rolland")
        self.assertEqual(bn.clean_name("MM. le D' Untel"), "Untel")
        self.assertEqual(bn.clean_name("Waldispul (Grand-Hôtel)"), "Waldispul")
        self.assertEqual(bn.clean_name("BUREAU : MM. Florian Ducurtil"), "Florian Ducurtil")

    def test_institutions_are_not_people(self):
        for text in ("la Municipalité", "Conférence Consultative", "le Gouvernement"):
            with self.subTest(text=text):
                self.assertEqual(bn.clean_name(text), "")

    def test_splits_a_plural_role_into_its_members(self):
        names = bn.split_names("MM. Courtade, L. Blanc, Girod et Verry")
        # Trailing periods are stripped; `name_key` ignores punctuation anyway.
        self.assertEqual(names, ["Courtade", "L Blanc", "Girod", "Verry"])

    def test_officer_lists_parse_in_both_printed_orders(self):
        found = dict((role, name) for role, name, _ in bn.officer_mentions(
            "Prés., M. Marcille; v.-prés., M. Brou; Vilatte L.-E., trés."
        ))
        self.assertEqual(found.get("president"), "Marcille")
        self.assertEqual(found.get("vice_president"), "Brou")
        self.assertEqual(bn.name_key(found.get("treasurer", "")), "VILATTE L E")

    def test_edit_distance_bound(self):
        self.assertTrue(bn.edit_distance_at_most_one("MAZIERE", "MAZIERES"))
        self.assertFalse(bn.edit_distance_at_most_one("BLANC", "BLAIVE"))

    def test_organisation_variants_merge_only_on_shared_distinctive_tokens(self):
        canon = bn.canonicalise_orgs([
            "institut de carthage",
            "institut de carthage section scientifique",
            "comite des fetes",
            "societe de geographie",
        ])
        self.assertEqual(
            canon["institut de carthage"], "institut de carthage section scientifique"
        )
        # One shared distinctive token is not evidence of the same body, so
        # these stay separate nodes.
        self.assertEqual(canon["comite des fetes"], "comite des fetes")
        self.assertEqual(canon["societe de geographie"], "societe de geographie")


if __name__ == "__main__":
    unittest.main()
