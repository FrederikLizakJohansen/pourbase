"""NEA hydrolysis values retain their meaning in the stored water basis."""

from dataclasses import replace
import unittest

import pourbase as pb
from pourbase.engine import transformed_gibbs_J_mol_metal


class NEAComponentBasisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_nickel_hydrolysis_is_invariant_under_one_water_conversion(self):
        item = next(s for s in self.database.load_system("Ni").species
                    if s.formula_ascii == "HNiO2" and s.charge == -1)
        self.assertEqual(item.gibbs_energy_J_mol, -353390)
        self.assertEqual((item.electrons_per_metal, item.protons_per_metal), (2, 3))
        source_form = replace(item, formula_ascii="Ni(OH)3",
                              core_oxygen_count=3, core_hydrogen_count=3,
                              gibbs_energy_J_mol=-590519)
        for activity in (-6, 0):
            conditions = pb.PourbaixConditions(
                aqueous_activities=pb.AqueousActivityModel(default_log10_activity=activity))
            for pH, potential in ((0, -1), (7, .2), (14, 1)):
                with self.subTest(activity=activity, pH=pH, potential=potential):
                    self.assertAlmostEqual(
                        float(transformed_gibbs_J_mol_metal(
                            item, self.database.reference_state, conditions, pH, potential)),
                        float(transformed_gibbs_J_mol_metal(
                            source_form, self.database.reference_state, conditions, pH, potential)),
                        places=7)

    def test_selected_gibbs_preserves_older_evidence_and_source_interval(self):
        record = self.database.species_records(("gfe-ni-hnio2-q-1-aqueous-aq",))[0]
        reported = {r.value_id: r for r in record.reported}
        value = reported[record.record_id + ":gf:nea02e-water-normalized"]
        self.assertEqual(value.uncertainty, 9735)
        self.assertIn("TableIII-1 printedp44", value.source.locator)
        self.assertIn("-590519-(-237129)=-353390", value.source.locator)
        self.assertIn("further sublicensees", value.source.locator)
        self.assertEqual(reported[record.record_id + ":gf:preferred"].value, -343004.32)
        self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.value, value.value)
        self.assertEqual(record.thermochemistry.entropy_J_mol_K.value, -150.624)
        self.assertAlmostEqual(record.thermochemistry.formation_enthalpy_J_mol.value,
                               -496943.9354)
