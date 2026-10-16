"""Source conventions and calculation scope for the NEA selenium continuation."""

import json
import unittest

import numpy as np

import pourbase as pb
from pourbase.engine import transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature


class NEASeleniumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def record(self, record_id):
        return self.database.species_records((record_id,))[0]

    def test_selenite_entropy_sign_and_protonation_are_consistent(self):
        record = self.record("gfe-se-seo3-q-2-aqueous-aq")
        thermal = record.thermochemistry
        self.assertEqual(thermal.entropy_J_mol_K.value, -5.055)
        self.assertEqual(thermal.entropy_J_mol_K.uncertainty, 7.011)
        # Conventional ionic entropy includes the H+ reference, with S(H+) = 0.
        formation_entropy = -5.055 - 42.090 - 1.5 * 205.152 - 130.680
        reconstructed = thermal.formation_enthalpy_J_mol.value - 298.15 * formation_entropy
        self.assertAlmostEqual(reconstructed, thermal.gibbs_energy_J_mol.value, delta=0.5)
        acid = self.record("gfe-se-hseo3-q-1-aqueous-aq")
        self.assertAlmostEqual(
            acid.thermochemistry.gibbs_energy_J_mol.value - thermal.gibbs_energy_J_mol.value,
            -47719, delta=1.01)
        self.assertTrue(any("discussionp143" in w.message for w in record.warnings))

    def test_trigonal_reference_and_metastable_monoclinic_phase_are_distinct(self):
        reference = self.record("gfe-se-se-q+0-solid-hexagonal-black")
        monoclinic = self.record("r11-se-se-mono-solid")
        self.assertEqual(reference.thermochemistry.gibbs_energy_J_mol.value, 0)
        self.assertEqual(monoclinic.thermochemistry.gibbs_energy_J_mol.value, 1281)
        with self.database.connect() as connection:
            identity = connection.execute(
                "SELECT identified_phase FROM phases WHERE record_id=?",
                (reference.record_id,)).fetchone()[0]
        self.assertIn("trigonal", identity)
        self.assertIn("monoclinic", monoclinic.phase_detail)
        self.assertGreater(len(reference.reported), 3)

    def test_polyselenide_full_formula_and_closed_balance_exclusions(self):
        system = self.database.load_system("Se")
        for n in (2, 3, 4):
            species = next(s for s in system.species
                           if s.record_id == f"r11-se-se{n}-2-aqueous")
            self.assertEqual(species.metal_count, n)
            self.assertEqual(species.charge, -2)
            self.assertAlmostEqual(species.electrons_per_metal, -2 / n)
        for model in (pb.IdealActivityCoefficientModel(),
                      pb.DaviesActivityCoefficientModel(0.01)):
            result = pb.MassBalanceEngine(
                self.database, activity_coefficient_model=model).calculate(
                    "Se", pb.PourbaixConditions(pH_points=7, eh_points=9),
                    pb.TotalMetalConcentration(1e-4))
            excluded = {s.record_id for s in result.system.excluded
                        if s.reason is pb.ExclusionReason.POLYNUCLEAR_AQUEOUS}
            self.assertEqual(excluded, {f"r11-se-se{n}-2-aqueous" for n in (2, 3, 4)})
            np.testing.assert_allclose(
                result.dissolved_metal_mol_L + 1e-4 * result.precipitated_metal_fraction,
                1e-4, rtol=1e-11, atol=1e-15)

    def test_optional_cluster_gas_uses_one_formula_and_one_fugacity_correction(self):
        system = self.database.load_system("Se", include_optional_gases=True)
        species = next(s for s in system.species if s.record_id == "r11-se-se8-g-gas")
        self.assertEqual(species.metal_count, 8)
        self.assertEqual(species.gibbs_energy_J_mol, 100307)
        reference = self.database.reference_state
        unit = pb.PourbaixConditions()
        dilute = pb.PourbaixConditions(
            gas_fugacities=pb.GasFugacityModel(default_log10_fugacity=-3))
        g0 = float(transformed_gibbs_J_mol_metal(species, reference, unit, 7, 0))
        g1 = float(transformed_gibbs_J_mol_metal(species, reference, dilute, 7, 0))
        self.assertAlmostEqual(g0, 100307 / 8)
        self.assertAlmostEqual(g1 - g0, -3 * 8.31446261815324 * 298.15 * np.log(10) / 8)
        for temperature in (298.15, 348.15):
            database = at_temperature(self.database, temperature)
            self.assertFalse(any(s.is_gas for s in database.load_system("Se").species))
            optional = database.load_system("Se", include_optional_gases=True)
            self.assertEqual(sum(s.is_gas for s in optional.species), 11)
        with self.assertRaises(pb.UnsupportedConditionError):
            pb.MassBalanceEngine(self.database).calculate_system(
                system, unit, pb.TotalMetalConcentration(1e-4))

    def test_enthalpy_only_crystals_keep_missing_gibbs_and_entropy(self):
        for record_id in ("r11-se-se2o5-cr-solid", "r11-se-h2seo3-cr-solid",
                          "r11-se-h2seo4-cr-solid"):
            record = self.record(record_id)
            self.assertIsNotNone(record.thermochemistry.formation_enthalpy_J_mol.value)
            self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
            self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
            excluded = next(s for s in self.database.load_system("Se").excluded
                            if s.record_id == record_id)
            self.assertIs(excluded.reason, pb.ExclusionReason.GIBBS_ENERGY_UNAVAILABLE)
        with self.database.connect() as connection:
            basis = connection.execute(
                "SELECT metal_count, metal_oxidation_state, electron_coefficient_per_metal "
                "FROM species WHERE record_id='r11-se-se2o5-cr-solid'").fetchone()
        self.assertEqual(tuple(basis), (2, 5, 5))

    def test_hydroselenide_retains_independent_thermal_alternatives(self):
        record = self.record("gfe-se-hse-q-1-aqueous-aq")
        thermal = record.thermochemistry
        self.assertEqual(thermal.gibbs_energy_J_mol.value, 43471)
        self.assertEqual(thermal.formation_enthalpy_J_mol.value, 15900)
        self.assertEqual(thermal.entropy_J_mol_K.value, 79)
        self.assertTrue(any(x.value == 44000 for x in record.reported))
        self.assertEqual(sum(x.source.source_id == "NEA_OECD_20261016_Se"
                             for x in record.reported), 1)

    def test_selected_source_conditions_and_downstream_acknowledgment_survive_api(self):
        record = self.record("r11-se-h2seo3-aq-aqueous")
        for value in record.reported:
            self.assertEqual((value.temperature_K, value.pressure_bar), (298.15, 1))
            self.assertIn("printedp42/PDFp83", value.source.locator)
            self.assertIn("further sublicensees", value.source.locator)
        permission = json.loads(self.database.metadata["source_permission_NEA_TDB_Se_2005"])
        self.assertEqual(permission["status"], "available_under_OECD_data_terms")
        self.assertTrue(permission["downstream_acknowledgment_required"])
