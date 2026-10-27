"""NEA silicate polymorphs and buffered nickel-ferrite thermochemistry."""
import json
import unittest
from contextlib import closing
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL,GAS_CONSTANT_J_MOL_K,LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'

class NEAIronSilicateFerriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()
        cls.review=json.loads(cls.db.metadata['R16d6f_NEA_iron_silicate_ferrite'])
        cls.obs=json.loads(cls.db.metadata['R16d6f_NEA_iron_silicate_ferrite_observations'])

    def test_exact_selected_source_cells_and_formula_units(self):
        expected={('r12-fe-fayalite',G):(-1377720,1076),('r12-fe-fayalite',H):(-1476790,1070),('r16d6f-fe-gamma-fe2sio4',S):(140.2,.8),('r16d6f-fe-nife2o4-trevorite',G):(-962271,3044),('r16d6f-fe-nife2o4-trevorite',H):(-1070900,2800),('r16d6f-fe-nife2o4-trevorite',S):(130,4)}
        for key,pair in expected.items():
            chosen=self.db.selections[key].chosen
            self.assertEqual((chosen.value,chosen.uncertainty),pair)
            self.assertEqual((chosen.evidence_class,chosen.family),('A','NEA-TDB'))
        self.assertEqual(len(self.obs),9)
        for row in self.obs:
            self.assertEqual(row['evidence']['formula_unit_factor'],1)
            self.assertEqual((row['temperature_K'],row['pressure_bar']),(298.15,1))
        self.assertEqual((self.review['main_cells_added'],self.review['main_cells_linked'],self.review['main_cells_held']),(6,1,1))

    def test_fayalite_older_observations_and_entropy_link_survive(self):
        record=self.db.species_records(('r12-fe-fayalite',))[0]
        self.assertIn(-1379100,{x.value for x in record.reported if x.property==G})
        self.assertIn(-1478200,{x.value for x in record.reported if x.property==H})
        link=self.review['existing_links'][0]
        self.assertEqual(self.db.selections[record.record_id,S].chosen.value_id,link['value_id'])
        for row in self.obs:
            if row['record_id']==record.record_id:
                ev=row['evidence'];self.assertEqual((ev['original_printed_page'],ev['original_pdf_page']),(47,89))
                self.assertTrue(ev['reprint']['same_observation'])

    def test_gamma_is_a_distinct_metastable_entropy_only_phase(self):
        rid='r16d6f-fe-gamma-fe2sio4';gamma=self.db.species_records((rid,))[0]
        self.assertEqual(gamma.formula_ascii,'Fe2SiO4')
        self.assertEqual(gamma.phase_identity.status,'resolved')
        self.assertNotIn((rid,G),self.db.selections)
        self.assertEqual({x.value:x.uncertainty for x in gamma.reported if x.property==S},{140.2:.8,140.1:None})
        self.assertIn('metastable',gamma.phase_identity.identified_phase)
        self.assertNotIn(rid,{x.record_id for x in self.db.load_system('Fe',ligand_ids=('silica-sio2-component',)).species})

    def test_nickel_reference_reuses_reviewed_observation_and_interval(self):
        ref=self.review['reference_review'];anchor=self.db.selections['gfe-ni-ni-q+2-aqueous-aq',G].chosen
        self.assertEqual(ref['anchor_value_id'],anchor.value_id)
        self.assertEqual(ref['total_source_interval_J_mol'],771)
        with closing(self.db.connect())as c:r=c.execute("select *from ligands where ligand_id='nickel-ni2'").fetchone()
        self.assertEqual((r['formula_ascii'],r['charge'],r['gibbs_energy_J_mol']),('Ni',2,-45773))
        self.assertEqual(r['source_id'],'NEA_OECD_20261014_Ni')
        self.assertEqual(len(self.db.available_ligands()),32)

    def test_ferrite_final_H_and_qualified_entropy_keep_all_alternatives(self):
        rid='r16d6f-fe-nife2o4-trevorite';record=self.db.species_records((rid,))[0]
        self.assertEqual({x.value:x.uncertainty for x in record.reported if x.property==H},{-1070900:2800,-1066900:4900,-1072700:3300})
        self.assertEqual(self.db.selections[rid,H].chosen.source_id,'R16d6f_NEA2020_silicate_ferrite')
        self.assertEqual(self.db.selections[rid,S].chosen.status,'source_verified_estimate')
        rule=next(x for x in self.db.policy.overrides if x.record_id==rid and x.property_name==H)
        self.assertIn('combined',rule.reason)
        self.assertEqual((len(self.db.policy.overrides),len(self.db.policy.exclusions)),(62,17))

    def test_positive_Ni_component_and_full_Fe_unit_balance(self):
        rid='r16d6f-fe-nife2o4-trevorite'
        self.assertNotIn(rid,{x.record_id for x in self.db.load_system('Fe').species})
        phase=next(x for x in self.db.load_system('Fe',ligand_ids=('nickel-ni2',)).species if x.record_id==rid)
        self.assertEqual((phase.metal_count,phase.ligand_count,phase.electrons_per_metal,phase.protons_per_metal),(2,1,3,4))
        self.assertEqual((phase.components[0].charge,phase.components[0].count),(2,1))
        rt=GAS_CONSTANT_J_MOL_K*298.15*LN_10
        values=[]
        for loga in[-6,-5]:
            cfg=pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((pb.LigandActivity('nickel-ni2',log10_free_activity=loga),)))
            got=float(standard_transformed_gibbs_J_mol_metal(phase,self.db.reference_state,cfg,7,.5))
            expected=(phase.gibbs_energy_J_mol-4*self.db.reference_state.water_gibbs_energy_J_mol-(-45773+rt*loga)-8*rt*7-6*FARADAY_C_MOL*.5)/2
            self.assertAlmostEqual(got,expected);values.append(got)
        self.assertAlmostEqual(values[1]-values[0],-rt/2)

    def test_OECD_reuse_and_chromium_reference_hold_are_separate(self):
        permission=json.loads(self.db.metadata['source_permission_NEA_TDB_Fe_silicate_ferrite'])
        self.assertTrue(permission['downstream_acknowledgment_required'])
        self.assertEqual(permission['status'],'available_under_OECD_data_terms')
        held=self.review['held'];self.assertEqual(len(held),1)
        self.assertEqual((held[0]['formula'],held[0]['property'],held[0]['value'],held[0]['status']),('FeCr2O4',S,152.2,'open_component_reference_followup'))
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'],'held_redistribution_rights')
