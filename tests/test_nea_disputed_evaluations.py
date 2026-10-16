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
            self.assertTrue(all("AppendixF printed781--782" in r.source.locator
                                and "not a replacement" in r.source.locator
                                and "further sublicensees" in r.source.locator
                                for r in record.reported))

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
            "Zr", pb.PourbaixConditions(pH_points=5, eh_points=5),
            pb.TotalMetalConcentration(1e-4))
        self.assertEqual(result.dominant_species_index.shape, (5, 5))
        with self.assertRaises(pb.UnsupportedConditionError):
            pb.MassBalanceEngine(self.database).calculate_system(
                self.database.load_system("Zr", include_optional_gases=True),
                pb.PourbaixConditions(pH_points=5, eh_points=5),
                pb.TotalMetalConcentration(1e-4))
