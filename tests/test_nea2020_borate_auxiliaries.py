"""Borate source distinctions, mixed-state hold and complete buffered formula units."""
from dataclasses import replace
import json
import unittest
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL,GAS_CONSTANT_J_MOL_K,LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature
SID='NEA_2020_R11j3e_calcium_borate';NBS='NBS_PDR_R11j3e_original_borates'
CA='r11j3e-b-cab2o4-crystalline';NA='r11j3e-b-nabo2-crystalline'
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
class NEA2020BorateAuxiliaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()

    def test_independent_open_and_own_selected_values_are_retained(self):
        for rid,source,expected,count in [(CA,SID,[(G,-1924561),(H,-2031500),(S,105.02)],6),(NA,NBS,[(G,-920700),(H,-977000),(S,73.51)],3)]:
            self.assertEqual(len(self.db.species_records((rid,))[0].reported),count)
            for prop,value in expected:
                chosen=self.db.selections[rid,prop].chosen
                self.assertEqual(chosen.source_id,source)
                self.assertAlmostEqual(chosen.value,value)
        self.assertFalse(any(r.source.source_id==SID for r in self.db.species_records((NA,))[0].reported))

    def test_mixed_boric_acid_row_and_copied_cells_remain_held(self):
        review=json.loads(self.db.metadata['R11j3e_NEA2020_borate_review'])
        self.assertEqual((review['full_Table14_2_GHS_slots'],review['own_CaB2O4_slots_admitted'],review['defined_reference_slots_no_import'],review['copied_or_hybrid_slots_held']),(15,3,2,10))
        self.assertIn('crystallineH/S',review['source_and_model_holds']['phase'])
        self.assertEqual(self.db.selections['gfe-b-h3bo3-q+0-aqueous-aq',H].chosen.value,-1072320)
        self.assertFalse(any(r.source.source_id==SID for r in self.db.species_records(('gfe-b-h3bo3-q+0-aqueous-aq',))[0].reported))

    def test_calcium_borate_full_formula_and_charge_balance(self):
        phase=next(x for x in self.db.load_system('B',ligand_ids=('calcium-ca2',)).species if x.record_id==CA)
        self.assertEqual((phase.metal_count,phase.core_oxygen_count,phase.core_hydrogen_count,phase.charge,phase.protons_per_metal,phase.electrons_per_metal),(2,4,0,0,4,3))
        self.assertEqual((phase.components[0].count,phase.components[0].charge),(1,2))
        self.assertEqual(replace(phase,electron_coefficient_per_metal=None).electrons_per_metal,3)
        cfg=pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((pb.LigandActivity('calcium-ca2',log10_free_activity=-3),)))
        rt=GAS_CONSTANT_J_MOL_K*298.15*LN_10
        expected=(-1924561-4*self.db.reference_state.water_gibbs_energy_J_mol-phase.components[0].gibbs_energy_J_mol+3*rt)/2-4*rt*7-3*FARADAY_C_MOL
        self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase,self.db.reference_state,cfg,7,1)),expected)

    def test_primary_source_locations_uncertainties_and_structure_status(self):
        record=self.db.species_records((CA,))[0]
        self.assertEqual(record.phase_identity.status,'unresolved')
        for row in record.reported:
            ev=json.loads(row.source.locator)
            if row.source.source_id==SID:
                self.assertEqual((ev['printed_page'],ev['pdf_page']),(606,670))
                self.assertIn(1206,ev['discussion_printed_pages'])
                self.assertIn('95%',ev['uncertainty_convention'])
                self.assertFalse(ev['direct_copied_compilation_cell'])
            else:
                self.assertEqual(ev['logical_csv_record'],9509)
                self.assertEqual(ev['original_source_formula'],'CaO·B2O3')
                self.assertIsNone(row.uncertainty)

    def test_thermal_scope_policy_and_downstream_obligation_remain(self):
        for rid,ligand in [(CA,'calcium-ca2'),(NA,'sodium-na')]:
            self.assertNotIn(rid,{x.record_id for x in self.db.load_system('B').species})
            self.assertIn(rid,{x.record_id for x in self.db.load_system('B',ligand_ids=(ligand,)).species})
            self.assertNotIn(rid,{x.record_id for x in at_temperature(self.db,323.15).load_system('B',ligand_ids=(ligand,)).species})
        self.assertEqual(self.db.policy.fingerprint,'7a2a7d316094')
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])

if __name__=='__main__':
    unittest.main()
