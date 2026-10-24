"""NEA ancillary observations and the dated ThermoHub catalog boundary."""
from dataclasses import replace
import json
import unittest

import numpy as np
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal


class ThermoHubReleaseSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_original_columns_units_and_quoted_widths(self):
        record = self.database.species_records(('r14-na-sodium-carbonate',))[0]
        self.assertEqual((record.thermochemistry.gibbs_energy_J_mol.value,
                          record.thermochemistry.formation_enthalpy_J_mol.value,
                          record.thermochemistry.entropy_J_mol_K.value), (-1045450, -1129250, 135))
        widths = {'gibbs_energy_of_formation': 345, 'enthalpy_of_formation': 300, 'absolute_entropy': .4}
        for row in record.reported:
            self.assertEqual(row.uncertainty, widths[row.property])
            self.assertEqual((row.temperature_K, row.pressure_bar), (298.15, 1))
            locator = json.loads(row.source.locator)
            self.assertEqual((locator['table'], locator['printed_page'], locator['pdf_page']), ('III-1', 47, 89))
            self.assertIn('95%', locator['uncertainty_convention'])
            self.assertEqual(self.database.selections[record.record_id, row.property].chosen.evidence_class, 'A')

    def test_carbonate_formula_unit_has_two_primary_atoms(self):
        rid = 'r14-na-sodium-carbonate'
        self.assertNotIn(rid, {s.record_id for s in self.database.load_system('Na').species})
        phase = next(s for s in self.database.load_system('Na', ligand_ids=('carbonate-co3',)).species
                     if s.record_id == rid)
        self.assertEqual((phase.metal_count, phase.components[0].count,
                          phase.core_oxygen_count, phase.core_hydrogen_count), (2, 1, 0, 0))
        self.assertEqual(replace(phase, electron_coefficient_per_metal=None).electrons_per_metal, 1)

    def test_bicarbonate_retains_hydrogen_and_pH_slope(self):
        phase = next(s for s in self.database.load_system('Na', ligand_ids=('carbonate-co3',)).species
                     if s.record_id == 'r14-na-sodium-bicarbonate')
        self.assertEqual((phase.metal_count, phase.core_oxygen_count,
                          phase.core_hydrogen_count, phase.protons_per_metal), (1, 0, 1, -1))
        cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity('carbonate-co3', log10_free_activity=-3),)))
        energies = [float(standard_transformed_gibbs_J_mol_metal(
            phase, self.database.reference_state, cfg, pH, 0)) for pH in [6, 7]]
        self.assertAlmostEqual(energies[1] - energies[0], GAS_CONSTANT_J_MOL_K * 298.15 * LN_10)

    def test_phosphate_hydrate_counts_water_and_protons_once(self):
        phase = next(s for s in self.database.load_system('Ca', ligand_ids=('phosphate-po4',)).species
                     if s.record_id == 'r14-ca-calcium-dihydrogen-phosphate-monohydrate')
        self.assertEqual((phase.metal_count, phase.components[0].count, phase.core_oxygen_count,
                          phase.core_hydrogen_count, phase.protons_per_metal), (1, 2, 1, 6, -4))
        self.assertEqual(replace(phase, electron_coefficient_per_metal=None).electrons_per_metal, 2)
        rtln = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity('phosphate-po4', log10_free_activity=-3),)))
        for pH, potential in [(0, -1), (7, 0), (14, 1)]:
            expected = (-3071840 - self.database.reference_state.water_gibbs_energy_J_mol
                        - 2 * (phase.components[0].gibbs_energy_J_mol - 3 * rtln)
                        + 4 * rtln * pH - 2 * FARADAY_C_MOL * potential)
            self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(
                phase, self.database.reference_state, cfg, pH, potential)), expected, places=7)

    def test_enthalpy_only_selections_preserve_gibbs_gaps(self):
        for rid, sym, ligand, enthalpy in [('r14-b-borax', 'B', 'sodium-na', -6289600),
                ('r14-k-potassium-bicarbonate', 'K', 'carbonate-co3', -960700)]:
            record = self.database.species_records((rid,))[0]
            self.assertEqual({r.property for r in record.reported}, {'enthalpy_of_formation'})
            self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, enthalpy)
            self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
            self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
            excluded = self.database.load_system(sym, ligand_ids=(ligand,)).excluded
            self.assertEqual(next(r.reason for r in excluded if r.record_id == rid),
                             pb.ExclusionReason.GIBBS_ENERGY_UNAVAILABLE)
        self.assertEqual(self.database.species_records(('r14-b-borax',))[0].formula_ascii, 'Na2B4O7(H2O)10')

    def test_phosphate_enabled_primary_balance(self):
        cfg = pb.PourbaixConditions(pH_points=7, U_points=9,
            ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('phosphate-po4', log10_free_activity=-3),)))
        system = self.database.load_system('Ca', ligand_ids=('phosphate-po4',))
        system = replace(system, species=tuple(s for s in system.species if not s.is_gas))
        for model in [pb.IdealActivityCoefficientModel(), pb.DaviesActivityCoefficientModel(.01)]:
            result = pb.MassBalanceEngine(self.database, activity_coefficient_model=model).calculate_system(
                system, cfg, pb.TotalMetalConcentration(1e-3))
            np.testing.assert_allclose(result.dissolved_metal_mol_L + 1e-3 * result.precipitated_metal_fraction,
                                       1e-3, rtol=1e-10, atol=1e-15)

    def test_catalog_licence_and_source_holds_remain_distinct(self):
        review = json.loads(self.database.metadata['R14_ThermoHub_release_review'])
        inventory = review['inventory']
        self.assertEqual((inventory['substance_records'], inventory['property_slots'],
                          inventory['dataset_families'], inventory['defined_datasets']), (9039, 27117, 9, 8))
        self.assertEqual(inventory['graph_numbers_imported'], 0)
        self.assertEqual(inventory['catalog_cutoff'], '2026-10-24')
        self.assertTrue(inventory['licence_route']['metadata_difference_preserved'])
        self.assertIn('GPL-3.0', inventory['licence_route']['selected_route'])
        self.assertEqual(len(json.loads(self.database.metadata['R14_NEA15_observations'])), 14)
        holds = json.loads(self.database.metadata['R14_source_and_version_holds'])
        self.assertIn('10a', holds['THERMOCHIMIE'])
        self.assertIn('12a', holds['THERMOCHIMIE'])
        self.assertIn('commercial', holds['CODATA'])
        self.assertIn('further sublicensees', review['reuse']['downstream_acknowledgment'])


if __name__ == '__main__':
    unittest.main()
