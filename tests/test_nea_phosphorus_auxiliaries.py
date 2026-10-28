"""Complete diphosphate formula units, original alternatives and explicit source gaps."""
from dataclasses import replace
import json
import unittest
import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K,LN_10,FARADAY_C_MOL
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature
SID='NEA_1992_R11j3j_phosphorus_auxiliaries';NBS='NBS_PDR_R11j3j_phosphorus_auxiliaries'
RED='r11j3j-p-red-amorphous';D2='r11j3j-p-h2p2o7-q-2-aqueous';D3='r11j3j-p-h3p2o7-q-1-aqueous';D4='r11j3j-p-h4p2o7-q-0-aqueous';ACID='gfe-p-h3po4-q+0-aqueous-aq'
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
class NEAPhosphorusAuxiliaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()

    def test_complete_formula_energies_and_thermal_routes(self):
        rt=GAS_CONSTANT_J_MOL_K*298.15*LN_10
        for rid,hydrogen,q,g in [(D2,2,-2,-2027117),(D3,3,-1,-2039960),(D4,4,0,-2045668)]:
            phase=next(x for x in self.db.load_system('P').species if x.record_id==rid)
            self.assertEqual((phase.metal_count,phase.core_oxygen_count,phase.core_hydrogen_count,phase.charge,phase.electrons_per_metal),(2,7,hydrogen,q,5))
            expected=(g-7*self.db.reference_state.water_gibbs_energy_J_mol)/2-(14-hydrogen)/2*rt*7-5*FARADAY_C_MOL
            self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase,self.db.reference_state,pb.PourbaixConditions(),7,1)),expected)
            h=self.db.selections[rid,H].chosen.value
            adjusted=next(x for x in at_temperature(self.db,323.15).load_system('P').species if x.record_id==rid)
            self.assertAlmostEqual(adjusted.gibbs_energy_J_mol,g-25*(h-g)/298.15)

    def test_original_NBS_values_and_cycle_discrepancies_are_preserved(self):
        for rid,g,h,entropy,residual in [(D2,-2010200,-2278600,163,-502.98235),(D3,-2023200,-2276500,213,-310.48235),(D4,-2032000,-2268600,268,-8.73235)]:
            record=self.db.species_records((rid,))[0]
            rows={r.property:r for r in record.reported if r.source.source_id==NBS}
            self.assertEqual({p:r.value for p,r in rows.items()},{G:g,H:h,S:entropy})
            self.assertTrue(all(r.uncertainty is None for r in rows.values()))
            self.assertEqual(self.db.selections[rid,G].chosen.source_id,SID)
            warnings=[w for w in record.warnings if w.type=='r11j3j_original_NBS_GHS_cycle_discrepancy']
            self.assertEqual(len(warnings),0 if rid==D4 else 1)
            cycles=json.loads(self.db.metadata['R11j3j_NEA_phosphorus_review'])['NBS_source_cycle_checks']
            self.assertAlmostEqual(next(x['residual_J_mol']for x in cycles if x['record_id']==rid),residual)

    def test_amorphous_red_P_is_H_only_and_distinct_from_white_reference(self):
        record=self.db.species_records((RED,))[0]
        self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
        self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value,-7500)
        self.assertEqual(len(record.reported),2)
        self.assertEqual(self.db.selections[RED,H].chosen.source_id,SID)
        self.assertEqual(record.phase_identity.status,'unresolved')
        self.assertIsNone(record.phase_identity.spacegroup_symbol)
        self.assertNotIn(RED,{x.record_id for x in self.db.load_system('P').species})
        self.assertEqual(self.db.selections['gfe-p-p-q+0-solid-white-crystalline',G].chosen.value,0)

    def test_original_acid_alternative_keeps_later_evaluation_preferred(self):
        record=self.db.species_records((ACID,))[0]
        for prop,value,width in [(G,-1149367,1576),(H,-1294120,1616),(S,161.912,2.575)]:
            row=next(r for r in record.reported if r.property==prop and r.source.source_id==SID)
            self.assertAlmostEqual(row.value,value)
            self.assertAlmostEqual(row.uncertainty,width)
            self.assertFalse(row.selected_as_recommended)
            self.assertEqual(self.db.selections[ACID,prop].chosen.source_id,'NEA_OECD_20261025_ancillary_R14e2')
        rt=GAS_CONSTANT_J_MOL_K*298.15*LN_10
        self.assertAlmostEqual(-(-2045668-237140+2*1149367)/rt,-2.79,delta=.001)

    def test_closed_primary_exclusions_reprint_links_and_reuse_conditions(self):
        system=self.db.load_system('P')
        ids={ACID,D2,D3,D4}
        result=pb.MassBalanceEngine(self.db).calculate_system(replace(system,species=tuple(x for x in system.species if x.record_id in ids),excluded=()),pb.PourbaixConditions(pH_points=3,U_points=3),pb.TotalMetalConcentration(1e-3))
        self.assertEqual({x.record_id for x in result.system.species},{ACID})
        self.assertTrue({D2,D3,D4}<={x.record_id for x in result.system.excluded})
        review=json.loads(self.db.metadata['R11j3j_NEA_phosphorus_review'])
        self.assertEqual((review['source_cells'],review['new_observations'],review['new_species'],review['original_NEA_observations'],review['independent_open_NBS_observations'],review['previously_retained_cells_linked']),(14,19,4,9,10,5))
        self.assertEqual(len(json.loads(self.db.metadata['R11j3j_phosphorus_observations'])),19)
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])
        self.assertEqual(self.db.policy.fingerprint,'4c1df55bbeff')

if __name__=='__main__':
    unittest.main()
