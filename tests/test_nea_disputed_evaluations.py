"""Qualified source estimates keep their scientific limitations and phase scope."""

import unittest

import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import transformed_gibbs_J_mol_metal


class NEADisputedEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_oxide_gas_estimates_keep_the_later_scientific_critique(self):
        for rid, gibbs, enthalpy, entropy, width in (
            ("nea02g3-zr-monoxide-gas", 30576, 56200, 227.6, 27124),
            ("nea02g3-zr-dioxide-gas", -298386, -289600, 273.7, 47042),
        ):
            record = self.database.species_records((rid,))[0]
            self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.value, gibbs)
            self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.uncertainty, width)
            self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, enthalpy)
            self.assertEqual(record.thermochemistry.entropy_J_mol_K.value, entropy)
            self.assertTrue(all(r.status == "source_verified_estimate" for r in record.reported))
            historical = [r for r in record.reported
                          if r.source.source_id == "NEA_OECD_20261014_Zr"]
            self.assertEqual(len(historical), 3)
            self.assertTrue(all("AppendixF printed781--782" in r.source.locator
                                and "not a replacement" in r.source.locator
                                and "further sublicensees" in r.source.locator
                                for r in historical))

    def test_optional_oxide_gases_have_the_full_water_reaction_response(self):
        database = self.database
        default = database.load_system("Zr")
        selected = database.load_system("Zr", include_optional_gases=True)
        for rid, oxygen, gibbs in (("nea02g3-zr-monoxide-gas", 1, 30576),
                                    ("nea02g3-zr-dioxide-gas", 2, -298386)):
            item = next(s for s in selected.species if s.record_id == rid)
            self.assertEqual((item.protons_per_metal, item.electrons_per_metal),
                             (2 * oxygen, 2 * oxygen))
            exclusion = next(s for s in default.excluded if s.record_id == rid)
            self.assertIs(exclusion.reason, pb.ExclusionReason.GAS_NOT_SELECTED)
            for fugacity in (0, -3, -12):
                conditions = pb.PourbaixConditions(
                    gas_fugacities=pb.GasFugacityModel(overrides={rid: fugacity}))
                for pH, potential in ((0, -1), (7, 0), (14, 1)):
                    rtln = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
                    expected = (gibbs - oxygen * database.reference_state.water_gibbs_energy_J_mol
                                + rtln * fugacity - 2 * oxygen * rtln * pH
                                - 2 * oxygen * FARADAY_C_MOL * potential)
                    self.assertAlmostEqual(float(transformed_gibbs_J_mol_metal(
                        item, database.reference_state, conditions, pH, potential)), expected)

    def test_sulfide_uses_selected_positive_entropy_and_exact_composition(self):
        database = self.database
        rid = "nea02g3-zr-sulfide-1p5"
        record = database.species_records((rid,))[0]
        self.assertEqual(record.formula_ascii, "ZrS1.5")
        self.assertEqual(record.thermochemistry.entropy_J_mol_K.value, 62.7)
        self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.value, -502107)
        self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.uncertainty, 3886)
        self.assertTrue(all("TableV-27" in r.source.locator for r in record.reported))
        self.assertTrue(any("structure type" in w.message and "1100K" in w.message
                            for w in record.warnings))
        self.assertAlmostEqual(-509400 - 298.15 * (62.7 - 39.08 - 1.5 * 32.054),
                               -502107, delta=.51)
        item = next(s for s in database.load_system("Zr", ligand_ids=("sulfide-s",)).species
                    if s.record_id == rid)
        self.assertEqual((item.metal_count, item.ligand_count,
                          item.protons_per_metal, item.electrons_per_metal), (1, 1.5, 0, 3))
        conditions = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity("sulfide-s", log10_free_activity=-3),)))
        expected = (-502107 - 1.5 * (item.ligand_gibbs_energy_J_mol
                    - 3 * GAS_CONSTANT_J_MOL_K * 298.15 * LN_10))
        self.assertAlmostEqual(float(transformed_gibbs_J_mol_metal(
            item, database.reference_state, conditions, 7, 0)), expected)

    def test_bulk_hydride_correlation_is_not_added_as_a_pure_phase(self):
        from contextlib import closing

        with closing(self.database.connect()) as connection:
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM species WHERE symbol='Zr' AND formula_ascii='ZrH' "
                "AND phase='solid'").fetchone()[0], 0)
        system = self.database.load_system("Zr")
        self.assertFalse(any(s.is_gas for s in system.species))
        result = pb.MassBalanceEngine(self.database).calculate(
            "Zr", pb.PourbaixConditions(pH_points=5, U_points=5),
            pb.TotalMetalConcentration(1e-4))
        self.assertEqual(result.dominant_species_index.shape, (5, 5))
        with self.assertRaises(pb.UnsupportedConditionError):
            pb.MassBalanceEngine(self.database).calculate_system(
                self.database.load_system("Zr", include_optional_gases=True),
                pb.PourbaixConditions(pH_points=5, U_points=5),
                pb.TotalMetalConcentration(1e-4))


    def test_original_1975_enthalpies_are_preserved_as_alternatives(self):
        import json

        sid = "MuradHildenbrand1975_NEA02g3b_original"
        for rid, value, width, preferred in (
            ("nea02g3-zr-monoxide-gas", 83000, 12000, 56200),
            ("nea02g3-zr-dioxide-gas", -298000, 30000, -289600),
        ):
            record = self.database.species_records((rid,))[0]
            original = next(r for r in record.reported if r.source.source_id == sid)
            self.assertEqual((original.property, original.value, original.uncertainty),
                             ("enthalpy_of_formation", value, width))
            self.assertEqual(original.temperature_K, 298.15)
            self.assertIsNone(original.pressure_bar)
            self.assertFalse(original.selected_as_recommended)
            self.assertIn("confidence convention", original.source.locator)
            self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, preferred)
            selection = self.database.selections[(rid, "enthalpy_of_formation")]
            candidate = next(c for c in selection.candidates if c.source_id == sid)
            self.assertEqual((candidate.family, candidate.evidence_class), ("estimates", "E"))
        route = json.loads(self.database.metadata["source_reuse_" + sid])
        self.assertEqual(route["status"], "available_individual_original_numerical_facts")
        self.assertFalse(route["NEA_permission_applies"])

    def test_zero_kelvin_observation_keeps_temperature_and_exclusion(self):
        rid = "nea02g3-zr-monoxide-gas"
        record = self.database.species_records((rid,))[0]
        zero = next(r for r in record.reported if r.temperature_K == 0)
        self.assertAlmostEqual(zero.value, 21.4 * 4184)
        self.assertIsNone(zero.uncertainty)
        self.assertIsNone(zero.pressure_bar)
        self.assertFalse(zero.selected_as_recommended)
        self.assertIn("1–2kcal/mol", zero.source.locator)
        self.assertIn("2000–2800K", zero.source.locator)
        candidates = self.database.selections[(rid, "enthalpy_of_formation")].candidates
        self.assertNotIn(zero.value_id, {r.value_id for r in candidates})
        exclusion = next(e for e in self.database.policy.exclusions
                         if e.record_id == rid and e.source_id == zero.source.source_id)
        self.assertIn("0 K", exclusion.reason)

    def test_original_298K_enthalpy_can_be_selected_without_changing_G_or_S(self):
        for rid, value in (("nea02g3-zr-monoxide-gas", 83000),
                           ("nea02g3-zr-dioxide-gas", -298000)):
            policy = self.database.policy.with_override(
                rid, "enthalpy_of_formation", "MuradHildenbrand1975_NEA02g3b_original",
                "Test an explicit original enthalpy preference")
            custom = pb.with_policy(self.database, policy)
            self.assertEqual(custom.selections[(rid, "enthalpy_of_formation")].chosen.value, value)
            for prop in ("gibbs_energy_of_formation", "absolute_entropy"):
                self.assertEqual(custom.selections[(rid, prop)].chosen.value_id,
                                 self.database.selections[(rid, prop)].chosen.value_id)
