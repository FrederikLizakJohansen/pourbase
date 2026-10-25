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
    "metadata", "species", "sources", "phases", "warnings",
    "materials_project_matches", "materials_project_energies", "ligands", "additional_components",
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
            for table, count in (("species", 1453), ("reported_thermochemistry", 4434),
                                 ("sources", 1792), ("warnings", 2180), ("additional_components", 59),
                                 ("computational_fallbacks", 6), ("element_coverage", 118)):
                self.assertEqual(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0], count, table)
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.database.metadata["dataset_version"], "1.0.0")
        self.assertEqual(self.database.metadata["publication_status"], "release_candidate_pending_collaborator_review")
        self.assertEqual(len(self.database.available_systems()), 75)

    def test_every_recommended_value_is_a_reported_value(self) -> None:
        recommended = self.database.recommended_value_ids()
        with closing(self.database.connect()) as connection:
            for prop, field, prefix in (("gibbs_energy_of_formation", "gibbs_energy_J_mol", "gibbs"),
                                        ("absolute_entropy", "entropy_J_mol_K", "entropy"),
                                        ("enthalpy_of_formation", "formation_enthalpy_J_mol", "formation_enthalpy")):
                rows = connection.execute(
                    f"SELECT t.{prefix}_value_id, r.value, t.{field} FROM selected_thermochemistry t "
                    f"JOIN reported_thermochemistry r ON r.value_id = t.{prefix}_value_id "
                    f"WHERE t.{field} IS NOT NULL").fetchall()
                self.assertTrue(rows, prop)
                self.assertTrue(all(value_id in recommended and value == stored for value_id, value, stored in rows),
                                prop)
                missing = connection.execute(
                    f"SELECT count(*) FROM selected_thermochemistry WHERE {field} IS NOT NULL AND {prefix}_value_id IS NULL"
                ).fetchone()[0]
                self.assertEqual(missing, 0, prop)

    def test_slop_bromide_complex_uses_explicit_free_ligand(self) -> None:
        rid = "r06-na-nabr-q+0-aq"
        default = self.database.load_system("Na")
        self.assertNotIn(rid, {s.record_id for s in default.species})
        buffered = self.database.load_system("Na", ligand_ids=("bromide-br",))
        complex_ = next(s for s in buffered.species if s.record_id == rid)
        self.assertEqual((complex_.metal_count, complex_.ligand_count,
                          complex_.electrons_per_metal), (1, 1, 1))
        self.assertEqual(complex_.ligand_gibbs_energy_J_mol, -103960)
        self.assertEqual(complex_.gibbs_energy_J_mol, -358192.24)
        conditions = pb.PourbaixConditions(
            pH_points=9, U_points=7,
            ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity("bromide-br", log10_free_activity=-3),)))
        diagram = pb.PourbaixEngine(self.database).calculate("Na", conditions, allow_incomplete=True)
        self.assertIn(rid, {s.record_id for s in diagram.system.species})

    def test_shock_iron_fits_retain_their_own_reference_enthalpies(self) -> None:
        record = self.database.species_records(("gfe-fe-feoh-q+1-aqueous-aq",))[0]
        self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.value, -275916)
        rows = [r for r in record.reported
                if r.source and r.source.source_id.startswith("Shock1997_R06_")]
        self.assertEqual({r.value for r in rows if r.property == "gibbs_energy_of_formation"},
                         {-275516.4, -267022.88})
        self.assertEqual({r.value for r in rows if r.property == "absolute_entropy"},
                         {-41.84, -75.312})
        self.assertEqual({r.value for r in rows if r.property == "enthalpy_of_formation"},
                         {-326705.47535, -328191.63215})
        self.assertEqual(record.thermochemistry.entropy_J_mol_K.value, -41.84)
        for row in rows:
            if row.property == "enthalpy_of_formation":
                self.assertIn("NBS-derived", row.source.source_id)
                self.assertIn("same-variant", row.source.locator)
                self.assertIsNone(row.uncertainty)

    def test_shock_remaining_fits_preserve_preferences_and_hydration(self) -> None:
        cobalt, zinc, aluminium = self.database.species_records((
            "r06-co-cooh-q+1-aq", "gfe-zn-zn-oh-2-q+0-aqueous-aq",
            "gfe-al-aloh-q+2-aqueous-aq"))
        self.assertEqual(cobalt.thermochemistry.gibbs_energy_J_mol.value, -234408.6)
        self.assertEqual(cobalt.thermochemistry.formation_enthalpy_J_mol.value, -286420.56935)
        self.assertEqual(zinc.thermochemistry.gibbs_energy_J_mol.value, -525020)
        self.assertEqual(aluminium.thermochemistry.gibbs_energy_J_mol.value, -697880)
        rows = {r.property: r for r in zinc.reported
                if r.source and r.source.source_id.startswith("Shock1997_R06_remaining-")}
        self.assertEqual(rows["gibbs_energy_of_formation"].value, -519214.28)
        self.assertEqual(rows["absolute_entropy"].value, 61.542)
        self.assertEqual(rows["enthalpy_of_formation"].value, -613402.8465)
        self.assertTrue(all(not r.selected_as_recommended for r in rows.values()))
        self.assertIn("source formula + 1 H2O(l)", rows["absolute_entropy"].source.locator)

    def test_shock_paper_identity_corrects_native_charge_errors(self) -> None:
        gallium, yttrium = self.database.species_records((
            "r06-ga-ga-oh-3-q+0-aq", "gfe-y-yo2-q-1-aqueous-aq"))
        self.assertEqual(gallium.formula_ascii, "Ga(OH)3")
        self.assertEqual(gallium.thermochemistry.entropy_J_mol_K.value, 82.0436)
        self.assertIsNone(gallium.thermochemistry.gibbs_energy_J_mol.value)
        self.assertIn("native release charge=1.0", gallium.reported[0].source.locator)
        with closing(sqlite3.connect(self.database.path)) as connection:
            charges = dict(connection.execute(
                "SELECT record_id,charge FROM species WHERE record_id IN (?,?)",
                (gallium.record_id, yttrium.record_id)))
        self.assertEqual(charges, {gallium.record_id: 0, yttrium.record_id: -1})
        self.assertEqual(sum(r.property == "absolute_entropy" and r.value == 87.0272
                             for r in yttrium.reported), 1)

    def test_shock_unresolved_entropy_ancestry_adds_no_observations(self) -> None:
        with closing(sqlite3.connect(self.database.path)) as connection:
            rows = connection.execute(
                "SELECT value_id FROM reported_thermochemistry "
                "WHERE record_id IN (?,?,?) AND property='absolute_entropy' "
                "AND source_id LIKE 'Shock1997_R06_remaining-%'",
                ("gfe-zr-zro-q+2-aqueous-aq", "gfe-hf-hfo-q+2-aqueous-aq",
                 "gfe-cd-cdo2-q-2-aqueous-aq")).fetchall()
        self.assertEqual(rows, [])

    def test_shock_entropy_conflicts_keep_dependent_properties_missing(self) -> None:
        records = self.database.species_records((
            "gfe-ni-ni-oh-2-q+0-aqueous-aq", "gfe-pb-pboh-q+1-aqueous-aq"))
        for record in records:
            self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
            self.assertIsNone(record.thermochemistry.formation_enthalpy_J_mol.value)
            rows = [r for r in record.reported
                    if r.source and r.source.source_id.startswith("Shock1997_R06_")]
            self.assertEqual([r.property for r in rows], ["gibbs_energy_of_formation"])
            with closing(sqlite3.connect(self.database.path)) as connection:
                warning = connection.execute(
                    "SELECT message FROM warnings WHERE record_id=? AND warning_type=?",
                    (record.record_id, "shock_r06_original_entropy_conflict")).fetchone()
            self.assertIn("Table 7", warning[0])
            self.assertIn("Table 10", warning[0])

    def test_shock_hydration_and_entropy_only_species_preserve_formula_basis(self) -> None:
        lead, tin = self.database.species_records((
            "r06-pb-pb-oh-2-q+0-aq", "r06-sn-sn-oh-2-q+0-aq"))
        self.assertEqual(lead.formula_ascii, "Pb(OH)2")
        self.assertEqual(lead.thermochemistry.gibbs_energy_J_mol.value, -401769.4)
        self.assertEqual(lead.thermochemistry.entropy_J_mol_K.value, 161.958)
        self.assertEqual(tin.thermochemistry.entropy_J_mol_K.value, 131.8332)
        self.assertEqual(tin.thermochemistry.gibbs_energy_J_mol.value, -457833)
        self.assertIsNone(tin.thermochemistry.formation_enthalpy_J_mol.value)
        self.assertIn("source formula + 1 H2O(l)", tin.reported[0].source.locator)
        solute = next(s for s in self.database.load_system("Pb").species
                      if s.record_id == lead.record_id)
        self.assertEqual((solute.core_oxygen_count, solute.core_hydrogen_count,
                          solute.electrons_per_metal, solute.protons_per_metal), (2, 2, 2, 2))
        self.assertIn(tin.record_id, {s.record_id for s in self.database.load_system("Sn").species})

    def test_slop_retains_zero_and_distinct_entropy_evaluations(self) -> None:
        silver, barium = self.database.species_records((
            "r06-ag-agco3-q-1-aq", "r06-ba-baf-q+1-aq"))
        self.assertEqual(silver.thermochemistry.entropy_J_mol_K.value, 0)
        self.assertEqual(silver.thermochemistry.formation_enthalpy_J_mol.value, -591845.34285)
        entropies = [r for r in barium.reported if r.property == "absolute_entropy"]
        self.assertEqual({r.value for r in entropies}, {23.012, 26.69392})
        self.assertEqual([r.value for r in entropies if r.selected_as_recommended], [23.012])
        self.assertTrue(all("CC BY 4.0" in r.source.citation for r in entropies))

    def test_slop_hydration_uses_stored_formula_and_preserves_preferred_gibbs(self) -> None:
        record = self.database.species_records(("gfe-si-h3sio4-q-1-aqueous-aq",))[0]
        rows = {r.property: r for r in record.reported
                if r.source and r.source.source_id.startswith("Sverjensky1997_R06_")}
        self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.value, -1252304)
        self.assertEqual(rows["gibbs_energy_of_formation"].value, -1253008.384)
        self.assertFalse(rows["gibbs_energy_of_formation"].selected_as_recommended)
        self.assertEqual(rows["absolute_entropy"].value, 90.83)
        self.assertEqual(rows["enthalpy_of_formation"].value, -1431792.2426)
        self.assertIn("Hydration", rows["absolute_entropy"].source.locator)
        self.assertIn("NBS CSV column 10", rows["enthalpy_of_formation"].source.locator)

    def test_slop_entropy_only_records_keep_original_charge_and_missing_gibbs(self) -> None:
        beryllium, thallium = self.database.species_records((
            "r06-be-becl-q+1-aq", "r06-tl-tlcl-q+2-aq"))
        self.assertIsNone(beryllium.thermochemistry.gibbs_energy_J_mol.value)
        self.assertEqual(beryllium.thermochemistry.entropy_J_mol_K.value, 386.22504)
        self.assertEqual(thallium.thermochemistry.entropy_J_mol_K.value, -77.48768)
        with closing(sqlite3.connect(self.database.path)) as connection:
            charge, oxidation = connection.execute(
                "SELECT charge,metal_oxidation_state FROM species WHERE record_id=?",
                (thallium.record_id,)).fetchone()
        self.assertEqual((charge, oxidation), (2, 3))
        conditions = pb.PourbaixConditions(
            pH_points=9, U_points=7,
            ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity("chloride-cl", log10_free_activity=-3),)))
        diagram = pb.PourbaixEngine(self.database).calculate("Be", conditions, allow_incomplete=True)
        self.assertNotIn(beryllium.record_id, {s.record_id for s in diagram.system.species})

    def test_sulfide_formula_basis_and_polymorphs_balance(self) -> None:
        arsenic = self.database.load_system("As", ligand_ids=("sulfide-s",))
        realgar = next(s for s in arsenic.species if s.record_id == "r05-as-as4s4-realgar")
        self.assertEqual((realgar.metal_count, realgar.ligand_count,
                          realgar.electrons_per_metal), (4, 4, 2))
        self.assertEqual(realgar.gibbs_energy_J_mol, -118400)
        iron = self.database.load_system("Fe", ligand_ids=("sulfide-s",))
        marcasite = next(s for s in iron.species if s.record_id == "r05-fe-fes2-marcasite")
        self.assertEqual((marcasite.metal_oxidation_state, marcasite.electrons_per_metal,
                          marcasite.ligand_count), (2, 4, 2))
        zinc = self.database.load_system("Zn", ligand_ids=("sulfide-s",))
        phases = {s.record_id for s in zinc.species if s.formula_ascii == "ZnS"}
        self.assertEqual(phases, {"r05-zn-zns-sphalerite", "r05-zn-zns-wurtzite"})
        # An entropy-only phase remains accessible without an invented formation G.
        pyrite = self.database.species_records(("r05-fe-fes2-pyrite",))[0]
        self.assertIsNone(pyrite.thermochemistry.gibbs_energy_J_mol.value)
        self.assertEqual(pyrite.thermochemistry.entropy_J_mol_K.value, 52.9)

    def test_phosphate_buffer_and_hydroxyl_balance(self) -> None:
        system = self.database.load_system("Ca", ligand_ids=("phosphate-po4",))
        apatite = next(s for s in system.species if s.formula_ascii == "Ca5(PO4)3OH")
        self.assertEqual((apatite.metal_count, apatite.ligand_count,
                          apatite.core_oxygen_count, apatite.core_hydrogen_count), (5, 3, 1, 1))
        self.assertEqual(apatite.electrons_per_metal, 2)
        self.assertAlmostEqual(apatite.protons_per_metal, .2)
        self.assertEqual(apatite.ligand_gibbs_energy_J_mol, -1018700)
        default = self.database.load_system("Ca")
        self.assertNotIn(apatite.record_id, {s.record_id for s in default.species})
        conditions = pb.PourbaixConditions(
            pH_points=11, U_points=9,
            ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity("phosphate-po4", log10_free_activity=-3),)))
        diagram = pb.PourbaixEngine(self.database).calculate("Ca", conditions, allow_incomplete=True)
        self.assertIn(apatite.record_id, {s.record_id for s in diagram.system.species})

    def test_tih2_review_preserves_hydride_basis_and_source_holds(self) -> None:
        rid = "gfe-ti-tih2-q+0-solid-delta-tih2-cubic-near-298-15-k"
        record = self.database.species_records((rid,))[0]
        thermo = record.thermochemistry
        self.assertEqual((thermo.gibbs_energy_J_mol.value,
                          thermo.formation_enthalpy_J_mol.value,
                          thermo.entropy_J_mol_K.value), (-105073, -144348, 29.711))
        self.assertEqual(len(record.reported), 3)
        self.assertTrue(all(row.selected_as_recommended for row in record.reported))
        self.assertEqual(record.phase_identity.spacegroup_symbol, "Fm-3m")
        solid = next(s for s in self.database.load_system("Ti").species if s.record_id == rid)
        self.assertEqual((solid.core_hydrogen_count, solid.core_oxygen_count,
                          solid.electrons_per_metal, solid.protons_per_metal), (2, 0, -2, -2))
        warnings = {row.type: row for row in record.warnings}
        phase = warnings["tih2_structural_specimen_crosswalk"]
        self.assertIn("TiH1.99", phase.message)
        self.assertIn("separate from the specimens", phase.message)
        nbs = warnings["tih2_nbs_phase_and_composition_hold"]
        self.assertIn("external review ledger", nbs.message)
        inherited = warnings["tih2_inherited_JANAF_source_hold"]
        self.assertIn("reference 7", inherited.message)
        self.assertIn("JANAF", inherited.message)

    def test_tio_original_entropy_preserves_specimen_basis_and_preferences(self) -> None:
        rid = "gfe-ti-tio-q+0-solid-alpha-tio-vacancy-ordered-monoclinic"
        record = self.database.species_records((rid,))[0]
        thermo = record.thermochemistry
        self.assertEqual((thermo.gibbs_energy_J_mol.value,
                          thermo.formation_enthalpy_J_mol.value,
                          thermo.entropy_J_mol_K.value), (-513278, -542665, 34.769))
        alternatives = [row for row in record.reported if not row.selected_as_recommended]
        self.assertEqual(len(alternatives), 1)
        row = alternatives[0]
        self.assertEqual((row.property, row.value, row.unit, row.uncertainty),
                         ("absolute_entropy", 34.26, "J/(mol K)", 0.07))
        self.assertEqual(row.source.source_id, "TiO_fallback_Beyer1982_entropy")
        self.assertIn("1/(1.006+-0.002)", row.source.locator)
        self.assertIn("one week at1180K", row.source.locator)
        self.assertIn("Pressure not explicitly specified", row.source.locator)
        self.assertEqual(record.phase_identity.spacegroup_symbol, "C2/m")
        self.assertEqual(sum(value.selected_as_recommended for value in record.reported), 3)
        with closing(sqlite3.connect(self.database.path)) as connection:
            pressure = connection.execute(
                "SELECT pressure_bar FROM reported_thermochemistry WHERE value_id=?",
                (row.value_id,),
            ).fetchone()[0]
            warnings = {value[0] for value in connection.execute(
                "SELECT warning_type FROM warnings WHERE record_id=?", (rid,),
            )}
        self.assertIsNone(pressure)
        self.assertIn("tio_original_specimen_and_nominal_composition", warnings)
        self.assertIn("tio_formation_JANAF_and_NBS_source_holds", warnings)

    def test_ko2_historical_evaluations_preserve_entropy_warning_and_preferences(self) -> None:
        rid = "gfe-k-ko2-q+0-solid-crystalline-ko2-polymorph-not-assigned"
        record = self.database.species_records((rid,))[0]
        thermo = record.thermochemistry
        self.assertEqual((thermo.gibbs_energy_J_mol.value,
                          thermo.formation_enthalpy_J_mol.value,
                          thermo.entropy_J_mol_K.value), (-239400.0, -284930.0, 116.7))
        alternatives = {(row.source.source_id, row.property): row.value for row in record.reported
                        if row.source and not row.selected_as_recommended}
        self.assertEqual(alternatives, {
            ("NIST_JANAF_K-010", "gibbs_energy_of_formation"): -240589,
            ("NIST_JANAF_K-010", "enthalpy_of_formation"): -284512,
            ("NIST_JANAF_K-010", "absolute_entropy"): 122.499,
            ("KO2_fallback_USBM1982_hf", "enthalpy_of_formation"): -284512,
        })
        self.assertEqual(sum(row.selected_as_recommended for row in record.reported), 3)
        for key in ("nist-047", "nist-049"):
            row = next(row for row in record.reported if row.source and key in row.source.source_id)
            self.assertIn("convention limitations", row.source.locator)
            self.assertIn("hypothesis", row.source.locator)
        self.assertEqual(record.phase_identity.spacegroup_symbol, "I4/mmm")
        solid = next(s for s in self.database.load_system("K").species if s.record_id == rid)
        self.assertEqual((solid.metal_count, solid.core_oxygen_count,
                          solid.electrons_per_metal, solid.protons_per_metal), (1, 2, 4, 4))
        with closing(sqlite3.connect(self.database.path)) as connection:
            recommended = self.database.recommended_value_ids()
            pressures = {source: pressure for value_id, source, pressure in connection.execute(
                "SELECT value_id,source_id,pressure_bar FROM reported_thermochemistry WHERE record_id=?", (rid,),
            ) if value_id not in recommended}
            warnings = {row[0] for row in connection.execute(
                "SELECT warning_type FROM warnings WHERE record_id=?", (rid,),
            )}
        self.assertEqual(pressures, {source: 1.01325 if source == "KO2_fallback_USBM1982_hf" else 1.0
                                    for source, _property in alternatives})
        self.assertIn("ko2_historical_entropy_convention_unresolved", warnings)
        self.assertIn("ko2_formal_oxidation_state_metadata_followup", warnings)

    def test_vo2_federal_alternatives_retain_formula_basis_phase_and_pressure(self) -> None:
        rid = "gfe-v-vo2-q+0-solid-m1-monoclinic"
        record = self.database.species_records((rid,))[0]
        thermo = record.thermochemistry
        self.assertEqual((thermo.gibbs_energy_J_mol.value,
                          thermo.formation_enthalpy_J_mol.value,
                          thermo.entropy_J_mol_K.value), (-659150.0, -713600.0, 51.25))
        self.assertEqual(len(record.reported), 10)
        self.assertEqual(sum(row.selected_as_recommended for row in record.reported), 3)
        alternatives = {(row.source.source_id, row.property): row.value for row in record.reported
                        if row.source and not row.selected_as_recommended}
        self.assertEqual(alternatives, {
            ("NIST_JANAF_O-073", "gibbs_energy_of_formation"): -659222.5,
            ("NIST_JANAF_O-073", "enthalpy_of_formation"): -713581,
            ("NIST_JANAF_O-073", "absolute_entropy"): 51.7625,
            ("VO2_fallback_NBS1971_gf", "gibbs_energy_of_formation"): -659189.2,
            ("VO2_fallback_NBS1971_hf", "enthalpy_of_formation"): -713581.2,
            ("VO2_fallback_NBS1971_entropy", "absolute_entropy"): 51.254,
            ("VO2_fallback_USBM1982_entropy", "absolute_entropy"): 51.4632,
        })
        for row in record.reported:
            if not row.source or not ("fallback" in row.source.source_id or "NBS_PDR" in row.source.source_id):
                continue
            self.assertIsNone(row.uncertainty)
            self.assertIn("multiplied by0.5", row.source.locator)
            self.assertIn("explicit cross-source inference", row.source.locator)
        self.assertEqual(record.phase_identity.spacegroup_symbol, "P21/c")
        solid = next(s for s in self.database.load_system("V").species if s.record_id == rid)
        self.assertEqual((solid.metal_count, solid.core_oxygen_count,
                          solid.electrons_per_metal, solid.protons_per_metal), (1, 2, 4, 4))
        with closing(sqlite3.connect(self.database.path)) as connection:
            recommended = self.database.recommended_value_ids()
            pressures = {source: pressure for value_id, source, pressure in connection.execute(
                "SELECT value_id,source_id,pressure_bar FROM reported_thermochemistry WHERE record_id=?", (rid,),
            ) if value_id not in recommended}
        self.assertEqual({source: pressures[source] for source, _property in alternatives},
                         {source: 1.0 if source.startswith(("NBS_PDR_", "NIST_JANAF")) else 1.01325
                          for source, _property in alternatives})

    def test_minium_retains_distinct_entropy_intervals_and_formula_unit(self) -> None:
        rid = "gfe-pb-pb3o4-q+0-solid-minium"
        record = self.database.species_records((rid,))[0]
        thermo = record.thermochemistry
        self.assertEqual((thermo.gibbs_energy_J_mol.value,
                          thermo.formation_enthalpy_J_mol.value,
                          thermo.entropy_J_mol_K.value), (-601200.0, -718400.0, 211.3))
        self.assertEqual(len(record.reported), 15)
        self.assertEqual(sum(row.selected_as_recommended for row in record.reported), 3)
        retained = {row.source.source_id: row for row in record.reported
                    if row.source and row.source.source_id.startswith("Minium_R05_")}
        self.assertEqual({key: (row.value, row.uncertainty) for key, row in retained.items()}, {
            "Minium_R05_USGS1968_gf": (-600956.288, 8619.04),
            "Minium_R05_USGS1968_hf": (-718392.8, 8368),
            "Minium_R05_USGS1968_entropy": (211.292, 6.276),
            "Minium_R05_NBS1966_gf": (-601240.8, None),
            "Minium_R05_NBS1966_hf": (-718392.8, None),
            "Minium_R05_NBS1966_entropy": (211.292, None),
            "Minium_R05_USBM1961_entropy": (211.292, 6.6944),
        })
        self.assertTrue(all(not row.selected_as_recommended for row in retained.values()))
        self.assertIn("extrapolation12.67", retained["Minium_R05_USBM1961_entropy"].source.locator)
        self.assertIn("H/Greference159 only", retained["Minium_R05_USGS1968_gf"].source.locator)
        self.assertEqual(record.phase_identity.spacegroup_symbol, "P42/mbc")
        solid = next(s for s in self.database.load_system("Pb").species if s.record_id == rid)
        self.assertEqual((solid.metal_count, solid.core_oxygen_count), (3, 4))
        self.assertAlmostEqual(solid.electrons_per_metal, 8 / 3)
        self.assertAlmostEqual(solid.protons_per_metal, 8 / 3)
        with closing(sqlite3.connect(self.database.path)) as connection:
            self.assertEqual(connection.execute(
                "SELECT pressure_bar FROM reported_thermochemistry WHERE record_id=? "
                "AND source_id LIKE 'Minium_R05_%'", (rid,),
            ).fetchall(), [(1.01325,)] * 7)
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM reported_thermochemistry WHERE record_id=? "
                "AND source_id LIKE 'Minium_R05_%1995%'", (rid,),
            ).fetchone()[0], 0)

    def test_anglesite_retains_federal_evaluations_with_original_intervals_and_pressure(self) -> None:
        rid = "gfe-pb-pbso4-q+0-solid-anglesite"
        record = self.database.species_records((rid,))[0]
        thermo = record.thermochemistry
        self.assertEqual((thermo.gibbs_energy_J_mol.value,
                          thermo.formation_enthalpy_J_mol.value,
                          thermo.entropy_J_mol_K.value), (-813140, -919940, 148.57))
        self.assertEqual(len(record.reported), 10)
        self.assertEqual(sum(row.selected_as_recommended for row in record.reported), 3)
        usgs = {row.property: row for row in record.reported
                if row.source and row.source.source_id.startswith("Anglesite_R05_USGS1968")}
        self.assertEqual({prop: (row.value, row.uncertainty) for prop, row in usgs.items()}, {
            "gibbs_energy_of_formation": (-813202.24, 1046),
            "enthalpy_of_formation": (-920023.944, 1087.84),
            "absolute_entropy": (148.57384, 0.29288),
        })
        nbs = {row.property: row for row in record.reported
               if row.source and row.source.source_id.startswith("Anglesite_R05_NBS1966")}
        self.assertEqual({prop: row.value for prop, row in nbs.items()}, {
            "gibbs_energy_of_formation": -813202.24,
            "enthalpy_of_formation": -919936.08,
            "absolute_entropy": 148.57384,
        })
        self.assertTrue(all(not row.selected_as_recommended
                            for row in (*usgs.values(), *nbs.values())))
        self.assertTrue(all(row.uncertainty is None for row in nbs.values()))
        self.assertIn("Sref41", usgs["absolute_entropy"].source.locator)
        self.assertIn("H/Gref159", usgs["enthalpy_of_formation"].source.locator)
        self.assertEqual(record.phase_identity.spacegroup_symbol, "Pnma")
        with closing(sqlite3.connect(self.database.path)) as connection:
            self.assertEqual(connection.execute(
                "SELECT pressure_bar FROM reported_thermochemistry WHERE record_id=? "
                "AND source_id LIKE 'Anglesite_R05_%'", (rid,),
            ).fetchall(), [(1.01325,)] * 6)
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM reported_thermochemistry WHERE record_id=? "
                "AND source_id LIKE 'Anglesite_R05_%1995%'", (rid,),
            ).fetchone()[0], 0)

    def test_litharge_retains_source_intervals_and_pressure_with_existing_preferences(self) -> None:
        rid = "gfe-pb-pbo-q+0-solid-litharge"
        record = self.database.species_records((rid,))[0]
        thermo = record.thermochemistry
        self.assertEqual((thermo.gibbs_energy_J_mol.value,
                          thermo.formation_enthalpy_J_mol.value,
                          thermo.entropy_J_mol_K.value), (-188930.0, -218990.0, 66.5))
        self.assertEqual(len(record.reported), 14)
        self.assertEqual(sum(row.selected_as_recommended for row in record.reported), 3)
        usgs = {row.property: row for row in record.reported
                if row.source and row.source.source_id.startswith("Litharge_R05_USGS1995")}
        self.assertEqual({prop: (row.value, row.uncertainty) for prop, row in usgs.items()}, {
            "gibbs_energy_of_formation": (-188900, 800),
            "enthalpy_of_formation": (-219000, 800),
        })
        usbm = {row.property: row for row in record.reported
                if row.source and row.source.source_id.startswith("Litharge_R05_USBM1982")}
        self.assertEqual({prop: row.value for prop, row in usbm.items()}, {
            "gibbs_energy_of_formation": -188936.888,
            "enthalpy_of_formation": -218990.56,
            "absolute_entropy": 66.5256,
        })
        self.assertTrue(all(not row.selected_as_recommended for row in (*usgs.values(), *usbm.values())))
        self.assertTrue(all(row.uncertainty is None for row in usbm.values()))
        self.assertIn("H/G reference column419 only", usgs["gibbs_energy_of_formation"].source.locator)
        self.assertIn("King128", usbm["absolute_entropy"].source.locator)
        self.assertEqual(record.phase_identity.spacegroup_symbol, "P4/nmm")
        with closing(sqlite3.connect(self.database.path)) as connection:
            self.assertEqual(connection.execute(
                "SELECT pressure_bar FROM reported_thermochemistry WHERE record_id=? "
                "AND source_id LIKE 'Litharge_R05_USBM1982%'", (rid,),
            ).fetchall(), [(1.01325,)] * 3)

    def test_cotunnite_retains_each_entropy_evaluation_and_source_state(self) -> None:
        rid = "gfe-pb-pbcl2-q+0-solid-cotunnite"
        record = self.database.species_records((rid,))[0]
        thermo = record.thermochemistry
        self.assertEqual((thermo.gibbs_energy_J_mol.value,
                          thermo.formation_enthalpy_J_mol.value,
                          thermo.entropy_J_mol_K.value), (-314100, -359410, 136.0))
        self.assertEqual(len(record.reported), 8)
        self.assertEqual(sum(row.selected_as_recommended for row in record.reported), 3)
        for value in (thermo.gibbs_energy_J_mol, thermo.formation_enthalpy_J_mol,
                      thermo.entropy_J_mol_K):
            self.assertIsNone(value.uncertainty)
            self.assertIn("logical record3241", value.source.locator)
        self.assertEqual(sorted((row.value, row.uncertainty) for row in record.reported
                                if row.property == "absolute_entropy"),
                         [(134.7248, 4.184), (135.98, 2.092), (136.0, None), (142.256, 4.184)])
        self.assertEqual(record.phase_identity.status, "resolved")
        self.assertIn("orthorhombic", record.phase_identity.identified_phase)
        self.assertIsNone(record.phase_identity.spacegroup_number)
        with closing(sqlite3.connect(self.database.path)) as connection:
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM reported_thermochemistry WHERE record_id=? "
                "AND source_id LIKE '%USBM1961%' AND pressure_bar IS NULL", (rid,),
            ).fetchone()[0], 3)
            self.assertEqual(connection.execute(
                "SELECT pressure_bar FROM reported_thermochemistry WHERE record_id=? "
                "AND source_id LIKE '%USBM1984%'", (rid,),
            ).fetchall(), [(1.01325,)] * 2)
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM reported_thermochemistry WHERE record_id=? "
                "AND source_id LIKE '%USGS%'", (rid,),
            ).fetchone()[0], 0)

    def test_cotunnite_solubility_and_boundaries_use_two_free_chlorides(self) -> None:
        from dataclasses import replace
        from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10

        rid = "gfe-pb-pbcl2-q+0-solid-cotunnite"
        self.assertFalse(any(s.record_id == rid for s in self.database.load_system("Pb").species))
        system = self.database.load_system("Pb", ligand_ids=("chloride-cl",))
        solid = next(s for s in system.species if s.record_id == rid)
        ion = next(s for s in system.species if s.formula_ascii == "Pb" and s.charge == 2)
        metal = next(s for s in system.species if s.formula_ascii == "Pb" and s.phase == "solid")
        self.assertEqual((solid.metal_count, solid.ligand_count, solid.ligand_charge,
                          solid.electrons_per_metal, solid.protons_per_metal), (1, 2, -1, 2, 0))
        thermal = GAS_CONSTANT_J_MOL_K * 298.15
        chloride_g = -131228
        ksp = math.exp(-(ion.gibbs_energy_J_mol + 2 * chloride_g
                         - solid.gibbs_energy_J_mol) / thermal)
        for ls in (-2, 0, 2):
            conditions = pb.PourbaixConditions(
                pH_points=3, U_points=3,
                ligand_activities=pb.LigandActivityModel((pb.LigandActivity(
                    "chloride-cl", log10_free_activity=ls
                ),)),
            )
            inventory = pb.MassBalanceEngine(self.database).calculate_system(
                replace(system, species=(ion, solid), excluded=()), conditions,
                pb.TotalMetalConcentration(1e-4),
            )
            expected = min(1e-4, ksp / 10**(2 * ls))
            for dissolved, precipitated in zip(inventory.dissolved_metal_mol_L.flat,
                                               inventory.precipitated_metal_fraction.flat):
                self.assertAlmostEqual(dissolved / expected, 1.0, places=10)
                self.assertAlmostEqual((dissolved + 1e-4 * precipitated) / 1e-4, 1.0, places=10)
            boundary = (solid.gibbs_energy_J_mol - 2 * chloride_g
                        - 2 * thermal * LN_10 * ls) / (2 * FARADAY_C_MOL)
            for offset, winner in ((-0.01, metal), (0.01, solid)):
                diagram = pb.PourbaixEngine(self.database).calculate_system(
                    replace(system, species=(metal, solid), excluded=()),
                    replace(conditions, U_min_V=boundary + offset - 0.001,
                            U_max_V=boundary + offset + 0.001),
                )
                self.assertEqual({diagram.system.species[int(i)].record_id
                                  for i in diagram.stable_species_index.flat}, {winner.record_id})

    def test_galena_retains_government_and_open_nbs_evaluations(self) -> None:
        rid = "gfe-pb-pbs-q+0-solid-galena"
        record = self.database.species_records((rid,))[0]
        thermo = record.thermochemistry
        self.assertEqual((thermo.gibbs_energy_J_mol.value,
                          thermo.formation_enthalpy_J_mol.value,
                          thermo.entropy_J_mol_K.value), (-98700.0, -100400.0, 91.2))
        self.assertIsNone(thermo.gibbs_energy_J_mol.uncertainty)
        self.assertIsNone(thermo.formation_enthalpy_J_mol.uncertainty)
        self.assertIsNone(thermo.entropy_J_mol_K.uncertainty)
        usgs = {row.property: row for row in record.reported if row.source and "USGS1995" in row.source.source_id}
        self.assertEqual({prop: (row.value, row.uncertainty, row.selected_as_recommended) for prop, row in usgs.items()},
                         {"gibbs_energy_of_formation": (-96800.0, 2000.0, False),
                          "enthalpy_of_formation": (-98300.0, 2000.0, False)})
        self.assertEqual(len(record.reported), 8)
        self.assertEqual(sum(row.selected_as_recommended for row in record.reported), 3)
        self.assertIn("logical record3275", thermo.entropy_J_mol_K.source.locator)
        self.assertIn("M32124", thermo.gibbs_energy_J_mol.source.locator)
        self.assertIn("cubic", record.phase_identity.identified_phase)
        self.assertEqual(record.phase_identity.status, "resolved")
        self.assertIsNone(record.phase_identity.spacegroup_number)
        entropies = [row.value for row in record.reported if row.property == "absolute_entropy"]
        self.assertEqual(sorted(entropies), [91.2, 91.2112])
        with closing(sqlite3.connect(self.database.path)) as connection:
            pressures = connection.execute(
                "SELECT pressure_bar FROM reported_thermochemistry WHERE record_id=? "
                "AND source_id LIKE '%USBM1987%'", (rid,),
            ).fetchall()
        self.assertEqual(pressures, [(1.01325,)] * 3)

    def test_galena_sulfide_solubility_and_boundaries_use_one_lead_atom(self) -> None:
        from dataclasses import replace
        from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10

        rid = "gfe-pb-pbs-q+0-solid-galena"
        self.assertFalse(any(s.record_id == rid for s in self.database.load_system("Pb").species))
        system = self.database.load_system("Pb", ligand_ids=("sulfide-s",))
        solid = next(s for s in system.species if s.record_id == rid)
        ion = next(s for s in system.species if s.formula_ascii == "Pb" and s.charge == 2)
        metal = next(s for s in system.species if s.formula_ascii == "Pb" and s.phase == "solid")
        self.assertEqual((solid.metal_count, solid.ligand_count, solid.ligand_charge,
                          solid.electrons_per_metal, solid.protons_per_metal), (1, 1, -2, 2, 0))
        thermal = GAS_CONSTANT_J_MOL_K * 298.15
        ksp = math.exp(-(ion.gibbs_energy_J_mol + 120695 - solid.gibbs_energy_J_mol) / thermal)
        for ls in (-18, -12, -6):
            conditions = pb.PourbaixConditions(
                pH_points=3, U_points=3,
                ligand_activities=pb.LigandActivityModel((pb.LigandActivity(
                    "sulfide-s", log10_free_activity=ls
                ),)),
            )
            inventory = pb.MassBalanceEngine(self.database).calculate_system(
                replace(system, species=(ion, solid), excluded=()), conditions,
                pb.TotalMetalConcentration(1e-6),
            )
            expected = min(1e-6, ksp / 10**ls)
            for dissolved, precipitated in zip(inventory.dissolved_metal_mol_L.flat,
                                               inventory.precipitated_metal_fraction.flat):
                self.assertAlmostEqual(dissolved / expected, 1.0, places=10)
                self.assertAlmostEqual((dissolved + 1e-6 * precipitated) / 1e-6, 1.0, places=10)
            boundary = (solid.gibbs_energy_J_mol - 120695 - thermal * LN_10 * ls) / (
                2 * FARADAY_C_MOL
            )
            for offset, winner in ((-0.01, metal), (0.01, solid)):
                diagram = pb.PourbaixEngine(self.database).calculate_system(
                    replace(system, species=(metal, solid), excluded=()),
                    replace(conditions, U_min_V=boundary + offset - 0.001,
                            U_max_V=boundary + offset + 0.001),
                )
                self.assertEqual({diagram.system.species[int(i)].record_id
                                  for i in diagram.stable_species_index.flat}, {winner.record_id})

    def test_europium_trifluoride_preserves_original_solubility_reference(self) -> None:
        from pourbase.constants import GAS_CONSTANT_J_MOL_K, LN_10

        rid = "gfe-eu-euf3-q+0-solid-crystalline-trifluoride"
        record = self.database.species_records((rid,))[0]
        expected = -574100 + 3 * -278790 + GAS_CONSTANT_J_MOL_K * 298.15 * LN_10 * -19.28
        self.assertAlmostEqual(record.thermochemistry.gibbs_energy_J_mol.value, expected, places=6)
        self.assertEqual(len(record.reported), 5)
        observation = next(row for row in record.reported if row.selected_as_recommended)
        self.assertTrue(observation.selected_as_recommended)
        self.assertEqual(observation.status, "source_verified_estimate")
        self.assertIsNone(observation.uncertainty)
        self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
        self.assertIsNone(record.thermochemistry.formation_enthalpy_J_mol.value)
        self.assertIn("column[8]", observation.source.locator)
        self.assertIn("logicalrecord119", observation.source.locator)
        self.assertIsNone(record.phase_identity.spacegroup_number)
        self.assertIn("polymorph unspecified", record.phase_identity.identified_phase)
        hydrate = self.database.species_records((
            "gfe-eu-euf3-h2o-q+0-solid-rare-earth-trifluoride-monohydrate",
        ))[0]
        self.assertIsNone(hydrate.thermochemistry.gibbs_energy_J_mol.value)
        self.assertEqual(hydrate.thermochemistry.formation_enthalpy_J_mol.value, -1873600)

    def test_europium_trifluoride_retains_original_pressure_and_estimate_status(self) -> None:
        rid = "gfe-eu-euf3-q+0-solid-crystalline-trifluoride"
        record = self.database.species_records((rid,))[0]
        alternatives = {row.property: row for row in record.reported
                        if row.source and row.source.source_id.startswith("EuF3_R05_USBM1984_")}
        enthalpy = alternatives["enthalpy_of_formation"]
        entropy = alternatives["absolute_entropy"]
        self.assertEqual((enthalpy.value, enthalpy.status), (-1584062.4, "verified"))
        self.assertEqual((entropy.value, entropy.status), (107.1104, "source_verified_estimate"))
        self.assertTrue(all(row.uncertainty is None and not row.selected_as_recommended
                            for row in alternatives.values()))
        self.assertIn("Kim/reference122", enthalpy.source.locator)
        self.assertIn("S/Cp298 expressly estimated", entropy.source.locator)
        self.assertIsNone(record.thermochemistry.formation_enthalpy_J_mol.value)
        self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
        self.assertEqual(sum(row.selected_as_recommended for row in record.reported), 1)
        with closing(sqlite3.connect(self.database.path)) as connection:
            self.assertEqual(connection.execute(
                "SELECT pressure_bar FROM reported_thermochemistry WHERE record_id=? "
                "AND source_id LIKE 'EuF3_R05_USBM1984_%'", (rid,),
            ).fetchall(), [(1.01325,)] * 2)
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM reported_thermochemistry WHERE record_id=? "
                "AND source_id='EuF3_R05_USBM1984_gf'", (rid,),
            ).fetchone()[0], 0)
            warning = connection.execute(
                "SELECT message FROM warnings WHERE record_id=? "
                "AND warning_type='euf3_USBM1984_G_inherited_JANAF_hold'", (rid,),
            ).fetchone()[0]
            self.assertIn("F2(g) entropy explicitly citesJANAF53", warning)

    def test_europium_trifluoride_uses_three_free_fluorides_in_solubility(self) -> None:
        from dataclasses import replace

        rid = "gfe-eu-euf3-q+0-solid-crystalline-trifluoride"
        self.assertFalse(any(s.record_id == rid for s in self.database.load_system("Eu").species))
        system = self.database.load_system("Eu", ligand_ids=("fluoride-f",))
        solid = next(s for s in system.species if s.record_id == rid)
        ion = next(s for s in system.species if s.formula_ascii == "Eu" and s.charge == 3)
        self.assertEqual((solid.metal_count, solid.ligand_count, solid.ligand_charge,
                          solid.electrons_per_metal, solid.protons_per_metal), (1, 3, -1, 3, 0))
        restricted = replace(system, species=(ion, solid), excluded=())
        for lf in (-6, -3, -1):
            conditions = pb.PourbaixConditions(
                pH_points=3, U_points=3,
                ligand_activities=pb.LigandActivityModel((pb.LigandActivity(
                    "fluoride-f", log10_free_activity=lf
                ),)),
            )
            inventory = pb.MassBalanceEngine(self.database).calculate_system(
                restricted, conditions, pb.TotalMetalConcentration(1e-6),
            )
            expected = min(1e-6, 10 ** (-19.28 - 3 * lf))
            for dissolved, precipitated in zip(inventory.dissolved_metal_mol_L.flat,
                                               inventory.precipitated_metal_fraction.flat):
                self.assertAlmostEqual(dissolved / expected, 1.0, places=10)
                self.assertAlmostEqual((dissolved + 1e-6 * precipitated) / 1e-6, 1.0, places=10)
        lf_boundary = (-19.28 + 6) / 3
        for offset, winner in ((-0.01, ion), (0.01, solid)):
            conditions = pb.PourbaixConditions(
                pH_points=3, U_points=3,
                aqueous_activities=pb.AqueousActivityModel(default_log10_activity=-6),
                ligand_activities=pb.LigandActivityModel((pb.LigandActivity(
                    "fluoride-f", log10_free_activity=lf_boundary + offset
                ),)),
            )
            diagram = pb.PourbaixEngine(self.database).calculate_system(restricted, conditions)
            self.assertEqual({diagram.system.species[int(i)].record_id
                              for i in diagram.stable_species_index.flat}, {winner.record_id})

    def test_lanthanide_hydroxide_alternatives_preserve_preferred_evaluations(self) -> None:
        for symbol, expected, count in (("La", (-1284200, -1416700, 117.8), 5),
                                        ("Nd", (-1283000, -1415600, 129.9), 10)):
            rid = f"gfe-{symbol.lower()}-{symbol.lower()}-oh-3-q+0-solid-hexagonal-ucl3-type"
            record = self.database.species_records((rid,))[0]
            t = record.thermochemistry
            self.assertEqual((t.gibbs_energy_J_mol.value, t.formation_enthalpy_J_mol.value,
                              t.entropy_J_mol_K.value), expected)
            self.assertEqual(len(record.reported), count)
            self.assertEqual(sum(r.selected_as_recommended for r in record.reported), 3)
            alternatives = [r for r in record.reported if r.source.source_id.startswith("Hydroxide_R05_")]
            self.assertEqual(len(alternatives), count - 3)
            self.assertTrue(all(not r.selected_as_recommended and r.source.locator for r in alternatives))
            if symbol == "La":
                nbs = next(r for r in alternatives if "NBS_PDR" in r.source.source_id)
                self.assertEqual(nbs.value, -1410000)
                self.assertIsNone(nbs.uncertainty)
            else:
                wood = next(r for r in alternatives if "Wood2002_original" in r.source.source_id)
                self.assertEqual((wood.value, wood.uncertainty), (-1414000, 5000))
                self.assertTrue(all(r.uncertainty is None for r in alternatives if r != wood))

    def test_wood_hydroxide_reaction_estimate_reproduces_original_solubility_boundary(self) -> None:
        from dataclasses import replace
        from pourbase.constants import GAS_CONSTANT_J_MOL_K, LN_10

        system = self.database.load_system("Nd")
        rid = "gfe-nd-nd-oh-3-q+0-solid-hexagonal-ucl3-type"
        record = self.database.species_records((rid,))[0]
        values = {r.property: r.value for r in record.reported
                  if "Wood_NBS_reaction_derived" in r.source.source_id}
        thermal = GAS_CONSTANT_J_MOL_K * 298.15
        self.assertAlmostEqual(values["gibbs_energy_of_formation"],
                               -671600 + 3 * -237129 + thermal * LN_10 * 17.92, places=6)
        self.assertEqual(values["enthalpy_of_formation"], -696200 + 3 * -285830 + 140300)
        self.assertAlmostEqual(values["absolute_entropy"], -206.7 + 3 * 69.91 + 130)
        ion = next(s for s in system.species if s.formula_ascii == "Nd" and s.charge == 3)
        solid = replace(next(s for s in system.species if s.record_id == rid),
                        gibbs_energy_J_mol=values["gibbs_energy_of_formation"])
        restricted = replace(system, species=(ion, solid), excluded=())
        boundary = (17.92 + 6) / 3
        for offset, winner in ((-0.01, ion), (0.01, solid)):
            conditions = pb.PourbaixConditions(
                pH_min=boundary + offset - 0.001, pH_max=boundary + offset + 0.001,
                pH_points=3, U_points=3,
                aqueous_activities=pb.AqueousActivityModel(default_log10_activity=-6),
            )
            diagram = pb.PourbaixEngine(self.database).calculate_system(restricted, conditions)
            self.assertEqual({diagram.system.species[int(i)].record_id
                              for i in diagram.stable_species_index.flat}, {winner.record_id})

    def test_acanthite_preserves_original_entropy_and_critical_energy_evaluation(self) -> None:
        rid = "gfe-ag-ag2s-q+0-solid-acanthite"
        record = self.database.species_records((rid,))[0]
        thermo = record.thermochemistry
        self.assertEqual((thermo.gibbs_energy_J_mol.value,
                          thermo.formation_enthalpy_J_mol.value,
                          thermo.entropy_J_mol_K.value), (-39700.0, -32000.0, 142.89))
        self.assertEqual(thermo.entropy_J_mol_K.uncertainty, 0.44)
        self.assertIn("1986", thermo.entropy_J_mol_K.source.citation)
        self.assertIn("printedp392/PDFp12", thermo.entropy_J_mol_K.source.locator)
        self.assertEqual(len(record.reported), 4)
        self.assertEqual(sum(row.selected_as_recommended for row in record.reported), 3)
        alternative = next(row for row in record.reported if not row.selected_as_recommended)
        self.assertAlmostEqual(alternative.value, -32000 - 298.15 * (142.89 - 2 * 42.55 - 31.80))
        self.assertEqual(alternative.status, "source_verified_estimate")
        self.assertIsNone(alternative.uncertainty)
        self.assertIn("NIST", alternative.source.locator)
        self.assertIn("monoclinic", record.phase_identity.identified_phase)
        with closing(sqlite3.connect(self.database.path)) as connection:
            pressure = connection.execute(
                "SELECT pressure_bar FROM reported_thermochemistry WHERE record_id=? "
                "AND property='absolute_entropy'", (rid,)
            ).fetchone()[0]
        self.assertIsNone(pressure)

    def test_acanthite_sulfide_boundaries_and_solubility_use_two_silver_atoms(self) -> None:
        from dataclasses import replace
        from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10

        rid = "gfe-ag-ag2s-q+0-solid-acanthite"
        self.assertFalse(any(s.record_id == rid for s in self.database.load_system("Ag").species))
        system = self.database.load_system("Ag", ligand_ids=("sulfide-s",))
        solid = next(s for s in system.species if s.record_id == rid)
        metal = next(s for s in system.species if s.formula_ascii == "Ag" and s.phase == "solid")
        ion = next(s for s in system.species if s.formula_ascii == "Ag" and s.charge == 1)
        self.assertEqual((solid.metal_count, solid.ligand_count, solid.ligand_charge,
                          solid.electrons_per_metal, solid.protons_per_metal), (2, 1, -2, 1, 0))
        self.assertEqual(solid.ligand_gibbs_energy_J_mol, 120695.0)
        thermal = GAS_CONSTANT_J_MOL_K * 298.15
        ksp = math.exp(-(2 * ion.gibbs_energy_J_mol + 120695 - solid.gibbs_energy_J_mol) / thermal)
        for log_activity in (-18, -12, -6):
            conditions = pb.PourbaixConditions(
                pH_points=3, U_points=3,
                ligand_activities=pb.LigandActivityModel((pb.LigandActivity(
                    "sulfide-s", log10_free_activity=log_activity
                ),)),
            )
            boundary = (solid.gibbs_energy_J_mol - 120695 - thermal * LN_10 * log_activity) / (
                2 * FARADAY_C_MOL
            )
            for offset, winner in ((-0.01, metal), (0.01, solid)):
                diagram = pb.PourbaixEngine(self.database).calculate_system(
                    replace(system, species=(metal, solid), excluded=()),
                    replace(conditions, U_min_V=boundary + offset - 0.001,
                            U_max_V=boundary + offset + 0.001),
                )
                self.assertEqual({diagram.system.species[int(i)].record_id
                                  for i in diagram.stable_species_index.flat}, {winner.record_id})
            balanced = pb.MassBalanceEngine(self.database).calculate_system(
                replace(system, species=(ion, solid), excluded=()), conditions,
                pb.TotalMetalConcentration(1e-6),
            )
            expected = math.sqrt(ksp / 10**log_activity)
            for dissolved, precipitated in zip(balanced.dissolved_metal_mol_L.flat,
                                               balanced.precipitated_metal_fraction.flat):
                self.assertAlmostEqual(dissolved / expected, 1.0, places=11)
                self.assertAlmostEqual((dissolved + 1e-6 * precipitated) / 1e-6, 1.0, places=11)

    def test_open_nbs_rare_earth_carbonates_preserve_source_properties(self) -> None:
        for symbol, gibbs, enthalpy, logical_record in (
            ("Y", -3147900.0, None, 7259), ("Tb", None, -3329200.0, 7690),
            ("Sm", -3101900.0, None, 7877), ("Nd", -3114800.0, None, 7954),
            ("Pr", None, -3213000.0, 8046), ("La", -3141600.0, None, 8261),
        ):
            rid = f"gfe-{symbol.lower()}-{symbol.lower()}2-co3-3-q+0-solid-nbs-cr"
            record = self.database.species_records((rid,))[0]
            thermo = record.thermochemistry
            self.assertEqual(thermo.gibbs_energy_J_mol.value, gibbs)
            self.assertEqual(thermo.formation_enthalpy_J_mol.value, enthalpy)
            self.assertIsNone(thermo.entropy_J_mol_K.value)
            self.assertEqual(len(record.reported), 1)
            self.assertTrue(record.reported[0].selected_as_recommended)
            self.assertIsNone(record.reported[0].uncertainty)
            self.assertIn(f"logical record {logical_record}", record.reported[0].source.locator)
            self.assertIn("10.18434/M32124", record.reported[0].source.url)
            self.assertIsNone(record.phase_identity.spacegroup_number)
            self.assertIn("polymorph unspecified", record.phase_identity.identified_phase)
            self.assertFalse(any(s.record_id == rid for s in self.database.load_system(symbol).species))
            activated = self.database.load_system(symbol, ligand_ids=["carbonate-co3"])
            if gibbs is None:
                self.assertTrue(any(s.record_id == rid for s in activated.excluded))
                self.assertFalse(any(s.record_id == rid for s in activated.species))
            else:
                s = next(s for s in activated.species if s.record_id == rid)
                self.assertEqual((s.metal_count, s.ligand_count, s.ligand_charge), (2, 3, -2))
                self.assertEqual((s.core_oxygen_count, s.core_hydrogen_count), (0, 0))
                self.assertEqual(s.formula_ascii, f"{symbol}2(CO3)3")
                self.assertEqual((s.electrons_per_metal, s.protons_per_metal), (3, 0))

    def test_rare_earth_carbonate_boundary_uses_full_two_metal_formula(self) -> None:
        from dataclasses import replace

        system = self.database.load_system("La", ligand_ids=["carbonate-co3"])
        solid = next(s for s in system.species if s.formula_ascii == "La2(CO3)3")
        ion = next(s for s in system.species if s.formula_ascii == "La" and s.charge == 3)
        with closing(sqlite3.connect(self.database.path)) as connection:
            carbonate_g = connection.execute(
                "SELECT gibbs_energy_J_mol FROM ligands WHERE ligand_id='carbonate-co3'"
            ).fetchone()[0]
        factor = 8.31446261815324 * 298.15 * math.log(10)
        boundary = (solid.gibbs_energy_J_mol - 2 * ion.gibbs_energy_J_mol - 3 * carbonate_g) / (3 * factor)
        restricted = replace(system, species=(ion, solid), excluded=())
        for offset, winner in ((-0.1, ion), (0.1, solid)):
            conditions = pb.PourbaixConditions(
                pH_points=3, U_points=3,
                aqueous_activities=pb.AqueousActivityModel(default_log10_activity=0),
                ligand_activities=pb.LigandActivityModel((pb.LigandActivity(
                    "carbonate-co3", log10_free_activity=boundary + offset
                ),)),
            )
            diagram = pb.PourbaixEngine(self.database).calculate_system(restricted, conditions)
            self.assertEqual({diagram.system.species[int(i)].record_id
                              for i in diagram.stable_species_index.flat}, {winner.record_id})

    def test_usgs_carbonate_polymorphs_and_buffered_solubility(self) -> None:
        from dataclasses import replace

        factor = 8.31446261815324 * 298.15 * math.log(10)
        for symbol, phase, gibbs in (
            ("Ca", "calcite", -1128500), ("Ca", "aragonite", -1127400),
            ("Ca", "vaterite", -1125500), ("Fe", "siderite", -682800),
            ("Mn", "rhodochrosite", -819100), ("Sr", "strontianite", -1137600),
            ("Ba", "witherite", -1132200),
        ):
            rid = f"r07-{symbol.lower()}-{symbol.lower()}co3-{phase}"
            record = self.database.species_records((rid,))[0]
            self.assertEqual(record.phase_identity.identified_phase, phase)
            original = [r for r in record.reported if r.value_id.endswith(":usgs-b2131-1995")]
            original_g = next(r for r in original if r.property == "gibbs_energy_of_formation")
            self.assertEqual(original_g.value, gibbs)
            self.assertIn("10.3133/b2131", original_g.source.url)
            self.assertTrue(all("Numbered numerical parents" in r.source.locator for r in original))
            if phase == "vaterite":
                self.assertEqual(len(original), 1)
                for value in (record.thermochemistry.entropy_J_mol_K,
                              record.thermochemistry.formation_enthalpy_J_mol):
                    self.assertEqual(value.status, pb.EvidenceStatus.SOURCE_VERIFIED_ESTIMATE)
                    self.assertIsNone(value.uncertainty)
            self.assertFalse(any(s.record_id == rid for s in self.database.load_system(symbol).species))
            system = self.database.load_system(symbol, ligand_ids=("carbonate-co3",))
            solid = next(s for s in system.species if s.record_id == rid)
            ion = next(s for s in system.species if s.formula_ascii == symbol and s.charge == 2)
            self.assertEqual((solid.electrons_per_metal, solid.protons_per_metal), (2, 0))
            restricted = replace(system, species=(ion, solid), excluded=())
            log_ksp = (solid.gibbs_energy_J_mol - ion.gibbs_energy_J_mol
                       - solid.ligand_gibbs_energy_J_mol) / factor
            for offset, winner in ((-0.1, ion), (0.1, solid)):
                conditions = pb.PourbaixConditions(
                    pH_points=3, U_points=3,
                    aqueous_activities=pb.AqueousActivityModel(default_log10_activity=0),
                    ligand_activities=pb.LigandActivityModel((pb.LigandActivity(
                        "carbonate-co3", log10_free_activity=log_ksp + offset
                    ),)),
                )
                diagram = pb.PourbaixEngine(self.database).calculate_system(restricted, conditions)
                self.assertEqual({diagram.system.species[int(i)].record_id
                                  for i in diagram.stable_species_index.flat}, {winner.record_id})
            # Ksp / a_CO3 fixes the saturation concentration at 1e-5 M.
            conditions = pb.PourbaixConditions(
                pH_points=3, U_points=3,
                ligand_activities=pb.LigandActivityModel((pb.LigandActivity(
                    "carbonate-co3", log10_free_activity=log_ksp + 5
                ),)),
            )
            balanced = pb.MassBalanceEngine(self.database).calculate_system(
                restricted, conditions, pb.TotalMetalConcentration(2e-5),
            )
            for dissolved, fraction in zip(balanced.dissolved_metal_mol_L.flat,
                                           balanced.precipitated_metal_fraction.flat):
                self.assertAlmostEqual(dissolved / 1e-5, 1, places=10)
                self.assertAlmostEqual(fraction, 0.5, places=10)
                self.assertAlmostEqual((dissolved + 2e-5 * fraction) / 2e-5, 1, places=12)

    def test_magnesium_carbonate_formula_units_and_hydrated_boundaries(self) -> None:
        from dataclasses import replace

        import numpy as np

        system = self.database.load_system("Mg", ligand_ids=("carbonate-co3",))
        ion = next(s for s in system.species if s.formula_ascii == "Mg" and s.charge == 2)
        factor = 8.31446261815324 * 298.15 * math.log(10)
        water = self.database.reference_state.water_gibbs_energy_J_mol
        for phase, metal, carbonate, oxygen, hydrogen, gibbs in (
            ("magnesite", 1, 1, 0, 0, -1028409),
            ("nesquehonite", 1, 1, 3, 6, -1726100),
            ("hydromagnesite", 5, 4, 6, 10, -5864200),
            ("artinite", 2, 1, 5, 8, -2568400),
            ("lansfordite", 1, 1, 5, 10, -2199200),
        ):
            solid = next(s for s in system.species if s.record_id == f"r07-mg-{phase}")
            self.assertEqual((solid.metal_count, solid.ligand_count,
                              solid.core_oxygen_count, solid.core_hydrogen_count),
                             (metal, carbonate, oxygen, hydrogen))
            self.assertAlmostEqual(solid.gibbs_energy_J_mol, gibbs)
            self.assertEqual(solid.electrons_per_metal, 2)
            protons = 2 * oxygen - hydrogen
            self.assertEqual(protons, 2 * metal - 2 * carbonate)
            self.assertEqual(solid.protons_per_metal, protons / metal)
            # Independently balance the full mineral dissolution at pH 8.
            reaction_g = (metal * ion.gibbs_energy_J_mol
                          + carbonate * solid.ligand_gibbs_energy_J_mol
                          + oxygen * water - gibbs)
            log_k = -reaction_g / factor
            log_carbonate = (log_k + 5 * metal - 8 * protons) / carbonate
            conditions = pb.PourbaixConditions(
                pH_min=8, pH_max=8.01, pH_points=2, U_points=2,
                ligand_activities=pb.LigandActivityModel((pb.LigandActivity(
                    "carbonate-co3", log10_free_activity=log_carbonate,
                ),)),
            )
            result = pb.MassBalanceEngine(self.database).calculate_system(
                replace(system, species=(ion, solid), excluded=()),
                conditions, pb.TotalMetalConcentration(2e-5),
            )
            np.testing.assert_allclose(result.dissolved_metal_mol_L[:, 0], 1e-5, rtol=2e-12)
            np.testing.assert_allclose(result.precipitated_metal_fraction[:, 0], .5, rtol=2e-12)

    def test_magnesium_original_entropies_and_open_nbs_evaluations(self) -> None:
        for phase, value, interval, status in (
            ("magnesite", 65.09, .13, pb.EvidenceStatus.VERIFIED),
            ("nesquehonite", 46.76 * 4.184, .14 * 4.184, pb.EvidenceStatus.VERIFIED),
            ("hydromagnesite", 120.38 * 4.184, .37 * 4.184,
             pb.EvidenceStatus.SOURCE_VERIFIED_ESTIMATE),
        ):
            record = self.database.species_records((f"r07-mg-{phase}",))[0]
            original = next(r for r in record.reported
                            if r.value_id.endswith(":usgs-original-calorimetry"))
            self.assertEqual((original.value, original.uncertainty, original.status),
                             (value, interval, status))
            self.assertFalse(original.selected_as_recommended)
            self.assertIn("correlated", original.source.locator)
            with closing(sqlite3.connect(self.database.path)) as c:
                self.assertIsNone(c.execute(
                    "SELECT pressure_bar FROM reported_thermochemistry WHERE value_id=?",
                    (original.value_id,),
                ).fetchone()[0])
            if phase == "hydromagnesite":
                self.assertIn("zero residual entropy", original.source.locator)
        ion = self.database.species_records(("gfe-mg-mg-q+2-aqueous-aq",))[0]
        self.assertEqual(ion.thermochemistry.formation_enthalpy_J_mol.value, -466850)
        complex_record = self.database.species_records(("gfe-mg-mghco3-q+1-aqueous-aq",))[0]
        self.assertEqual(complex_record.thermochemistry.gibbs_energy_J_mol.value, -1047200)
        self.assertIn("10.18434/M32124", complex_record.thermochemistry.gibbs_energy_J_mol.source.url)
        self.assertTrue(any(r.value == -1048857 and not r.selected_as_recommended
                            for r in complex_record.reported))

    def test_artinite_residual_entropy_and_nbs_magnesium_mineral_variants(self) -> None:
        artinite = self.database.species_records(("r07-mg-artinite",))[0]
        original = next(r for r in artinite.reported
                        if r.value_id.endswith(":usgs-original-configurational-entropy"))
        self.assertAlmostEqual(original.value, (54.29 + 1.38) * 4.184)
        self.assertAlmostEqual(original.uncertainty, .16 * 4.184)
        self.assertEqual(original.status, pb.EvidenceStatus.SOURCE_VERIFIED_ESTIMATE)
        self.assertFalse(original.selected_as_recommended)
        self.assertIn("configurational", original.source.locator)
        self.assertEqual(artinite.thermochemistry.entropy_J_mol_K.value, 232.9)
        for value in artinite.reported:
            if value.value_id.endswith(":usgs-b2131-1995") and value.property != "absolute_entropy":
                self.assertIn("535–541", value.source.locator)
                self.assertNotIn("Mineralogist58", value.source.locator)
        magnesite = self.database.species_records(("r07-mg-magnesite",))[0]
        self.assertAlmostEqual(magnesite.thermochemistry.gibbs_energy_J_mol.value, -1028409)
        self.assertEqual(magnesite.thermochemistry.formation_enthalpy_J_mol.value, -1112200)
        self.assertEqual(magnesite.thermochemistry.entropy_J_mol_K.value, 65.1)
        self.assertTrue(any(r.value == -1029500 for r in magnesite.reported))
        self.assertTrue(any(r.value == -1113300 for r in magnesite.reported))
        system = self.database.load_system("Mg", ligand_ids=("carbonate-co3",))
        four_id = "r07-mg-basic-carbonate-four-mg-trihydrate"
        four = self.database.species_records((four_id,))[0]
        self.assertIsNone(four.thermochemistry.gibbs_energy_J_mol.value)
        self.assertTrue(any(r.value == -4603300 for r in four.reported))
        self.assertIn(four_id, {s.record_id for s in system.excluded})
        five = next(s for s in system.species if s.record_id == "r07-mg-hydromagnesite")
        self.assertEqual((five.metal_count, five.ligand_count, five.protons_per_metal), (5, 4, .4))
        lansfordite = self.database.species_records(("r07-mg-lansfordite",))[0]
        self.assertEqual(lansfordite.thermochemistry.gibbs_energy_J_mol.value, -2199200)
        self.assertIsNone(lansfordite.thermochemistry.entropy_J_mol_K.value)
        self.assertIsNone(lansfordite.thermochemistry.formation_enthalpy_J_mol.value)

    def test_open_carbonate_calorimetry_reconstruction_preserves_source_assumptions(self) -> None:
        for phase, enthalpy, gibbs in (
            ("nesquehonite", -1977298.52, -1723798.819996),
            ("hydromagnesite", -6515063.04, -5864394.767348),
        ):
            record = self.database.species_records((f"r07-mg-{phase}",))[0]
            estimates = {r.property: r for r in record.reported
                         if r.value_id.endswith(":open-calorimetry-reconstruction")}
            self.assertAlmostEqual(estimates["enthalpy_of_formation"].value, enthalpy)
            self.assertAlmostEqual(estimates["gibbs_energy_of_formation"].value, gibbs)
            for value in estimates.values():
                self.assertEqual(value.status, pb.EvidenceStatus.SOURCE_VERIFIED_ESTIMATE)
                self.assertIsNone(value.uncertainty)
                self.assertFalse(value.selected_as_recommended)
                self.assertIn("pressure-flat", value.source.locator)
                self.assertIn("205.138", value.source.locator)
                self.assertIn("10.18434/M32124", value.source.locator)
        artinite = self.database.species_records(("r07-mg-artinite",))[0]
        self.assertFalse(any(r.value_id.endswith(":open-calorimetry-reconstruction")
                             for r in artinite.reported))
        exclusion = next(e for e in self.database.policy.exclusions
                         if e.record_id == "r07-mg-basic-carbonate-four-mg-trihydrate")
        self.assertIn("incorrect", exclusion.reason)
        self.assertEqual(len(self.database.policy.exclusions), 13)

    def test_magnesite_1965_solubility_estimate_uses_correct_gas_reference(self) -> None:
        record = self.database.species_records(("r07-mg-magnesite",))[0]
        estimate = next(r for r in record.reported
                        if r.value_id.endswith(":open-1965-solubility-reconstruction"))
        rt = 8.31446261815324 * 298.15
        reaction_atm = -rt * math.log(6.3e-6)
        reaction_bar = reaction_atm + rt * math.log(1.01325)
        self.assertAlmostEqual(estimate.value,
                               -454800 + 2 * -586770 + 394359 + 237129 - reaction_bar)
        self.assertEqual(estimate.status, pb.EvidenceStatus.SOURCE_VERIFIED_ESTIMATE)
        self.assertIsNone(estimate.uncertainty)
        self.assertFalse(estimate.selected_as_recommended)
        self.assertAlmostEqual(record.thermochemistry.gibbs_energy_J_mol.value, -1028409)
        self.assertIn("complexing", estimate.source.locator)
        self.assertIn("Eq.21", estimate.source.locator)
        self.assertIn("pressure-flat", estimate.source.locator)
        # Chemical potentials balance at the source's 1 atm CO2 pressure.
        magnesium_activity = 1e-5
        bicarbonate_activity = math.sqrt(6.3e-6 / magnesium_activity)
        reactants = estimate.value - 394359 + rt * math.log(1.01325) - 237129
        products = (-454800 + rt * math.log(magnesium_activity)
                    + 2 * (-586770 + rt * math.log(bicarbonate_activity)))
        self.assertAlmostEqual(reactants, products, places=8)

    def test_calcium_original_association_fit_and_missing_ion_enthalpy(self) -> None:
        ion = self.database.species_records(("gfe-ca-ca-q+2-aqueous-aq",))[0]
        h = ion.thermochemistry.formation_enthalpy_J_mol
        self.assertEqual(h.value, -542830)
        self.assertEqual(h.status, pb.EvidenceStatus.VERIFIED)
        self.assertIn("10.18434/M32124", h.source.url)
        self.assertIn("logical record 9196", h.source.locator)
        for formula, log_k, selected_g in (
            ("CaCO3", 3.22, -1098795), ("CaHCO3", 1.11, -1145214),
        ):
            charge = 0 if formula == "CaCO3" else 1
            rid = f"gfe-ca-{formula.lower()}-q+{charge}-aqueous-aq"
            record = self.database.species_records((rid,))[0]
            fitted = {r.property: r for r in record.reported
                      if r.value_id.endswith(":original-fit-nbs-pressure-flat")}
            self.assertEqual(len(fitted), 3)
            self.assertTrue(all(not r.selected_as_recommended for r in fitted.values()))
            self.assertTrue(all(r.uncertainty is None for r in fitted.values()))
            self.assertTrue(all(r.status == pb.EvidenceStatus.SOURCE_VERIFIED_ESTIMATE
                                for r in fitted.values()))
            ligand_g = -527810 if charge == 0 else -586770
            reaction_g = fitted["gibbs_energy_of_formation"].value + 553580 - ligand_g
            observed = -reaction_g / (8.31446261815324 * 298.15 * math.log(10))
            self.assertAlmostEqual(observed, log_k, delta=.005)
            self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.value, selected_g)
            self.assertIn("pressure-flat reaction approximation",
                          fitted["gibbs_energy_of_formation"].source.locator)
            self.assertIn("different reaction-H point entries",
                          fitted["enthalpy_of_formation"].source.locator)

    def test_fe_mn_original_calorimetry_and_open_ion_enthalpies(self) -> None:
        for symbol, phase, original_s, interval, evaluated_s, enthalpy in (
            ("Fe", "siderite", 95.47, .15, 95.5, -89100),
            ("Mn", "rhodochrosite", 98.03, .10, 98.0, -220750),
        ):
            rid = f"r07-{symbol.lower()}-{symbol.lower()}co3-{phase}"
            record = self.database.species_records((rid,))[0]
            entropy = next(r for r in record.reported
                           if r.value_id.endswith(":usgs-1984-original-calorimetry"))
            self.assertEqual((entropy.value, entropy.uncertainty), (original_s, interval))
            self.assertEqual(entropy.status, pb.EvidenceStatus.VERIFIED)
            self.assertFalse(entropy.selected_as_recommended)
            self.assertIn("corrected pure MCO3 endmember", entropy.source.locator)
            self.assertIn("correlated representations", entropy.source.locator)
            evaluation = next(r for r in record.reported if r.property == "absolute_entropy"
                              and r.value_id.endswith(":usgs-b2131-1995"))
            self.assertEqual(evaluation.value, evaluated_s)
            with closing(sqlite3.connect(self.database.path)) as c:
                temperature, pressure = c.execute(
                    "SELECT temperature_K,pressure_bar FROM reported_thermochemistry WHERE value_id=?",
                    (entropy.value_id,),
                ).fetchone()
            self.assertEqual(temperature, 298.15)
            self.assertIsNone(pressure)  # The helium fill pressure belongs to the apparatus.
            ion = self.database.species_records((
                f"gfe-{symbol.lower()}-{symbol.lower()}-q+2-aqueous-aq",
            ))[0]
            h = next(r for r in ion.reported if r.property == "enthalpy_of_formation"
                     and r.source and r.source.source_id.startswith(f"NBS_R07_{symbol}_ion"))
            self.assertEqual(h.value, enthalpy)
            self.assertEqual(h.status, pb.EvidenceStatus.VERIFIED)
            self.assertIsNone(h.uncertainty)
            self.assertIn("10.18434/M32124", h.source.url)
            self.assertIn("zero-based column 7", h.source.locator)
            if symbol == "Fe":
                self.assertEqual(ion.thermochemistry.gibbs_energy_J_mol.value, -90719)
                self.assertTrue(any(r.value == -90530 and r.source and "Parker" in r.source.citation
                                    for r in ion.reported))

    def test_open_sr_ba_anchors_and_original_fit_alternatives(self) -> None:
        for symbol, enthalpy, previous_g in (
            ("Sr", -545800, -1108174.24), ("Ba", -537640, -1103864.72),
        ):
            ion = self.database.species_records((
                f"gfe-{symbol.lower()}-{symbol.lower()}-q+2-aqueous-aq",
            ))[0]
            value = ion.thermochemistry.formation_enthalpy_J_mol
            self.assertEqual(value.value, enthalpy)
            self.assertEqual(value.status, pb.EvidenceStatus.VERIFIED)
            self.assertIn("10.18434/M32124", value.source.url)
            self.assertIn("Column 7 (zero-based)", value.source.locator)
            neutral = self.database.species_records((
                f"r06-{symbol.lower()}-{symbol.lower()}co3-q+0-aq",
            ))[0]
            self.assertTrue(any(r.value == previous_g and not r.selected_as_recommended
                                for r in neutral.reported))
            fitted = [r for r in neutral.reported
                      if r.value_id.endswith(":original-fit-nbs-pressure-flat")]
            self.assertEqual(len(fitted), 3)
            for row in fitted:
                self.assertTrue(row.selected_as_recommended)
                self.assertEqual(row.status, pb.EvidenceStatus.SOURCE_VERIFIED_ESTIMATE)
                self.assertIsNone(row.uncertainty)
                self.assertIn("pressure-flat reaction approximation", row.source.locator)
                self.assertIn("not a certified error bound", row.source.locator)

    def test_sr_ba_association_matches_original_points_and_proton_balance(self) -> None:
        from dataclasses import replace

        import numpy as np

        log_carbonate = -6
        # Independent rounded point constants from the original USGS author abstracts.
        for symbol, carbonate_log_k, bicarbonate_log_k in (
            ("Sr", 2.81, 1.18), ("Ba", 2.71, .982),
        ):
            rid = f"r07-{symbol.lower()}-{symbol.lower()}hco3-q+1-aq"
            self.assertNotIn(rid, {s.record_id for s in self.database.load_system(symbol).species})
            system = self.database.load_system(symbol, ligand_ids=("carbonate-co3",))
            ion = next(s for s in system.species if s.formula_ascii == symbol and s.charge == 2)
            neutral = next(s for s in system.species
                           if s.formula_ascii == symbol + "CO3" and s.is_aqueous)
            bicarbonate = next(s for s in system.species if s.record_id == rid)
            self.assertEqual((bicarbonate.electrons_per_metal, bicarbonate.protons_per_metal), (2, -1))
            self.assertEqual((bicarbonate.core_oxygen_count, bicarbonate.core_hydrogen_count,
                              bicarbonate.ligand_count), (0, 1, 1))
            conditions = pb.PourbaixConditions(
                pH_points=3, U_points=3,
                ligand_activities=pb.LigandActivityModel((pb.LigandActivity(
                    "carbonate-co3", log10_free_activity=log_carbonate,
                ),)),
            )
            diagram = pb.MassBalanceEngine(self.database).calculate_system(
                replace(system, species=(ion, neutral, bicarbonate), excluded=()),
                conditions, pb.TotalMetalConcentration(1e-4),
            )
            concentrations = diagram.aqueous_concentration_mol_L
            np.testing.assert_allclose(concentrations.sum(axis=0), 1e-4, rtol=1e-12)
            observed = np.log10(concentrations[1] / concentrations[0]) - log_carbonate
            np.testing.assert_allclose(observed, carbonate_log_k, atol=.005, rtol=0)
            p_k = (-527810 + 586770) / (8.31446261815324 * 298.15 * math.log(10))
            observed = (np.log10(concentrations[2] / concentrations[0])
                        - log_carbonate - p_k + diagram.pH[None, :])
            np.testing.assert_allclose(observed, bicarbonate_log_k, atol=.005, rtol=0)

    def test_original_carbonate_relative_fit_preserves_phase_thermodynamics(self) -> None:
        calcite = self.database.species_records(("r07-ca-caco3-calcite",))[0]
        # The retained relative model uses its original USGS anchors.
        anchors = {row.property: row.value for row in calcite.reported
                   if row.source and row.source.source_id.startswith("USGS_R07_B2131_calcite_")}
        temperature, gas_constant = 298.15, 8.31446261815324
        for phase, coefficients, volume in (
            ("aragonite", (-171.9773, 2903.293), 34.15),
            ("vaterite", (-172.1295, 3074.688), 37.63),
        ):
            record = self.database.species_records((f"r07-ca-caco3-{phase}",))[0]
            derived = {r.property: r for r in record.reported
                       if r.value_id.endswith(":pb1982-relative-calcite-model")}
            self.assertEqual(set(derived), set(anchors))
            delta_g = derived["gibbs_energy_of_formation"].value - anchors["gibbs_energy_of_formation"]
            delta_h = derived["enthalpy_of_formation"].value - anchors["enthalpy_of_formation"]
            delta_s = derived["absolute_entropy"].value - anchors["absolute_entropy"]
            self.assertAlmostEqual(delta_g, delta_h - temperature * delta_s, places=8)
            # Differentiate the full original logK expressions numerically.
            def relative_g(t):
                def log_k(a, c):
                    return a - .077993 * t + c / t + 71.595 * math.log10(t)
                return gas_constant * t * math.log(10) * (
                    log_k(*coefficients) - log_k(-171.9065, 2839.319)
                )
            finite_difference = -(relative_g(temperature + .01) - relative_g(temperature - .01)) / .02
            self.assertAlmostEqual(delta_s, finite_difference, places=6)
            pressure = (volume - 36.93) * 1e-6 * (100000 - 101325)
            self.assertAlmostEqual(delta_g, relative_g(temperature) + pressure, places=8)
            for value in derived.values():
                self.assertEqual(value.status, pb.EvidenceStatus.SOURCE_VERIFIED_ESTIMATE)
                self.assertIsNone(value.uncertainty)
                self.assertIn("total uncertainty NULL", value.source.locator)
                self.assertEqual(value.selected_as_recommended,
                                 phase == "vaterite" and value.property != "gibbs_energy_of_formation")

    def test_yttrium_fluoride_source_units_charge_and_derived_enthalpy(self) -> None:
        for formula, charge, count, g_cal, s_cal in (
            ("YF", 2, 1, -237220.0, -33.37),
            ("YF2", 1, 2, -308470.0, -14.33),
        ):
            rid = f"gfe-y-{formula.lower()}-q+{charge}-aqueous-aq"
            record = self.database.species_records((rid,))[0]
            thermo = record.thermochemistry
            self.assertEqual(thermo.gibbs_energy_J_mol.value, g_cal * 4.184)
            self.assertAlmostEqual(thermo.entropy_J_mol_K.value, s_cal * 4.184, places=8)
            formation_entropy = s_cal * 4.184 - 44.43 - count * 202.78 / 2 + charge * 130.684 / 2
            self.assertAlmostEqual(thermo.formation_enthalpy_J_mol.value,
                                   g_cal * 4.184 + 298.15 * formation_entropy, places=6)
            self.assertIn("NBS_derived", thermo.formation_enthalpy_J_mol.source.source_id)
            self.assertIn("Table 5", thermo.gibbs_energy_J_mol.source.locator)
            self.assertEqual(len(record.reported), 3)
            self.assertTrue(all(r.selected_as_recommended and r.uncertainty is None
                                and r.status == "source_verified_estimate" for r in record.reported))
            self.assertTrue(any(w.type == "loges_author_republication_provenance" for w in record.warnings))
            self.assertTrue(any(w.type == "loges_native_precision_and_H_hold" for w in record.warnings))

    def test_yttrium_fluoride_ligand_gating_and_analytical_crossover(self) -> None:
        from dataclasses import replace

        plain = self.database.load_system("Y")
        full = self.database.load_system("Y", ligand_ids=["fluoride-f"])
        complexes = sorted((s for s in full.species if s.ligand_id == "fluoride-f"),
                           key=lambda s: s.ligand_count)
        self.assertEqual(len(complexes), 2)
        self.assertFalse(any(s.ligand_id == "fluoride-f" for s in plain.species))
        for s in complexes:
            self.assertEqual(s.charge + s.ligand_count, 3)
            self.assertEqual((s.electrons_per_metal, s.protons_per_metal), (3, 0))
            self.assertEqual((s.core_oxygen_count, s.core_hydrogen_count), (0, 0))
        mono, bis = complexes
        with closing(sqlite3.connect(self.database.path)) as connection:
            fluoride_g = connection.execute(
                "SELECT gibbs_energy_J_mol FROM ligands WHERE ligand_id='fluoride-f'"
            ).fetchone()[0]
        crossover = (bis.gibbs_energy_J_mol - mono.gibbs_energy_J_mol - fluoride_g) / (
            8.31446261815324 * 298.15 * math.log(10)
        )
        restricted = replace(full, species=tuple(complexes), excluded=())
        for offset, winner in ((-0.1, mono), (0.1, bis)):
            conditions = pb.PourbaixConditions(
                pH_points=3, U_points=3,
                ligand_activities=pb.LigandActivityModel((pb.LigandActivity(
                    "fluoride-f", log10_free_activity=crossover + offset
                ),)),
            )
            diagram = pb.PourbaixEngine(self.database).calculate_system(restricted, conditions)
            self.assertEqual({diagram.system.species[int(i)].record_id
                              for i in diagram.stable_species_index.flat}, {winner.record_id})

    def test_ferrihydrite_phases_retain_physical_bounds_and_source_uncertainty(self) -> None:
        for phase, energies, entropies, enthalpy in (
            ("2-line", {-708500.0, -705200.0}, {122.2, 133.0}, -827100.0),
            ("6-line", {-711000.0, -708500.0}, {122.2, 130.7}, -830300.0),
        ):
            rid = f"gfe-fe-fe-oh-3-q+0-solid-ferrihydrite-{phase}"
            record = self.database.species_records((rid,))[0]
            original = [r for r in record.reported if "_original-" in r.source.source_id]
            self.assertEqual(len(original), 5)
            self.assertEqual({r.value for r in original if r.property == "gibbs_energy_of_formation"}, energies)
            self.assertEqual({r.value for r in original if r.property == "absolute_entropy"}, entropies)
            self.assertEqual({r.value for r in original if r.property == "enthalpy_of_formation"}, {enthalpy})
            # NEA's nominal model adjustment is retained alongside the original calorimetry.
            self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, enthalpy + 400)
            self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.uncertainty,
                             2100.0 if phase == "2-line" else 2000.0)
            self.assertEqual(record.thermochemistry.entropy_J_mol_K.uncertainty,
                             None if phase == "2-line" else 10.0)
            self.assertEqual(record.thermochemistry.entropy_J_mol_K.value,
                             122.2 if phase == "2-line" else 130.0)
            self.assertEqual(sum(r.selected_as_recommended for r in record.reported), 3)
            self.assertIsNone(record.phase_identity.spacegroup_number)
            self.assertTrue(any(w.type == "ferrihydrite_bounds_and_preference" for w in record.warnings))
            self.assertTrue(all("Table 1" in r.source.locator for r in original))
            # Unspecified original G pressure is retained without assigning the 2011 Psat state.
            with closing(sqlite3.connect(self.database.path)) as connection:
                pressures = connection.execute(
                    "SELECT pressure_bar FROM reported_thermochemistry WHERE record_id=? "
                    "AND property='gibbs_energy_of_formation' AND source_id LIKE '%_original-%'",
                    (rid,),
                ).fetchall()
            self.assertEqual(pressures, [(None,), (None,)])

    def test_ferrihydrite_gibbs_uses_open_references_and_balanced_nominal_formula(self) -> None:
        system = self.database.load_system("Fe")
        self.assertEqual({item.record_id for item in system.missing_gibbs},
                         {"r06-fe-fe-oh-3-q+0-aq"})
        reference_entropy = 27.28 + 1.5 * 130.684 + 1.5 * 205.138
        energies = []
        goethite = next(s for s in system.species if s.phase_detail == "goethite")
        for phase, enthalpy in (("2-line", -827100.0), ("6-line", -830300.0)):
            rid = f"gfe-fe-fe-oh-3-q+0-solid-ferrihydrite-{phase}"
            record = self.database.species_records((rid,))[0]
            preferred = record.thermochemistry.gibbs_energy_J_mol
            self.assertAlmostEqual(preferred.value, enthalpy - 298.15 * (122.2 - reference_entropy), places=6)
            self.assertEqual(preferred.status, "source_verified_estimate")
            self.assertIsNone(preferred.uncertainty)
            self.assertIn("NBS-derived-upper-G", preferred.source.source_id)
            self.assertIn("least-stable", preferred.source.locator)
            self.assertIn("unquantified", preferred.source.locator)
            solid = next(s for s in system.species if s.record_id == rid)
            self.assertEqual((solid.core_oxygen_count, solid.core_hydrogen_count), (3, 3))
            self.assertEqual((solid.electrons_per_metal, solid.protons_per_metal), (3, 3))
            self.assertGreater(solid.gibbs_energy_J_mol - goethite.gibbs_energy_J_mol
                               - self.database.reference_state.water_gibbs_energy_J_mol, 0)
            energies.append(preferred.value)
        self.assertAlmostEqual(energies[1] - energies[0], -3200.0)

    def test_miron_evaluations_and_discrepant_representations_are_retained(self) -> None:
        aluminum, calcium = self.database.species_records((
            "gfe-al-al-q+3-aqueous-aq", "gfe-ca-cacl-q+1-aqueous-aq"
        ))
        self.assertEqual(aluminum.thermochemistry.gibbs_energy_J_mol.value, -488824.0)
        energies = {row.value for row in aluminum.reported if row.property == "gibbs_energy_of_formation"}
        self.assertGreaterEqual(energies, {-485000.0, -486627.0, -486594.0})
        calcium_energies = {row.value for row in calcium.reported if row.property == "gibbs_energy_of_formation"}
        self.assertEqual(calcium_energies, {-689297.0, -689279.0, -682410.4})
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

    def test_miron_silica_versions_preserve_preference_and_formula_basis(self) -> None:
        neutral, charged, calcium = self.database.species_records((
            "gfe-si-h4sio4-q+0-aqueous-aq", "gfe-si-h3sio4-q-1-aqueous-aq",
            "gfe-ca-cah3sio4-q+1-aqueous-aq",
        ))
        self.assertEqual(neutral.thermochemistry.gibbs_energy_J_mol.value, -1309201.0)
        self.assertGreaterEqual({r.value for r in neutral.reported
                                 if r.property == "gibbs_energy_of_formation"},
                                {-834103 - 2 * 237129, -834041 - 2 * 237129})
        self.assertEqual(charged.thermochemistry.gibbs_energy_J_mol.value, -1015175 - 237129)
        miron_rows = [r for r in charged.reported if r.source
                      and r.source.source_id.startswith("Miron_")]
        self.assertEqual({r.value for r in miron_rows},
                         {-1015237 - 237129, -1015175 - 237129})
        self.assertTrue(all(r.property == "gibbs_energy_of_formation" for r in miron_rows))
        self.assertTrue(any(w.type == "miron_appendix_entropy_source_hold" for w in charged.warnings))
        self.assertEqual(calcium.thermochemistry.gibbs_energy_J_mol.value, -1575097 - 237129)
        self.assertTrue(any(w.type == "miron_published_dataset_discrepancy" for w in calcium.warnings))

    def test_miron_conductance_entropy_and_explicit_nbs_enthalpy_sources(self) -> None:
        sodium = self.database.species_records(("gfe-na-naoh-q+0-aqueous-aq",))[0]
        self.assertEqual(sodium.thermochemistry.entropy_J_mol_K.value, 42.4)
        enthalpies = [r for r in sodium.reported if r.property == "enthalpy_of_formation"
                     and r.source and r.source.source_id.startswith("Miron_R04_")]
        self.assertEqual(len(enthalpies), 2)
        self.assertEqual(sum(r.selected_as_recommended for r in enthalpies), 1)
        self.assertEqual({r.value for r in enthalpies}, {
            round(g + 298.15 * (42.4 - 65.342 - 102.569 - 51.21), 6)
            for g in (-411567, -411594)
        })
        self.assertTrue(all("10.18434/M32124" in r.source.locator for r in enthalpies))
        self.assertTrue(all("NBS-derived" in r.source.source_id for r in enthalpies))

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
        with closing(self.database.connect()) as connection:
            statuses = {row[0] for row in connection.execute("SELECT DISTINCT gibbs_status FROM selected_thermochemistry")}
        self.assertLessEqual(statuses, {item.value for item in pb.EvidenceStatus})

    def test_sulfate_gibbs_uses_original_zero_ionic_strength_constant(self) -> None:
        neodymium = self.database.species_records((
            "gfe-nd-ndso4-q+1-aqueous-aq",
        ))[0]
        factor = 8.31446261815324 * 298.15 * math.log(10)
        self.assertAlmostEqual(neodymium.thermochemistry.gibbs_energy_J_mol.value,
                               -671600 - 744530 - factor * 3.60, places=5)
        self.assertEqual(neodymium.thermochemistry.gibbs_energy_J_mol.status,
                         "source_verified_estimate")
        self.assertIsNone(neodymium.thermochemistry.gibbs_energy_J_mol.uncertainty)
        self.assertIsNone(neodymium.thermochemistry.entropy_J_mol_K.value)
        self.assertIsNone(neodymium.thermochemistry.formation_enthalpy_J_mol.value)
        self.assertIn("LAST COLUMN", neodymium.reported[0].source.locator)
        self.assertTrue(any(w.type == "sulfate_2016_Nd_constant_discrepancy"
                            for w in neodymium.warnings))

    def test_yttrium_sulfate_preserves_and_exposes_parent_reference_difference(self) -> None:
        system = self.database.load_system("Y", ligand_ids=("sulfate-so4",))
        ion = next(s for s in system.species if s.formula_ascii == "Y" and s.charge == 3)
        complex_ = next(s for s in system.species if s.formula_ascii == "YSO4")
        factor = 8.31446261815324 * 298.15 * math.log(10)
        self.assertEqual(ion.gibbs_energy_J_mol, -685339.2)
        implied = (ion.gibbs_energy_J_mol + complex_.ligand_gibbs_energy_J_mol
                   - complex_.gibbs_energy_J_mol) / factor
        self.assertAlmostEqual(implied, 3.50 + (-685339.2 + 693800) / factor, places=9)
        record = self.database.species_records((complex_.record_id,))[0]
        self.assertTrue(any(w.type == "sulfate_parent_reference_mismatch"
                            for w in record.warnings))

    def test_sulfate_hydrates_preserve_water_counts_and_distinct_phases(self) -> None:
        calcium = self.database.load_system("Ca", ligand_ids=("sulfate-so4",))
        halves = [s for s in calcium.species if s.formula_ascii == "CaSO4(H2O)0.5"]
        self.assertEqual(len(halves), 2)
        for species in halves:
            self.assertEqual((species.core_oxygen_count, species.core_hydrogen_count), (.5, 1))
            self.assertEqual((species.electrons_per_metal, species.protons_per_metal), (2, 0))
        self.assertEqual({s.gibbs_energy_J_mol for s in halves}, {-1436740, -1435780})
        nickel = self.database.load_system("Ni", ligand_ids=("sulfate-so4",))
        hydrate = next(s for s in nickel.species if "alpha-green-tetragonal" in s.record_id)
        self.assertEqual((hydrate.core_oxygen_count, hydrate.core_hydrogen_count), (6, 12))
        self.assertIn("alpha-green-tetragonal", hydrate.record_id)
        self.assertEqual(hydrate.gibbs_energy_J_mol, -2225467)
        ordinary = self.database.load_system("Ni")
        self.assertFalse(any(s.record_id == hydrate.record_id for s in ordinary.species))
        blue = self.database.species_records((
            "gfe-ni-niso4-h2o-6-q+0-solid-nickel-sulfate-beta-blue-monoclinic-hexahydrate",
        ))[0]
        self.assertEqual(blue.thermochemistry.gibbs_energy_J_mol.value, -2224915)
        self.assertEqual(blue.thermochemistry.gibbs_energy_J_mol.status,
                         pb.EvidenceStatus.VERIFIED.value)
        self.assertEqual(blue.thermochemistry.formation_enthalpy_J_mol.value, -2677287)
        self.assertTrue(any(r.property == "enthalpy_of_formation" and r.value == -2672300
                            for r in blue.reported))
        self.assertTrue(any(s.record_id == blue.record_id for s in nickel.species))

    def test_hydrate_gibbs_estimate_preserves_open_enthalpy_and_water_basis(self) -> None:
        record = self.database.species_records((
            "gfe-mn-mnso4-h2o-4-q+0-solid-manganese-sulfate-tetrahydrate",
        ))[0]
        thermo = record.thermochemistry
        self.assertEqual(thermo.formation_enthalpy_J_mol.value, -2258100)
        self.assertAlmostEqual(thermo.entropy_J_mol_K.value, 65 * 4.184)
        # Mn + S + 4 O2 + 4 H2 form the complete tetrahydrate formula unit.
        reference_entropy = 32.01 + 31.80 + 4 * 205.138 + 4 * 130.684
        self.assertAlmostEqual(thermo.gibbs_energy_J_mol.value,
                               -2258100 - 298.15 * (65 * 4.184 - reference_entropy))
        self.assertEqual(thermo.gibbs_energy_J_mol.status, "source_verified_estimate")
        self.assertIsNone(thermo.gibbs_energy_J_mol.uncertainty)
        self.assertTrue(any(w.type == "sulfate_hydrate_missing_properties_resolved"
                            for w in record.warnings))
        self.assertFalse(any(w.type == "sulfate_enthalpy_retained_G_unavailable"
                             for w in record.warnings))
        enabled = self.database.load_system("Mn", ligand_ids=("sulfate-so4",))
        hydrate = next(s for s in enabled.species if s.record_id == record.record_id)
        self.assertEqual((hydrate.core_oxygen_count, hydrate.core_hydrogen_count), (4, 8))
        self.assertEqual((hydrate.electrons_per_metal, hydrate.protons_per_metal), (2, 0))

    def test_original_fluoride_solid_rows_resolve_lutetium_formula_conflict(self) -> None:
        lutetium, ytterbium = self.database.species_records((
            "gfe-lu-luf3-q+0-solid-crystalline-rare-earth-trifluoride",
            "gfe-yb-ybf3-q+0-solid-crystalline-rare-earth-trifluoride",
        ))
        self.assertEqual(lutetium.formula_ascii, "LuF3")
        self.assertEqual(lutetium.thermochemistry.gibbs_energy_J_mol.value, -1610370)
        self.assertEqual(ytterbium.thermochemistry.gibbs_energy_J_mol.value, -1587370)
        self.assertTrue(any(w.type == "ree_fluoride_native_G_discrepancy"
                            and "YbF3" in w.message for w in lutetium.warnings))
        loaded = self.database.load_system("Lu", ligand_ids=("fluoride-f",))
        solid = next(s for s in loaded.species if s.record_id == lutetium.record_id)
        self.assertEqual((solid.charge, solid.ligand_count, solid.electrons_per_metal), (0, 3, 3))
        self.assertEqual(solid.ligand_gibbs_energy_J_mol, -278790)
        self.assertFalse(any(s.record_id == solid.record_id
                             for s in self.database.load_system("Lu").species))

    def test_fluoride_monohydrate_retains_h_without_borrowing_anhydrous_g(self) -> None:
        record = self.database.species_records((
            "gfe-la-laf3-h2o-q+0-solid-rare-earth-trifluoride-monohydrate",
        ))[0]
        self.assertEqual(record.formula_ascii, "LaF3(H2O)")
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, -1987400)
        self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
        self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.status, "not_available")
        self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
        self.assertFalse(any(s.record_id == record.record_id for s in
                             self.database.load_system("La", ligand_ids=("fluoride-f",)).species))

    def test_rare_earth_chloride_fit_variants_and_derived_enthalpies(self) -> None:
        mono, double = self.database.species_records((
            "gfe-la-lacl-q+2-aqueous-aq", "gfe-la-lacl2-q+1-aqueous-aq",
        ))
        self.assertAlmostEqual(mono.thermochemistry.gibbs_energy_J_mol.value, -196390 * 4.184)
        entropies = [r for r in mono.reported if r.property == "absolute_entropy"]
        self.assertEqual({r.value for r in entropies}, {
            round(s * 4.184, 6) for s in (-47.06, -27.49)
        })
        selected = next(r for r in entropies if r.selected_as_recommended)
        self.assertAlmostEqual(selected.value, -27.49 * 4.184)
        self.assertIn("Table7", selected.source.source_id)
        enthalpies = [r for r in mono.reported if r.property == "enthalpy_of_formation"]
        self.assertEqual(len(enthalpies), 2)
        for row in enthalpies:
            self.assertIn("NBSderived", row.source.source_id)
            self.assertIn("10.18434/M32124", row.source.locator)
            self.assertIsNone(row.uncertainty)
            self.assertEqual(row.status, "source_verified_estimate")
        expected = -196390 * 4.184 + 298.15 * (-27.49 * 4.184 - 56.9 - 223.066 / 2 + 130.684)
        self.assertAlmostEqual(mono.thermochemistry.formation_enthalpy_J_mol.value, expected, places=5)
        loaded = self.database.load_system("La", ligand_ids=("chloride-cl",))
        encoded = {r.record_id: r for r in loaded.species}
        self.assertEqual((encoded[mono.record_id].charge, encoded[mono.record_id].ligand_count), (2, 1))
        self.assertEqual((encoded[double.record_id].charge, encoded[double.record_id].ligand_count), (1, 2))
        self.assertEqual(encoded[double.record_id].electrons_per_metal, 3)

    def test_rare_earth_fluoride_reference_and_metal_inventory(self) -> None:
        ordinary = self.database.load_system("La")
        self.assertFalse(any(r.formula_ascii == "LaF" for r in ordinary.species))
        enabled = self.database.load_system("La", ligand_ids=("fluoride-f",))
        fluoride = next(r for r in enabled.species if r.formula_ascii == "LaF")
        self.assertEqual((fluoride.charge, fluoride.ligand_count, fluoride.electrons_per_metal), (2, 1, 3))
        self.assertEqual(fluoride.ligand_gibbs_energy_J_mol, -278790)
        conditions = pb.PourbaixConditions(pH_points=5, U_points=5,
            ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity("fluoride-f", log10_free_activity=-3),
            )))
        total = 1e-6
        balance = pb.MassBalanceEngine(self.database).calculate(
            "La", conditions, pb.TotalMetalConcentration(total), allow_incomplete=True,
        )
        error = abs(balance.dissolved_metal_mol_L + total * balance.precipitated_metal_fraction - total)
        self.assertLess(float(error.max()), 1e-15)

    def test_aluminum_oxyhydroxide_polymorphs_have_separate_records(self) -> None:
        boehmite, diaspore, gibbsite = self.database.species_records((
            "gfe-al-alooh-q+0-solid-boehmite", "gfe-al-alooh-q+0-solid-diaspore",
            "gfe-al-al-oh-3-q+0-solid-gibbsite",
        ))
        self.assertEqual(boehmite.formula_ascii, diaspore.formula_ascii)
        self.assertEqual(boehmite.thermochemistry.gibbs_energy_J_mol.value, -918400)
        self.assertEqual(diaspore.thermochemistry.gibbs_energy_J_mol.value, -922700)
        self.assertEqual(boehmite.thermochemistry.gibbs_energy_J_mol.uncertainty, 2200)
        self.assertEqual(gibbsite.thermochemistry.gibbs_energy_J_mol.value, -1155775)
        self.assertTrue(all("10.3133/b2131" in r.source.url for r in boehmite.reported))

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
        original_parent = next(row for row in iron.reported
                               if row.value_id == "gfe-fe-fe-q+2-aqueous-aq:gf:preferred")
        self.assertEqual(hydrated.thermochemistry.gibbs_energy_J_mol.value, -370871.0)
        # The original fit retains its recorded parent evaluation when policy choices change.
        self.assertAlmostEqual(-(original_iron.value - original_parent.value
                                 - 2 * self.database.reference_state.water_gibbs_energy_J_mol)
                               / rt_log10, -32.48, places=6)
        self.assertIn("Fe(OH)3(-)=HFeO2(-)+H2O", original_iron.source.locator)

    def test_akinfiev_diamond_alternatives_use_molal_gas_and_absolute_entropy(self) -> None:
        for formula, symbol, element_entropy in (
            ("CH4", "C", 5.740 + 2 * 130.684),
            ("CO2", "C", 5.740 + 205.138),
            ("N2", "N", 191.61),
            ("NH3", "N", 191.61 / 2 + 1.5 * 130.684),
        ):
            record = self.database.species_records((
                f"gfe-{symbol.lower()}-{formula.lower()}-q+0-aqueous-aq",
            ))[0]
            triplet = {row.property: row for row in record.reported
                       if row.source and row.source.source_id.startswith(
                           f"AkinfievDiamond2003_Table1_{formula}_")}
            self.assertEqual(len(triplet), 3)
            self.assertTrue(all(not row.selected_as_recommended for row in triplet.values()))
            self.assertTrue(all(row.status == "source_verified_estimate" and row.uncertainty is None
                                for row in triplet.values()))
            self.assertTrue(all("Table1" in row.source.locator and "Appendix A.4" in row.source.locator
                                and "10.18434/M32124" in row.source.locator
                                for row in triplet.values()))
            gibbs = triplet["gibbs_energy_of_formation"].value
            entropy = triplet["absolute_entropy"].value
            enthalpy = triplet["enthalpy_of_formation"].value
            self.assertGreater(entropy, 0)
            self.assertAlmostEqual(enthalpy, gibbs + 298.15 * (entropy - element_entropy),
                                   delta=0.001)
            if formula == "CH4":
                # Independent Eq. 17 Henry-law check, including Nw exactly once.
                temperature, density, water_mass = 298.15, 0.9970, 18.0152
                log_henry = ((1 + 0.1131) * -3.4773
                             - 0.1131 * math.log(83.1441 * temperature / water_mass * density)
                             + density * (-11.8462 + 14.8615 * math.sqrt(1000 / temperature)))
                henry_gibbs = -50720 + 1.9872 * 4.184 * temperature * (
                    log_henry - math.log(1000 / water_mass))
                self.assertAlmostEqual(gibbs, henry_gibbs, delta=5)
                self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.value, -34330)
            if formula == "CO2":
                self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.value, -385980)
        self.assertTrue(self.database.load_system("C").is_thermochemically_complete)

    def test_akinfiev_diamond_preserves_both_hydrogen_sulfide_fits(self) -> None:
        record = self.database.species_records(("gfe-s-h2s-q+0-aqueous-aq",))[0]
        observations = [row for row in record.reported if row.source
                        and row.source.source_id.startswith("AkinfievDiamond2003_")]
        self.assertEqual(len(observations), 7)
        self.assertTrue(all(not row.selected_as_recommended for row in observations))
        entropies = {row.source.source_id: row.value for row in observations
                     if row.property == "absolute_entropy"}
        self.assertAlmostEqual(entropies["AkinfievDiamond2003_H2S_below200_printed_entropy"],
                               29.96 * 4.184, places=6)
        self.assertAlmostEqual(entropies["AkinfievDiamond2003_Table1_H2S_below200_entropy_NBS_estimate"],
                               29.96 * 4.184, delta=0.02)
        self.assertLess(entropies["AkinfievDiamond2003_Table1_H2S_all_entropy_NBS_estimate"], 117)
        self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.value, -27830)
        self.assertEqual(record.thermochemistry.entropy_J_mol_K.value, 121)

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
        self.assertEqual(aluminum.thermochemistry.entropy_J_mol_K.value, 28.33)
        entropy = next(row for row in aluminum.reported if row.property == "absolute_entropy"
                       and row.source and row.source.source_id.startswith("NBS_PDR_M32124_retained_"))
        self.assertEqual(entropy.value, 28.33)
        self.assertTrue(entropy.selected_as_recommended)
        self.assertIn("CSV logical record 3558", entropy.source.locator)

    def test_aluminum_reference_corrections_retain_distinct_evaluations(self) -> None:
        aluminum = self.database.species_records(("gfe-al-al-q+3-aqueous-aq",))[0]
        for model, gibbs, enthalpy, entropy in (
            ("PokrovskiiHelgeson1995", -487759.0, -538572.0, -338.148),
            ("TagirovSchott2001", -487621.0, -538937.0, -339.834),
        ):
            rows = {row.property: row for row in aluminum.reported if row.source
                    and row.source.source_id.startswith(f"WoleryJoveColon2017_Table24_{model}_")}
            self.assertEqual({prop: row.value for prop, row in rows.items()}, {
                "gibbs_energy_of_formation": gibbs,
                "enthalpy_of_formation": enthalpy,
                "absolute_entropy": entropy,
            })
            self.assertTrue(all(not row.selected_as_recommended and row.uncertainty is None
                                for row in rows.values()))
            self.assertTrue(all("10.1016/j.gca.2016.09.028" in row.source.locator
                                and "Table24" in row.source.locator for row in rows.values()))
        for rid, value in (("gfe-al-al-oh-3-q+0-solid-gibbsite", -1154903.0),
                           ("gfe-al-al2o3-q+0-solid-alpha-al2o3-corundum", -1582257.0)):
            record = self.database.species_records((rid,))[0]
            rows = [row for row in record.reported if row.source
                    and row.source.source_id.startswith("WoleryJoveColon2017_Table23_")]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].value, value)
            self.assertFalse(rows[0].selected_as_recommended)

    def test_aluminum_calorimetry_alternative_keeps_reported_uncertainty(self) -> None:
        aluminum = self.database.species_records(("gfe-al-al-q+3-aqueous-aq",))[0]
        rows = {row.property: row for row in aluminum.reported if row.source
                and row.source.source_id.startswith("WoleryJoveColon2017_Table25_")}
        for prop, value, uncertainty in (("gibbs_energy_of_formation", -490115.0, 1623.0),
                                        ("enthalpy_of_formation", -538350.0, 862.0),
                                        ("absolute_entropy", -329.5, 4.61)):
            self.assertEqual(rows[prop].value, value)
            self.assertEqual(rows[prop].uncertainty, uncertainty)
            self.assertIn("TWO standard deviations", rows[prop].source.locator)
            self.assertFalse(rows[prop].selected_as_recommended)
        thermo = aluminum.thermochemistry
        self.assertEqual(thermo.formation_enthalpy_J_mol.value, -531000.0)
        self.assertIsNone(thermo.formation_enthalpy_J_mol.uncertainty)
        self.assertEqual(thermo.gibbs_energy_J_mol.value, -488824.0)
        self.assertEqual(thermo.entropy_J_mol_K.value, -334)
        self.assertTrue(any("different evaluations" in warning.message for warning in aluminum.warnings))

    def test_silica_corrections_use_the_stored_hydrated_formula(self) -> None:
        record = self.database.species_records(("gfe-si-h4sio4-q+0-aqueous-aq",))[0]
        rows = [row for row in record.reported if row.source
                and row.source.source_id.startswith("WoleryJoveColon2017_Table20_")]
        self.assertEqual(len(rows), 11)
        for model, gibbs, enthalpy, entropy in (
            ("Rimstidt1997", -1309228.0, -1461166.0, None),
            ("GunnarssonArnorsson2000", -1309187.0, -1461721.0, 178.871),
            ("Stefansson2001", -1308817.0, -1458518.0, 188.374),
            ("AppsSpycher2004", -1308801.0, -1459186.0, 186.080),
        ):
            values = {row.property: row.value for row in rows if model in row.source.source_id}
            expected = {"gibbs_energy_of_formation": gibbs, "enthalpy_of_formation": enthalpy}
            if entropy is not None:
                expected["absolute_entropy"] = entropy
            self.assertEqual(values, expected)
        self.assertTrue(all(not row.selected_as_recommended and row.uncertainty is None
                            for row in rows))
        self.assertTrue(all("H4SiO4(aq) columns" in row.source.locator for row in rows))
        self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.value, -1309201.0)
        self.assertEqual(record.thermochemistry.entropy_J_mol_K.value, 181.105)
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, -1461070.0)
        self.assertFalse(any(s.formula_ascii == "SiO2" and s.phase == "aqueous"
                             for s in self.database.load_system("Si").species))

    def test_rimstidt_original_outputs_preserve_one_sigma_and_entropy_identity(self) -> None:
        record = self.database.species_records(("gfe-si-h4sio4-q+0-aqueous-aq",))[0]
        rows = {row.property: row for row in record.reported if row.source
                and row.source.source_id.startswith("Rimstidt1997_original_abstract_")}
        for prop, value, uncertainty in (("gibbs_energy_of_formation", -1309231.0, 610.0),
                                        ("enthalpy_of_formation", -1460913.0, 542.0),
                                        ("absolute_entropy", 180.87, 0.49)):
            self.assertEqual(rows[prop].value, value)
            self.assertEqual(rows[prop].uncertainty, uncertainty)
            self.assertIn("+/-1 standard deviation", rows[prop].source.locator)
            self.assertIn("10.1016/S0016-7037(97)00103-8", rows[prop].source.locator)
            self.assertFalse(rows[prop].selected_as_recommended)
        self.assertEqual(sum(row.property == "absolute_entropy" and row.value == 180.87
                             for row in record.reported), 1)

    def test_periodic_screen(self) -> None:
        screen = pb.screen_periodic_table(self.database, pH=0, potential_V=1.6, reference="RHE",
                                          allow_incomplete=False)
        self.assertEqual((len(screen.elements), screen.supported_count, screen.calculated_count), (118, 75, 55))
        # The new H-only bayerite makes the strict Al phase inventory incomplete.
        self.assertIs(screen.element("Al").status, pb.ElementStatus.INCOMPLETE)
        # The three retained H-only Se crystals keep its Gibbs inventory incomplete.
        self.assertIs(screen.element("Se").status, pb.ElementStatus.INCOMPLETE)
        # Finite-I Nb evidence stays retained and excluded from standard-state calculations.
        self.assertIs(screen.element("Nb").status, pb.ElementStatus.INCOMPLETE)
        default = pb.screen_periodic_table(self.database, pH=0, potential_V=1.6, reference="RHE")
        self.assertEqual(sum(item.stable is not None for item in default.elements), 75)
        self.assertIs(screen.element("Fe").status, pb.ElementStatus.INCOMPLETE)
        relaxed = pb.screen_periodic_table(self.database, pH=0, potential_V=1.6, reference="RHE",
                                            allow_incomplete=True)
        self.assertEqual(relaxed.element("Fe").stable.species, "Fe³⁺")
        self.assertEqual(relaxed.calculated_count, 75)
        titanium = screen.element("Ti")
        self.assertEqual((titanium.stable.species, titanium.category, titanium.structure_label),
                         ("TiO₂", pb.Category.SOLID_OXIDE, "rutile"))
        fallback = pb.screen_periodic_table(self.database, pH=0, potential_V=1.6, reference="RHE",
                                            energy_policy="experimental_then_mp", allow_incomplete=False)
        self.assertEqual(fallback.calculated_count, 58)
        platinum = self.database.load_system("Pt", energy_policy="experimental_then_mp")
        self.assertEqual({item.formula_ascii for item in platinum.species
                          if item.gibbs_status is pb.EvidenceStatus.MATERIALS_PROJECT_FALLBACK}, {"PtO", "PtO2"})

    def test_materials_project_rows(self) -> None:
        rows = self.database.materials_project_thermochemistry()
        self.assertEqual((len(rows), len({item["record_id"] for item in rows})), (299, 105))
        self.assertEqual(sum(item["experimental_enthalpy_eV_atom"] is not None for item in rows), 291)
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


class SelectionPolicyGuardTests(unittest.TestCase):
    """The recommended values follow from the evidence and the default policy."""

    def test_recommendations_are_pinned(self) -> None:
        import hashlib
        from collections import Counter

        database = pb.ThermodynamicDatabase.bundled()
        selections = database.selections
        self.assertEqual(Counter(key[1] for key in selections),
                         {"gibbs_energy_of_formation": 1166, "absolute_entropy": 1139, "enthalpy_of_formation": 1023})
        chosen = sorted(f"{key[0]}|{key[1]}|{item.chosen.value_id}" for key, item in selections.items())
        self.assertEqual(hashlib.sha256("\n".join(chosen).encode()).hexdigest()[:16], "e8e6dbb8e1139039",
                         "the evidence or the default policy changed the recommended values")

    def test_the_file_holds_no_recommendations(self) -> None:
        database = pb.ThermodynamicDatabase.bundled()
        self.assertFalse(database._stores_recommendations)
        self.assertEqual(database.metadata["schema_version"], "9")
