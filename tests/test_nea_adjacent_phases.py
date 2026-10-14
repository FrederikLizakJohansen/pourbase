"""Metastable liquid and gas observations in the adjacent NEA phase review."""

import unittest

import pourbase as pb
from pourbase.engine import transformed_gibbs_J_mol_metal


class NEAAdjacentPhaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_supercooled_liquid_is_distinct_from_the_nickel_reference(self):
        system = self.database.load_system("Ni")
        liquid = next(s for s in system.species if s.record_id == "nea02f-ni-liquid")
        metal = next(s for s in system.species
                     if s.record_id == "gfe-ni-ni-q+0-solid-metal")
        self.assertEqual(liquid.phase, "liquid")
        self.assertTrue(liquid.is_condensed)
        self.assertEqual((liquid.electrons_per_metal, liquid.protons_per_metal), (0, 0))
        self.assertEqual(metal.gibbs_energy_J_mol, 0)
        for pH, potential in ((0, -2), (7, 0), (14, 2)):
            self.assertEqual(float(transformed_gibbs_J_mol_metal(
                liquid, self.database.reference_state, pb.PourbaixConditions(), pH, potential)),
                14035)
        record = self.database.species_records((liquid.record_id,))[0]
        self.assertEqual(record.thermochemistry.entropy_J_mol_K.value, 41.49)
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, 17500)
        self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.uncertainty, 272)
        self.assertTrue(any("supercooled" in w.message for w in record.warnings))

    def test_gas_properties_and_hydride_sign_survive_explicit_phase_selection(self):
        for rid, gibbs, enthalpy, entropy in (("nea02f-ni-gas", 384686, 430100, 182.19),
                                             ("nea02f-sn-stannane-gas", 188065, 162800, 227.8)):
            with self.subTest(record_id=rid):
                record = self.database.species_records((rid,))[0]
                self.assertEqual(record.phase, "gas")
                self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, enthalpy)
                self.assertEqual(record.thermochemistry.entropy_J_mol_K.value, entropy)
                self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.value, gibbs)
                self.assertTrue(any("include_optional_gases=True" in w.message
                                    for w in record.warnings))
                for observation in record.reported:
                    self.assertIn("TableIII-1 printedp44", observation.source.locator)
                    self.assertIn("further sublicensees", observation.source.locator)
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT charge, metal_count, core_hydrogen_count, metal_oxidation_state, "
                "electron_coefficient_per_metal FROM species "
                "WHERE record_id='nea02f-sn-stannane-gas'").fetchone()
        self.assertEqual(tuple(row), (0, 1, 4, 4, -4))

    def test_optional_gases_and_temperature_cache_have_separate_scopes(self):
        from pourbase.temperature import at_temperature

        user_database = pb.with_user_species(self.database, ())
        for base in (self.database, pb.with_policy(self.database, self.database.policy),
                     user_database, pb.with_policy(user_database, self.database.policy)):
            for temperature in (298.15, 348.15):
                database = at_temperature(base, temperature)
                for symbol in ("Ni", "Sn"):
                    self._check_gas_scope(database, temperature, symbol)
                with self.assertRaises(TypeError):
                    database.load_system("Ni", include_optional_gases="false")

    def _check_gas_scope(self, database, temperature, symbol):
        with self.subTest(temperature=temperature, symbol=symbol,
                          database=type(database).__name__):
            selected = database.load_system(symbol, include_optional_gases=True)
            self.assertTrue(any(s.is_gas for s in selected.species))
            default = database.load_system(symbol)
            self.assertFalse(any(s.is_gas for s in default.species))
            self.assertIn(pb.ExclusionReason.GAS_NOT_SELECTED,
                          {s.reason for s in default.excluded})
            self.assertIs(selected, database.load_system(symbol, include_optional_gases=True))
            with self.assertRaises(pb.UnsupportedConditionError):
                pb.MassBalanceEngine(database).calculate_system(
                    selected, pb.PourbaixConditions(temperature_K=temperature),
                    pb.TotalMetalConcentration(1e-4))

    def test_default_nickel_and_tin_closed_balances_remain_available(self):
        for symbol in ("Ni", "Sn"):
            with self.subTest(symbol=symbol):
                self.assertFalse(any(s.is_gas for s in self.database.load_system(symbol).species))
                result = pb.MassBalanceEngine(self.database).calculate(
                    symbol, pb.PourbaixConditions(pH_points=5, eh_points=5),
                    pb.TotalMetalConcentration(1e-4))
                self.assertEqual(result.dominant_species_index.shape, (5, 5))
