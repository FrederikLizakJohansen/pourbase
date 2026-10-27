"""Original Sr/Ba source alternatives, reference conventions and buffered nitrate."""
import json
import unittest
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL,GAS_CONSTANT_J_MOL_K,LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature
SID='NEA_1992_R11j3h_selected_Sr_Ba_auxiliaries'
NBS='NBS_PDR_R11j3h_strontium_nitrate'
RID='r11j3h-sr-nitrate-crystalline'
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
class NEASrBaAuxiliaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()

    def test_original_ion_triplets_and_source_widths_are_retained(self):
        for symbol,values in [('Sr',[(G,-563864,781),(H,-550900,500),(S,-31.5,2)]),('Ba',[(G,-557656,2582),(H,-534800,2500),(S,8.4,2)])]:
            rid=f'gfe-{symbol.lower()}-{symbol.lower()}-q+2-aqueous-aq'
            record=self.db.species_records((rid,))[0]
            for prop,value,width in values:
                original=next(r for r in record.reported if r.property==prop and r.source.source_id==SID)
                self.assertAlmostEqual(original.value,value)
                self.assertAlmostEqual(original.uncertainty,width)
                self.assertEqual(self.db.selections[rid,prop].chosen.value_id,original.value_id)
                self.assertEqual(self.db.selections[rid,prop].chosen.evidence_class,'A')
                ev=json.loads(original.source.locator)
                self.assertEqual((ev['printed_page'],ev['pdf_page']),(77,95))
                self.assertIn('95%',ev['uncertainty_convention'])
                self.assertFalse(ev['table_cell_is_bold_CODATA_copy'])
            self.assertTrue(any(r.property==H and r.source.source_id.startswith(f'NBS_R07_{symbol}_ion') for r in record.reported))

    def test_nitrate_identity_and_full_balanced_energy(self):
        self.assertNotIn(RID,{x.record_id for x in self.db.load_system('Sr').species})
        phase=next(x for x in self.db.load_system('Sr',ligand_ids=('nitrate-no3',)).species if x.record_id==RID)
        self.assertEqual((phase.metal_count,phase.core_oxygen_count,phase.core_hydrogen_count,phase.components[0].count,phase.components[0].charge,phase.electrons_per_metal,phase.protons_per_metal),(1,0,0,2,-1,2,0))
        cfg=pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((pb.LigandActivity('nitrate-no3',log10_free_activity=-3),)))
        expected=-783146-2*(phase.components[0].gibbs_energy_J_mol-3*GAS_CONSTANT_J_MOL_K*298.15*LN_10)-2*FARADAY_C_MOL
        self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase,self.db.reference_state,cfg,7,1)),expected)
        self.assertEqual(self.db.species_records((RID,))[0].phase_identity.status,'unresolved')

    def test_independent_nitrate_NBS_alternatives_keep_original_values_and_missing_widths(self):
        record=self.db.species_records((RID,))[0]
        self.assertEqual(len(record.reported),6)
        for prop,value in [(G,-780020),(H,-978220),(S,194.56)]:
            row=next(r for r in record.reported if r.property==prop and r.source.source_id==NBS)
            self.assertAlmostEqual(row.value,value)
            self.assertIsNone(row.uncertainty)
            self.assertEqual(json.loads(row.source.locator)['logical_csv_record'],9772)
            self.assertFalse(row.selected_as_recommended)

    def test_ion_thermal_triplet_and_buffered_salt_exclusion(self):
        view=at_temperature(self.db,323.15)
        for symbol,g,h in [('Sr',-563864,-550900),('Ba',-557656,-534800)]:
            rid=f'gfe-{symbol.lower()}-{symbol.lower()}-q+2-aqueous-aq'
            phase=next(x for x in view.load_system(symbol).species if x.record_id==rid)
            self.assertAlmostEqual(phase.gibbs_energy_J_mol,g-25*(h-g)/298.15)
        self.assertNotIn(RID,{x.record_id for x in view.load_system('Sr',ligand_ids=('nitrate-no3',)).species})
        for symbol,entropy in [('Sr',55.7),('Ba',62.42)]:
            rid=f'gfe-{symbol.lower()}-{symbol.lower()}-q+0-solid-metal'
            self.assertAlmostEqual(self.db.selections[rid,S].chosen.value,entropy)
            self.assertEqual(self.db.selections[rid,G].chosen.status,'defined_reference_state')
            self.assertEqual(self.db.selections[rid,G].chosen.value,0)

    def test_reprints_reuse_conditions_and_earlier_source_holds_remain(self):
        review=json.loads(self.db.metadata['R11j3h_NEA_Sr_Ba_review'])
        self.assertEqual((review['new_observations'],review['new_species'],review['NEA_own_observations'],review['open_NBS_observations'],review['same2020reprint_cells_linked']),(20,1,17,3,17))
        self.assertEqual(len(json.loads(self.db.metadata['R11j3h_Sr_Ba_observations'])),20)
        self.assertEqual(self.db.policy.fingerprint,'4d3bf8cf952c')
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'],'held_redistribution_rights')

if __name__=='__main__':
    unittest.main()
