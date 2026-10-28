"""NEA phosphate/arsenate source units, proton balance and qualified evidence."""
import json
import unittest
from contextlib import closing
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL,GAS_CONSTANT_J_MOL_K,LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
SID='R16d6c_NEA2020_Fe_P_As_main'

class NEAIronPhosphateArsenateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()
        cls.review=json.loads(cls.db.metadata['R16d6c_NEA_Fe_P_As'])
        cls.observations=json.loads(cls.db.metadata['R16d6c_NEA_Fe_P_As_observations'])

    def test_original_cells_complete_molar_units_and_intervals(self):
        expected={
            ('fehpo4-aq',G):(-1207253,5954),('feh2po4-plus',G):(-1243283,5954),
            ('vivianite',G):(-4425748,4341),
            ('fepo4-trigonal',G):(-1161338,1411),('fepo4-trigonal',H):(-1267560,1350),('fepo4-trigonal',S):(122.21,1.34),
            ('scorodite',G):(-1283269,4725),('scorodite',H):(-1507180,4680),('scorodite',S):(188,2.1),
            ('fe4-arsenate-trihydrate',G):(-3971457,18332),('fe4-arsenate-trihydrate',H):(-4559684,18357),('fe4-arsenate-trihydrate',S):(616.8,2),
        }
        self.assertEqual(len(self.observations),22)
        for (slug,prop),pair in expected.items():
            value=self.db.selections['r16d6c-fe-'+slug,prop].chosen
            self.assertEqual((value.value,value.uncertainty),pair)
            self.assertEqual((value.evidence_class,value.family),('A','NEA-TDB'))
        for row in self.observations:
            ev=row['evidence'];self.assertEqual(ev['formula_unit_factor'],1)
            self.assertEqual(ev['conversion_factor'],1 if row['property']==S else 1000)
            self.assertEqual((row['temperature_K'],row['pressure_bar']),(298.15,1))
            self.assertIn(ev['original_printed_page'],[47,48])
            self.assertEqual(ev['original_pdf_page'],ev['original_printed_page']+35)
            self.assertTrue(ev['visually_verified'])

    def test_water_core_hydrogen_and_full_primary_counts(self):
        for slug,M,O,hc,nL,protons,e in [
            ('fehpo4-aq',1,0,1,1,-1,2),('feh2po4-plus',1,0,2,1,-2,2),
            ('vivianite',3,8,16,2,0,2),('fe3po7-cr',3,3,0,1,2,3),
            ('fe4-arsenate-trihydrate',4,3,6,4,0,3)]:
            rid='r16d6c-fe-'+slug
            with closing(self.db.connect())as c:row=c.execute('select *from species where record_id=?',(rid,)).fetchone()
            self.assertEqual((row['metal_count'],row['core_oxygen_count'],row['core_hydrogen_count'],row['ligand_count']),(M,O,hc,nL))
            self.assertEqual((2*O-hc)/M,protons)
            self.assertEqual(row['electron_coefficient_per_metal'],e)
        for slug,e in [('fe2p2o7-cr',2),('fe4-p2o7-3-cr',3),('fe3-p2o7-2-cr',8/3)]:
            with closing(self.db.connect())as c:row=c.execute('select *from species where record_id=?',('r16d6c-fe-'+slug,)).fetchone()
            self.assertEqual((row['metal_oxidation_state'],row['electron_coefficient_per_metal']),(e,e))

    def test_energy_accounts_for_proton_consumption_and_four_Fe_unit(self):
        for slug,ligand,M,O,hc,nL,e in [
            ('fehpo4-aq','phosphate-po4',1,0,1,1,2),
            ('feh2po4-plus','phosphate-po4',1,0,2,1,2),
            ('vivianite','phosphate-po4',3,8,16,2,2),
            ('fe4-arsenate-trihydrate','arsenate-aso4',4,3,6,4,3)]:
            phase=next(x for x in self.db.load_system('Fe',ligand_ids=(ligand,)).species if x.record_id=='r16d6c-fe-'+slug)
            cfg=pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((pb.LigandActivity(ligand,log10_free_activity=-6),)))
            rt=GAS_CONSTANT_J_MOL_K*298.15*LN_10
            expected=(phase.gibbs_energy_J_mol-O*self.db.reference_state.water_gibbs_energy_J_mol-nL*(phase.components[0].gibbs_energy_J_mol-6*rt)-(2*O-hc)*rt*7-e*M*FARADAY_C_MOL*.5)/M
            self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase,self.db.reference_state,cfg,7,.5)),expected)

    def test_nominal_kankite_values_are_reported_and_excluded(self):
        rid='r16d6c-fe-kankite-nominal';record=self.db.species_records((rid,))[0]
        self.assertEqual(record.phase_identity.status,'unresolved')
        self.assertEqual({x.property:(x.value,x.uncertainty)for x in record.reported if x.source.source_id==SID},{G:(-1628340,4738),H:(-1938590,4660),S:(248.3,2.8)})
        for prop in [G,H,S]:self.assertNotIn((rid,prop),self.db.selections)
        self.assertTrue(all(not x.selected_as_recommended for x in record.reported))
        self.assertEqual(len([x for x in self.db.policy.exclusions if x.record_id==rid]),3)
        self.assertNotIn(rid,{x.record_id for x in self.db.load_system('Fe',ligand_ids=('arsenate-aso4',)).species})

    def test_estimated_entropy_and_missing_G_remain_explicit(self):
        entropy=self.db.selections['r16d6c-fe-strengite',S].chosen
        self.assertEqual((entropy.value,entropy.uncertainty,entropy.status),(174,7,'source_verified_estimate'))
        for slug in ['strengite','fe2p2o7-cr','fe3po7-cr','fe4-p2o7-3-cr','fe3-p2o7-2-cr','feaso4-cr','parascorodite']:
            self.assertNotIn(('r16d6c-fe-'+slug,G),self.db.selections)
        self.assertEqual(self.db.selections['r16d6c-fe-feaso4-cr',H].chosen.value,-897250)
        self.assertEqual(self.db.selections['r16d6c-fe-parascorodite',H].chosen.value,-1504940)
        scorodite,parascorodite=self.db.species_records(('r16d6c-fe-scorodite','r16d6c-fe-parascorodite'))
        self.assertEqual(scorodite.formula_ascii,parascorodite.formula_ascii)
        self.assertNotEqual(scorodite.record_id,parascorodite.record_id)

    def test_finite_component_holds_and_reference_variant_are_traceable(self):
        self.assertEqual((self.review['source_rows'],self.review['source_numeric_cells'],self.review['new_observations'],self.review['newly_available_properties']),(16,24,22,19))
        self.assertEqual(len(self.review['held']),2)
        self.assertEqual({x['source_formula']for x in self.review['held']},{'Fe(PO3)3','Fe(PO3)3·0.128H2O'})
        diagnostic=self.review['phosphate_component_variant_diagnostic']
        self.assertEqual((diagnostic['source_PO4_G_J'],diagnostic['fixed_component_G_J'],diagnostic['source_minus_fixed_G_J']),(-1025491,-1018700,-6791))
        self.assertEqual(len(self.db.available_ligands()),33)
        with closing(self.db.connect())as c:
            self.assertEqual(c.execute("select gibbs_energy_J_mol from ligands where ligand_id='phosphate-po4'").fetchone()[0],-1018700)
            self.assertEqual(c.execute("select count(*)from species where record_id like 'r16d6c-%'and(core_oxygen_count<0 or core_hydrogen_count<0)").fetchone()[0],0)

    def test_OECD_downstream_acknowledgment_and_other_holds_remain(self):
        permission=json.loads(self.db.metadata['source_permission_NEA_TDB_Fe2020_P_As'])
        self.assertTrue(permission['downstream_acknowledgment_required'])
        self.assertEqual(permission['status'],'available_under_OECD_data_terms')
        self.assertEqual(permission['applicable_source_ids'],[SID])
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'],'held_redistribution_rights')
        self.assertEqual((len(self.db.policy.overrides),len(self.db.policy.exclusions)),(62,18))
        self.assertEqual(self.db.policy.fingerprint,'4b21643c5aa9')
