"""Snapshot of the released dataset.

These tests pin counts and selected results of the bundled database. Update them on purpose
when the data change; they are not tests of the calculation code.
"""

from __future__ import annotations

import math
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
            for table, count in (("species", 493), ("reported_thermochemistry", 1630),
                                 ("computational_fallbacks", 6), ("element_coverage", 118)):
                self.assertEqual(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0], count, table)
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.database.metadata["dataset_version"], "1.0.0")
        self.assertEqual(self.database.metadata["publication_status"], "release_candidate_pending_collaborator_review")
        self.assertEqual(len(self.database.available_systems()), 74)

    def test_retained_values_have_one_preferred_per_available_property(self) -> None:
        with closing(sqlite3.connect(self.database.path)) as connection:
            duplicates = connection.execute(
                "SELECT record_id,property FROM reported_thermochemistry "
                "WHERE selected_as_recommended=1 GROUP BY record_id,property HAVING count(*)>1"
            ).fetchall()
            self.assertEqual(duplicates, [])
            for prop, field in (("gibbs_energy_of_formation", "gibbs_energy_J_mol"),
                                ("absolute_entropy", "entropy_J_mol_K"),
                                ("enthalpy_of_formation", "formation_enthalpy_J_mol")):
                missing = connection.execute(
                    f"SELECT t.record_id FROM thermochemistry t WHERE t.{field} IS NOT NULL "
                    "AND NOT EXISTS (SELECT 1 FROM reported_thermochemistry r "
                    f"WHERE r.record_id=t.record_id AND r.property=? "
                    f"AND r.selected_as_recommended=1 AND r.value=t.{field})", (prop,)
                ).fetchall()
                self.assertEqual(missing, [], prop)

    def test_miron_evaluations_and_discrepant_representations_are_retained(self) -> None:
        aluminum, calcium = self.database.species_records((
            "gfe-al-al-q+3-aqueous-aq", "gfe-ca-cacl-q+1-aqueous-aq"
        ))
        self.assertEqual(aluminum.thermochemistry.gibbs_energy_J_mol.value, -485000.0)
        energies = {row.value for row in aluminum.reported if row.property == "gibbs_energy_of_formation"}
        self.assertGreaterEqual(energies, {-485000.0, -486627.0, -486594.0})
        calcium_energies = {row.value for row in calcium.reported if row.property == "gibbs_energy_of_formation"}
        self.assertEqual(calcium_energies, {-689297.0, -689279.0})
        self.assertEqual(calcium.thermochemistry.gibbs_energy_J_mol.value, -689297.0)
        self.assertEqual(calcium.thermochemistry.gibbs_energy_J_mol.status, "source_verified_estimate")
        self.assertTrue(any(row.type == "miron_published_dataset_discrepancy" for row in calcium.warnings))
        self.assertTrue(all(row.source and row.source.locator for row in calcium.reported))

    def test_carbonate_complex_uses_explicit_balanced_ligand_reservoir(self) -> None:
        ordinary = self.database.load_system("Ca")
        enabled = self.database.load_system("Ca", ligand_ids=("carbonate-co3",))
        self.assertFalse(any(row.formula_ascii == "CaHCO3" for row in ordinary.species))
        bicarbonate = next(row for row in enabled.species if row.formula_ascii == "CaHCO3")
        self.assertEqual((bicarbonate.electrons_per_metal, bicarbonate.protons_per_metal), (2.0, -1.0))
        self.assertEqual((bicarbonate.core_oxygen_count, bicarbonate.ligand_count), (0.0, 1.0))
        self.assertEqual(bicarbonate.ligand_gibbs_energy_J_mol, -527810.0)

    def test_mines_copper_evaluations_preserve_existing_preference(self) -> None:
        copper, trichloride = self.database.species_records((
            "gfe-cu-cucl2-q-1-aqueous-aq", "gfe-cu-cucl3-q-2-aqueous-aq"
        ))
        self.assertEqual(copper.thermochemistry.gibbs_energy_J_mol.value, -245600.0)
        evaluations = {row.source.source_id.split("_")[1]: row.value for row in copper.reported
                       if row.property == "gibbs_energy_of_formation"
                       and row.source is not None
                       and row.source.source_id.startswith("MINES_")}
        self.assertAlmostEqual(evaluations["2001"], -57610 * 4.184)
        self.assertAlmostEqual(evaluations["2005"], -58241 * 4.184)
        self.assertAlmostEqual(copper.thermochemistry.formation_enthalpy_J_mol.value, -65648 * 4.184)
        self.assertEqual(copper.thermochemistry.formation_enthalpy_J_mol.status, "source_verified_estimate")
        encoded = next(row for row in self.database.load_system("Cu", ligand_ids=("chloride-cl",)).species
                       if row.record_id == trichloride.record_id)
        self.assertEqual((encoded.charge, encoded.ligand_count,
                          encoded.electrons_per_metal), (-2.0, 3.0, 1.0))
        self.assertTrue(any(row.type == "mines_later_evaluation_pending" for row in trichloride.warnings))

    def test_mines_zinc_hydration_uses_the_stored_formula_basis(self) -> None:
        zinc, gold = self.database.species_records((
            "gfe-zn-zn-oh-2-q+0-aqueous-aq", "gfe-au-au-oh-2-q-1-aqueous-aq"
        ))
        self.assertEqual(zinc.thermochemistry.gibbs_energy_J_mol.value, -525020.0)
        normalized = next(row for row in zinc.reported if row.property == "gibbs_energy_of_formation"
                          and row.source is not None
                          and row.source.source_id.startswith("MINES_2014_"))
        self.assertAlmostEqual(normalized.value, -65720 * 4.184 - 237129)
        self.assertIn("CSV logical record 41", normalized.source.locator)
        self.assertAlmostEqual(zinc.thermochemistry.formation_enthalpy_J_mol.value,
                               -72176 * 4.184 - 285830)
        self.assertTrue(any(row.type == "mines_hydration_normalization" for row in zinc.warnings))
        self.assertAlmostEqual(gold.thermochemistry.formation_enthalpy_J_mol.value, -94664 * 4.184)
        self.assertTrue(any(row.type == "mines_native_enthalpy_discrepancy" for row in gold.warnings))

    def test_every_gibbs_status_is_known(self) -> None:
        with closing(sqlite3.connect(self.database.path)) as connection:
            statuses = {row[0] for row in connection.execute("SELECT DISTINCT gibbs_status FROM thermochemistry")}
        self.assertLessEqual(statuses, {item.value for item in pb.EvidenceStatus})

    def test_original_hydrolysis_fits_preserve_parent_and_hydration_basis(self) -> None:
        nickel, solid, iron, hydrated = self.database.species_records((
            "gfe-ni-ni-oh-2-q+0-aqueous-aq", "gfe-ni-ni-oh-2-q+0-solid-s",
            "gfe-fe-fe-q+2-aqueous-aq", "gfe-fe-hfeo2-q-1-aqueous-aq"
        ))
        rt_log10 = 8.31446261815324 * 298.15 * math.log(10)
        original_solid = next(row for row in solid.reported if row.source
                              and row.source.source_id.startswith("GonzalezSiso_2018_original_fit_"))
        self.assertEqual(solid.thermochemistry.gibbs_energy_J_mol.value, -457100.0)
        self.assertAlmostEqual(-(nickel.thermochemistry.gibbs_energy_J_mol.value
                                 - original_solid.value) / rt_log10, -7.6, places=6)
        self.assertEqual(nickel.thermochemistry.gibbs_energy_J_mol.status, "source_verified_estimate")
        original_iron = next(row for row in hydrated.reported if row.source
                            and row.source.source_id.startswith("Furst_2025_2026_original_fit_"))
        self.assertEqual(hydrated.thermochemistry.gibbs_energy_J_mol.value, -370871.0)
        self.assertAlmostEqual(-(original_iron.value - iron.thermochemistry.gibbs_energy_J_mol.value
                                 - 2 * self.database.reference_state.water_gibbs_energy_J_mol)
                               / rt_log10, -32.48, places=6)
        self.assertIn("Fe(OH)3(-)=HFeO2(-)+H2O", original_iron.source.locator)

    def test_open_nitrogen_estimate_uses_absolute_entropy(self) -> None:
        nitrogen = self.database.species_records(("gfe-n-n2-q+0-aqueous-aq",))[0]
        triplet = {row.property: row for row in nitrogen.reported
                   if row.source and row.source.source_id.startswith("Sander_2023_N2_molal_estimate_")}
        self.assertEqual(set(triplet), {
            "gibbs_energy_of_formation", "enthalpy_of_formation", "absolute_entropy"
        })
        entropy = triplet["absolute_entropy"].value
        self.assertGreater(entropy, 0)
        self.assertAlmostEqual(entropy, 191.61 + (triplet["enthalpy_of_formation"].value
                                                - triplet["gibbs_energy_of_formation"].value) / 298.15,
                               places=5)
        self.assertTrue(all(not row.selected_as_recommended for row in triplet.values()))
        self.assertTrue(any(row.type == "absolute_entropy_convention_issue" for row in nitrogen.warnings))

    def test_open_evaluations_are_available_without_changing_preferences(self) -> None:
        lead, aluminum = self.database.species_records((
            "gfe-pb-pbo2-q+0-solid-plattnerite", "gfe-al-al-q+0-solid-metal"
        ))
        self.assertEqual(lead.thermochemistry.gibbs_energy_J_mol.value, -215397.0)
        alternatives = {row.property: row for row in lead.reported
                        if row.source and row.source.source_id.startswith("USGS_B2131_1995_retained_")}
        self.assertEqual(set(alternatives), {
            "gibbs_energy_of_formation", "enthalpy_of_formation", "absolute_entropy"
        })
        for prop, value, uncertainty in (("gibbs_energy_of_formation", -218300.0, 2900.0),
                                          ("enthalpy_of_formation", -277400.0, 2900.0),
                                          ("absolute_entropy", 71.8, 0.4)):
            row = alternatives[prop]
            self.assertEqual(row.value, value)
            self.assertEqual(row.uncertainty, uncertainty)
            self.assertFalse(row.selected_as_recommended)
            self.assertIn("plattnerite", row.source.locator)
            self.assertIn("p. 209", row.source.locator)
        self.assertEqual(aluminum.thermochemistry.entropy_J_mol_K.value, 28.275)
        entropy = next(row for row in aluminum.reported if row.property == "absolute_entropy"
                       and row.source and row.source.source_id.startswith("NBS_PDR_M32124_retained_"))
        self.assertEqual(entropy.value, 28.33)
        self.assertFalse(entropy.selected_as_recommended)
        self.assertIn("CSV logical record 3558", entropy.source.locator)

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
