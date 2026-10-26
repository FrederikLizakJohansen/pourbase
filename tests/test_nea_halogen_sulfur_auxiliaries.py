"""Exact NEA versions, full HF2 formula and fixed free-reference conventions."""
from dataclasses import replace
import json
import unittest
import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K,LN_10,FARADAY_C_MOL
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature
SID='NEA_1992_R11j3i_halogen_sulfur_auxiliaries';LATER='NEA_2003_R11j3i_internal_auxiliary_recalculations'
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
HF='gfe-f-hf-q+0-aqueous-aq';HF2='gfe-f-hf2-q-1-aqueous-aq'
class NEAHalogenSulfurAuxiliaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()

    def test_entropy_versions_keep_distinct_original_widths_and_values(self):
        for rid,original,width,later,laterwidth in [(HF,88,1.341,88,3.362),(HF2,92.685,7.260,92.683,8.469)]:
            record=self.db.species_records((rid,))[0]
            for source,value,uncertainty in [(SID,original,width),(LATER,later,laterwidth)]:
                row=next(r for r in record.reported if r.property==S and r.source.source_id==source)
                self.assertAlmostEqual(row.value,value)
                self.assertAlmostEqual(row.uncertainty,uncertainty)
                ev=json.loads(row.source.locator)
                self.assertIn('95%',ev['uncertainty_convention'])
                self.assertFalse(ev['direct_copied_compilation_cell'])
            self.assertEqual(self.db.selections[rid,S].chosen.source_id,LATER)

    def test_sulfite_rounding_variants_keep_all_original_alternatives(self):
        for rid,old,new in [('gfe-s-so3-q-2-aqueous-aq',-487473,-487472),('gfe-s-hso3-q-1-aqueous-aq',-528685,-528684)]:
            record=self.db.species_records((rid,))[0]
            for source,value in [(SID,old),(LATER,new)]:
                row=next(r for r in record.reported if r.property==G and r.source.source_id==source)
                self.assertAlmostEqual(row.value,value)
            self.assertEqual(self.db.selections[rid,G].chosen.source_id,LATER)
            self.assertTrue(any(r.source.source_id.startswith('NIST_NBS_1982') for r in record.reported))
            phase=next(x for x in at_temperature(self.db,323.15).load_system('S').species if x.record_id==rid)
            h=self.db.selections[rid,H].chosen.value
            self.assertAlmostEqual(phase.gibbs_energy_J_mol,new-25*(h-new)/298.15)

    def test_HF2_energy_normalizes_complete_two_fluorine_formula(self):
        phase=next(x for x in self.db.load_system('F').species if x.record_id==HF2)
        self.assertEqual((phase.metal_count,phase.core_oxygen_count,phase.core_hydrogen_count,phase.charge,phase.electrons_per_metal,phase.protons_per_metal),(2,0,1,-1,-1,-.5))
        rt=GAS_CONSTANT_J_MOL_K*298.15*LN_10
        expected=-583709/2+.5*rt*7+FARADAY_C_MOL
        self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase,self.db.reference_state,pb.PourbaixConditions(),7,1)),expected)
        system=self.db.load_system('F')
        monomer=next(x for x in system.species if x.formula_ascii=='F' and x.charge==-1 and x.is_aqueous)
        result=pb.MassBalanceEngine(self.db).calculate_system(
            replace(system,species=(monomer,phase),excluded=()),
            pb.PourbaixConditions(pH_points=3,U_points=3),pb.TotalMetalConcentration(1e-3))
        self.assertNotIn(HF2,{x.record_id for x in result.system.species})
        self.assertTrue(any(x.record_id==HF2 for x in result.system.excluded))

    def test_selected_acid_pair_and_fixed_fluoride_reference_are_separate_choices(self):
        rt=GAS_CONSTANT_J_MOL_K*298.15*LN_10
        reference=next(x for x in self.db.available_ligands()if x.ligand_id=='fluoride-f')
        self.assertEqual(reference.gibbs_energy_J_mol,-278790)
        self.assertAlmostEqual(-(-299675+281523)/rt,3.18,delta=.001)
        self.assertAlmostEqual(-(-299675-reference.gibbs_energy_J_mol)/rt,3.6588936985)
        self.assertAlmostEqual(-(-583709+299675-reference.gibbs_energy_J_mol)/rt,.9187090522)
        self.assertEqual(next(x for x in self.db.available_ligands()if x.ligand_id=='sulfide-s').gibbs_energy_J_mol,120695)

    def test_existing_reprints_identity_hold_and_OECD_conditions_are_explicit(self):
        review=json.loads(self.db.metadata['R11j3i_NEA_halogen_sulfur_review'])
        self.assertEqual((review['source_cells'],review['new_observations'],review['original1992_observations'],review['distinct2003_revisions'],review['current2020_cells_linked'],review['previously_retained_cells_linked']),(20,21,17,4,19,2))
        self.assertEqual(len(review['scientific_identity_holds']),1)
        self.assertEqual(review['scientific_identity_holds'][0]['source_label'],'H2SO3(aq)')
        self.assertEqual(len(json.loads(self.db.metadata['R11j3i_halogen_sulfur_observations'])),21)
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])
        self.assertEqual(self.db.policy.fingerprint,'586e3da17300')
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'],'held_redistribution_rights')

if __name__=='__main__':
    unittest.main()
