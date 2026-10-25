"""NEA ancillary evaluations, exact polymorphs and source-specific exclusions."""
from dataclasses import replace
import json
import unittest
import numpy as np
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal

SID = 'NEA_OECD_20261025_ancillary_R14e'

class NEAAncillaryExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()

    def test_original_units_uncertainties_and_source_cells(self):
        record = self.db.species_records(('gfe-al-al-oh-4-q-1-aqueous-aq',))[0]
        rows = [x for x in record.reported if x.source and x.source.source_id == SID]
        self.assertEqual({x.property: (x.value, x.uncertainty) for x in rows}, {
            'gibbs_energy_of_formation': (-1306404, 1521),
            'enthalpy_of_formation': (-1499018, 1884), 'absolute_entropy': (119.275, 3.911)})
        for row in rows:
            ev = json.loads(row.source.locator)
            self.assertEqual((ev['printed_page'], ev['pdf_page']), (45, 87))
            self.assertFalse(ev['table_cell_is_bold_CODATA_copy'])
            self.assertIn('95%', ev['uncertainty_convention'])
            self.assertEqual(self.db.selections[record.record_id, row.property].chosen.evidence_class, 'A')

    def test_bold_codata_enthalpies_are_separate(self):
        for rid in ['gfe-al-al-q+3-aqueous-aq', 'gfe-mg-mg-q+2-aqueous-aq']:
            record = self.db.species_records((rid,))[0]
            self.assertEqual({x.property for x in record.reported if x.source and x.source.source_id == SID},
                             {'gibbs_energy_of_formation', 'absolute_entropy'})
            self.assertNotEqual(self.db.selections[rid, 'enthalpy_of_formation'].chosen.source_id, SID)
        self.assertIn('Directly copied bold CODATA', json.loads(self.db.metadata['R14e_source_and_model_holds'])['R14e3'])

    def test_source_polymorphs_and_enthalpy_only_states(self):
        for rid, value in [('r14e-al-bayerite', -1289000), ('r14e-mg-alpha-sulfate', -1288600)]:
            record = self.db.species_records((rid,))[0]
            self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
            self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
            self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, value)
        beta = self.db.species_records(('r14e-mg-beta-sulfate',))[0]
        self.assertEqual(beta.phase_identity.spacegroup_symbol, 'Pbnm')
        self.assertEqual(beta.thermochemistry.gibbs_energy_J_mol.value, -1170481)
        generic = self.db.species_records(('gfe-mg-mgso4-q+0-solid-magnesium-sulfate',))[0]
        self.assertTrue(all(x.source is None or x.source.source_id != SID for x in generic.reported))

    def test_existing_carbonate_gains_enthalpy(self):
        rid = 'gfe-mg-mgco3-q+0-aqueous-aq'
        record = self.db.species_records((rid,))[0]
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, -1128126)
        self.assertEqual(self.db.selections[rid, 'enthalpy_of_formation'].chosen.source_id, SID)
        self.assertGreater(len(record.reported), 3)

    def test_gypsum_water_and_phosphate_molar_basis(self):
        for sym, rid, lid, count, waters, metal in [
            ('Ca', 'gfe-ca-caso4-h2o-2-q+0-solid-gypsum', 'sulfate-so4', 1, 2, 1),
            ('Ca', 'r05-ca-ca3-po4-2-whitlockite-ideal-beta-calcium-phosphate', 'phosphate-po4', 2, 0, 3)]:
            phase = next(s for s in self.db.load_system(sym, ligand_ids=(lid,)).species if s.record_id == rid)
            cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((pb.LigandActivity(lid, log10_free_activity=-3),)))
            rt = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
            expected = (phase.gibbs_energy_J_mol - waters * self.db.reference_state.water_gibbs_energy_J_mol
                        - count * (phase.components[0].gibbs_energy_J_mol - 3 * rt)) / metal - 2 * FARADAY_C_MOL
            self.assertEqual((phase.metal_count, phase.core_oxygen_count, phase.core_hydrogen_count), (metal, waters, 2 * waters))
            self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase, self.db.reference_state, cfg, 7, 1)), expected, places=7)

    def test_sulfate_gate_and_closed_primary_inventory(self):
        rid = 'r14e-mg-sulfate-aqueous'
        self.assertNotIn(rid, {s.record_id for s in self.db.load_system('Mg').species})
        system = self.db.load_system('Mg', ligand_ids=('sulfate-so4',))
        self.assertIn(rid, {s.record_id for s in system.species})
        cfg = pb.PourbaixConditions(pH_points=7, U_points=9, ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity('sulfate-so4', log10_free_activity=-3),)))
        system = replace(system, species=tuple(s for s in system.species if not s.is_gas))
        for model in [pb.IdealActivityCoefficientModel(), pb.DaviesActivityCoefficientModel(.01)]:
            result = pb.MassBalanceEngine(self.db, activity_coefficient_model=model).calculate_system(system, cfg, pb.TotalMetalConcentration(1e-3))
            np.testing.assert_allclose(result.dissolved_metal_mol_L + 1e-3 * result.precipitated_metal_fraction,
                                       1e-3, rtol=1e-10, atol=1e-15)

    def test_all_alternatives_and_source_obligations_are_retained(self):
        self.assertEqual(len(json.loads(self.db.metadata['R14e_NEA2024_observations'])), 63)
        review = json.loads(self.db.metadata['R14e_NEA2024_source_review'])
        self.assertEqual((review['new_observations'], review['new_species']), (63, 4))
        self.assertIn('further sublicensees', review['reuse']['downstream_acknowledgment'])
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'], 'held_redistribution_rights')
        record = self.db.species_records(('gfe-al-al-oh-3-q+0-solid-gibbsite',))[0]
        self.assertGreater(len(record.reported), 3)

if __name__ == '__main__':
    unittest.main()
