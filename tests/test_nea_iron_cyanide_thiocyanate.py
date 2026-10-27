"""NEA fitted cyanides: full salt units, source uncertainty and exclusion scope."""
import json
import unittest
from contextlib import closing
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL,GAS_CONSTANT_J_MOL_K,LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
SID='R16d6g_NEA2020_Fe_CN_SCN_main'

class NEAIronCyanideThiocyanateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()
        cls.review=json.loads(cls.db.metadata['R16d6g_NEA_Fe_CN_SCN'])
        cls.obs=json.loads(cls.db.metadata['R16d6g_NEA_Fe_CN_SCN_observations'])

    def test_exact_cells_and_complete_source_formula_units(self):
        expected={('fecn6-minus4',G):(680226,21260),('fecn6-minus4',H):(434945,21255),('fecn6-minus4',S):(75.035,6.369),('fecn6-minus3',G):(714921,None),('hfecn6-minus3',H):(437045,None),('h2fecn6-minus2',G):(642097,None),('fescn-plus2',G):(59007,4062),('fe-scn2-plus',G):(138978,6376),('k4fecn6-trihydrate',G):(-1187609,None),('k4fecn6-trihydrate',H):(-1486279,None),('k3fecn6-cr',S):(426.494,.206)}
        for (slug,prop),pair in expected.items():
            chosen=self.db.selections['r16d6g-fe-'+slug,prop].chosen
            self.assertEqual((chosen.value,chosen.uncertainty),pair)
            self.assertEqual((chosen.evidence_class,chosen.family),('A','NEA-TDB'))
        self.assertEqual(len(self.obs),27)
        for o in self.obs:
            ev=o['evidence'];self.assertEqual(ev['formula_unit_factor'],1)
            self.assertEqual(ev['original_pdf_page'],ev['original_printed_page']+35)
            self.assertEqual((o['temperature_K'],o['pressure_bar']),(298.15,1))
        self.assertEqual((self.review['new_species'],self.review['newly_available_properties']),(11,26))

    def test_fit_only_errors_are_separate_from_total_intervals(self):
        qualified=[o for o in self.obs if 'conditional_fit_error'in o['evidence']]
        self.assertEqual(len(qualified),6)
        for o in qualified:
            fit=o['evidence']['conditional_fit_error']
            self.assertFalse(fit['is_total_formation_interval'])
            self.assertIn('fixed exactly',fit['condition'])
            self.assertTrue(o['uncertainty']is None or o['uncertainty']>fit['value_J_mol'])
        fe3=self.db.selections['r16d6g-fe-fecn6-minus3',H].chosen
        self.assertEqual(fe3.value,547185);self.assertIsNone(fe3.uncertainty)
        self.assertIsNone(self.db.selections['r16d6g-fe-k4fecn6-trihydrate',G].chosen.uncertainty)

    def test_discrepant_entropy_is_reported_and_exactly_excluded(self):
        rid='r16d6g-fe-kfecn6-minus3';record=self.db.species_records((rid,))[0]
        entropies=[x for x in record.reported if x.property==S]
        self.assertEqual([(x.value,x.uncertainty)for x in entropies],[(234.3,None)])
        self.assertNotIn((rid,S),self.db.selections)
        self.assertEqual(self.db.selections[rid,G].chosen.value,384302)
        self.assertEqual(self.db.selections[rid,H].chosen.value,186405)
        rule=next(r for r in self.db.policy.exclusions if r.record_id==rid and r.property_name==S)
        self.assertEqual(rule.source_id,SID)
        self.assertIn('one J/(molK)',rule.reason)
        self.assertEqual((len(self.db.policy.overrides),len(self.db.policy.exclusions)),(62,18))

    def test_protonated_complexes_and_formal_electron_coefficients(self):
        for slug,charge,hc,formal,protons in [('fecn6-minus4',-4,0,2,0),('fecn6-minus3',-3,0,3,0),('hfecn6-minus3',-3,1,2,-1),('h2fecn6-minus2',-2,2,2,-2),('fescn-plus2',2,0,3,0),('fe-scn2-plus',1,0,3,0)]:
            rid='r16d6g-fe-'+slug
            with closing(self.db.connect())as c:r=c.execute('select *from species where record_id=?',(rid,)).fetchone()
            self.assertEqual((r['charge'],r['core_hydrogen_count'],r['metal_count']),(charge,hc,1))
            self.assertEqual((r['metal_oxidation_state'],r['electron_coefficient_per_metal']),(formal,formal))
            self.assertEqual(2*r['core_oxygen_count']-hc,protons)
        self.assertNotIn(('r16d6g-fe-h2fecn6-minus2',H),self.db.selections)
        self.assertNotIn(('r16d6g-fe-fe-scn2-plus',S),self.db.selections)

    def test_K_counts_and_trihydrate_water_are_not_lost(self):
        for slug,nK,O,hc,e in [('kfecn6-minus3',1,0,0,2),('kfecn6-minus2',1,0,0,3),('k4fecn6-trihydrate',4,3,6,2),('k4fecn6-anhydrous',4,0,0,2),('k3fecn6-cr',3,0,0,3)]:
            rid='r16d6g-fe-'+slug
            with closing(self.db.connect())as c:
                r=c.execute('select *from species where record_id=?',(rid,)).fetchone()
                extra=c.execute('select *from additional_components where record_id=?',(rid,)).fetchall()
            self.assertEqual((r['metal_count'],r['ligand_count'],r['core_oxygen_count'],r['core_hydrogen_count']),(1,6,O,hc))
            self.assertEqual([(x['ligand_id'],x['component_count'])for x in extra],[('potassium-k',nK)])
            self.assertEqual(r['electron_coefficient_per_metal'],e)
            self.assertNotIn(rid,{x.record_id for x in self.db.load_system('Fe',ligand_ids=('cyanide-cn',)).species})
            self.assertNotIn(rid,{x.record_id for x in self.db.load_system('Fe',ligand_ids=('potassium-k',)).species})

    def test_dual_buffer_energy_and_potassium_reference(self):
        ref=self.review['reference_review'];anchor=self.db.selections['gfe-k-k-q+1-aqueous-aq',G].chosen
        self.assertEqual((anchor.value,ref['anchor_value_id']),(-283270,anchor.value_id))
        self.assertEqual(ref['reuse']['doi'],'10.18434/M32124')
        self.assertEqual(ref['bounded_digitization_crosscheck']['logical_CSV_record'],12095)
        self.assertEqual(len(self.db.available_ligands()),33)
        phase=next(x for x in self.db.load_system('Fe',ligand_ids=('cyanide-cn','potassium-k')).species if x.record_id=='r16d6g-fe-k4fecn6-trihydrate')
        self.assertEqual({c.ligand_id:c.count for c in phase.components},{'cyanide-cn':6,'potassium-k':4})
        rt=GAS_CONSTANT_J_MOL_K*298.15*LN_10;logs={'cyanide-cn':-6,'potassium-k':-2}
        cfg=pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel(tuple(pb.LigandActivity(k,log10_free_activity=a)for k,a in logs.items())))
        expected=phase.gibbs_energy_J_mol-3*self.db.reference_state.water_gibbs_energy_J_mol-sum(c.count*(c.gibbs_energy_J_mol+rt*logs[c.ligand_id])for c in phase.components)-2*FARADAY_C_MOL*.5
        self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase,self.db.reference_state,cfg,7,.5)),expected)

    def test_source_reuse_and_independent_holds_remain(self):
        reuse=json.loads(self.db.metadata['source_permission_NEA_TDB_Fe_CN_SCN'])
        self.assertTrue(reuse['downstream_acknowledgment_required'])
        self.assertEqual(reuse['applicable_source_ids'],[SID])
        self.assertIn('NIST',self.review['reference_review']['reuse']['credit'])
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'],'held_redistribution_rights')
        self.assertEqual(self.review['scientifically_excluded_observations'],1)
