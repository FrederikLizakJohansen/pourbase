"""Formula, phase and source conventions in the zirconium NEA extension."""

import unittest

import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import transformed_gibbs_J_mol_metal


class NEAZirconiumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_polynuclear_energy_uses_one_full_formula_and_three_metals(self):
        system = self.database.load_system("Zr")
        item = next(s for s in system.species if s.formula_ascii == "Zr3(OH)4")
        self.assertEqual((item.metal_count, item.charge), (3, 8))
        self.assertEqual(item.gibbs_energy_J_mol, -2536373)
        self.assertEqual(item.electrons_per_metal, 4)
        self.assertAlmostEqual(item.protons_per_metal, 4 / 3)
        conditions = pb.PourbaixConditions(
            aqueous_activities=pb.AqueousActivityModel(default_log10_activity=0))
        rtln = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        expected = (-2536373 - 4 * self.database.reference_state.water_gibbs_energy_J_mol
                    - 4 * rtln * 7 - 12 * FARADAY_C_MOL * .2) / 3
        actual = transformed_gibbs_J_mol_metal(
            item, self.database.reference_state, conditions, 7, .2)
        self.assertAlmostEqual(float(actual), expected, places=7)
        result = pb.MassBalanceEngine(self.database).calculate(
            "Zr", pb.PourbaixConditions(pH_points=5, eh_points=5),
            pb.TotalMetalConcentration(1e-4))
        self.assertTrue(any(x.record_id == item.record_id and
                            x.reason is pb.ExclusionReason.POLYNUCLEAR_AQUEOUS
                            for x in result.system.excluded))

    def test_epsilon_hydride_keeps_formal_valence_and_reaction_sign(self):
        item = next(s for s in self.database.load_system("Zr").species if s.formula_ascii == "ZrH2")
        self.assertEqual((item.formal_metal_oxidation_state, item.electrons_per_metal,
                          item.protons_per_metal), (2, -2, -2))
        record = self.database.species_records((item.record_id,))[0]
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, -164400)
        self.assertEqual(record.thermochemistry.entropy_J_mol_K.value, 35.2)
        reconstructed = -164400 - 298.15 * (35.2 - 39.08 - 130.68)
        self.assertAlmostEqual(item.gibbs_energy_J_mol, reconstructed, delta=.5)
        self.assertTrue(any("average of two experimental" in w.message for w in record.warnings))

    def test_missing_bromide_gibbs_and_questioned_bare_gases_remain_explicit(self):
        self.assertFalse(any(s.is_gas for s in self.database.load_system("Zr").species))
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT record_id FROM species WHERE symbol='Zr' AND formula_ascii='ZrBr' AND phase='gas'"
            ).fetchone()
        record = self.database.species_records((row[0],))[0]
        self.assertEqual(record.thermochemistry.entropy_J_mol_K.value, 268.2)
        self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
        self.assertIsNone(record.thermochemistry.formation_enthalpy_J_mol.value)
        buffered = self.database.load_system("Zr", ligand_ids=("bromide-br",))
        self.assertTrue(any(x.record_id == record.record_id and
                            x.reason is pb.ExclusionReason.GIBBS_ENERGY_UNAVAILABLE
                            for x in buffered.excluded))

    def test_sulfite_reference_and_sulfide_estimates_keep_their_conventions(self):
        reference = next(x for x in self.database.available_ligands() if x.ligand_id == "sulfite-so3")
        self.assertEqual((reference.formula_ascii, reference.charge,
                          reference.gibbs_energy_J_mol), ("SO3", -2, -486500))
        self.assertIn("573", self.database.source(reference.source_id).locator)
        system = self.database.load_system("Zr", ligand_ids=("sulfide-s",))
        trisulfide = next(s for s in system.species if s.formula_ascii == "ZrS3")
        self.assertEqual((trisulfide.formal_metal_oxidation_state,
                          trisulfide.electrons_per_metal), (4, 6))
        for formula in ("ZrS2", "ZrS3"):
            item = next(s for s in system.species if s.formula_ascii == formula)
            record = self.database.species_records((item.record_id,))[0]
            self.assertEqual(record.thermochemistry.entropy_J_mol_K.status, "source_verified_estimate")
            self.assertTrue(any("analogy" in w.message or "estimate" in w.message for w in record.warnings))
