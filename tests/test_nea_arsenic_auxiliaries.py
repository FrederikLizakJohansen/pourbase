"""Source versions, full arsenic formulas and one-population water conversions."""
from dataclasses import replace
import json
import unittest
import numpy as np
import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K,LN_10,FARADAY_C_MOL
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
SID='NEA_1992_R11j3k_arsenic_auxiliaries';UPD='NEA_2003_R11j3k_monoclinic_recalculation';GAS='NEA_2005_R11j3k_As4O6_gas';NBS='NBS_PDR_R11j3k_arsenic_alternatives';LOCAL='R11j3k_local_water_representation'
MONO='r11j3k-as-as4o6-monoclinic';VAP='r11j3k-as-as4o6-gas';HYD='r11j3k-as-as2o5-trimer-pentahydrate';CUBIC='gfe-as-as4o6-q+0-solid-octahedral'
G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
class NEAArsenicAuxiliaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()

    def test_complete_solid_formula_units_and_existing_cubic_identity(self):
        with self.db.connect()as c:
            row=c.execute('SELECT * FROM species WHERE record_id=?',(HYD,)).fetchone()
            self.assertEqual((row['metal_count'],row['core_oxygen_count'],row['core_hydrogen_count'],row['atom_count'],row['electron_coefficient_per_metal']),(6,20,10,36,5))
        hydrate=self.db.species_records((HYD,))[0]
        self.assertIsNone(hydrate.thermochemistry.gibbs_energy_J_mol.value)
        self.assertIsNone(hydrate.thermochemistry.entropy_J_mol_K.value)
        self.assertAlmostEqual(hydrate.thermochemistry.formation_enthalpy_J_mol.value,-4248400)
        self.assertEqual(len(hydrate.reported),2)
        self.assertEqual(self.db.species_records((CUBIC,))[0].phase_identity.spacegroup_symbol,'Fd-3m')
        for rid in[MONO,HYD]:self.assertEqual(self.db.species_records((rid,))[0].phase_identity.status,'unresolved')
        for rid in[MONO,VAP,CUBIC]:
            phase=next(x for x in self.db.load_system('As').species if x.record_id==rid)
            self.assertEqual((phase.formula_ascii,phase.metal_count,phase.core_oxygen_count,phase.electrons_per_metal),('As4O6',4,6,3))

    def test_water_conversions_keep_raw_quantities_and_one_canonical_population(self):
        observations=json.loads(self.db.metadata['R11j3k_arsenic_observations'])
        local=[r for r in observations if r['source_id']==LOCAL]
        self.assertEqual(len(local),6)
        self.assertEqual(len({r['record_id']for r in local}),2)
        for row in local:
            ev=row['evidence']
            self.assertEqual(row['value'],ev['raw_original_value']*ev['raw_conversion_factor']+ev['water_anchor']['value'])
            self.assertIsNone(row['uncertainty'])
            selection=self.db.selections[row['record_id'],row['property']]
            self.assertEqual(next(x.evidence_class for x in selection.candidates if x.value_id==row['value_id']),'E')
            self.assertNotEqual(selection.chosen.value_id,row['value_id'])
            if row['property']!=G:continue
            phase=next(x for x in self.db.load_system('As').species if x.record_id==row['record_id'])
            converted=replace(phase,gibbs_energy_J_mol=row['value'])
            raw=replace(converted,formula_ascii=ev['raw_source_formula'],gibbs_energy_J_mol=ev['raw_original_value']*1000,core_oxygen_count=phase.core_oxygen_count-1,core_hydrogen_count=phase.core_hydrogen_count-2)
            self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(converted,self.db.reference_state,pb.PourbaixConditions(),7,1)),float(standard_transformed_gibbs_J_mol_metal(raw,self.db.reference_state,pb.PourbaixConditions(),7,1)))
        self.assertEqual(self.db.reference_state.water_gibbs_energy_J_mol,-237129)

    def test_gas_revision_keeps_older_NBS_values_and_cycle_warning(self):
        record=self.db.species_records((VAP,))[0]
        for prop,value,width,legacy in[(G,-1092716,16116,-1097800),(H,-1196250,16000,-1209200),(S,408.6,6,381)]:
            source=next(r for r in record.reported if r.property==prop and r.source.source_id==GAS)
            self.assertAlmostEqual(source.value,value)
            self.assertAlmostEqual(source.uncertainty,width)
            self.assertEqual(self.db.selections[VAP,prop].chosen.source_id,GAS)
            ev=json.loads(source.source.locator)
            self.assertEqual((ev['printed_page'],ev['pdf_page']),(60,88))
            old=next(r for r in record.reported if r.property==prop and r.source.source_id==NBS)
            self.assertEqual(old.value,legacy)
            self.assertIsNone(old.uncertainty)
        self.assertTrue(any(w.type=='r11j3k_original_NBS_GHS_cycle_discrepancy'for w in record.warnings))
        review=json.loads(self.db.metadata['R11j3k_NEA_arsenic_review'])
        self.assertEqual(review['gas_G_spread_review']['spread_J_mol'],5084)
        self.assertAlmostEqual(next(x['residual_J_mol']for x in review['NBS_source_cycle_checks']if x['record_id']==VAP),350.7941)

    def test_monoclinic_versions_energy_and_positive_four_As_precipitation(self):
        record=self.db.species_records((MONO,))[0]
        for source,value in[(SID,-1154008),(UPD,-1154009),(NBS,-1153930)]:
            self.assertAlmostEqual(next(r.value for r in record.reported if r.property==G and r.source.source_id==source),value)
        self.assertEqual(self.db.selections[MONO,G].chosen.source_id,UPD)
        system=self.db.load_system('As');phase=next(x for x in system.species if x.record_id==MONO)
        expected=(-1154009-6*self.db.reference_state.water_gibbs_energy_J_mol)/4-3*GAS_CONSTANT_J_MOL_K*298.15*LN_10*7-3*FARADAY_C_MOL
        self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase,self.db.reference_state,pb.PourbaixConditions(),7,1)),expected)
        keep={MONO,'gfe-as-h3aso3-q+0-aqueous-aq'}
        result=pb.MassBalanceEngine(self.db).calculate_system(replace(system,species=tuple(x for x in system.species if x.record_id in keep),excluded=()),pb.PourbaixConditions(pH_points=3,U_points=3),pb.TotalMetalConcentration(1))
        self.assertGreater(result.precipitated_metal_fraction.min(),.5)
        np.testing.assert_allclose(result.dissolved_metal_mol_L+result.precipitated_metal_fraction,1,rtol=1e-10,atol=1e-15)

    def test_source_scope_counts_reuse_and_strict_completeness(self):
        review=json.loads(self.db.metadata['R11j3k_NEA_arsenic_review'])
        self.assertEqual((review['source_cells'],review['new_observations'],review['new_species'],review['newly_available_properties'],review['original1992_observations'],review['distinct2003_recalculation'],review['own2005_gas_observations'],review['independent_open_NBS_observations'],review['local_water_conversions']),(35,46,3,7,29,1,3,7,6))
        self.assertIn('interim',review['source_and_model_holds']['source_quality'])
        self.assertEqual(len(json.loads(self.db.metadata['R11j3k_arsenic_observations'])),46)
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])
        self.assertEqual((len(self.db.policy.overrides),len(self.db.policy.exclusions)),(62,18))
        self.assertEqual(self.db.policy.fingerprint,'4c1df55bbeff')
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'],'held_redistribution_rights')

if __name__=='__main__':
    unittest.main()
