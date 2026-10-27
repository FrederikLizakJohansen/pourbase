"""Distinct NEA 2020 auxiliary editions and links to the published ancillary review."""
from dataclasses import replace
import json
import unittest
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature

SID = 'NEA_2020_R11j3_Iron2_auxiliary_silicates'
G = 'gibbs_energy_of_formation'
H = 'enthalpy_of_formation'
S = 'absolute_entropy'

class NEA2020SilicateVersionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()

    def test_earlier_monomer_values_keep_original_units_and_widths(self):
        record = self.db.species_records(('gfe-si-h3sio4-q-1-aqueous-aq',))[0]
        rows = {r.property: r for r in record.reported if r.source and r.source.source_id == SID}
        for prop, value, width in [(G, -1251740, 1162), (H, -1431360, 3743), (S, 88.024, 13.144)]:
            self.assertAlmostEqual(rows[prop].value, value)
            self.assertAlmostEqual(rows[prop].uncertainty, width)
            ev = json.loads(rows[prop].source.locator)
            self.assertEqual((ev['printed_page'], ev['pdf_page']), (67, 102))
            self.assertIn('1992', ev['original_evaluation'])
            self.assertIn('95%', ev['uncertainty_convention'])
            self.assertFalse(ev['table_cell_is_bold_CODATA_copy'])
            self.assertEqual((rows[prop].temperature_K, rows[prop].pressure_bar), (298.15, 1))

    def test_late_2020_uses_the_same_forthcoming_2024_evaluation(self):
        review = json.loads(self.db.metadata['R11j3_NEA2020_silicate_version_review'])
        self.assertEqual(review['late_source']['same_forthcoming_2024_cells_linked'], 15)
        self.assertEqual(review['early_source']['same_original_cells_linked'], 4)
        self.assertEqual((review['full_silicon_GHS_slots'], review['direct_copied_reference_GHS_cells_held']), (78, 24))
        self.assertEqual(review['dispositions']['no_selected_numerical_value'], 24)
        self.assertEqual(len(json.loads(self.db.metadata['R11j3_NEA2020_earlier_observations'])), 11)

    def test_repeated_H2_and_tetramer_cells_add_no_duplicate_observation(self):
        for rid in ['r11j-si-h2sio4-q-2-aqueous', 'r11j-si-h4si4o12-q-4-aqueous']:
            self.assertFalse(any(row.source and row.source.source_id == SID
                                 for row in self.db.species_records((rid,))[0].reported))
        old = self.db.species_records(('r11j-si-h2sio4-q-2-aqueous',))[0]
        self.assertTrue(any(r.source.source_id == 'NEA_2003_R11j_selected_silicates'
                            and r.property == S and r.value == -1.488 for r in old.reported))

    def test_older_oligomer_energy_uses_complete_trimer_formula(self):
        rid = 'r14e2-si-h5si3o10-q-3-linear-aqueous'
        record = self.db.species_records((rid,))[0]
        earlier = next(r for r in record.reported if r.source.source_id == SID)
        self.assertAlmostEqual(earlier.value, -3291955)
        self.assertAlmostEqual(earlier.uncertainty, 3869)
        phase = next(s for s in self.db.load_system('Si').species if s.record_id == rid)
        phase = replace(phase, gibbs_energy_J_mol=earlier.value)
        self.assertEqual((phase.metal_count, phase.core_oxygen_count, phase.core_hydrogen_count,
                          phase.charge, phase.protons_per_metal, phase.electrons_per_metal), (3, 10, 5, -3, 5, 4))
        expected = (earlier.value - 10 * self.db.reference_state.water_gibbs_energy_J_mol) / 3
        expected -= 5 * GAS_CONSTANT_J_MOL_K * 298.15 * LN_10 * 7 + 4 * FARADAY_C_MOL
        self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(
            phase, self.db.reference_state, pb.PourbaixConditions(), 7, 1)), expected, places=7)

    def test_an_older_triplet_is_selectable_in_a_temporary_policy_view(self):
        rid = 'gfe-si-h4sio4-q+0-aqueous-aq'
        policy = self.db.policy
        for prop in [G, H, S]:
            policy = policy.with_override(rid, prop, SID, 'Temporary source-version test')
        view = pb.ThermodynamicDatabase(self.db.path, policy=policy)
        for temperature in [323.15, 373.15]:
            phase = next(s for s in at_temperature(view, temperature).load_system('Si').species if s.record_id == rid)
            expected = -1307735 - (temperature - 298.15) * (-1456960 + 1307735) / 298.15
            self.assertAlmostEqual(phase.gibbs_energy_J_mol, expected)
        self.assertEqual(self.db.policy.fingerprint, '544b421b7f1c')
        self.assertEqual(self.db.selections[rid, G].chosen.source_id, 'NEA_OECD_20261025_ancillary_R14e2')

    def test_current_preferences_references_and_source_holds_are_preserved(self):
        rid = 'gfe-si-h3sio4-q-1-aqueous-aq'
        self.assertTrue(self.db.selections[rid, G].basis.startswith('override:'))
        self.assertEqual(self.db.selections[rid, G].chosen.value, -1252304)
        self.assertEqual(self.db.selections[rid, H].chosen.source_id, 'NEA_OECD_20261025_ancillary_R14e2')
        ligand = next(x for x in self.db.available_ligands() if x.ligand_id == 'silicate-h2sio4')
        self.assertEqual(ligand.gibbs_energy_J_mol, -1175651)
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])
        holds = json.loads(self.db.metadata['R11j3_source_and_model_holds'])
        self.assertIn('CODATA', holds['copied_silicon_rows'])

if __name__ == '__main__':
    unittest.main()
