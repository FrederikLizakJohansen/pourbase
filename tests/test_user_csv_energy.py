"""CSV formation-energy naming and compatibility with older files."""

import tempfile
import unittest
from pathlib import Path

from pourbase import open_database, read_user_species, with_user_species, dataset_from_csv


class UserCsvEnergyTest(unittest.TestCase):
    def test_new_and_legacy_columns_and_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "species.csv"
            for column in ("formation_energy_kJ_mol", "gibbs_energy_kJ_mol"):
                path.write_text(f"symbol,formula,phase,{column}\nZn,ZnO,solid,-320\n")
                species, = read_user_species(path)
                self.assertEqual((species.species, species.charge, species.citation), ("ZnO", 0, "user supplied"))
                self.assertEqual(species.gibbs_energy_J_mol, -320000)
                overlay = with_user_species(open_database(), path)
                self.assertEqual(overlay.species_records([species.record_id])[0].thermochemistry.gibbs_energy_J_mol.value, -320000)
                standalone = dataset_from_csv(path, Path(directory) / "dataset.sqlite")
                self.assertEqual(standalone.species_records([species.record_id])[0].thermochemistry.gibbs_energy_J_mol.value, -320000)

    def test_conflicting_columns_raise(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "species.csv"
            path.write_text("symbol,formula,phase,formation_energy_kJ_mol,gibbs_energy_kJ_mol\nZn,ZnO,solid,-320,-321\n")
            with self.assertRaisesRegex(ValueError, "disagree"):
                read_user_species(path)
