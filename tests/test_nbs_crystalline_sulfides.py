"""Open NBS sulfides preserve full formulas, source versions and held phases."""
import json
import unittest
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL,GAS_CONSTANT_J_MOL_K,LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy';SID='R16d4a_open_NBS_Gibbs_bearing_sulfides'
class NBSCrystallineSulfideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()
        cls.review=json.loads(cls.db.metadata['R16d4a_NBS_sulfide_source_review'])
        cls.rows=cls.review['records']

    def row(self,logical):
        return next(r for r in self.rows if r['logical_record']==logical)

    def phase(self,logical):
        r=self.row(logical)
        return next(x for x in self.db.load_system(r['symbol'],ligand_ids=('sulfide-s',)).species if x.record_id==r['record_id'])

    def test_original_cells_units_widths_and_evaluation_identity(self):
        self.assertEqual((self.review['source_Gibbs_bearing_rows'],self.review['eligible_source_rows'],self.review['source_numeric_cells'],self.review['new_observations'],self.review['new_species'],self.review['retained_original_cells']),(38,34,102,99,27,3))
        observations=json.loads(self.db.metadata['R16d4a_NBS_sulfide_observations'])
        for obs in observations:
            reported=next(x for x in self.db.species_records((obs['record_id'],))[0].reported if x.value_id==obs['value_id']);ev=json.loads(reported.source.locator)
            self.assertEqual(reported.value,ev['original_value']*ev['conversion_factor'])
            self.assertEqual(reported.unit,'J/(mol K)'if reported.property==S else'J/mol')
            self.assertIsNone(reported.uncertainty)
            self.assertEqual((reported.temperature_K,reported.pressure_bar),(298.15,1))
            self.assertEqual(reported.evaluation_lineage.evaluation_id,'NBS1982-with-errata:logical-'+str(ev['logical_csv_record']))
            candidate=next(x for x in self.db.selections[obs['record_id'],reported.property].candidates if x.value_id==reported.value_id)
            self.assertEqual(candidate.evidence_class,'B')
        self.assertFalse(self.row(3275)['admitted_properties'])
        self.assertEqual(len(self.row(3275)['retained_original_properties']),3)

    def test_full_primary_counts_and_per_primary_transformed_energies(self):
        for logical,M,sulfur in[(5914,7,8),(6072,4,1),(7939,2,3),(11062,2,1),(5345,3,2)]:
            phase=self.phase(logical)
            self.assertEqual((phase.metal_count,phase.components[0].count,phase.components[0].charge),(M,sulfur,-2))
            self.assertAlmostEqual(phase.electrons_per_metal,2*sulfur/M)
            cfg=pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((pb.LigandActivity('sulfide-s',log10_free_activity=-6),)))
            expected=(phase.gibbs_energy_J_mol-sulfur*(phase.components[0].gibbs_energy_J_mol-6*GAS_CONSTANT_J_MOL_K*298.15*LN_10)-2*sulfur*FARADAY_C_MOL)/M
            self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase,self.db.reference_state,cfg,7,1)),expected)

    def test_formal_states_and_electron_coefficients_remain_distinct(self):
        pd=self.phase(6071);na=self.phase(11078)
        self.assertEqual((pd.formal_metal_oxidation_state,pd.electrons_per_metal),(2,4))
        self.assertEqual((na.metal_count,na.formal_metal_oxidation_state,na.electrons_per_metal),(2,1,2))
        report=self.db.species_records((pd.record_id,))[0]
        ev=json.loads(next(x for x in report.reported if x.source.source_id==SID).source.locator)
        self.assertEqual(ev['formal_state_definition_reference']['doi'],'10.1002/zaac.201700140')

    def test_explicit_phase_matches_and_carried_phase_holds(self):
        self.assertEqual(self.row(4114)['record_id'],'r05-zn-zns-sphalerite')
        self.assertEqual(self.row(4114)['source_name'],'sphalerite')
        self.assertEqual(self.row(5912)['record_id'],'r05-fe-fes2-pyrite')
        holds=self.review['source_phase_holds'];self.assertEqual({x['logical_record']for x in holds},{4838,5105,5106,5343})
        self.assertTrue(all(x['logical_record']not in{r['logical_record']for r in self.rows}for x in holds))
        red=self.row(4633)['record_id'];black=self.row(4634)['record_id'];self.assertNotEqual(red,black)
        for rid,label in[(red,'red'),(black,'black')]:
            record=self.db.species_records((rid,))[0];self.assertIn(label,record.phase_detail)
            self.assertEqual(record.phase_identity.status,'unresolved')
            self.assertIsNone(record.phase_identity.spacegroup_symbol)

    def test_revised_molybdenite_triplet_stays_preferred_with_all_NBS_alternatives(self):
        rid='r05-mo-mos2-molybdenite'
        for prop,value,width in[(G,-262800,4900),(H,-271800,4900),(S,62.6,.2)]:
            selection=self.db.selections[rid,prop]
            self.assertEqual((selection.chosen.value,selection.chosen.uncertainty),(value,width))
            self.assertTrue(selection.basis.startswith('override:'))
            self.assertIn('1988',selection.basis)
            self.assertTrue(any(x.source_id==SID for x in selection.candidates))
        self.assertEqual((len(self.db.policy.overrides),len(self.db.policy.exclusions)),(62,18))
        self.assertEqual(self.db.policy.fingerprint,'7d50a722bdbb')
        self.assertEqual(self.review['preference_review']['original_NBS_cells']['preparation_year'],1966)

    def test_pyrite_now_has_G_and_H_while_original_entropy_is_retained(self):
        rid='r05-fe-fes2-pyrite';record=self.db.species_records((rid,))[0]
        self.assertTrue(any(x.property==G and x.value==-166900 and x.source.source_id==SID for x in record.reported))
        self.assertTrue(any(x.property==H and x.value==-178200 and x.source.source_id==SID for x in record.reported))
        self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.value,-162219)
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value,-173630)
        self.assertTrue(any(x.property==S and x.value==52.9 and x.uncertainty==.1 for x in record.reported))
        self.assertEqual(record.thermochemistry.entropy_J_mol_K.value,52.92)
        self.assertNotIn(rid,{x.record_id for x in self.db.load_system('Fe').species})
        self.assertIn(rid,{x.record_id for x in self.db.load_system('Fe',ligand_ids=('sulfide-s',)).species})

    def test_printed_PdS_rounding_and_independent_source_conditions_are_explicit(self):
        r=self.row(6070);record=self.db.species_records((r['record_id'],))[0]
        self.assertEqual({x.property:x.value for x in record.reported if x.source.source_id==SID},{G:-67000,H:-75000,S:46})
        ev=json.loads(next(x for x in record.reported if x.property==G).source.locator)
        self.assertEqual((ev['original_table'],ev['original_printed_page'],ev['original_pdf_page']),('42:Pd','2-183',191))
        self.assertTrue(ev['printed_GHS_cells_visually_verified'])
        self.assertAlmostEqual(ev['source_cycle_residual_J_mol'],-1032.2345)
        self.assertEqual(len(self.db.available_ligands()),33)
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'],'held_redistribution_rights')

if __name__=='__main__':
    unittest.main()
