"""Chemical identities and reservoir conventions in the NEA ligand extension."""

import math
import unittest
from dataclasses import replace

import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import transformed_gibbs_J_mol_metal


class NEALigandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def conditions(self, ligand):
        return pb.PourbaixConditions(
            aqueous_activities=pb.AqueousActivityModel(default_log10_activity=0),
            ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity(ligand, log10_free_activity=-3),)))

    def test_tetrachloride_charge_and_phase_define_distinct_species(self):
        system = self.database.load_system("Sn", ligand_ids=("chloride-cl",))
        dianion = next(s for s in system.species if s.formula_ascii == "SnCl4" and s.is_aqueous)
        gas = next(s for s in system.species if s.formula_ascii == "SnCl4" and s.is_gas)
        self.assertEqual((dianion.charge, dianion.electrons_per_metal), (-2, 2))
        self.assertEqual((gas.charge, gas.electrons_per_metal), (0, 4))
        liquid = self.database.species_records(("nea02c-sn-sncl4-q+0-liquid",))[0]
        self.assertIsNone(liquid.thermochemistry.gibbs_energy_J_mol.value)
        self.assertEqual(liquid.thermochemistry.formation_enthalpy_J_mol.value, -517000)
        self.assertTrue(any(x.record_id == liquid.record_id and
                            x.reason is pb.ExclusionReason.GIBBS_ENERGY_UNAVAILABLE
                            for x in system.excluded))

    def test_protonated_complexes_use_the_declared_free_ligand(self):
        rtln = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        for ligand, formula, charge, formation_g in (
            ("sulfide-s", "NiHS", 1, -63098),
            ("phosphate-po4", "NiHPO4", 0, -1159167),
            ("pyrophosphate-p2o7", "HNiP2O7", -1, -2064270),
            ("arsenate-aso4", "NiHAsO4", 0, -776918),
        ):
            with self.subTest(formula=formula):
                item = next(s for s in self.database.load_system("Ni", ligand_ids=(ligand,)).species
                            if s.formula_ascii == formula and s.charge == charge)
                self.assertEqual((item.core_oxygen_count, item.core_hydrogen_count), (0, 1))
                self.assertEqual((item.protons_per_metal, item.electrons_per_metal), (-1, 2))
                conditions = self.conditions(ligand)
                actual = transformed_gibbs_J_mol_metal(
                    item, self.database.reference_state, conditions, 7, .2)
                expected = (formation_g - item.ligand_gibbs_energy_J_mol
                            + 3 * rtln + 7 * rtln - 2 * FARADAY_C_MOL * .2)
                self.assertAlmostEqual(float(actual), expected, places=7)

    def test_free_references_retain_open_nbs_and_selected_nea_sources(self):
        references = {r.ligand_id: r for r in self.database.available_ligands()}
        for ligand, formula, charge, energy in (
            ("thiocyanate-scn", "SCN", -1, 92710),
            ("arsenate-aso4", "AsO4", -3, -648410),
        ):
            reference = references[ligand]
            self.assertEqual((reference.formula_ascii, reference.charge,
                              reference.gibbs_energy_J_mol), (formula, charge, energy))
            self.assertIn("M32124", reference.source_citation)
            self.assertIn("logical record", self.database.source(reference.source_id).locator)
        pyro = references["pyrophosphate-p2o7"]
        self.assertEqual((pyro.formula_ascii, pyro.charge, pyro.gibbs_energy_J_mol),
                         ("P2O7", -4, -1935503))
        self.assertEqual(pyro.source_id, "NEA2003_R11k_pyrophosphate")
        self.assertIn("M32124", self.database.source("NEA02c_NBS_PDR_P2O7_reference").citation)
        item = next(s for s in self.database.load_system("Ni", ligand_ids=("pyrophosphate-p2o7",)).species
                    if s.formula_ascii == "NiP2O7")
        self.assertEqual((item.core_oxygen_count, item.ligand_count, item.charge), (0, 1, -2))
        record = self.database.species_records((item.record_id,))[0]
        self.assertTrue(any("2.891" in w.message for w in record.warnings))

    def test_gas_fugacity_and_ligand_activity_have_separate_energy_terms(self):
        item = next(s for s in self.database.load_system("Sn", ligand_ids=("bromide-br",)).species
                    if s.formula_ascii == "SnBr4" and s.is_gas)
        conditions = self.conditions("bromide-br")
        changed = replace(conditions, gas_fugacities=pb.GasFugacityModel(default_log10_fugacity=-2))
        baseline = transformed_gibbs_J_mol_metal(item, self.database.reference_state, conditions, 4, .3)
        actual = transformed_gibbs_J_mol_metal(item, self.database.reference_state, changed, 4, .3)
        expected = -2 * GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        self.assertTrue(math.isclose(float(actual - baseline), expected, abs_tol=1e-8))
        self.assertFalse(any(s.record_id == item.record_id for s in self.database.load_system("Sn").species))
