"""Original NEA observations, linked reprints and explicit policy-version effects."""
from dataclasses import replace
import json
import unittest
import pourbase as pb
from pourbase.temperature import at_temperature
SID='NEA_1992_R11j3f_selected_auxiliary_oxides';LATER='NEA_2020_R11j3b_auxiliary_oxides'
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
class NEAOxideEvaluationHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()

    def test_exact_original_triplets_and_quoted_widths_are_retained(self):
        for slug,data in [('sr-sro',[(G,-559939,914),(H,-590600,900),(S,55.44,.5)]),('ba-bao',[(G,-520394,2515),(H,-548100,2500),(S,72.07,.38)])]:
            rid='r11j3b-'+slug+'-crystalline'
            original=[r for r in self.db.species_records((rid,))[0].reported if r.source.source_id==SID]
            self.assertEqual(len(original),3)
            for prop,value,width in data:
                row=next(r for r in original if r.property==prop)
                self.assertAlmostEqual(row.value,value)
                self.assertAlmostEqual(row.uncertainty,width)
                self.assertEqual(row.status,'verified')
                ev=json.loads(row.source.locator)
                self.assertEqual((ev['printed_page'],ev['pdf_page']),(77,95))
                self.assertFalse(ev['table_cell_is_bold_CODATA_copy'])
                self.assertIn('95%',ev['uncertainty_convention'])

    def test_reviewed_lineage_selects_independent_revision_and_retains_original_values(self):
        for rid in ['r11j3b-sr-sro-crystalline','r11j3b-ba-bao-crystalline']:
            for prop in [G,H,S]:
                selection=self.db.selections[rid,prop]
                self.assertEqual(selection.chosen.source_id,SID if prop==H else LATER)
                self.assertEqual(selection.chosen.evidence_class,'A')
                if prop in [G,S]:
                    later=next(x for x in selection.candidates if x.source_id==LATER)
                    original=next(x for x in selection.candidates if x.source_id==SID)
                    self.assertEqual((original.year,later.year),(1992,2020))
                    self.assertNotEqual(original.value,later.value)
        self.assertEqual(self.db.policy.fingerprint,'544b421b7f1c')

    def test_recency_view_and_reviewed_default_agree_on_the_independent_revision(self):
        policy=replace(self.db.policy,tie_breaks=('element_consistency','stated_uncertainty','recency','original_publication'),source_text='')
        view=pb.ThermodynamicDatabase(self.db.path,policy=policy)
        for rid in ['r11j3b-sr-sro-crystalline','r11j3b-ba-bao-crystalline']:
            for prop in [G,S]:
                self.assertEqual(view.selections[rid,prop].chosen.source_id,LATER)
            self.assertEqual(view.selections[rid,H].chosen.source_id,SID)
        self.assertEqual(self.db.policy.fingerprint,'544b421b7f1c')

    def test_revised_same_source_entropy_drives_thermal_model(self):
        rid='r11j3b-ba-bao-crystalline'
        for temperature in [323.15,373.15]:
            phase=next(x for x in at_temperature(self.db,temperature).load_system('Ba').species if x.record_id==rid)
            self.assertAlmostEqual(phase.gibbs_energy_J_mol,-519780-(temperature-298.15)*(-94.986))
            self.assertEqual(at_temperature(self.db,temperature).formation_entropies()[rid][1],"S°, source of ΔfG°")
        self.assertEqual(self.db.species_records((rid,))[0].phase_identity.status,'unresolved')

    def test_reprints_add_no_duplicate_observations_and_keep_OECD_conditions(self):
        review=json.loads(self.db.metadata['R11j3f_NEA_oxide_history_review'])
        self.assertEqual((review['new_observations'],review['same2003reprint_cells_linked'],review['same2020H_cells_linked']),(6,6,2))
        self.assertIn('R11j3f1',review['policy_review_followup'])
        self.assertEqual(len(json.loads(self.db.metadata['R11j3f_oxide_history_observations'])),6)
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])

if __name__=='__main__':
    unittest.main()
