"""Elemental buffers preserve full formulas and their physical formation reactions."""

import unittest

import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import transformed_gibbs_J_mol_metal


class NEAElementalReservoirTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_tellurides_keep_composition_and_normalize_per_zirconium_once(self):
        database = self.database
        system = database.load_system("Zr", ligand_ids=("elemental-te-cr",))
        conditions = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity("elemental-te-cr", log10_free_activity=0),)))
        for rid, metal, tellurium, gibbs, formal in (
            ("nea02g2-zr-telluride-1p843", 1, 1.843, -291328, 3.686),
            ("nea02g2-zr-ditelluride", 1, 2, -290037, 4),
            ("nea02g2-zr-telluride-5-4", 5, 4, -810430, 1.6),
        ):
            item = next(s for s in system.species if s.record_id == rid)
            self.assertEqual((item.metal_count, item.ligand_count), (metal, tellurium))
            self.assertEqual((item.metal_oxidation_state, item.electrons_per_metal,
                              item.protons_per_metal), (formal, 0, 0))
            for pH, potential in ((0, -1), (7, 0), (14, 1)):
                with self.subTest(record_id=rid, pH=pH):
                    self.assertAlmostEqual(float(transformed_gibbs_J_mol_metal(
                        item, database.reference_state, conditions, pH, potential)), gibbs / metal)

    def test_nitride_consumes_half_a_nitrogen_gas_molecule(self):
        database = self.database
        item = next(s for s in database.load_system(
            "Zr", ligand_ids=("nitrogen-n2-gas",)).species
            if s.record_id == "nea02g2-zr-nitride")
        self.assertEqual((item.ligand_count, item.metal_oxidation_state,
                          item.electrons_per_metal), (.5, 3, 0))
        for log_fugacity in (-12, -6, 0):
            conditions = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity("nitrogen-n2-gas", log10_free_activity=log_fugacity),)))
            expected = -341852 - .5 * GAS_CONSTANT_J_MOL_K * 298.15 * LN_10 * log_fugacity
            self.assertAlmostEqual(float(transformed_gibbs_J_mol_metal(
                item, database.reference_state, conditions, 7, 0)), expected)

    def test_carbide_preserves_the_source_thermal_estimate(self):
        record = self.database.species_records(("nea02g2-zr-carbide",))[0]
        self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.value, -203476)
        self.assertEqual(record.thermochemistry.entropy_J_mol_K.value, 33)
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, -207000)
        self.assertTrue(all(row.status == "source_verified_estimate" for row in record.reported))
        self.assertTrue(all("ZrC0.96" in row.source.locator for row in record.reported))
        self.assertTrue(all("95% confidence" in row.source.locator for row in record.reported))
        self.assertTrue(all("further sublicensees" in row.source.locator for row in record.reported))

    def test_tellurite_keeps_its_enthalpy_and_explicit_gibbs_gap(self):
        rid = "nea02g2-zr-tellurite"
        record = self.database.species_records((rid,))[0]
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, -2119200)
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.uncertainty, 9600)
        self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
        self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
        selected = self.database.load_system("Zr", ligand_ids=("elemental-te-cr",))
        exclusion = next(x for x in selected.excluded if x.record_id == rid)
        self.assertIs(exclusion.reason, pb.ExclusionReason.GIBBS_ENERGY_UNAVAILABLE)

    def test_elemental_buffers_are_explicit_and_metal_inventory_is_conserved(self):
        import numpy as np

        database = self.database
        default = database.load_system("Zr")
        self.assertFalse(any(s.record_id.startswith("nea02g2-") for s in default.species))
        self.assertTrue(all(x.reason is pb.ExclusionReason.LIGAND_NOT_SELECTED
                            for x in default.excluded if x.record_id.startswith("nea02g2-")))
        refs = {r.ligand_id: r for r in database.available_ligands()}
        for lid in ("elemental-te-cr", "nitrogen-n2-gas", "carbon-graphite"):
            self.assertEqual((refs[lid].charge, refs[lid].gibbs_energy_J_mol), (0, 0))
        conditions = pb.PourbaixConditions(pH_points=7, U_points=9,
            ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity("elemental-te-cr", log10_free_activity=0),
                pb.LigandActivity("nitrogen-n2-gas", log10_free_activity=-6),
                pb.LigandActivity("carbon-graphite", log10_free_activity=0))))
        # Nitrogen is an external buffer; this conserves zirconium with gas-free Zr species.
        result = pb.MassBalanceEngine(database).calculate(
            "Zr", conditions, pb.TotalMetalConcentration(1e-4))
        np.testing.assert_allclose(result.dissolved_metal_mol_L
                                   + 1e-4 * result.precipitated_metal_fraction, 1e-4,
                                   rtol=1e-11, atol=1e-15)
