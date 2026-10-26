"""Own revised NEA oxide selections and independent original open NBS alternatives."""
import json
import unittest
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL,GAS_CONSTANT_J_MOL_K,LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature,ENTROPY_O2
SID='NEA_2020_R11j3b_auxiliary_oxides';NBS='NBS_PDR_R11j3b_original_oxides'
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
class NEA2020AuxiliaryOxideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()

    def original_source_view(self,rid):
        policy=self.db.policy
        for prop,source in [(G,SID),(S,SID),(H,NBS)]:
            policy=policy.with_override(rid,prop,source,'Temporary original-source regression view')
        return pb.ThermodynamicDatabase(self.db.path,policy=policy)

    def test_independent_original_evaluations_are_retained_in_source_specific_views(self):
        for symbol,g,h,entropy,oldg in [('Sr',-559400,-592000,53.63,-561900),('Ba',-519780,-553500,70.01,-525100)]:
            rid=f'r11j3b-{symbol.lower()}-{symbol.lower()}o-crystalline'
            record=self.db.species_records((rid,))[0]
            self.assertEqual(sum(r.source.source_id in {SID,NBS} for r in record.reported),5)
            view=self.original_source_view(rid)
            for prop,value,source in [(G,g,SID),(H,h,NBS),(S,entropy,SID)]:
                chosen=view.selections[rid,prop].chosen
                self.assertEqual(chosen.source_id,source)
                self.assertAlmostEqual(chosen.value,value)
            self.assertTrue(any(r.property==G and r.value==oldg and r.source.source_id==NBS for r in record.reported))

    def test_source_locations_uncertainties_and_phase_identity_remain_explicit(self):
        for symbol,page,csvrecord in [('Sr',607,9636),('Ba',608,9933)]:
            record=self.db.species_records((f'r11j3b-{symbol.lower()}-{symbol.lower()}o-crystalline',))[0]
            self.assertEqual(record.phase_identity.status,'unresolved')
            self.assertIsNone(record.phase_identity.spacegroup_symbol)
            for row in record.reported:
                if row.source.source_id not in {SID,NBS}:
                    continue
                ev=json.loads(row.source.locator)
                self.assertEqual((row.temperature_K,row.pressure_bar),(298.15,1))
                if row.source.source_id==SID:
                    self.assertEqual((ev['printed_page'],ev['pdf_page']),(page,page+64))
                    self.assertIn('95%',ev['uncertainty_convention'])
                    self.assertFalse(ev['direct_copied_compilation_cell'])
                else:
                    self.assertEqual(ev['logical_csv_record'],csvrecord)
                    self.assertIsNone(row.uncertainty)

    def test_mo_oxide_energy_keeps_complete_atom_and_electron_balance(self):
        phase=next(x for x in self.original_source_view('r11j3b-sr-sro-crystalline').load_system('Sr').species if x.record_id=='r11j3b-sr-sro-crystalline')
        self.assertEqual((phase.metal_count,phase.core_oxygen_count,phase.core_hydrogen_count,phase.charge,phase.electrons_per_metal),(1,1,0,0,2))
        expected=-559400-self.db.reference_state.water_gibbs_energy_J_mol-2*GAS_CONSTANT_J_MOL_K*298.15*LN_10*7-2*FARADAY_C_MOL
        self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase,self.db.reference_state,pb.PourbaixConditions(),7,1)),expected)

    def test_same_g_source_entropy_drives_thermal_derivative(self):
        rid='r11j3b-ba-bao-crystalline'
        view=at_temperature(self.original_source_view(rid),323.15)
        with self.db.connect() as c:
            element=c.execute("select t.entropy_J_mol_K/s.metal_count from selected_thermochemistry t join species s using(record_id) where s.symbol='Ba'and t.gibbs_status='defined_reference_state'and t.entropy_J_mol_K is not null").fetchone()[0]
        self.assertEqual(view.formation_entropies()[rid][1],'S°, source of ΔfG°')
        phase=next(x for x in view.load_system('Ba').species if x.record_id==rid)
        self.assertAlmostEqual(phase.gibbs_energy_J_mol,-519780-25*(70.01-element-ENTROPY_O2/2))

    def test_permission_conditions_and_earlier_holds_are_preserved(self):
        review=json.loads(self.db.metadata['R11j3b_NEA2020_oxide_review'])
        self.assertEqual((review['NEA_own_observations'],review['open_NBS_observations'],review['new_species']),(4,6,2))
        self.assertEqual(len(json.loads(self.db.metadata['R11j3b_oxide_observations'])),10)
        self.assertEqual(self.db.policy.fingerprint,'f8ee0083e857')
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])
        self.assertIn('CsCl',review['source_and_model_holds']['other_NEAsolids'])

if __name__=='__main__':
    unittest.main()
