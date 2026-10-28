"""Original H/S-only fluorides retain missing G, exact phase and hydrate identity."""
import json
import unittest
import pourbase as pb
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy';SID='R16d3b_open_NBS_crystalline_fluoride_HS'
class NBSFluorideThermalPropertyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()
        cls.review=json.loads(cls.db.metadata['R16d3b_NBS_fluoride_HS_review'])
        cls.rows=cls.review['records']

    def row(self,logical):
        return next(r for r in self.rows if r['logical_record']==logical)

    def test_exact_original_HS_cells_and_retained_links(self):
        self.assertEqual((self.review['source_rows'],self.review['source_numeric_cells'],self.review['source_blank_cells'],self.review['new_observations'],self.review['new_species'],self.review['retained_original_cells']),(35,35,70,23,23,12))
        rows=json.loads(self.db.metadata['R16d3b_NBS_fluoride_HS_observations'])
        self.assertEqual(sum(r['property']==H for r in rows),19)
        self.assertEqual(sum(r['property']==S for r in rows),4)
        for obs in rows:
            record=self.db.species_records((obs['record_id'],))[0]
            self.assertEqual(len(record.reported),1)
            reported=record.reported[0];ev=json.loads(reported.source.locator)
            self.assertEqual(reported.value,ev['original_value']*ev['conversion_factor'])
            self.assertEqual(reported.unit,'J/(mol K)'if reported.property==S else'J/mol')
            self.assertIsNone(reported.uncertainty)
            self.assertEqual((reported.temperature_K,reported.pressure_bar),(298.15,1))
            self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
            self.assertEqual(reported.evaluation_lineage.evaluation_id,'NBS1982-with-errata:logical-'+str(ev['logical_csv_record']))
            self.assertEqual(self.db.selections[obs['record_id'],obs['property']].chosen.evidence_class,'B')
        for r in self.rows:
            for retained in r['retained_original_properties']:
                self.assertTrue(retained['value_ids'])
                record=self.db.species_records((r['record_id'],))[0]
                self.assertFalse(any(x.source.source_id==SID for x in record.reported))

    def test_beta_cristobalite_stays_distinct_from_alpha_quartz(self):
        beta=self.row(8763)['record_id'];alpha='r16d3a-be-nbs-record8762'
        self.assertNotEqual(beta,alpha)
        self.assertEqual(self.db.selections[beta,H].chosen.value,-1023800)
        self.assertEqual(self.db.selections[alpha,H].chosen.value,-1026800)
        self.assertNotIn((beta,G),self.db.selections)
        self.assertNotIn((beta,S),self.db.selections)
        record=self.db.species_records((beta,))[0]
        self.assertIn('β, cristobalite',record.phase_detail)
        self.assertEqual(record.phase_identity.status,'unresolved')
        self.assertEqual(self.row(8763)['distinct_other_phase_ids'],[alpha])
        self.assertIn('No G or S is copied',json.loads(record.reported[0].source.locator)['distinct_phase'])

    def test_fractional_Rb_Cs_hydrates_retain_full_formula_units(self):
        for logical,symbol in[(13479,'Rb'),(13970,'Cs')]:
            rid=self.row(logical)['record_id']
            row=self.db._evidence_rows('SELECT *FROM species WHERE record_id=?',(rid,))[0]
            self.assertEqual(row['formula_ascii'],symbol+'F(H2O)1.5')
            self.assertEqual((row['metal_count'],row['core_oxygen_count'],row['core_hydrogen_count'],row['atom_count'],row['ligand_count'],row['electron_coefficient_per_metal']),(1,1.5,3,6.5,1,1))
            self.assertEqual(self.db.selections[rid,H].chosen.value,-1013800)
            self.assertNotIn((rid,G),self.db.selections)

    def test_entropy_only_cubic_and_generic_phases_keep_missing_H_and_G(self):
        for logical,entropy in[(6149,235.6),(6276,246.),(6309,92.26),(6814,96.99)]:
            rid=self.row(logical)['record_id'];record=self.db.species_records((rid,))[0]
            self.assertEqual(record.reported[0].property,S)
            self.assertEqual(record.reported[0].value,entropy)
            self.assertIsNone(record.thermochemistry.formation_enthalpy_J_mol.value)
            self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
            if logical in[6149,6276]:
                self.assertIn('cubic',record.phase_detail)
                self.assertIsNone(record.phase_identity.spacegroup_symbol)

    def test_missing_G_is_reported_only_in_requested_fluoride_scope(self):
        for r in self.rows:
            if not r['new_species']:continue
            rid=r['record_id'];plain=self.db.load_system(r['symbol']);enabled=self.db.load_system(r['symbol'],ligand_ids=('fluoride-f',))
            self.assertNotIn(rid,{x.record_id for x in plain.species})
            self.assertEqual(next(x for x in plain.excluded if x.record_id==rid).reason.value,"ligand_species_not_selected")
            self.assertNotIn(rid,{x.record_id for x in enabled.species})
            self.assertEqual(next(x for x in enabled.excluded if x.record_id==rid).reason.value,"recommended_gibbs_energy_unavailable")
        self.assertEqual(self.db.policy.fingerprint,'4b21643c5aa9')
        self.assertEqual(len(self.db.available_ligands()),33)
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'],'held_redistribution_rights')
        self.assertEqual(json.loads(self.db.metadata['R16d3a_NBS_fluoride_source_review'])['new_observations'],80)

if __name__=='__main__':
    unittest.main()
