"""NEA zirconium observations retain their source and component conventions."""

from dataclasses import replace
import unittest

import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import transformed_gibbs_J_mol_metal


class NEAZirconiumComponentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_hydroxo_source_and_stored_component_have_equal_energy(self):
        database = self.database
        for rid, formula, waters, source_g in (
            ("gfe-zr-zro-q+2-aqueous-aq", "Zr(OH)2", 1, -1008384),
            ("gfe-zr-zro2-q+0-aqueous-aq", "Zr(OH)4", 2, -1464570),
        ):
            item = next(s for s in database.load_system("Zr").species if s.record_id == rid)
            self.assertEqual(item.gibbs_energy_J_mol,
                             source_g - waters * database.reference_state.water_gibbs_energy_J_mol)
            self.assertEqual(item.electrons_per_metal, 4)
            source = replace(item, formula_ascii=formula, core_hydrogen_count=2 * waters,
                             core_oxygen_count=item.core_oxygen_count + waters,
                             gibbs_energy_J_mol=source_g)
            for activity in (-6, 0):
                conditions = pb.PourbaixConditions(aqueous_activities=pb.AqueousActivityModel(
                    default_log10_activity=activity))
                for pH, potential in ((0, -1), (7, .2), (14, 1)):
                    with self.subTest(record_id=rid, activity=activity, pH=pH):
                        self.assertAlmostEqual(float(transformed_gibbs_J_mol_metal(
                            item, database.reference_state, conditions, pH, potential)),
                            float(transformed_gibbs_J_mol_metal(
                                source, database.reference_state, conditions, pH, potential)),
                            places=7)

    def test_hydrolysis_keeps_older_observations_and_source_intervals(self):
        for rid, old_g, selected_g, width in (
            ("gfe-zr-zro-q+2-aqueous-aq", -784918.4, -771255, 11034),
            ("gfe-zr-zro2-q+0-aqueous-aq", -976545.6, -990312, 13391),
        ):
            record = self.database.species_records((rid,))[0]
            old = next(row for row in record.reported if row.value_id == rid + ":gf:preferred")
            selected = next(row for row in record.reported
                            if row.value_id == rid + ":gibbs_energy_of_formation:nea02g1-selected")
            self.assertEqual(old.value, old_g)
            self.assertFalse(old.selected_as_recommended)
            self.assertTrue(selected.selected_as_recommended)
            self.assertEqual((selected.value, selected.uncertainty), (selected_g, width))
            self.assertIn("95% confidence", selected.source.locator)
            self.assertIn("further sublicensees", selected.source.locator)
            self.assertTrue(any("not a molecular-structure assignment" in w.message
                                for w in record.warnings))
            for prop in ("absolute_entropy", "enthalpy_of_formation"):
                self.assertTrue(any(row.property == prop and row.selected_as_recommended
                                    and ":nea02g1-" not in row.value_id for row in record.reported))

    def test_zircon_matches_the_physical_neutral_silica_reaction(self):
        database = self.database
        system = database.load_system("Zr", ligand_ids=("silica-sio2-component",))
        zircon = next(s for s in system.species if s.record_id == "nea02g1-zr-zircon")
        self.assertEqual((zircon.core_oxygen_count, zircon.core_hydrogen_count,
                          zircon.electrons_per_metal, zircon.protons_per_metal), (2, 0, 4, 4))
        ligand = next(l for l in database.available_ligands()
                      if l.ligand_id == "silica-sio2-component")
        self.assertEqual((ligand.formula_ascii, ligand.charge,
                          ligand.gibbs_energy_J_mol), ("SiO2", 0, -842342))
        # Zr + H4SiO4 = ZrSiO4 + 4H+ + 4e-; both references remove two waters.
        rtln = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        for activity in (-6, -3, -1):
            conditions = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity(ligand.ligand_id, log10_free_activity=activity),)))
            for pH, potential in ((0, -1), (7, 0), (14, 1)):
                expected = (-1919712 + 1316600 - rtln * activity
                            - 4 * rtln * pH - 4 * FARADAY_C_MOL * potential)
                self.assertAlmostEqual(float(transformed_gibbs_J_mol_metal(
                    zircon, database.reference_state, conditions, pH, potential)), expected, places=7)

    def test_selenite_retains_selected_enthalpy_and_explicit_gibbs_gap(self):
        record = self.database.species_records(("nea02g1-zr-selenite",))[0]
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, -1609550)
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.uncertainty, 2689)
        self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
        self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
        system = self.database.load_system("Zr", ligand_ids=("selenite-seo3",))
        excluded = next(s for s in system.excluded if s.record_id == record.record_id)
        self.assertIs(excluded.reason, pb.ExclusionReason.GIBBS_ENERGY_UNAVAILABLE)

    def test_zirconium_gas_is_explicit_and_default_closed_balance_still_works(self):
        default = self.database.load_system("Zr")
        self.assertFalse(any(s.is_gas for s in default.species))
        excluded = next(s for s in default.excluded if s.record_id == "nea02g1-zr-gas")
        self.assertIs(excluded.reason, pb.ExclusionReason.GAS_NOT_SELECTED)
        selected = self.database.load_system("Zr", include_optional_gases=True)
        gas = next(s for s in selected.species if s.record_id == "nea02g1-zr-gas")
        conditions = pb.PourbaixConditions(pH_points=5, U_points=5,
            gas_fugacities=pb.GasFugacityModel(overrides={gas.record_id: -3}))
        self.assertAlmostEqual(float(transformed_gibbs_J_mol_metal(
            gas, self.database.reference_state, conditions, 7, 0)),
            566882 - 3 * GAS_CONSTANT_J_MOL_K * 298.15 * LN_10)
        engine = pb.MassBalanceEngine(self.database)
        result = engine.calculate("Zr", conditions, pb.TotalMetalConcentration(1e-4))
        self.assertEqual(result.dominant_species_index.shape, (5, 5))
        with self.assertRaises(pb.UnsupportedConditionError):
            engine.calculate_system(selected, conditions, pb.TotalMetalConcentration(1e-4))
