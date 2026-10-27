"""Own NEA vanadium reanalysis, source distinctions and complete ionic conventions."""
import json
import unittest
import pourbase as pb
from pourbase.temperature import at_temperature
from pourbase.constants import FARADAY_C_MOL,GAS_CONSTANT_J_MOL_K,LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal

SID='NEA_2020_R11j3a_vanadium_reanalysis'
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
VO2='gfe-v-vo2-q+1-aqueous-aq';VO4='gfe-v-vo4-q-3-aqueous-aq'

class NEA2020VanadiumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()

    def test_selected_ionic_entropy_is_absolute_and_enthalpy_is_filled(self):
        expected={G:(-590280,1530),H:(-651840,1580),S:(-38,7.4)}
        for prop,(value,width) in expected.items():
            selected=self.db.selections[VO2,prop].chosen
            self.assertEqual(selected.source_id,SID)
            self.assertAlmostEqual(selected.value,value)
            self.assertAlmostEqual(selected.uncertainty,width)
            self.assertEqual(selected.evidence_class,'A')
        self.assertTrue(any(r.property==G and r.value==-587000 for r in self.db.species_records((VO2,))[0].reported))

    def test_source_evidence_distinguishes_own_outputs_and_compilation_inputs(self):
        record=self.db.species_records((VO4,))[0]
        added=[r for r in record.reported if r.source.source_id==SID]
        self.assertEqual(len(added),1)
        self.assertEqual(added[0].property,G)
        self.assertAlmostEqual(added[0].value,-892750)
        ev=json.loads(added[0].source.locator)
        self.assertEqual((ev['printed_page'],ev['pdf_page']),(605,669))
        self.assertFalse(ev['direct_copied_compilation_cell'])
        self.assertIn('95%',ev['uncertainty_convention'])
        self.assertIn('0.51',ev['qualification'])
        self.assertTrue(any(r.property==G and r.value==-899000 for r in record.reported))

    def test_revised_vo4_energy_keeps_formula_charge_and_electron_balance(self):
        phase=next(x for x in self.db.load_system('V').species if x.record_id==VO4)
        self.assertEqual((phase.metal_count,phase.core_oxygen_count,phase.core_hydrogen_count,phase.charge,phase.electrons_per_metal),(1,4,0,-3,5))
        expected=-892750-4*self.db.reference_state.water_gibbs_energy_J_mol-8*GAS_CONSTANT_J_MOL_K*298.15*LN_10*7-5*FARADAY_C_MOL
        self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase,self.db.reference_state,pb.PourbaixConditions(),7,1)),expected)

    def test_complete_own_triplet_drives_existing_thermal_model(self):
        for temperature in [323.15,373.15]:
            phase=next(x for x in at_temperature(self.db,temperature).load_system('V').species if x.record_id==VO2)
            self.assertAlmostEqual(phase.gibbs_energy_J_mol,-590280-(temperature-298.15)*(-651840+590280)/298.15)
        self.assertEqual(self.db.policy.fingerprint,'4ffe2d63a073')

    def test_copied_cs_candidates_remain_separate_and_OECD_obligation_is_retained(self):
        review=json.loads(self.db.metadata['R11j3a_NEA2020_vanadium_review'])
        self.assertEqual((review['new_observations'],review['new_species'],review['direct_Cs_compilation_cells_held']),(4,0,6))
        self.assertEqual(len(json.loads(self.db.metadata['R11j3a_NEA2020_vanadium_observations'])),4)
        self.assertIn('82GLU/GUR',review['source_and_model_holds']['CsCl_CsBr'])
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])

if __name__=='__main__':
    unittest.main()
