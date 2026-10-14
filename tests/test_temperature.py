from __future__ import annotations

import unittest

import numpy as np

import support  # noqa: F401

import pourbase as pb
from pourbase.exceptions import UnsupportedConditionError
from pourbase.models import ExclusionReason
from pourbase.temperature import DatabaseAtTemperature, at_temperature, water_gibbs_energy_J_mol


class TemperatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_25_degrees_is_the_database_itself(self) -> None:
        self.assertIs(at_temperature(self.database, 298.15), self.database)
        base = pb.calculate(pb.Scenario("Fe"))
        np.testing.assert_array_equal(base.diagram.stable_species_index,
                                      pb.calculate(pb.Scenario("Fe", temperature_K=298.15)).diagram.stable_species_index)

    def test_water_follows_the_steam_tables(self) -> None:
        # NIST-JANAF: ΔfG°(H2O, l) = -225.160 kJ/mol at 373.15 K; the database holds -237.129 at 298.15 K
        self.assertAlmostEqual(water_gibbs_energy_J_mol(-237129.0, 373.15) / 1000, -225.16, delta=0.05)

    def test_gibbs_energies_shift_by_the_entropy_of_formation(self) -> None:
        view = DatabaseAtTemperature(self.database, 348.15)
        entropies = view.formation_entropies()
        cold = {item.record_id: item for item in self.database.load_system("Fe").species}
        for item in view.load_system("Fe").species:
            expected = cold[item.record_id].gibbs_energy_J_mol - 50.0 * entropies[item.record_id][0]
            self.assertAlmostEqual(item.gibbs_energy_J_mol, expected, places=6)
            if item.gibbs_status.value != "defined_reference_state":
                self.assertGreater(item.temperature_uncertainty_J_mol, 0.0)

    def test_species_without_entropy_data_are_left_out_and_reported(self) -> None:
        calculation = pb.calculate(pb.Scenario("Fe", temperature_K=353.15))
        left_out = [item for item in calculation.excluded
                    if item.reason is ExclusionReason.TEMPERATURE_DATA_UNAVAILABLE]
        self.assertTrue(left_out)
        kept = {item.record_id for item in calculation.diagram.system.species}
        self.assertFalse(kept & {item.record_id for item in left_out})

    def test_ligand_species_are_left_out_away_from_25_degrees(self) -> None:
        scenario = pb.Scenario("Cu", temperature_K=323.15,
                               ligands=(pb.LigandActivity("chloride-cl", log10_free_activity=-1.0),))
        system = pb.calculate(scenario).diagram.system
        self.assertTrue(all(item.is_ligand_free for item in system.species))

    def test_temperatures_beyond_100_degrees_are_refused(self) -> None:
        with self.assertRaises(UnsupportedConditionError):
            pb.calculate(pb.Scenario("Fe", temperature_K=423.15))

    def test_the_oxygen_line_moves_with_temperature(self) -> None:
        hot = pb.calculate(pb.Scenario("Fe", temperature_K=373.15)).diagram
        self.assertAlmostEqual(float(hot.oer_V[0]), 1.167, places=3)


if __name__ == "__main__":
    unittest.main()
