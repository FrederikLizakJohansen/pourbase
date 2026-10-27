"""Printed hydrate identity, polyhalide redox balance and retained alternatives."""
from dataclasses import replace
import json
import unittest

import numpy as np
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal

G = 'gibbs_energy_of_formation'
H = 'enthalpy_of_formation'
S = 'absolute_entropy'
SID = 'R16d2a_open_NBS_crystalline_bromides_iodides'
HYDRATE = 'r16d2a-na-nbs-record11029'


class NBSBromideIodideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()

    def test_printed_dihydrate_identity_and_complete_water_basis(self):
        record = self.db.species_records((HYDRATE,))[0]
        self.assertEqual(record.formula_ascii, 'NaI(H2O)2')
        self.assertIn('NaI·2H2O', record.species)
        with self.db.connect() as c:
            row = c.execute('SELECT * FROM species WHERE record_id=?', (HYDRATE,)).fetchone()
            self.assertEqual((row['metal_count'], row['core_oxygen_count'], row['core_hydrogen_count'], row['atom_count']), (1, 2, 4, 8))
        for prop, value in [(G, -771100), (H, -883096), (S, 196.2)]:
            observation = next(x for x in record.reported if x.property == prop and x.source.source_id == SID)
            self.assertAlmostEqual(observation.value, value)
            self.assertIsNone(observation.uncertainty)
            evidence = json.loads(observation.source.locator)
            self.assertEqual((evidence['source_formula'], evidence['stored_formula']), ('NaI·H2O', 'NaI(H2O)2'))
            self.assertEqual((evidence['original_printed_page'], evidence['original_pdf_page']), ('2-305', 313))
            self.assertIn('dropped', evidence['digitization_formula_correction'])
        phase = next(x for x in self.db.load_system('Na', ligand_ids=('iodide-i',)).species if x.record_id == HYDRATE)
        conditions = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((pb.LigandActivity('iodide-i', log10_free_activity=-3),)))
        expected = -771100 - 2 * self.db.reference_state.water_gibbs_energy_J_mol - phase.components[0].gibbs_energy_J_mol + 3 * GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase, self.db.reference_state, conditions, 7, 0)), expected)

    def test_polyhalide_formal_alkali_state_and_net_electron_balance(self):
        for rid, ligand, count in [('r16d2a-rb-nbs-record13535', 'iodide-i', 3), ('r16d2a-cs-nbs-record14049', 'bromide-br', 3), ('r16d2a-cs-nbs-record14076', 'iodide-i', 4)]:
            symbol = 'Rb' if '-rb-' in rid else 'Cs'
            phase = next(x for x in self.db.load_system(symbol, ligand_ids=(ligand,)).species if x.record_id == rid)
            with self.db.connect() as c:
                row = c.execute('SELECT metal_oxidation_state FROM species WHERE record_id=?', (rid,)).fetchone()
                self.assertEqual(row[0], 1)
            self.assertEqual(phase.electrons_per_metal, count)
            self.assertEqual(phase.protons_per_metal, 0)
            self.assertEqual([(x.ligand_id, x.count, x.charge) for x in phase.components], [(ligand, count, -1)])
            cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((pb.LigandActivity(ligand, log10_free_activity=-3),)))
            first = float(standard_transformed_gibbs_J_mol_metal(phase, self.db.reference_state, cfg, 0, -1))
            second = float(standard_transformed_gibbs_J_mol_metal(phase, self.db.reference_state, cfg, 14, 1))
            self.assertAlmostEqual(second - first, -2 * count * FARADAY_C_MOL)

    def test_source_cycle_qualifications_preserve_original_numbers(self):
        review = json.loads(self.db.metadata['R16d2a_NBS_halide_source_review'])
        cycles = {x['logical_record']: x for x in review['source_cycle_checks']}
        self.assertAlmostEqual(cycles[10987]['residual_J_mol'], 1484.367125)
        self.assertAlmostEqual(cycles[11029]['residual_J_mol'], 1176.820525)
        for rid in ['r16d2a-na-nbs-record10987', HYDRATE]:
            record = self.db.species_records((rid,))[0]
            self.assertTrue(any(w.type == 'r16d2a_original_reported_GHS_cycle_discrepancy' for w in record.warnings))
        record = self.db.species_records(('r16d2a-na-nbs-record10987',))[0]
        self.assertIn('constraint has been relaxed', json.loads(record.reported[0].source.locator)['source_description'])
        self.assertEqual(self.db.selections['r16d2a-na-nbs-record10987', G].chosen.value, -286060)

    def test_original_reprints_and_earlier_potassium_choices_are_retained(self):
        review = json.loads(self.db.metadata['R16d2a_NBS_halide_source_review'])
        self.assertEqual((review['source_rows'], review['new_observations'], review['new_species'], review['retained_original_cells']), (64, 175, 57, 15))
        retained = {x['source_formula']: len(x['retained_original_properties']) for x in review['records'] if x['retained_original_properties']}
        self.assertEqual(retained, {'PbI2': 3, 'CuI': 3, 'AgI': 3, 'KBr': 3, 'KI': 3})
        for rid in ['r11j3l-k-kbr-crystalline', 'r11j3l-k-ki-crystalline']:
            self.assertEqual(self.db.selections[rid, H].chosen.source_id, 'NEA_2005_R11j3l_nickel_potassium')
            self.assertFalse(any(x.source.source_id == SID for x in self.db.species_records((rid,))[0].reported))
        self.assertEqual(self.db.policy.fingerprint, '118f85cc935a')
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'], 'held_redistribution_rights')

    def test_buffered_halide_scope_and_primary_balance(self):
        rid = 'r16d2a-zn-nbs-record4100'
        self.assertNotIn(rid, {x.record_id for x in self.db.load_system('Zn').species})
        system = self.db.load_system('Zn', ligand_ids=('bromide-br',))
        phase = next(x for x in system.species if x.record_id == rid)
        self.assertEqual((phase.formula_ascii, phase.core_oxygen_count, phase.core_hydrogen_count, phase.electrons_per_metal), ('ZnBr2(H2O)2', 2, 4, 2))
        cfg = pb.PourbaixConditions(pH_points=7, U_points=9, ligand_activities=pb.LigandActivityModel((pb.LigandActivity('bromide-br', log10_free_activity=-3),)))
        system = replace(system, species=tuple(x for x in system.species if not x.is_gas))
        result = pb.MassBalanceEngine(self.db).calculate_system(system, cfg, pb.TotalMetalConcentration(1e-3))
        np.testing.assert_allclose(result.dissolved_metal_mol_L + 1e-3 * result.precipitated_metal_fraction, 1e-3, rtol=1e-10, atol=1e-15)
        with self.db.connect() as c:
            self.assertEqual(c.execute('SELECT count(*) FROM ligands').fetchone()[0], 31)


if __name__ == '__main__':
    unittest.main()
