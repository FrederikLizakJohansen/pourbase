"""The element production table: one row per element, cited values and explicit gaps."""

from contextlib import closing
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from support import ROOT
import pourbase as pb

REUSE_BASES = {"U.S. public domain", "U.S. public domain; data release marked CC0 1.0"}
WITHHELD = {"H", "B", "O", "Ne", "Ar", "Sc", "Ge", "Kr", "Rb", "Xe", "Cs", "La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd",
            "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Hf", "Os", "U"}


class ElementProductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = pb.ThermodynamicDatabase.bundled()
        cls.rows = cls.database.element_production()
        cls.by_symbol = {row["symbol"]: row for row in cls.rows}

    def test_one_row_for_every_element(self) -> None:
        self.assertEqual([(row["atomic_number"], row["symbol"]) for row in self.rows],
                         [(row["atomic_number"], row["symbol"]) for row in self.database.element_coverage()])
        self.assertEqual(sum(row["production_t_per_year"] is not None for row in self.rows), 54)

    def test_every_value_is_cited_from_usgs_without_conditions(self) -> None:
        for row in self.rows:
            if row["production_t_per_year"] is None:
                continue
            with self.subTest(symbol=row["symbol"]):
                self.assertIn("U.S. Geological Survey", row["source_citation"])
                self.assertTrue(row["source_url"].startswith("https://"))
                self.assertTrue(row["source_locator"])
                self.assertIn(row["reuse_basis"], REUSE_BASES)
                self.assertIsNotNone(row["reference_year"])

    def test_gaps_are_explicit_and_carry_no_value(self) -> None:
        for row in self.rows:
            if row["value_basis"] != "gap":
                continue
            with self.subTest(symbol=row["symbol"]):
                self.assertIsNone(row["production_t_per_year"])
                self.assertIsNone(row["source_citation"])
                self.assertTrue(row["notes"])

    def test_values_with_redistribution_conditions_stay_withheld(self) -> None:
        for symbol in WITHHELD:
            with self.subTest(symbol=symbol):
                self.assertEqual(self.by_symbol[symbol]["value_basis"], "gap")
                self.assertTrue(self.by_symbol[symbol]["notes"].startswith("Withheld"))

    def test_released_values(self) -> None:
        expected = {"Fe": 1_600_000_000, "Au": 3_300, "Pt": 170, "Rh": 21, "Ru": 27, "Ir": 6.5, "C": 1_800_000}
        for symbol, value in expected.items():
            with self.subTest(symbol=symbol):
                self.assertEqual(self.by_symbol[symbol]["production_t_per_year"], value)
        self.assertEqual(self.by_symbol["Rh"]["value_basis"], "modelled")
        self.assertEqual(self.by_symbol["Tl"]["reference_year"], 2023)

    def test_a_database_without_the_table_opens_and_returns_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "without.sqlite"
            shutil.copyfile(ROOT / "src/pourbase/data/pourbase.sqlite", path)
            with closing(sqlite3.connect(path)) as connection, connection:
                connection.execute("DROP TABLE element_production")
            self.assertEqual(pb.ThermodynamicDatabase(path).element_production(), ())


if __name__ == "__main__":
    unittest.main()
