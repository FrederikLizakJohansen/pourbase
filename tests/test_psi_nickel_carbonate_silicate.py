"""Nickel follow-up preserves full formulas, source variants and estimate scope."""

import json
import math
import unittest

import numpy as np

import pourbase as pb
from pourbase.engine import transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature


class PSINickelFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()
        cls.derivations = json.loads(cls.database.metadata["R11e_nickel_derivations"])

    def test_annabergite_keeps_three_nickels_two_arsenates_and_eight_waters(self):
        system = self.database.load_system("Ni", ligand_ids=("arsenate-aso4",))
        species = next(s for s in system.species if s.record_id ==
                       "r11e-ni-ni3-aso4-2-h2o-8-annabergite")
        self.assertEqual(species.formula_ascii, "Ni3(AsO4)2(H2O)8")
        self.assertEqual((species.metal_count, species.ligand_count,
                          species.core_oxygen_count, species.core_hydrogen_count,
                          species.electrons_per_metal, species.protons_per_metal), (3, 2, 8, 16, 2, 0))
        conditions = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity("arsenate-aso4", log10_free_activity=-6),)))
        rtln = 8.31446261815324 * 298.15 * math.log(10)
        expected = (-3491557 + 8 * 237129 - 2 * (-648410 - 6 * rtln)) / 3
        self.assertAlmostEqual(float(transformed_gibbs_J_mol_metal(
            species, self.database.reference_state, conditions, 7, 0)), expected)
        record = self.database.species_records((species.record_id,))[0]
        self.assertEqual({v.property: v.value for v in record.reported}, {
            "gibbs_energy_of_formation": -3491557, "enthalpy_of_formation": -4179000,
            "absolute_entropy": 540.771})
        self.assertTrue(all(v.selected_as_recommended for v in record.reported))

    def test_bicarbonate_approximation_retains_its_own_reaction_and_carbonate_conversion(self):
        d = next(d for d in self.derivations if d["variant"] == "bicarbonate_PSI_supplemental")
        system = self.database.load_system("Ni", ligand_ids=("carbonate-co3",))
        species = next(s for s in system.species if s.record_id == d["record_id"])
        self.assertIn("approximate", d["reaction_value_kind"])
        self.assertEqual((species.core_hydrogen_count, species.electrons_per_metal,
                          species.protons_per_metal), (1, 2, -1))
        rtln = 8.31446261815324 * 298.15 * math.log(10)
        self.assertAlmostEqual(-(species.gibbs_energy_J_mol + 45773 + 586770) / rtln, 1)
        for pH in (7, 10, 14):
            loghco3 = -5
            logco3 = loghco3 + pH - d["runtime_reference"]["pKa"]
            cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity("carbonate-co3", log10_free_activity=logco3),)))
            expected = (species.gibbs_energy_J_mol + 586770 - rtln * loghco3
                        + rtln * cfg.aqueous_activities.log10_activity_for(
                            species.record_id, species.species, species.formula_ascii))
            self.assertAlmostEqual(float(transformed_gibbs_J_mol_metal(
                species, self.database.reference_state, cfg, pH, 0)), expected)

    def test_silicate_original_result_and_native_water_basis_have_same_reaction_energy(self):
        d = next(d for d in self.derivations if d["variant"] == "silicate_PSI_original_SIT")
        record = self.database.species_records((d["record_id"],))[0]
        self.assertEqual(record.formula_ascii, "NiH3SiO4")
        self.assertEqual(len(record.reported), 1)
        self.assertEqual((d["log10_beta"], d["source_log10_beta_interval"],
                          d["rounded_supplemental_model_log10_beta"]), (6.34, 0.1, 6.3))
        native = d["native_water_component"]
        physical = d["value"] - d["ligand_input"]["value"]
        normalized = native["native_component_G_J_mol"] - (d["ligand_input"]["value"] + 237129)
        self.assertAlmostEqual(physical, normalized)
        self.assertIn("unconfirmed", d["scientific_qualification"])

    def test_pyrophosphate_triplets_keep_local_g_alternatives_and_distinct_neutralization(self):
        for rid, free, reaction, expected_difference in (
                ("nea02c-ni-nip2o7-q-2-aqueous", "P2O7", (-49831, 30600, 269.768), 16503),
                ("nea02c-ni-hnip2o7-q-1-aqueous", "HP2O7", (-29339, 47900, 259.062), 16958)):
            record = self.database.species_records((rid,))[0]
            rows = [d for d in self.derivations if d["record_id"] == rid]
            self.assertEqual(len(rows), 3)
            for d in rows:
                prop = d["property"]
                key = {"gibbs_energy_of_formation": "G", "enthalpy_of_formation": "H",
                       "absolute_entropy": "S"}[prop]
                self.assertEqual(d["free_ion_input"]["formula_html"].split("<")[0], free)
                value = next(v for v in record.reported if v.property == prop and
                             v.source.source_id == "pourbase_R11e_Ni_pyrophosphate_triplets")
                self.assertAlmostEqual(value.value, d["Ni_input"]["value"]
                                       + d["free_ion_input"][key] + d["source_reaction_value"])
                self.assertIsNone(value.uncertainty)
                self.assertEqual(value.status, "source_verified_estimate")
                self.assertEqual(value.selected_as_recommended, key != "G")
                self.assertIn("further sublicensees", value.source.locator)
                self.assertEqual(d["G_difference_from_preferred_NEA_J_mol"], expected_difference)
            self.assertAlmostEqual(reaction[1] - 298.15 * reaction[2], reaction[0], delta=1)

    def test_ligand_temperature_scope_remains_even_for_complete_triplets(self):
        database = at_temperature(self.database, 323.15)
        system = database.load_system("Ni", ligand_ids=(
            "arsenate-aso4", "carbonate-co3", "silicate-h3sio4", "pyrophosphate-p2o7"))
        ids = {s.record_id for s in system.species}
        for rid in {d["record_id"] for d in self.derivations} | {
                "r11e-ni-ni3-aso4-2-h2o-8-annabergite"}:
            self.assertNotIn(rid, ids)

    def test_closed_nickel_balance_with_all_three_new_species(self):
        cfg = pb.PourbaixConditions(pH_points=7, eh_points=9,
            ligand_activities=pb.LigandActivityModel(tuple(
                pb.LigandActivity(ligand, log10_free_activity=-6) for ligand in
                ("arsenate-aso4", "carbonate-co3", "silicate-h3sio4"))))
        for model in (pb.IdealActivityCoefficientModel(), pb.DaviesActivityCoefficientModel(0.001)):
            result = pb.MassBalanceEngine(self.database, activity_coefficient_model=model).calculate(
                "Ni", cfg, pb.TotalMetalConcentration(1e-4))
            np.testing.assert_allclose(
                result.dissolved_metal_mol_L + 1e-4 * result.precipitated_metal_fraction,
                1e-4, rtol=1e-11, atol=1e-15)
