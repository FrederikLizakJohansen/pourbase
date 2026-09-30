"""Snapshot of the released dataset.

These tests pin counts and selected results of the bundled database. Update them on purpose
when the data change; they are not tests of the calculation code.
"""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from support import ROOT

import pourbase as pb

TABLES = {
    "metadata", "species", "thermochemistry", "sources", "phases", "warnings",
    "materials_project_matches", "materials_project_energies", "ligands",
    "reported_thermochemistry", "computational_fallbacks", "element_coverage",
}


class DatasetSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_tables_counts_and_integrity(self) -> None:
        with closing(sqlite3.connect(self.database.path)) as connection:
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )}
            self.assertEqual(tables, TABLES)
            for table, count in (("species", 460), ("reported_thermochemistry", 1414),
                                 ("computational_fallbacks", 6), ("element_coverage", 118)):
                self.assertEqual(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0], count, table)
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.database.metadata["dataset_version"], "1.0.0")
        self.assertEqual(self.database.metadata["publication_status"], "release_candidate_pending_collaborator_review")
        self.assertEqual(len(self.database.available_systems()), 74)

    def test_every_gibbs_status_is_known(self) -> None:
        with closing(sqlite3.connect(self.database.path)) as connection:
            statuses = {row[0] for row in connection.execute("SELECT DISTINCT gibbs_status FROM thermochemistry")}
        self.assertLessEqual(statuses, {item.value for item in pb.EvidenceStatus})

    def test_periodic_screen(self) -> None:
        screen = pb.screen_periodic_table(self.database, pH=0, potential_V=1.6, reference="RHE")
        self.assertEqual((len(screen.elements), screen.supported_count, screen.calculated_count), (118, 74, 69))
        self.assertEqual(screen.element("Fe").stable.species, "Fe³⁺")
        titanium = screen.element("Ti")
        self.assertEqual((titanium.stable.species, titanium.category, titanium.structure_label),
                         ("TiO₂", pb.Category.SOLID_OXIDE, "rutile"))
        fallback = pb.screen_periodic_table(self.database, pH=0, potential_V=1.6, reference="RHE",
                                            energy_policy="experimental_then_mp")
        self.assertEqual(fallback.calculated_count, 74)
        platinum = self.database.load_system("Pt", energy_policy="experimental_then_mp")
        self.assertEqual({item.formula_ascii for item in platinum.species
                          if item.gibbs_status is pb.EvidenceStatus.MATERIALS_PROJECT_FALLBACK}, {"PtO", "PtO2"})

    def test_materials_project_rows(self) -> None:
        rows = self.database.materials_project_thermochemistry()
        self.assertEqual((len(rows), len({item["record_id"] for item in rows})), (299, 105))
        self.assertEqual(sum(item["experimental_enthalpy_eV_atom"] is not None for item in rows), 288)
        with tempfile.TemporaryDirectory() as directory:
            metadata = pb.write_mp_thermochemistry_bundle(self.database, directory)
            self.assertEqual(metadata["materials_project_energy_rows"], 299)
            for name in ("mp-enthalpy-comparison.png", "mp-gibbs-comparison.pdf",
                         "mp-thermochemistry-points.csv", "mp-thermochemistry-metadata.json", "README.md"):
                self.assertGreater((Path(directory) / name).stat().st_size, 100)

    def test_public_documents_do_not_mention_the_curation_record(self) -> None:
        text = "\n".join((ROOT / name).read_text(encoding="utf-8")
                         for name in ("README.md", "docs/DATA_DICTIONARY.md", "CITATION.cff"))
        self.assertNotIn("audit", text.lower())


if __name__ == "__main__":
    unittest.main()
