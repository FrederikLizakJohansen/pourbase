"""Selected vanadate evaluations, complete formula units and fixed buffers."""
from dataclasses import replace
import json
import unittest
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL,GAS_CONSTANT_J_MOL_K,LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature
SID='NEA_2020_R11j3c_selected_vanadates';NBS='NBS_PDR_R11j3c_original_vanadates'
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
class NEA2020VanadateSolidTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()

    def test_selected_properties_and_original_alternatives_are_retained(self):
        for slug,g,h,entropy in [('navo3',-1067480,-1149140,113.68),('cav2o6',-2174750,-2334350,179.1)]:
            rid='r11j3c-v-'+slug+'-crystalline'
            self.assertEqual(len(self.db.species_records((rid,))[0].reported),5)
            for prop,value,source in [(G,g,SID),(H,h,SID),(S,entropy,NBS)]:
                selected=self.db.selections[rid,prop].chosen
                self.assertEqual(selected.source_id,source)
                self.assertAlmostEqual(selected.value,value)

    def test_calcium_salt_keeps_complete_two_v_formula_and_cation_charge(self):
        rid='r11j3c-v-cav2o6-crystalline'
        phase=next(x for x in self.db.load_system('V',ligand_ids=('calcium-ca2',)).species if x.record_id==rid)
        self.assertEqual((phase.metal_count,phase.core_oxygen_count,phase.core_hydrogen_count,phase.charge,phase.protons_per_metal,phase.electrons_per_metal),(2,6,0,0,6,5))
        self.assertEqual((phase.components[0].count,phase.components[0].charge),(1,2))
        self.assertEqual(replace(phase,electron_coefficient_per_metal=None).electrons_per_metal,5)
        cfg=pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((pb.LigandActivity('calcium-ca2',log10_free_activity=-3),)))
        rt=GAS_CONSTANT_J_MOL_K*298.15*LN_10
        expected=(-2174750-6*self.db.reference_state.water_gibbs_energy_J_mol-phase.components[0].gibbs_energy_J_mol+3*rt)/2-6*rt*7-5*FARADAY_C_MOL
        self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase,self.db.reference_state,cfg,7,1)),expected)

    def test_source_locations_meaning_and_bibliographic_qualifications(self):
        rid='r11j3c-v-cav2o6-crystalline';record=self.db.species_records((rid,))[0]
        self.assertEqual(record.phase_identity.status,'unresolved')
        for row in record.reported:
            ev=json.loads(row.source.locator)
            if row.source.source_id==SID:
                self.assertEqual((ev['printed_page'],ev['pdf_page']),(605,669))
                self.assertIn(1204,ev['discussion_printed_pages'])
                self.assertFalse(ev['direct_copied_compilation_cell'])
                self.assertIn('95%',ev['uncertainty_convention'])
            else:
                self.assertEqual(ev['logical_csv_record'],9604)
                self.assertEqual(ev['original_source_formula'],'CaO·V2O5')
                self.assertIsNone(row.uncertainty)
        self.assertIn('bibliography',json.loads(self.db.metadata['R11j3c_source_and_model_holds']))

    def test_disabled_buffers_and_ligand_thermal_exclusions_remain(self):
        default={x.record_id for x in self.db.load_system('V').species}
        for slug,ligand in [('navo3','sodium-na'),('cav2o6','calcium-ca2')]:
            rid='r11j3c-v-'+slug+'-crystalline'
            self.assertNotIn(rid,default)
            self.assertIn(rid,{x.record_id for x in self.db.load_system('V',ligand_ids=(ligand,)).species})
            self.assertNotIn(rid,{x.record_id for x in at_temperature(self.db,323.15).load_system('V',ligand_ids=(ligand,)).species})

    def test_source_scopes_and_downstream_obligation_are_preserved(self):
        review=json.loads(self.db.metadata['R11j3c_NEA2020_vanadate_review'])
        self.assertEqual((review['NEA_own_observations'],review['open_NBS_observations'],review['new_species']),(4,6,2))
        self.assertEqual(len(json.loads(self.db.metadata['R11j3c_vanadate_observations'])),10)
        self.assertEqual(self.db.policy.fingerprint,'118f85cc935a')
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])

if __name__=='__main__':
    unittest.main()
