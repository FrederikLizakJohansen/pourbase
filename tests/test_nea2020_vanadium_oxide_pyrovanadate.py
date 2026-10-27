"""Selected oxide/pyrovanadate observations and a reference linked to retained evidence."""
from dataclasses import replace
import json
import unittest
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL,GAS_CONSTANT_J_MOL_K,LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature
SID='NEA_2020_R11j3d_vanadium_oxide_pyrovanadate';NBS='NBS_PDR_R11j3d_magnesium_pyrovanadate'
MG='r11j3d-v-mg2v2o7-crystalline';OX='gfe-v-v2o5-q+0-solid-solid';LIGAND='magnesium-mg2'
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
class NEA2020OxidePyrovanadateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()

    def test_selected_v2o5_preserves_prior_evaluation_and_source_sign_qualification(self):
        for prop,value,width in [(G,-1424840,3010),(H,-1556000,3000),(S,130.3,.2)]:
            chosen=self.db.selections[OX,prop].chosen
            self.assertEqual(chosen.source_id,SID)
            self.assertAlmostEqual(chosen.value,value)
            self.assertAlmostEqual(chosen.uncertainty,width)
        rows=self.db.species_records((OX,))[0].reported
        self.assertTrue(any(r.property==G and r.value==-1419500 for r in rows))
        ev=json.loads(next(r.source.locator for r in rows if r.property==S and r.source.source_id==SID))
        self.assertIn('IVTAN',ev['source_selection'])
        self.assertIn('−439.915',ev['qualification'])

    def test_free_magnesium_reuses_a_retained_eligible_observation(self):
        ref=next(x for x in self.db.available_ligands()if x.ligand_id==LIGAND)
        review=json.loads(self.db.metadata['R11j3d_NEA2020_vanadium_review'])
        source=review['Mg_reference']
        self.assertEqual((ref.formula_ascii,ref.charge,ref.gibbs_energy_J_mol),('Mg',2,-455703))
        self.assertEqual(ref.source_id,'NEA_OECD_20261025_ancillary_R14e')
        self.assertEqual(source['quoted_source_uncertainty_J_mol'],786)
        self.assertEqual(self.db.selections[source['record_id'],G].chosen.value_id,source['original_value_id'])
        self.assertEqual(self.db.policy.fingerprint,'7d50a722bdbb')

    def test_pyrovanadate_energy_keeps_two_mg_and_two_v_atoms(self):
        phase=next(x for x in self.db.load_system('V',ligand_ids=(LIGAND,)).species if x.record_id==MG)
        self.assertEqual((phase.metal_count,phase.core_oxygen_count,phase.charge,phase.protons_per_metal,phase.electrons_per_metal),(2,7,0,7,5))
        self.assertEqual((phase.components[0].count,phase.components[0].charge),(2,2))
        self.assertEqual(replace(phase,electron_coefficient_per_metal=None).electrons_per_metal,5)
        cfg=pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((pb.LigandActivity(LIGAND,log10_free_activity=-3),)))
        rt=GAS_CONSTANT_J_MOL_K*298.15*LN_10
        expected=(-2650170-7*self.db.reference_state.water_gibbs_energy_J_mol)/2+455703+3*rt-7*rt*7-5*FARADAY_C_MOL
        self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase,self.db.reference_state,cfg,7,1)),expected)
        rows=self.db.species_records((MG,))[0].reported
        self.assertEqual(len(rows),6)
        self.assertTrue(any(r.property==G and r.source.source_id==NBS and r.value==-2645180 for r in rows))

    def test_source_consistent_oxide_thermal_route_and_ligand_exclusion_remain(self):
        view=at_temperature(self.db,323.15)
        phase=next(x for x in view.load_system('V').species if x.record_id==OX)
        self.assertAlmostEqual(phase.gibbs_energy_J_mol,-1424840-25*(-1556000+1424840)/298.15)
        self.assertNotIn(MG,{x.record_id for x in view.load_system('V',ligand_ids=(LIGAND,)).species})
        self.assertEqual(self.db.species_records((MG,))[0].phase_identity.status,'unresolved')

    def test_source_locations_widths_and_downstream_terms_are_preserved(self):
        review=json.loads(self.db.metadata['R11j3d_NEA2020_vanadium_review'])
        self.assertEqual((review['NEA_own_selected_observations'],review['open_NBS_observations'],review['new_species'],review['new_free_references']),(6,3,1,1))
        self.assertEqual(len(json.loads(self.db.metadata['R11j3d_vanadium_observations'])),9)
        for row in self.db.species_records((MG,))[0].reported:
            ev=json.loads(row.source.locator)
            if row.source.source_id==SID:
                self.assertEqual((ev['printed_page'],ev['pdf_page']),(605,669))
                self.assertIn('95%',ev['uncertainty_convention'])
            else:
                self.assertEqual(ev['logical_csv_record'],9168)
                self.assertIsNone(row.uncertainty)
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])

if __name__=='__main__':
    unittest.main()
