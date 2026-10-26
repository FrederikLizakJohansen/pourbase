"""Original open NBS fluoride observations, hydrate units and source qualifications."""
import json
import unittest
from dataclasses import replace
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL,GAS_CONSTANT_J_MOL_K,LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature
SID='R16d3a_open_NBS_crystalline_fluorides';G='gibbs_energy_of_formation';H='enthalpy_of_formation';S='absolute_entropy'
class NBSCrystallineFluorideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db=pb.ThermodynamicDatabase.bundled()
        cls.review=json.loads(cls.db.metadata['R16d3a_NBS_fluoride_source_review'])
        cls.rows=cls.review['records']

    def row(self,logical):
        return next(r for r in self.rows if r['logical_record']==logical)

    def test_original_cells_retain_exact_values_units_missing_widths_and_lineage(self):
        self.assertEqual((self.review['source_rows'],self.review['source_numeric_cells'],self.review['source_blank_cells'],self.review['new_observations'],self.review['new_species'],self.review['retained_original_cells']),(29,83,4,80,25,3))
        observations=json.loads(self.db.metadata['R16d3a_NBS_fluoride_observations'])
        for obs in observations:
            reported=next(x for x in self.db.species_records((obs['record_id'],))[0].reported if x.value_id==obs['value_id'])
            evidence=json.loads(reported.source.locator)
            self.assertEqual(reported.value,evidence['original_value']*evidence['conversion_factor'])
            self.assertEqual(reported.unit,'J/(mol K)'if reported.property==S else'J/mol')
            self.assertIsNone(reported.uncertainty)
            self.assertEqual((reported.temperature_K,reported.pressure_bar),(298.15,1))
            self.assertEqual(reported.evaluation_lineage.evaluation_id,'NBS1982-with-errata:logical-'+str(evidence['logical_csv_record']))
            candidate=next(x for x in self.db.selections[obs['record_id'],reported.property].candidates if x.value_id==reported.value_id)
            self.assertEqual(candidate.evidence_class,'B')
        self.assertEqual(self.row(10791)['admitted_properties'],[])
        self.assertEqual(len(self.row(10791)['retained_original_properties']),3)

    def test_hydrate_formula_and_buffered_energy_use_every_water_once(self):
        for logical,water,F in [(4785,2,2),(5069,2,1),(5070,4,1),(5305,4,2),(12190,2,1)]:
            r=self.row(logical);phase=next(x for x in self.db.load_system(r['symbol'],ligand_ids=('fluoride-f',)).species if x.record_id==r['record_id'])
            self.assertEqual((phase.metal_count,phase.core_oxygen_count,phase.core_hydrogen_count,phase.electrons_per_metal,phase.protons_per_metal),(1,water,2*water,F,0))
            self.assertEqual((phase.components[0].count,phase.components[0].charge),(F,-1))
            cfg=pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((pb.LigandActivity('fluoride-f',log10_free_activity=-3),)))
            expected=phase.gibbs_energy_J_mol-water*self.db.reference_state.water_gibbs_energy_J_mol-F*(phase.components[0].gibbs_energy_J_mol-3*GAS_CONSTANT_J_MOL_K*298.15*LN_10)-F*FARADAY_C_MOL
            self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(phase,self.db.reference_state,cfg,7,1)),expected)

    def test_original_chromium_source_discrepancy_remains_visible(self):
        r=self.row(6543);record=self.db.species_records((r['record_id'],))[0]
        values={x.property:x.value for x in record.reported if x.source.source_id==SID}
        self.assertEqual(values,{G:-1088000,H:-1159000,S:93.89})
        ev=json.loads(next(x for x in record.reported if x.property==G).source.locator)
        self.assertEqual((ev['original_printed_page'],ev['original_pdf_page']),('2-198',206))
        self.assertTrue(ev['printed_GHS_cells_visually_verified'])
        self.assertAlmostEqual(ev['source_cycle_residual_J_mol'],-1217.9925)
        self.assertTrue(any(w.type=='r16d3a_original_NBS_source_cycle_discrepancy'for w in record.warnings))

    def test_named_source_phases_and_resolved_beta_zirconium_are_preserved(self):
        r=self.row(7062);self.assertEqual(r['record_id'],'nea02d-zr-beta-zrf4-q+0-solid')
        self.assertEqual(self.db.species_records((r['record_id'],))[0].phase_identity.identified_phase,'beta crystalline')
        for logical,label in [(7130,'monoclinic'),(8762,'α, quartz')]:
            record=self.db.species_records((self.row(logical)['record_id'],))[0]
            self.assertIn(label,record.phase_detail)
            self.assertEqual(record.phase_identity.status,'unresolved')
            self.assertIsNone(record.phase_identity.spacegroup_symbol)

    def test_existing_NEA_fluorides_keep_their_selected_evaluations(self):
        for logical in[5302,5824,7062]:
            rid=self.row(logical)['record_id'];record=self.db.species_records((rid,))[0]
            self.assertEqual(sum(x.source.source_id==SID for x in record.reported),3)
            for prop in[G,H,S]:
                self.assertEqual(self.db.selections[rid,prop].chosen.evidence_class,'A')
                self.assertNotEqual(self.db.selections[rid,prop].chosen.source_id,SID)
        self.assertEqual(self.db.policy.fingerprint,'f8ee0083e857')
        self.assertEqual(len(self.db.available_ligands()),31)
        self.assertEqual(json.loads(self.db.metadata['R11j3f2_explicit_evaluation_lineage'])['lineage_annotations'],10)
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])

    def test_new_fluorides_require_explicit_component_and_thermal_data_stay_missing(self):
        for logical in[4785,5305]:
            r=self.row(logical);record=self.db.species_records((r['record_id'],))[0]
            self.assertEqual({x.property for x in record.reported},{G})
            self.assertNotIn(r['record_id'],{x.record_id for x in self.db.load_system(r['symbol']).species})
            thermal=at_temperature(self.db,323.15).load_system(r['symbol'],ligand_ids=('fluoride-f',))
            self.assertNotIn(r['record_id'],{x.record_id for x in thermal.species})
        r=self.row(8877)
        cfg=pb.PourbaixConditions(pH_points=9,U_points=11,ligand_activities=pb.LigandActivityModel((pb.LigandActivity('fluoride-f',log10_free_activity=0),)))
        diagram=pb.PourbaixEngine(self.db).calculate('Mg',cfg,allow_incomplete=True)
        self.assertIn(r['record_id'],{x.record_id for x in diagram.system.species})

if __name__=='__main__':
    unittest.main()
