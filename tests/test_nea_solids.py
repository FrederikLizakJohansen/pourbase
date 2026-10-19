"""Preserve phase identity and full formula units in the NEA solid extension."""

import sqlite3
import unittest
from contextlib import closing
from dataclasses import replace

import numpy as np

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

    def test_wustite_composition_and_entropy_caveat_are_preserved(self):
        wustite, endpoint = self.database.species_records((
            "nea02b-fe-fe0-932o-wustite-fixed-composition",
            "gfe-fe-feo-q+0-solid-wustite-stoichiometric-endmember",
        ))
        self.assertEqual(wustite.formula_ascii, "Fe0.932O")
        self.assertEqual(endpoint.formula_ascii, "FeO")
        self.assertEqual(endpoint.thermochemistry.gibbs_energy_J_mol.value, -251429)
        for value, expected, interval in (
            (wustite.thermochemistry.gibbs_energy_J_mol, -244593, 1906),
            (wustite.thermochemistry.formation_enthalpy_J_mol, -265800, 1900),
            (wustite.thermochemistry.entropy_J_mol_K, 56.690, .490),
        ):
            self.assertEqual((value.value, value.uncertainty), (expected, interval))
            self.assertEqual(value.status, "source_verified_estimate")
            self.assertIn("TableIII-1", value.source.locator)
        residual = next(w for w in wustite.warnings if w.type == "nea02b_entropy_residual_contribution")
        self.assertIn("zero-point configurational", residual.message)
        self.assertIn("2.07", residual.message)

    def test_fractional_metal_count_normalizes_energy_and_precipitation(self):
        system = self.database.load_system("Fe")
        wustite = next(s for s in system.species if s.formula_ascii == "Fe0.932O")
        ion = next(s for s in system.species if s.formula_ascii == "Fe" and s.charge == 2)
        self.assertEqual(wustite.metal_count, .932)
        self.assertAlmostEqual(wustite.electrons_per_metal, 2 / .932)
        integer = replace(wustite, record_id="test-fe233o250", formula_ascii="Fe233O250",
                          metal_count=233, core_oxygen_count=250,
                          gibbs_energy_J_mol=250 * wustite.gibbs_energy_J_mol,
                          gibbs_uncertainty_J_mol=250 * wustite.gibbs_uncertainty_J_mol)
        conditions = pb.PourbaixConditions(pH_points=7, U_points=9)
        systems = [replace(system, species=(ion, solid), excluded=()) for solid in (wustite, integer)]
        diagrams = [pb.PourbaixEngine(self.database).calculate_system(s, conditions) for s in systems]
        np.testing.assert_allclose(diagrams[0].transformed_gibbs_J_mol_metal,
                                   diagrams[1].transformed_gibbs_J_mol_metal, rtol=1e-12, atol=1e-8)
        balances = [pb.MassBalanceEngine(self.database).calculate_system(
            s, conditions, pb.TotalMetalConcentration(1e-4)) for s in systems]
        self.assertGreater(float(balances[0].precipitated_metal_fraction.max()), .9)
        np.testing.assert_allclose(balances[0].dissolved_metal_mol_L,
                                   balances[1].dissolved_metal_mol_L, rtol=1e-11, atol=1e-15)
        for balance in balances:
            np.testing.assert_allclose(balance.dissolved_metal_mol_L
                                       + 1e-4 * balance.precipitated_metal_fraction,
                                       1e-4, rtol=1e-12, atol=1e-16)
