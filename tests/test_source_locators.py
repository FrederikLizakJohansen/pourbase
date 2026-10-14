"""Property-specific evidence locations must survive API reads and exports."""

import shutil
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from support import ROOT

import pourbase as pb


class SourceLocatorTests(unittest.TestCase):
    def test_shared_source_keeps_each_observations_own_location(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.sqlite"
            shutil.copy2(ROOT / "src/pourbase/data/pourbase.sqlite", path)
            with closing(sqlite3.connect(path)) as connection, connection:
                rows = connection.execute(
                    "SELECT value_id,record_id FROM reported_thermochemistry "
                    "WHERE source_id='NEA_OECD_20261014_Fe' ORDER BY value_id LIMIT 2"
                ).fetchall()
                self.assertEqual(len(rows), 2)
                for index, (value_id, _) in enumerate(rows):
                    connection.execute(
                        "UPDATE reported_thermochemistry SET source_locator=? WHERE value_id=?",
                        (f"Individual table cell {index}", value_id),
                    )
            database = pb.ThermodynamicDatabase(path)
            for index, (value_id, record_id) in enumerate(rows):
                observation = next(row for row in database.species_records((record_id,))[0].reported
                                   if row.value_id == value_id)
                self.assertEqual(observation.source.locator, f"Individual table cell {index}")

    def test_missing_property_location_uses_general_source_location(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.sqlite"
            shutil.copy2(ROOT / "src/pourbase/data/pourbase.sqlite", path)
            with closing(sqlite3.connect(path)) as connection, connection:
                value_id, record_id = connection.execute(
                    "SELECT value_id,record_id FROM reported_thermochemistry "
                    "WHERE source_id='NEA_OECD_20261014_Fe' LIMIT 1"
                ).fetchone()
                connection.execute(
                    "UPDATE reported_thermochemistry SET source_locator=NULL WHERE value_id=?",
                    (value_id,),
                )
            database = pb.ThermodynamicDatabase(path)
            observation = next(row for row in database.species_records((record_id,))[0].reported
                               if row.value_id == value_id)
            self.assertEqual(observation.source.locator,
                             database.source("NEA_OECD_20261014_Fe").locator)
