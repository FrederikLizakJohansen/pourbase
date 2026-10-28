"""Whole-database representation checks and realistic malformed imports."""

from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest

from support import ROOT
import pourbase as pb

sys.path.insert(0, str(ROOT / "scripts"))
from audit_database_representation import audit_database, formula_counts  # noqa: E402


class DatabaseRepresentationTests(unittest.TestCase):
    def test_all_species_and_observations_follow_the_field_contract(self):
        report = audit_database(ROOT / "src/pourbase/data/pourbase.sqlite")
        self.assertEqual(report["species_checked"], 1771)
        self.assertEqual(report["errors"], 0, report["findings"])
        self.assertEqual(len(report["species"]), report["counts"]["species"])

    def test_fractional_hydrates_and_nested_groups_keep_complete_formula_units(self):
        self.assertEqual(formula_counts("CaSO4(H2O)0.5"), {"Ca": 1, "S": 1, "O": 4.5, "H": 1})
        counts = formula_counts("(AlAlO3)[Ca3O3(SiO2)0.84(H2O)4.32]")
        self.assertEqual(counts["Al"], 2)
        self.assertAlmostEqual(sum(counts.values()), 26.48)
        self.assertEqual(formula_counts("Ca4Al2(OH)12N2O6(H2O)4")["N"], 2)

    def test_unbalanced_groups_and_native_oxidation_annotations_are_rejected(self):
        for formula in ("Ca4Al2(OH)12N|5|2O6(H2O)4", "Fe(OH", "Fe)OH(", "Fe[]", "2Fe", "Fe0O"):
            with self.subTest(formula=formula), self.assertRaises(ValueError):
                formula_counts(formula)

    def test_ageing_and_model_limits_stay_visible_outside_the_phase_label(self):
        aged, amorphous = pb.ThermodynamicDatabase.bundled().species_records(
            ("r09-al-alohmic", "r09-al-aloham"))
        self.assertEqual(aged.phase_detail, "microcrystalline aluminium hydroxide")
        self.assertEqual(aged.phase_identity.identified_phase, aged.phase_detail)
        self.assertIn("19-month", aged.phase_identity.evidence_summary)
        self.assertIn("5 to 60 C", aged.phase_identity.notes)
        self.assertTrue(any("19-month" in warning.message and "60 C" in warning.message
                            for warning in aged.warnings))
        self.assertEqual(amorphous.phase_detail, "amorphous aluminium hydroxide")
        self.assertIn("early-age", amorphous.phase_identity.evidence_summary)
        self.assertNotEqual(aged.record_id, amorphous.record_id)

    def test_import_errors_are_detected_without_rewriting_the_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.sqlite"
            shutil.copyfile(ROOT / "src/pourbase/data/pourbase.sqlite", path)
            with sqlite3.connect(path) as connection:
                connection.execute("UPDATE species SET atom_count=3 WHERE record_id='gfe-sn-sn-q+0-solid-metal'")
                connection.execute("UPDATE species SET phase='crystalline' WHERE record_id='gfe-fe-fe-q+0-solid-metal'")
                connection.execute("UPDATE reported_thermochemistry SET unit='kJ/mol' "
                                   "WHERE value_id='gfe-sn-sn-q+0-solid-metal:gf:preferred'")
                connection.execute("UPDATE sources SET locator='{} trailing prose' "
                                   "WHERE source_id='IUPAC_Gold_Book_R05233'")
            before = path.read_bytes()
            report = audit_database(path)
            fields = {(row["table"], row["field"]) for row in report["findings"]}
            self.assertTrue({("species", "atom_count"), ("species", "phase"),
                             ("reported_thermochemistry", "unit"), ("sources", "locator")} <= fields)
            tin = next(row for row in report["species"] if row["record_id"] == "gfe-sn-sn-q+0-solid-metal")
            self.assertGreaterEqual(tin["representation_errors"], 3)
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
