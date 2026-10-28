"""Ce3S4 evidence keeps formal valence separate from reaction electrons."""
import json
import unittest
from contextlib import closing
import pourbase as pb
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
RID='r16d4c-ce-nbs-record8113'
class NBSCeriumSulfideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()
        cls.review=json.loads(cls.db.metadata['R16d4c_source_definition_review'])
        cls.record=cls.db.species_records((RID,))[0]

    def test_original_full_formula_enthalpy_and_missing_width(self):
        report=self.record.reported[0];ev=json.loads(report.source.locator)
        self.assertEqual((self.record.formula_ascii,report.property,report.value),('Ce3S4',H,-1661000))
        self.assertEqual((ev['logical_csv_record'],ev['csv_column_zero_based'],ev['original_value_string'],ev['conversion_factor']),(8113,7,'-1661.',1000))
        self.assertEqual((report.temperature_K,report.pressure_bar,report.unit),(298.15,1,'J/mol'))
        self.assertIsNone(report.uncertainty)
        self.assertEqual(report.evaluation_lineage.evaluation_id,'NBS1982-with-errata:logical-8113')
        self.assertEqual(self.db.selections[RID,H].chosen.evidence_class,'B')

    def test_published_ionic_model_and_net_electron_balance_are_distinct(self):
        with closing(self.db.connect())as c:sp=c.execute('select *from species where record_id=?',(RID,)).fetchone()
        self.assertEqual((sp['metal_count'],sp['ligand_count'],sp['atom_count'],sp['metal_oxidation_state']),(3,4,7,3))
        self.assertAlmostEqual(sp['electron_coefficient_per_metal'],8/3)
        ev=json.loads(self.record.reported[0].source.locator)
        self.assertEqual(ev['component_definition']['conduction_electrons_per_source_formula'],1)
        self.assertEqual(3*sp['metal_oxidation_state']-2*sp['ligand_count']-1,0)
        proof=ev['formal_state_definition_reference']
        self.assertEqual((proof['printed_page'],proof['pdf_page']),(38,42))
        self.assertTrue(proof['page_visually_verified'])
        self.assertIn('Arbouw',proof['citation'])

    def test_missing_G_and_S_are_explicit_in_evidence_and_calculation_scope(self):
        self.assertIsNone(self.record.thermochemistry.gibbs_energy_J_mol.value)
        self.assertIsNone(self.record.thermochemistry.entropy_J_mol_K.value)
        self.assertNotIn((RID,G),self.db.selections)
        self.assertNotIn((RID,S),self.db.selections)
        self.assertEqual(self.record.phase_identity.status,'unresolved')
        self.assertIsNone(self.record.phase_identity.spacegroup_number)
        for ligands in[(),('sulfide-s',)]:
            system=self.db.load_system('Ce',ligand_ids=ligands)
            self.assertNotIn(RID,{s.record_id for s in system.species})
            self.assertIn(RID,{s.record_id for s in system.excluded})

    def test_remaining_source_holds_and_independent_permissions_remain(self):
        self.assertEqual((self.review['reviewed_held_source_rows'],self.review['reviewed_held_numeric_cells'],self.review['new_observations'],self.review['remaining_held_numeric_cells']),(9,17,1,16))
        self.assertEqual({r['logical_record']for r in self.review['remaining_source_holds']},{4838,5105,5106,5343,5344,6256,6481,8109})
        self.assertEqual(self.review['source_research']['Ag2S']['decision'],'carry_completed_R05_review')
        self.assertEqual(self.review['source_research']['Re2S7']['doi'],'10.1021/cm034467v')
        self.assertEqual(self.db.policy.fingerprint,'4c1df55bbeff')
        self.assertEqual((len(self.db.policy.overrides),len(self.db.policy.exclusions)),(62,18))
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'],'held_redistribution_rights')

if __name__=='__main__':unittest.main()
