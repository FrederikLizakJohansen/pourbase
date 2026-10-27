"""USGS empirical sulfide units preserve fractional primary counts and source data."""
import json
import unittest
from contextlib import closing
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
G = 'gibbs_energy_of_formation'
H = 'enthalpy_of_formation'
S = 'absolute_entropy'

class USGSCopperSulfideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()
        cls.review = json.loads(cls.db.metadata['R16d5b_USGS_Cu_sulfides'])
        cls.rows = cls.review['records']
        cls.observations = json.loads(cls.db.metadata['R16d5b_USGS_Cu_observations'])

    def test_source_cells_units_intervals_and_ancestry(self):
        self.assertEqual((self.review['released_Cu_rows'], len(self.observations)), (3, 9))
        for obs in self.observations:
            record = self.db.species_records((obs['record_id'],))[0]
            reported = next(r for r in record.reported if r.value_id == obs['value_id'])
            ev = json.loads(reported.source.locator)
            self.assertEqual((ev['original_printed_page'], ev['original_pdf_page']), (11, 17))
            self.assertEqual((reported.temperature_K, reported.pressure_bar), (298.15, 1))
            self.assertEqual(reported.value, ev['original_value'] * ev['conversion_factor'])
            self.assertEqual(reported.uncertainty, ev['original_width'] * ev['conversion_factor'])
            self.assertEqual(ev['formula_unit_factor'], 1)
            expected = [394] if 'djurleite' in record.record_id else [133]
            if reported.property != S:
                expected = [337, 140] if 'anilite' in record.record_id else [337]
            self.assertEqual(ev['property_specific_reference_numbers'], expected)
            candidate = next(c for c in self.db.selections[record.record_id, reported.property].candidates
                             if c.value_id == reported.value_id)
            self.assertEqual((candidate.evidence_class, candidate.family), ('B', 'Robie & Hemingway'))
            self.assertIsNotNone(reported.evaluation_lineage)

    def test_complete_empirical_units_keep_fractional_Cu_counts(self):
        for row in self.rows:
            rid = row['record_id']
            with closing(self.db.connect()) as c:
                sp = c.execute('select *from species where record_id=?', (rid,)).fetchone()
            M = row['primary_count']
            self.assertIn(M, [1.75, 1.8, 1.95])
            self.assertEqual((sp['metal_count'], sp['ligand_count'], sp['atom_count']), (M, 1, M + 1))
            self.assertEqual(sp['formula_ascii'], row['source_formula'])
            self.assertAlmostEqual(sp['electron_coefficient_per_metal'], 2 / M)
            self.assertAlmostEqual(sp['metal_oxidation_state'], 2 / M)
            self.assertEqual((sp['core_oxygen_count'], sp['core_hydrogen_count']), (0, 0))

    def test_transformed_energy_divides_by_fractional_primary_once(self):
        cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity('sulfide-s', log10_free_activity=-6),)))
        phases = {x.record_id: x for x in self.db.load_system('Cu', ligand_ids=('sulfide-s',)).species}
        for row in self.rows:
            phase = phases[row['record_id']]
            M = row['primary_count']
            expected = (phase.gibbs_energy_J_mol - phase.components[0].gibbs_energy_J_mol
                        + GAS_CONSTANT_J_MOL_K * 298.15 * LN_10 * 6 - 2 * FARADAY_C_MOL) / M
            self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(
                phase, self.db.reference_state, cfg, 7, 1)), expected)
            self.assertEqual(self.db.species_records((phase.record_id,))[0].phase_identity.status, 'resolved')
            self.assertIsNone(self.db.species_records((phase.record_id,))[0].phase_identity.spacegroup_number)
            self.assertNotIn(phase.record_id, {x.record_id for x in self.db.load_system('Cu').species})

    def test_endpoint_diagnostic_is_traceable_and_preserves_reported_values(self):
        for diagnostic in self.review['source_consistency_diagnostics']:
            M = diagnostic['primary_per_source_unit']
            parents = diagnostic['selected_endpoint_observations']
            mix = ((M - 1) * parents['r05-cu-cu2s-chalcocite']['value']
                   + (2 - M) * parents['r05-cu-cus-covellite']['value'])
            self.assertEqual(diagnostic['mixture_G_J_per_source_unit'], mix)
            self.assertGreater(diagnostic['above_endpoint_mixture_J_per_source_unit'], 0)
            self.assertEqual(diagnostic['new_selected_G_J_per_source_unit'] - mix,
                             diagnostic['above_endpoint_mixture_J_per_source_unit'])
            for rid, endpoint in parents.items():
                reported = next(x for x in self.db.species_records((rid,))[0].reported
                                if x.value_id == endpoint['value_id'])
                self.assertEqual(reported.value, endpoint['value'])
            self.assertIn('not a confidence interval', diagnostic['qualification'])

    def test_Fe_crosswalk_and_independent_holds_remain_separate(self):
        self.assertEqual((self.review['held_Fe_source_rows'], self.review['held_Fe_source_cells']), (2, 6))
        self.assertTrue(all(r['symbol'] == 'Cu' for r in self.rows))
        self.assertEqual(self.db.policy.fingerprint, '7d50a722bdbb')
        self.assertEqual((len(self.db.policy.overrides), len(self.db.policy.exclusions)), (62, 18))
        self.assertEqual(len(json.loads(self.db.metadata['R16d4c_remaining_source_holds'])), 8)
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'],
                         'held_redistribution_rights')

if __name__ == '__main__':
    unittest.main()
