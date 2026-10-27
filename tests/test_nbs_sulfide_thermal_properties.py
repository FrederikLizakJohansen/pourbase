"""Original sulfide H/S retains formula units, alternatives and missing G."""
import json
import unittest
import pourbase as pb
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
SID='R16d4b_open_NBS_sulfide_HS'
class NBSSulfideThermalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()
        cls.review=json.loads(cls.db.metadata['R16d4b_NBS_sulfide_HS_review'])
        cls.observations=json.loads(cls.db.metadata['R16d4b_NBS_sulfide_HS_observations'])

    def row(self,logical):
        return next(r for r in self.review['records']if r['logical_record']==logical)

    def test_source_units_evaluation_and_missing_widths(self):
        self.assertEqual((self.review['remaining_source_rows'],self.review['eligible_source_rows'],self.review['eligible_numeric_cells'],self.review['eligible_source_blanks'],self.review['new_observations'],self.review['new_species']),(53,48,48,96,48,42))
        for obs in self.observations:
            record=self.db.species_records((obs['record_id'],))[0]
            reported=next(x for x in record.reported if x.value_id==obs['value_id'])
            ev=json.loads(reported.source.locator)
            self.assertEqual(reported.value,ev['original_value']*ev['conversion_factor'])
            self.assertEqual((reported.temperature_K,reported.pressure_bar),(298.15,1))
            self.assertEqual(reported.unit,'J/(mol K)'if reported.property==S else'J/mol')
            self.assertIsNone(reported.uncertainty)
            self.assertEqual(reported.evaluation_lineage.evaluation_id,'NBS1982-with-errata:logical-'+str(ev['logical_csv_record']))
            candidate=next(x for x in self.db.selections[obs['record_id'],reported.property].candidates if x.value_id==reported.value_id)
            self.assertEqual(candidate.evidence_class,'B')

    def test_realgar_normalizes_As2S2_to_As4S4_and_keeps_published_discrepancy(self):
        rid='r05-as-as4s4-realgar';record=self.db.species_records((rid,))[0]
        self.assertEqual(record.formula_ascii,'As4S4')
        reported=next(x for x in record.reported if x.source.source_id==SID)
        ev=json.loads(reported.source.locator)
        self.assertEqual((reported.value,ev['original_value'],ev['formula_unit_factor'],ev['conversion_factor']),(-285400,-142.7,2,2000))
        self.assertIn('original_unit_and_version_proof',ev)
        self.assertEqual((record.thermochemistry.formation_enthalpy_J_mol.value,record.thermochemistry.formation_enthalpy_J_mol.uncertainty),(-123600,20000))
        self.assertFalse(reported.selected_as_recommended)
        self.assertIn('shared nominal ancestry',self.db.metadata['R16d4b_source_and_model_holds'])

    def test_full_primary_counts_and_fractional_hydrates(self):
        for logical,M,sulfur,water in[(3867,3,4,0),(3868,4,5,0),(5346,6,5,0),(5347,7,6,0),(11075,2,1,4.5),(12443,2,4,.5)]:
            row=self.row(logical)
            with self.db.connect()as c:sp=c.execute('select *from species where record_id=?',(row['record_id'],)).fetchone()
            self.assertEqual((sp['metal_count'],sp['ligand_count'],sp['core_oxygen_count'],sp['core_hydrogen_count']),(M,sulfur,water,2*water))
            self.assertEqual(sp['atom_count'],M+sulfur+3*water)
            self.assertAlmostEqual(sp['electron_coefficient_per_metal'],2*sulfur/M)
        for logical in[10465,11081,11084,11088,12433,12436,12439,12445,12447]:
            row=self.row(logical)
            self.assertEqual(row['formal_primary_oxidation'],1)
            self.assertGreater(row['electron_coefficient_per_primary'],1)

    def test_formal_N_Ru_Os_definitions_are_separate_from_net_electrons(self):
        for logical,formal,net in[(1183,-3,2),(6136,2,4),(6281,2,4)]:
            row=self.row(logical)
            self.assertEqual((row['formal_primary_oxidation'],row['electron_coefficient_per_primary']),(formal,net))
            reported=self.db.species_records((row['record_id'],))[0].reported[0]
            self.assertIn('formal_state_definition',json.loads(reported.source.locator))
        self.assertEqual(self.db.selections[self.row(1183)['record_id'],H].chosen.value,535600)

    def test_HS_only_records_report_missing_G_when_sulfide_enabled(self):
        for row in self.review['records']:
            if not row['new_species']:continue
            rid=row['record_id'];record=self.db.species_records((rid,))[0]
            self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
            self.assertEqual(record.phase_identity.status,'unresolved')
            system=self.db.load_system(row['symbol'],ligand_ids=('sulfide-s',))
            self.assertNotIn(rid,{x.record_id for x in system.species})
            self.assertIn(rid,{x.record_id for x in system.excluded})
            self.assertNotIn((rid,G),self.db.selections)

    def test_coherent_triplets_and_NEAA_values_stay_preferred(self):
        for rid,value,width in[('r05-as-as4s4-realgar',-123600,20000),('r05-zn-zns-wurtzite',-203800,1500),('r05-fe-fes2-marcasite',-169500,2100),('r05-w-ws2-tungstenite',-241600,2500)]:
            selection=self.db.selections[rid,H]
            self.assertEqual((selection.chosen.value,selection.chosen.uncertainty),(value,width))
            self.assertTrue(selection.basis.startswith('override:'))
            self.assertTrue(any(x.source_id==SID for x in selection.candidates))
        for logical,prop,value in[(3163,S,87.4),(7095,H,-573200)]:
            selection=self.db.selections[self.row(logical)['record_id'],prop]
            self.assertEqual((selection.chosen.value,selection.chosen.evidence_class),(value,'A'))
            self.assertNotEqual(selection.chosen.source_id,SID)
        self.assertEqual((len(self.db.policy.overrides),len(self.db.policy.exclusions)),(53,13))
        self.assertEqual(self.db.policy.fingerprint,'544b421b7f1c')

    def test_source_holds_and_independent_reuse_conditions_carry_forward(self):
        holds=self.review['source_phase_held_rows']
        self.assertEqual({x['logical_record']for x in holds},{5344,6256,6481,8109,8113})
        self.assertTrue({x['logical_record']for x in holds}.isdisjoint(x['logical_record']for x in self.review['records']))
        self.assertEqual(len(self.db.available_ligands()),31)
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'],'held_redistribution_rights')

if __name__=='__main__':unittest.main()
