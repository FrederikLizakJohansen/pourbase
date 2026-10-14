"""Preserve phase identity and full formula units in the NEA solid extension."""

import sqlite3
import unittest
from contextlib import closing

import pourbase as pb


class NEASolidTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_tin_polymorphs_and_amorphous_phase_remain_distinct(self):
        amorphous, cassiterite, alpha, beta = self.database.species_records((
            "nea02a-sn-sno2-amorphous-tin-dioxide",
            "gfe-sn-sno2-q+0-solid-cassiterite",
            "nea02a-sn-sn-alpha-grey-tin",
            "gfe-sn-sn-q+0-solid-metal",
        ))
        self.assertEqual(amorphous.formula_ascii, cassiterite.formula_ascii)
        self.assertEqual(amorphous.thermochemistry.gibbs_energy_J_mol.value, -511870)
        self.assertEqual(cassiterite.thermochemistry.gibbs_energy_J_mol.value, -516640)
        self.assertIn("amorphous", amorphous.phase_detail)
        self.assertEqual(alpha.thermochemistry.gibbs_energy_J_mol.value, 119)
        self.assertEqual(beta.thermochemistry.gibbs_energy_J_mol.value, 0)
        self.assertEqual(alpha.thermochemistry.formation_enthalpy_J_mol.value, -1980)
        self.assertEqual(alpha.thermochemistry.gibbs_energy_J_mol.status, "verified")

    def test_heat_capacity_columns_do_not_become_entropy(self):
        for record_id, enthalpy in (
            ("nea02a-fe-fecl3-h2o-6-chloride-hexahydrate", -2221926),
            ("nea02a-ni-ni-no3-2-h2o-6-nitrate-hexahydrate", -2214452),
        ):
            record = self.database.species_records((record_id,))[0]
            self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, enthalpy)
            self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
            self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
            self.assertFalse(any(row.property == "absolute_entropy" for row in record.reported))

    def test_fractional_hydration_and_large_formulas_keep_molar_basis(self):
        with closing(sqlite3.connect(self.database.path)) as connection:
            hydrate = connection.execute(
                "SELECT atom_count,core_oxygen_count,core_hydrogen_count FROM species WHERE record_id=?",
                ("nea02a-ni-nico3-h2o-5-5-carbonate-hemiundecahydrate",),
            ).fetchone()
            self.assertEqual(hydrate, (21.5, 5.5, 11))
        system = self.database.load_system("Sn", ligand_ids=("chloride-cl",))
        basic = next(s for s in system.species if s.formula_ascii == "Sn21Cl16(OH)14O6")
        self.assertEqual((basic.metal_count, basic.core_oxygen_count,
                          basic.core_hydrogen_count, basic.ligand_count), (21, 20, 14, 16))
        self.assertEqual(basic.gibbs_energy_J_mol, -7611662)
        self.assertEqual(basic.electrons_per_metal, 2)
        self.assertAlmostEqual(basic.protons_per_metal, 26 / 21)

    def test_sulfide_phase_and_disulfide_reaction_are_explicit(self):
        mackinawite, troilite = self.database.species_records((
            "nea02a-fe-fes-mackinawite", "r05-fe-fes-troilite",
        ))
        self.assertEqual(mackinawite.formula_ascii, troilite.formula_ascii)
        self.assertEqual(mackinawite.thermochemistry.gibbs_energy_J_mol.value, -96677)
        self.assertIsNone(troilite.thermochemistry.gibbs_energy_J_mol.value)
        system = self.database.load_system("Ni", ligand_ids=("sulfide-s",))
        disulfide = next(s for s in system.species if s.formula_ascii == "NiS2")
        self.assertEqual(disulfide.formal_metal_oxidation_state, 2)
        self.assertEqual(disulfide.electrons_per_metal, 4)
        large = next(s for s in system.species if s.formula_ascii == "Ni9S8")
        self.assertEqual(large.gibbs_energy_J_mol, -746803)
        self.assertEqual(large.metal_count, 9)
        self.assertAlmostEqual(large.electrons_per_metal, 16 / 9)
