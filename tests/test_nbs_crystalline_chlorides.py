"""Original open NBS chloride cells, source gaps and model boundaries."""
from dataclasses import replace
import json
import unittest
import numpy as np
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature

SID = 'R16d1_open_NBS_crystalline_chlorides'

class NBSChlorideExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()

    def test_original_columns_and_missing_uncertainty(self):
        record = self.db.species_records(('r16d1-al-nbs-record3608',))[0]
        self.assertEqual({r.property: r.value for r in record.reported}, {
            'gibbs_energy_of_formation': -628800, 'enthalpy_of_formation': -704200,
            'absolute_entropy': 110.67})
        for row in record.reported:
            self.assertEqual((row.temperature_K, row.pressure_bar, row.uncertainty), (298.15, 1, None))
            ev = json.loads(row.source.locator)
            self.assertEqual(ev['logical_csv_record'], 3608)
            self.assertEqual(ev['csv_column_zero_based'], {'gibbs_energy_of_formation': 8,
                             'enthalpy_of_formation': 7, 'absolute_entropy': 10}[row.property])
            self.assertIn('distinction is not recoverable', ev['evaluation_type'])
            self.assertEqual(self.db.selections[record.record_id, row.property].chosen.evidence_class, 'B')

    def test_prior_original_evaluations_are_linked(self):
        review = json.loads(self.db.metadata['R16d1_NBS_chloride_source_review'])
        self.assertEqual((review['source_rows'], review['supported_systems'], review['retained_original_cells']), (157, 66, 95))
        retained = next(r for r in review['records'] if r['source_csv_record'] == 4043)
        self.assertEqual(retained['record_id'], 'r16-zn-nbs-record4043')
        self.assertEqual(retained['admitted_properties'], [])
        self.assertEqual(len(retained['retained_original_properties']), 3)
        self.assertEqual(len(self.db.species_records(('r16-zn-nbs-record4043',))[0].reported), 3)

    def test_halite_gains_G_H_and_preserves_earlier_entropy(self):
        rid = 'r05-na-nacl-halite'
        record = self.db.species_records((rid,))[0]
        self.assertIsNotNone(record.thermochemistry.gibbs_energy_J_mol.value)
        self.assertIsNotNone(record.thermochemistry.formation_enthalpy_J_mol.value)
        self.assertEqual(record.thermochemistry.entropy_J_mol_K.value, 72.13)
        old = next(r for r in record.reported if r.value_id == rid + ':entropy:USGS1995')
        self.assertEqual(old.value, 72.1)
        self.assertFalse(old.selected_as_recommended)

    def test_source_H_only_S_only_and_phase_codes_remain_explicit(self):
        for rid, prop, value in [('r16d1-la-nbs-record8179', 'enthalpy_of_formation', -1071100),
                                 ('r16d1-ra-nbs-record10250', 'absolute_entropy', 134)]:
            record = self.db.species_records((rid,))[0]
            self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
            self.assertEqual([(r.property, r.value) for r in record.reported], [(prop, value)])
        beta = self.db.species_records(('r16d1-dy-nbs-record7585',))[0]
        self.assertIn('β', beta.phase_identity.possible_phases)
        self.assertEqual(beta.phase_identity.status, 'unresolved')
        self.assertIsNone(beta.phase_identity.spacegroup_symbol)

    def test_strontium_hydrate_counts_each_water_once(self):
        rid = 'r16d1-sr-nbs-record9682'
        self.assertNotIn(rid, {s.record_id for s in self.db.load_system('Sr').species})
        phase = next(s for s in self.db.load_system('Sr', ligand_ids=('chloride-cl',)).species if s.record_id == rid)
        self.assertEqual((phase.metal_count, phase.core_oxygen_count, phase.core_hydrogen_count,
                          phase.components[0].count, phase.electrons_per_metal, phase.protons_per_metal), (1, 6, 12, 2, 2, 0))
        cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity('chloride-cl', log10_free_activity=-3),)))
        rt = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        expected = (-2240920 - 6 * self.db.reference_state.water_gibbs_energy_J_mol
                    - 2 * (phase.components[0].gibbs_energy_J_mol - 3 * rt) - 2 * FARADAY_C_MOL)
        self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(
            phase, self.db.reference_state, cfg, 7, 1)), expected, places=7)

    def test_source_cycle_discrepancies_are_not_silently_corrected(self):
        for rid, g, h, entropy in [('r16d1-re-nbs-record6471', -188000, -264000, 123.8),
                                   ('r16d1-ra-nbs-record10252', -1302800, -1464000, 213)]:
            record = self.db.species_records((rid,))[0]
            self.assertEqual({r.property: r.value for r in record.reported}, {
                'gibbs_energy_of_formation': g, 'enthalpy_of_formation': h, 'absolute_entropy': entropy})
            self.assertTrue(any(w.type == 'r16d1_original_reported_GHS_cycle_discrepancy' for w in record.warnings))
            for row in record.reported:
                self.assertTrue(json.loads(row.source.locator)['original_printed_cells_visually_verified'])
                self.assertIsNone(row.uncertainty)

    def test_primary_inventory_and_existing_thermal_exclusion(self):
        system = self.db.load_system('Sr', ligand_ids=('chloride-cl',))
        system = replace(system, species=tuple(s for s in system.species if not s.is_gas))
        cfg = pb.PourbaixConditions(pH_points=7, U_points=9, ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity('chloride-cl', log10_free_activity=-3),)))
        for model in [pb.IdealActivityCoefficientModel(), pb.DaviesActivityCoefficientModel(.01)]:
            result = pb.MassBalanceEngine(self.db, activity_coefficient_model=model).calculate_system(system, cfg, pb.TotalMetalConcentration(1e-3))
            np.testing.assert_allclose(result.dissolved_metal_mol_L + 1e-3 * result.precipitated_metal_fraction,
                                       1e-3, rtol=1e-10, atol=1e-15)
        self.assertNotIn('r16d1-sr-nbs-record9682', {s.record_id for s in at_temperature(
            self.db, 323.15).load_system('Sr', ligand_ids=('chloride-cl',)).species})

    def test_independent_permission_and_all_new_observations(self):
        self.assertEqual(len(json.loads(self.db.metadata['R16d1_NBS_chloride_observations'])), 210)
        review = json.loads(self.db.metadata['R16d1_NBS_chloride_source_review'])
        self.assertEqual(review['new_species'], 111)
        self.assertEqual(review['holds'], [])
        self.assertEqual(review['reuse']['doi'], '10.18434/M32124')
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'], 'held_redistribution_rights')

if __name__ == '__main__':
    unittest.main()
