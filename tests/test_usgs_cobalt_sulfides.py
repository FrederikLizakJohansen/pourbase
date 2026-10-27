"""USGS cobalt selections retain source cells, basis and entropy-column proof."""
import json
import unittest
from contextlib import closing
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL,GAS_CONSTANT_J_MOL_K,LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
class USGSCobaltSulfideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()
        cls.review=json.loads(cls.db.metadata['R16d5a_USGS_cobalt_sulfides'])
        cls.rows=cls.review['records']
        cls.observations=json.loads(cls.db.metadata['R16d5a_USGS_cobalt_observations'])

    def test_original_cells_intervals_and_property_specific_ancestry(self):
        self.assertEqual((self.review['source_rows'],self.review['source_GHS_cells'],len(self.observations)),(2,6,6))
        for obs in self.observations:
            record=self.db.species_records((obs['record_id'],))[0]
            reported=next(r for r in record.reported if r.value_id==obs['value_id'])
            ev=json.loads(reported.source.locator)
            self.assertEqual((ev['original_printed_page'],ev['original_pdf_page']),(11,17))
            self.assertEqual((reported.temperature_K,reported.pressure_bar),(298.15,1))
            self.assertEqual(reported.value,ev['original_value']*ev['conversion_factor'])
            self.assertEqual(reported.uncertainty,ev['original_width']*ev['conversion_factor'])
            self.assertEqual(ev['property_specific_reference_numbers'],[399]if reported.property==S else[60,376]if record.formula_ascii=='CoS2'else[60])
            self.assertEqual((self.db.selections[obs['record_id'],reported.property].chosen.evidence_class,self.db.selections[obs['record_id'],reported.property].chosen.family),('B','Robie & Hemingway'))
            self.assertIsNotNone(reported.evaluation_lineage)

    def test_full_formula_and_separate_formal_and_net_electron_definitions(self):
        for row in self.rows:
            phase=next(x for x in self.db.load_system('Co',ligand_ids=('sulfide-s',)).species if x.record_id==row['record_id'])
            M=row['primary_count'];sulfur=row['sulfur_count']
            self.assertEqual((phase.metal_count,phase.components[0].count,phase.components[0].charge),(M,sulfur,-2))
            self.assertAlmostEqual(phase.electrons_per_metal,2*sulfur/M)
            self.assertAlmostEqual(phase.formal_metal_oxidation_state,2 if M==1 else 8/3)
            cfg=pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((pb.LigandActivity('sulfide-s',log10_free_activity=-6),)))
            expected=(phase.gibbs_energy_J_mol-sulfur*(phase.components[0].gibbs_energy_J_mol-GAS_CONSTANT_J_MOL_K*298.15*LN_10*6)-2*sulfur*FARADAY_C_MOL)/M
            self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase,self.db.reference_state,cfg,7,1)),expected)

    def test_named_phases_enter_only_the_enabled_sulfide_inventory(self):
        ids={r['record_id']for r in self.rows}
        self.assertTrue(ids.isdisjoint(x.record_id for x in self.db.load_system('Co').species))
        self.assertTrue(ids<={x.record_id for x in self.db.load_system('Co',ligand_ids=('sulfide-s',)).species})
        for rid in ids:
            record=self.db.species_records((rid,))[0]
            self.assertEqual(record.phase_identity.status,'resolved')
            self.assertIsNone(record.phase_identity.spacegroup_number)
            self.assertEqual({r.property for r in record.reported},{G,H,S})
            self.assertTrue(all(r.selected_as_recommended for r in record.reported))

    def test_entropy_column_and_source_specimen_qualification_are_preserved(self):
        proof=self.review['source_entropy_proof']
        self.assertTrue(proof['original_pages_visually_verified'])
        self.assertEqual((proof['CoS2']['S_column_value_cal_mol_K'],proof['CoS2']['Cp_column_cal_mol_K']),(17.876,16.313))
        self.assertEqual((proof['Co3S4']['S_column_value_cal_mol_K'],proof['Co3S4']['Cp_column_cal_mol_K']),(14.018,12.958))
        self.assertEqual(round(proof['CoS2']['S_SI_before_source_rounding'],1),74.8)
        self.assertEqual(round(proof['Co3S4']['S_SI_before_source_rounding'],1),176.)
        self.assertIn('CoS1.973',proof['CoS2']['original_specimen_analysis'])
        self.assertIn('Do not transfer',proof['qualification'])
        self.assertEqual(proof['rights'],'Public Domain')

    def test_policy_and_independent_source_holds_remain(self):
        self.assertEqual(self.db.policy.fingerprint,'4ffe2d63a073')
        self.assertEqual((len(self.db.policy.overrides),len(self.db.policy.exclusions)),(58,14))
        self.assertEqual(len(json.loads(self.db.metadata['R16d4c_remaining_source_holds'])),8)
        self.assertEqual(len(self.db.available_ligands()),31)
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'],'held_redistribution_rights')

if __name__=='__main__':unittest.main()
