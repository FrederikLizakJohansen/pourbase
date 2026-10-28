"""Source-defined NEA sulfide phases, alternatives and final uncertainty choices."""
import json
import unittest
from contextlib import closing
import pourbase as pb
G='gibbs_energy_of_formation'
H='enthalpy_of_formation'
S='absolute_entropy'
SID='R16d6_NEA2020_Fe_sulfide_main'
MID='R16d6_NEA2020_Fe_sulfide_intermediate'
BID='R16d6_NEA2020_Fe_sulfide_body'

class NEAIronSulfideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()
        cls.review=json.loads(cls.db.metadata['R16d6_NEA_iron_sulfides'])
        cls.observations=json.loads(cls.db.metadata['R16d6_NEA_iron_observations'])

    def test_full_polytype_units_and_source_widths(self):
        for stem,M,n,factor,Gv,Hv,Sv in [
            ('fe11s12-6c',11,12,12,None,(-1169760,47160),None),
            ('fe9s10-5c',9,10,10,(-978930,22320),(-958900,22300),(631.5,2.5)),
            ('fe7s8-4c',7,8,8,(-776040,16024),(-764240,16000),(485.6,2.72))]:
            rid='r16d6-fe-'+stem+'-pyrrhotite'
            with closing(self.db.connect())as c:row=c.execute('select *from species where record_id=?',(rid,)).fetchone()
            self.assertEqual((row['metal_count'],row['ligand_count'],row['atom_count']),(M,n,M+n))
            self.assertAlmostEqual(row['electron_coefficient_per_metal'],2*n/M)
            for prop,expected in [(G,Gv),(H,Hv),(S,Sv)]:
                if expected is None:self.assertNotIn((rid,prop),self.db.selections);continue
                chosen=self.db.selections[rid,prop].chosen
                self.assertEqual((chosen.value,chosen.uncertainty),expected)
                ev=next(r['evidence']for r in self.observations if r['value_id']==chosen.value_id)
                self.assertEqual(ev['formula_unit_factor'],factor)
                self.assertEqual((ev['temperature_K'],ev['pressure_bar']),(298.15,1))

    def test_named_polytypes_stay_separate_from_legacy_ordering(self):
        ids=['r16d6-fe-fe7s8-4c-pyrrhotite','r16d4a-fe-nbs-record5914']
        records={r.record_id:r for r in self.db.species_records(ids)}
        self.assertEqual(len(records),2)
        self.assertEqual(records[ids[0]].phase_identity.status,'resolved')
        self.assertIsNone(records[ids[0]].phase_identity.spacegroup_number)
        self.assertEqual(self.db.selections[ids[1],G].chosen.value,-748500)
        self.assertNotEqual(self.db.selections[ids[0],G].chosen.value,self.db.selections[ids[1],G].chosen.value)
        system=self.db.load_system('Fe',ligand_ids=('sulfide-s',))
        self.assertNotIn('r16d6-fe-fe11s12-6c-pyrrhotite',{r.record_id for r in system.species})

    def test_all_variants_remain_eligible_with_final_broadening(self):
        for rid,prop,final,intermediate in [
            ('r05-fe-fes-troilite',H,(-100910,2000),(-100910,1590)),
            ('r16d6-fe-fe7s8-4c-pyrrhotite',H,(-764240,16000),(-764240,14160)),
            ('r16d6-fe-fe3s4-greigite',G,(-309000,10000),(-308700,7900))]:
            choice=self.db.selections[rid,prop]
            self.assertEqual((choice.chosen.value,choice.chosen.uncertainty),final)
            self.assertEqual(choice.chosen.source_id,SID)
            other=next(x for x in choice.candidates if x.source_id==MID)
            self.assertEqual((other.value,other.uncertainty),intermediate)
            self.assertEqual((other.evidence_class,other.family),('A','NEA-TDB'))
            self.assertTrue(choice.basis.startswith('override:'))

    def test_marcasite_table_and_body_discrepancy_is_preserved(self):
        rid='r05-fe-fes2-marcasite';choice=self.db.selections[rid,H]
        self.assertEqual((choice.chosen.value,choice.chosen.uncertainty,choice.chosen.source_id),(-169430,2380,BID))
        table=next(x for x in choice.candidates if x.source_id==SID)
        self.assertEqual((table.value,table.uncertainty),(-169430,2438))
        self.assertTrue(any(x.value==-169500 and x.uncertainty==2100 for x in choice.candidates))
        self.assertEqual(self.db.selections[rid,G].chosen.uncertainty,2442)
        self.assertTrue(json.loads(self.db.metadata['R16d6_NEA_marcasite_width_discrepancy'])['visually_verified_both_pages'])

    def test_experimental_ancestry_and_mackinawite_reprint_link(self):
        self.assertEqual(len(self.observations),21)
        for row in self.observations:
            choices=self.db.selections[row['record_id'],row['property']].candidates
            candidate=next(c for c in choices if c.value_id==row['value_id'])
            self.assertEqual((candidate.evidence_class,candidate.family),('A','NEA-TDB'))
            self.assertEqual(row['status'],'verified')
            self.assertTrue(row['evidence']['method'])
            self.assertTrue(row['evidence']['evaluation_lineage']['evaluation_id'])
        link=self.review['existing_source_links'][0]
        self.assertEqual(self.db.selections['nea02a-fe-fes-mackinawite',G].chosen.value_id,link['value_id'])
        self.assertFalse(any(r['record_id']=='nea02a-fe-fes-mackinawite'for r in self.observations))

    def test_greigite_keeps_missing_properties_and_metastability(self):
        rid='r16d6-fe-fe3s4-greigite'
        self.assertNotIn((rid,H),self.db.selections);self.assertNotIn((rid,S),self.db.selections)
        reaction=self.db.selections['r16d6-fe-fe7s8-4c-pyrrhotite',G].chosen.value/3+2*self.db.selections['r05-fe-fes2-pyrite',G].chosen.value/3-self.db.selections[rid,G].chosen.value
        self.assertAlmostEqual(reaction,-57826)
        phase=next(x for x in self.db.load_system('Fe',ligand_ids=('sulfide-s',)).species if x.record_id==rid)
        self.assertEqual((phase.metal_count,phase.ligand_count),(3,4))
        self.assertAlmostEqual(phase.electrons_per_metal,8/3)

    def test_OECD_terms_and_separate_holds_carry_forward(self):
        permission=json.loads(self.db.metadata['source_permission_NEA_TDB_Fe2020_main'])
        self.assertEqual(permission['status'],'available_under_OECD_data_terms')
        self.assertTrue(permission['downstream_acknowledgment_required'])
        self.assertEqual(set(permission['applicable_source_ids']),{SID,MID,BID})
        self.assertFalse(permission['source_specific_additional_restrictions_found'])
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'],'held_redistribution_rights')
        self.assertEqual((len(self.db.policy.overrides),len(self.db.policy.exclusions)),(62,18))
        self.assertEqual(self.db.policy.fingerprint,'4c1df55bbeff')
