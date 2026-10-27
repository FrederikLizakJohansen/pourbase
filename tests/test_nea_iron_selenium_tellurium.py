"""NEA Se/Te formula units, edition revisions and buffered reaction balance."""
import json
import unittest
from contextlib import closing
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL,GAS_CONSTANT_J_MOL_K,LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
SID='R16d6d_NEA2020_Fe_Se_Te_main'

class NEAIronSeleniumTelluriumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()
        cls.review=json.loads(cls.db.metadata['R16d6d_NEA_Fe_Se_Te'])
        cls.observations=json.loads(cls.db.metadata['R16d6d_NEA_Fe_Se_Te_observations'])

    def test_source_cells_and_empirical_molar_units(self):
        expected={
            ('r16d6d-fe-fe1-042se-beta',G):(-75233,4009),
            ('r16d6d-fe-fe1-042se-beta',H):(-74700,4000),
            ('r16d6d-fe-fe1-042se-beta',S):(72.1,.8),
            ('r16d6d-fe-fe1-111te-beta',G):(-29014,1811),
            ('r16d6d-fe-fe1-111te-beta',H):(-26060,1810),
            ('r16d6d-fe-fe1-111te-beta',S):(89.22,.15),
            ('r16d6d-fe-fe2-selenite-trihydrate',G):(-2083916,4463)}
        for key,pair in expected.items():
            chosen=self.db.selections[key].chosen
            self.assertEqual((chosen.value,chosen.uncertainty),pair)
            self.assertEqual((chosen.evidence_class,chosen.family),('A','NEA-TDB'))
        self.assertEqual(len(self.observations),19)
        for row in self.observations:
            ev=row['evidence'];self.assertEqual(ev['formula_unit_factor'],1)
            self.assertEqual(ev['original_pdf_page'],ev['original_printed_page']+35)
            self.assertEqual((row['temperature_K'],row['pressure_bar']),(298.15,1))

    def test_older_editions_and_unchanged_source_links_remain(self):
        for rid,prop,old,new in [
            ('r10-fe-alpha-fe7se8',H,-463500,-521000),
            ('r10-fe-gamma-fe3se4',H,-235000,-248000),
            ('r10-fe-fese2-cr',H,-108700,-120000),
            ('r10-fe-fese2-cr',S,86.8,83.5)]:
            record=self.db.species_records((rid,))[0]
            self.assertIn(old,{x.value for x in record.reported if x.property==prop})
            self.assertEqual(self.db.selections[rid,prop].chosen.value,new)
        self.assertEqual(len(self.review['existing_links']),2)
        for link in self.review['existing_links']:
            self.assertEqual(self.db.selections[link['record_id'],link['property']].chosen.value_id,link['value_id'])
        self.assertEqual((self.review['main_cells_added'],self.review['main_cells_linked']),(17,2))

    def test_own_enthalpy_variants_preserve_missing_interval_and_final_choice(self):
        rid='r16d6d-fe-fe1-042se-beta';record=self.db.species_records((rid,))[0]
        rows={x.value:x for x in record.reported if x.property==H}
        self.assertEqual(set(rows),{-74700,-69800,-77400})
        self.assertEqual(rows[-69800].uncertainty,4000)
        self.assertIsNone(rows[-77400].uncertainty)
        self.assertEqual(self.db.selections[rid,H].chosen.value,-74700)
        self.assertIn('positive',rows[-69800].source.locator)

    def test_iron_selenite_reuses_charged_record_and_preserves_estimate(self):
        record=self.db.species_records(('r11c-fe-feseo3-aqueous',))[0]
        self.assertEqual(record.charge,1)
        self.assertEqual({x.value for x in record.reported if x.property==G},{-442263,-446544})
        self.assertEqual(self.db.selections[record.record_id,G].chosen.value,-446544)
        with closing(self.db.connect())as c:
            self.assertEqual(c.execute("select count(*)from species where symbol='Fe'and formula_ascii='FeSeO3'and charge=1").fetchone()[0],1)
        self.assertEqual(self.review['new_species'],5)
        self.assertEqual(self.review['newly_available_properties'],12)

    def test_formal_and_net_electrons_are_independent(self):
        for slug,M,nL,formal in [('fe1-042se-beta',1.042,1,2/1.042),('fe1-111te-beta',1.111,1,2/1.111),('fese1-95',1,1.95,1.95),('fete2-epsilon',1,2,2)]:
            with closing(self.db.connect())as c:row=c.execute('select *from species where record_id=?',('r16d6d-fe-'+slug,)).fetchone()
            self.assertEqual((row['metal_count'],row['ligand_count']),(M,nL))
            self.assertAlmostEqual(row['metal_oxidation_state'],formal)
            self.assertEqual(row['electron_coefficient_per_metal'],0)
        for slug in ['fese1-95','fete2-epsilon']:
            self.assertNotIn(('r16d6d-fe-'+slug,G),self.db.selections)

    def test_trihydrate_and_noninteger_beta_energy_balances(self):
        for rid,ligand,M,O,hc,nL,e in [
            ('r16d6d-fe-fe1-042se-beta','elemental-se-cr',1.042,0,0,1,0),
            ('r16d6d-fe-fe1-111te-beta','elemental-te-cr',1.111,0,0,1,0),
            ('r16d6d-fe-fe2-selenite-trihydrate','selenite-seo3',2,3,6,3,3),
            ('r11c-fe-feseo3-aqueous','selenite-seo3',1,0,0,1,3)]:
            phase=next(x for x in self.db.load_system('Fe',ligand_ids=(ligand,)).species if x.record_id==rid)
            self.assertEqual((phase.metal_count,phase.electrons_per_metal),(M,e))
            cfg=pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((pb.LigandActivity(ligand,log10_free_activity=-6),)))
            rt=GAS_CONSTANT_J_MOL_K*298.15*LN_10
            expected=(phase.gibbs_energy_J_mol-O*self.db.reference_state.water_gibbs_energy_J_mol-nL*(phase.components[0].gibbs_energy_J_mol-6*rt)-(2*O-hc)*rt*7-e*M*FARADAY_C_MOL*.5)/M
            self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase,self.db.reference_state,cfg,7,.5)),expected)

    def test_permission_and_separate_thermal_upstream_holds(self):
        reuse=json.loads(self.db.metadata['source_permission_NEA_TDB_Fe2020_Se_Te'])
        self.assertTrue(reuse['downstream_acknowledgment_required'])
        self.assertEqual(reuse['status'],'available_under_OECD_data_terms')
        self.assertEqual(len(self.db.available_ligands()),32)
        self.assertEqual((len(self.db.policy.overrides),len(self.db.policy.exclusions)),(62,17))
        self.assertEqual({x['status']for x in self.review['held']},{'R18_heat_capacity_representation','separate_upstream_source_and_consistency_review'})
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'],'held_redistribution_rights')
