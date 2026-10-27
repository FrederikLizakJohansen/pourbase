"""NEA own adjusted experiments retain source variants and specimen qualifications."""
import json
import unittest
import pourbase as pb
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
SID='R16d6b_NEA2020_adjusted_experiments'
CID='R16d6b_NEA2020_comparison2014'

class NEAAdjustedSulfideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()
        cls.review=json.loads(cls.db.metadata['R16d6b_NEA_adjusted_sulfides'])
        cls.observations=json.loads(cls.db.metadata['R16d6b_NEA_adjusted_observations'])

    def test_original_adjustments_and_full_formula_intervals(self):
        expected={
            'troilite-1951-thirdlaw':(-100050,2110),
            'quenched-FeS-1964':(-98910,2280),
            'troilite-1988-calorimetry':(-102590,2940),
            'troilite-2010-oxide-melt':(-100890,4200),
            '5C-equilibrium':(-958200,26300),
            '5C-2010-oxide-melt':(-960500,42000),
            '3C-2010-oxide-melt':(-756880,25520),
            '4C-updated-thirdlaw':(-767840,24000),
            '4C-electrochemical-thirdlaw':(-767200,24000),
            '4C-2014-comparison':(-745280,24080),
            'pyrite-1988-calorimetry':(-171640,5880),
            'pyrite-2010-oxide-melt':(-175850,6180),
            'pyrite-equilibrium':(-173630,2830),
            'wurtzite-1964-adjusted':(-191170,2010),
            '4C-solid-sulfur-conversion':(-817600,24000),
        }
        self.assertEqual(len(self.observations),15)
        for row in self.observations:
            slug=row['value_id'].split(':R16d6b:')[1]
            record=self.db.species_records((row['record_id'],))[0]
            reported=next(x for x in record.reported if x.value_id==row['value_id'])
            self.assertEqual((reported.value,reported.uncertainty),expected[slug])
            ev=json.loads(reported.source.locator)
            self.assertEqual(ev['original_pdf_page'],ev['original_printed_page']+35)
            self.assertEqual((reported.temperature_K,reported.pressure_bar),(298.15,1))
            self.assertIn(ev['formula_unit_factor'],[1,8,10])
            self.assertTrue(ev['visually_verified'])
            self.assertIsNotNone(reported.evaluation_lineage)

    def test_actual_3C_calorimetric_specimen_stays_distinct(self):
        rid='r16d6b-fe-fe7s8-3c-pyrrhotite'
        record=self.db.species_records((rid,))[0]
        self.assertEqual(record.formula_ascii,'Fe7S8')
        self.assertEqual(record.phase_identity.status,'resolved')
        self.assertIsNone(record.phase_identity.spacegroup_number)
        self.assertEqual(self.db.selections[rid,H].chosen.value,-756880)
        self.assertEqual(self.db.selections['r16d6-fe-fe7s8-4c-pyrrhotite',H].chosen.value,-764240)
        self.assertEqual(self.db.selections['r16d4a-fe-nbs-record5914',H].chosen.value,-736400)
        self.assertNotIn((rid,G),self.db.selections)
        self.assertNotIn((rid,S),self.db.selections)
        self.assertNotIn(rid,{x.record_id for x in self.db.load_system('Fe',ligand_ids=('sulfide-s',)).species})

    def test_quenched_FeS_preserves_unresolved_ordering(self):
        rid='r16d6b-fe-fes-quenched-1964'
        record=self.db.species_records((rid,))[0]
        self.assertEqual(record.phase_identity.status,'unresolved')
        self.assertEqual(self.db.selections[rid,H].chosen.value,-98910)
        self.assertNotIn((rid,G),self.db.selections)
        self.assertNotIn((rid,S),self.db.selections)
        self.assertNotEqual(rid,'r05-fe-fes-troilite')
        self.assertEqual(self.db.selections['r05-fe-fes-troilite',H].chosen.value,-100910)

    def test_comparison_only_result_remains_reported_and_excluded(self):
        rid='r16d6-fe-fe7s8-4c-pyrrhotite'
        record=self.db.species_records((rid,))[0]
        reported=next(x for x in record.reported if x.source.source_id==CID)
        self.assertEqual((reported.value,reported.uncertainty),(-745280,24080))
        self.assertFalse(reported.selected_as_recommended)
        self.assertNotIn(CID,{x.source_id for x in self.db.selections[rid,H].candidates})
        exclusion=next(x for x in self.db.policy.exclusions if x.source_id==CID)
        self.assertIn('Ag2S',exclusion.reason)
        self.assertEqual(len([x for x in self.observations if x['evidence']['scientific_selection_excluded']]),1)

    def test_final_combinations_and_coherent_wurtzite_stay_preferred(self):
        for rid,value,width in [
            ('r05-fe-fes-troilite',-100910,2000),
            ('r16d6-fe-fe9s10-5c-pyrrhotite',-958900,22300),
            ('r16d6-fe-fe7s8-4c-pyrrhotite',-764240,16000),
            ('r05-fe-fes2-pyrite',-173630,2360),
            ('r05-zn-zns-wurtzite',-203800,1500)]:
            choice=self.db.selections[rid,H]
            self.assertEqual((choice.chosen.value,choice.chosen.uncertainty),(value,width))
            self.assertTrue(choice.basis.startswith('override:'))
            self.assertTrue(any(x.source_id==SID for x in choice.candidates))
        choice=self.db.selections['r05-zn-zns-wurtzite',H]
        alternative=next(x for x in choice.candidates if x.source_id==SID)
        self.assertEqual((alternative.evidence_class,alternative.value-choice.chosen.value),('A',12630))
        converted=next(x for x in self.observations if x['value_id'].endswith('4C-solid-sulfur-conversion'))
        self.assertEqual(converted['evidence']['original_value'],-166.5+.5*128.6)

    def test_finite_ledger_reuse_and_independent_holds(self):
        self.assertEqual((self.review['source_cells_in_scope'],len(self.observations),len(self.review['existing_source_links']),len(self.review['held_source_cells'])),(19,15,1,3))
        self.assertEqual({x['source_formula']for x in self.review['held_source_cells']},{'Fe0.94S','Fe0.96S','Fe0.98S'})
        link=self.review['existing_source_links'][0]
        self.assertEqual(self.db.selections['r16d6-fe-fe11s12-6c-pyrrhotite',H].chosen.value_id,link['value_id'])
        permission=json.loads(self.db.metadata['source_permission_NEA_TDB_Fe2020_adjusted'])
        self.assertTrue(permission['downstream_acknowledgment_required'])
        self.assertEqual(permission['status'],'available_under_OECD_data_terms')
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'],'held_redistribution_rights')
        self.assertEqual((len(self.db.policy.overrides),len(self.db.policy.exclusions)),(58,17))
        self.assertEqual(self.db.policy.fingerprint,'5bbebf8f20e9')
