"""Buffered selenium compounds retain source identity and formation conventions."""

import json
import unittest

import numpy as np

import pourbase as pb
from pourbase.engine import transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature


class NEAMetalSeleniumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def record(self, record_id):
        return self.database.species_records((record_id,))[0]

    def test_selenite_reference_follows_preferred_observation_and_keeps_nbs_alternative(self):
        record = self.record("gfe-se-seo3-q-2-aqueous-aq")
        with self.database.connect() as connection:
            reference = connection.execute(
                "SELECT gibbs_energy_J_mol, source_id FROM ligands "
                "WHERE ligand_id='selenite-seo3'").fetchone()
        self.assertEqual(reference[0], record.thermochemistry.gibbs_energy_J_mol.value)
        self.assertEqual(tuple(reference), (-362392, "NEA_OECD_20261016_Se"))
        self.assertTrue(any(v.property == "gibbs_energy_of_formation" and v.value == -369800
                            for v in record.reported))
        history = json.loads(self.database.metadata["R11c_selenium_reference_history"])
        self.assertEqual(history["prior_selenite_pin"]["gibbs_energy_J_mol"], -369800)
        self.assertTrue(history["prior_selenite_observation_ids"])

    def test_hydrate_waters_and_external_selenite_are_removed_once(self):
        conditions = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity("selenite-seo3", log10_free_activity=-3),)))
        for symbol, formula, waters in (("Mg", "MgSeO3(H2O)6", 6),
                                         ("Ni", "NiSeO3(H2O)2", 2),
                                         ("Ca", "CaSeO3(H2O)", 1),
                                         ("Mn", "MnSeO3(H2O)2", 2)):
            system = self.database.load_system(symbol, ligand_ids=("selenite-seo3",))
            species = next(s for s in system.species if s.formula_ascii == formula)
            self.assertEqual((species.metal_count, species.ligand_count,
                              species.core_oxygen_count, species.core_hydrogen_count),
                             (1, 1, waters, 2 * waters))
            self.assertEqual((species.electrons_per_metal, species.protons_per_metal), (2, 0))
            reference = self.database.reference_state
            expected = (species.gibbs_energy_J_mol
                        - waters * reference.water_gibbs_energy_J_mol
                        - (-362392 - 3 * 8.31446261815324 * 298.15 * np.log(10)))
            for pH in (0, 7, 14):
                self.assertAlmostEqual(float(transformed_gibbs_J_mol_metal(
                    species, reference, conditions, pH, 0)), expected)

    def test_selenocyanate_count_sets_activity_response_and_preserves_formation_g(self):
        conditions = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity("selenocyanate-secn", log10_free_activity=-3),)))
        shifted = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity("selenocyanate-secn", log10_free_activity=-2),)))
        system = self.database.load_system("Ni", ligand_ids=("selenocyanate-secn",))
        for formula, charge, count, gibbs in (("NiSeCN", 1, 1, 80175),
                                               ("Ni(SeCN)2", 0, 2, 213544)):
            species = next(s for s in system.species if s.formula_ascii == formula)
            self.assertEqual((species.charge, species.ligand_count,
                              species.electrons_per_metal), (charge, count, 2))
            self.assertEqual(species.gibbs_energy_J_mol, gibbs)
            delta = float(transformed_gibbs_J_mol_metal(
                species, self.database.reference_state, shifted, 7, 0)
                - transformed_gibbs_J_mol_metal(
                    species, self.database.reference_state, conditions, 7, 0))
            self.assertAlmostEqual(delta, -count * 8.31446261815324 * 298.15 * np.log(10))
        history = json.loads(self.database.metadata["R11c_selenium_reference_history"])
        self.assertEqual(history["new_selenocyanate_reference"]["total_source_interval_J_mol"], 3800)

    def test_iron_formation_estimate_has_all_inputs_and_no_invented_total_uncertainty(self):
        record = self.record("r11c-fe-feseo3-aqueous")
        value = next(row for row in record.reported if row.source.source_id == "pourbase_R11c_FeSeO3_derived_G")
        self.assertEqual(value.value, -442263)
        self.assertEqual(value.status, "source_verified_estimate")
        self.assertIsNone(value.uncertainty)
        derivation = json.loads(self.database.metadata["source_reuse_R11c_FeSeO3_derived"])
        self.assertEqual(sum(x["value_J_mol"] for x in derivation["inputs"]), value.value)
        self.assertIn("296K", derivation["source_temperature_qualification"])
        self.assertEqual((value.temperature_K, value.pressure_bar), (298.15, 1))
        self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
        self.assertIsNone(record.thermochemistry.formation_enthalpy_J_mol.value)

    def test_appendix_evaluations_keep_unreviewed_auxiliary_qualification(self):
        ca = self.record("r11c-ca-caseo3-h2o-solid")
        mn = self.record("r11c-mn-mnseo3-h2o-2-solid")
        ca_extra = [v for v in ca.reported if v.source.source_id.endswith("appendix_E")]
        self.assertEqual(len(ca_extra), 2)
        for value in (*ca_extra, *mn.reported):
            self.assertEqual(value.status, "source_verified_estimate")
            self.assertIn("not TDB-selected", value.source.citation)
            self.assertIn("further sublicensees", value.source.locator)
        self.assertEqual(ca.thermochemistry.entropy_J_mol_K.value, 168.754)
        self.assertEqual(ca.thermochemistry.formation_enthalpy_J_mol.value, -1324800)

    def test_aqueous_selenate_pairs_keep_missing_thermal_values_and_temperature_scope(self):
        for symbol in ("Ca", "Mg", "Mn", "Ni"):
            system = self.database.load_system(symbol, ligand_ids=("selenate-seo4",))
            species = next(s for s in system.species if s.formula_ascii == symbol + "SeO4")
            record = self.record(species.record_id)
            self.assertIsNone(record.thermochemistry.formation_enthalpy_J_mol.value)
            self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
            self.assertNotIn(species.record_id, {s.record_id for s in
                at_temperature(self.database, 323.15).load_system(
                    symbol, ligand_ids=("selenate-seo4",)).species})
            self.assertNotIn(species.record_id,
                             {s.record_id for s in self.database.load_system(symbol).species})

    def test_closed_balance_conserves_primary_metal_with_external_selenium(self):
        conditions = pb.PourbaixConditions(pH_points=7, U_points=9,
            ligand_activities=pb.LigandActivityModel(tuple(
                pb.LigandActivity(ligand, log10_free_activity=-3)
                for ligand in ("selenite-seo3", "selenate-seo4", "selenocyanate-secn"))))
        for model in (pb.IdealActivityCoefficientModel(), pb.DaviesActivityCoefficientModel(0.01)):
            result = pb.MassBalanceEngine(
                self.database, activity_coefficient_model=model).calculate(
                    "Ni", conditions, pb.TotalMetalConcentration(1e-4))
            np.testing.assert_allclose(
                result.dissolved_metal_mol_L + 1e-4 * result.precipitated_metal_fraction,
                1e-4, rtol=1e-11, atol=1e-15)
