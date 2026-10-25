"""Independent NBS chloride cells and the separate Thermoddem bulk hold."""
from dataclasses import replace
import json
import unittest

import numpy as np
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal


class ThermoddemOriginalSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_original_columns_and_conditions(self):
        record = self.database.species_records(('r16-zn-nbs-record4043',))[0]
        self.assertEqual((record.thermochemistry.gibbs_energy_J_mol.value,
                          record.thermochemistry.formation_enthalpy_J_mol.value,
                          record.thermochemistry.entropy_J_mol_K.value), (-369398, -415050, 111.46))
        for row in record.reported:
            self.assertEqual((row.temperature_K, row.pressure_bar, row.uncertainty), (298.15, 1, None))
            ev = json.loads(row.source.locator)
            self.assertEqual(ev['logical_csv_record'], 4043)
            self.assertEqual(ev['csv_column_zero_based'], {'gibbs_energy_of_formation': 8,
                             'enthalpy_of_formation': 7, 'absolute_entropy': 10}[row.property])
            self.assertEqual(ev['reuse']['doi'], '10.18434/M32124')
            self.assertEqual(self.database.selections[record.record_id, row.property].chosen.evidence_class, 'B')

    def test_existing_iron_dihydrate_gains_enthalpy(self):
        rid = 'nea02a-fe-fecl2-h2o-2-chloride-dihydrate'
        record = self.database.species_records((rid,))[0]
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, -953100)
        self.assertEqual(self.database.selections[rid, 'enthalpy_of_formation'].chosen.source_id,
                         'R16_open_NBS_chloride_originals')
        self.assertEqual(self.database.selections[rid, 'gibbs_energy_of_formation'].chosen.source_id,
                         'NEA_OECD_20261014_Fe')

    def test_fractional_hydrate_counts_water_once(self):
        rid = 'r16-cd-nbs-record4342'
        phase = next(s for s in self.database.load_system('Cd', ligand_ids=('chloride-cl',)).species
                     if s.record_id == rid)
        self.assertEqual((phase.metal_count, phase.core_oxygen_count, phase.core_hydrogen_count,
                          phase.components[0].count, phase.protons_per_metal), (1, 2.5, 5, 2, 0))
        self.assertEqual(replace(phase, electron_coefficient_per_metal=None).electrons_per_metal, 2)
        cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity('chloride-cl', log10_free_activity=-3),)))
        rtln = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        for pH, potential in [(0, -1), (7, 0), (14, 1)]:
            expected = (-943939 - 2.5 * self.database.reference_state.water_gibbs_energy_J_mol
                        - 2 * (phase.components[0].gibbs_energy_J_mol - 3 * rtln)
                        - 2 * FARADAY_C_MOL * potential)
            self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(
                phase, self.database.reference_state, cfg, pH, potential)), expected, places=7)

    def test_copper_valences_are_not_interchanged(self):
        system = self.database.load_system('Cu', ligand_ids=('chloride-cl',))
        for rid, expected in [('r16-cu-nbs-record4786', 1), ('r16-cu-nbs-record4789', 2)]:
            phase = next(s for s in system.species if s.record_id == rid)
            self.assertEqual((phase.components[0].count, phase.electrons_per_metal), (expected, expected))
            self.assertEqual(replace(phase, electron_coefficient_per_metal=None).electrons_per_metal, expected)

    def test_source_enthalpy_only_and_missing_gibbs_remain_explicit(self):
        for rid, sym in [('r16-co-nbs-record5513', 'Co'),
                         ('nea02a-fe-fecl3-h2o-6-chloride-hexahydrate', 'Fe')]:
            record = self.database.species_records((rid,))[0]
            self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
            self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
            self.assertTrue(all(r.property == 'enthalpy_of_formation' for r in record.reported))
            excluded = self.database.load_system(sym, ligand_ids=('chloride-cl',)).excluded
            self.assertEqual(next(x.reason for x in excluded if x.record_id == rid),
                             pb.ExclusionReason.GIBBS_ENERGY_UNAVAILABLE)

    def test_chloride_gate_and_primary_balance(self):
        rid = 'r16-cd-nbs-record4342'
        self.assertNotIn(rid, {s.record_id for s in self.database.load_system('Cd').species})
        cfg = pb.PourbaixConditions(pH_points=7, U_points=9,
            ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('chloride-cl', log10_free_activity=-3),)))
        system = self.database.load_system('Cd', ligand_ids=('chloride-cl',))
        system = replace(system, species=tuple(s for s in system.species if not s.is_gas))
        for model in [pb.IdealActivityCoefficientModel(), pb.DaviesActivityCoefficientModel(.01)]:
            result = pb.MassBalanceEngine(self.database, activity_coefficient_model=model).calculate_system(
                system, cfg, pb.TotalMetalConcentration(1e-3))
            np.testing.assert_allclose(result.dissolved_metal_mol_L + 1e-3 * result.precipitated_metal_fraction,
                                       1e-3, rtol=1e-10, atol=1e-15)

    def test_original_crystal_is_not_assigned_a_native_alias(self):
        record = self.database.species_records(('r16-cu-nbs-record4789',))[0]
        self.assertEqual(record.phase_identity.status, 'unresolved')
        self.assertNotIn('Melanothallite', record.species)
        holds = json.loads(self.database.metadata['R16_source_and_model_holds'])
        self.assertIn('Melanothallite', holds['R16c'])

    def test_independent_source_route_clears_no_bulk_permission(self):
        review = json.loads(self.database.metadata['R16_Thermoddem_rights_review'])
        self.assertEqual((review['new_observations'], review['new_species']), (64, 15))
        self.assertEqual(review['native_Thermoddem_numbers_imported'], 0)
        self.assertFalse(review['rights']['new_compatible_data_grant_identified'])
        self.assertEqual(review['rights']['bulk_data_status'], 'held_redistribution_rights')
        self.assertFalse(review['rights']['outreach_performed'])
        self.assertEqual(len(json.loads(self.database.metadata['R16_open_NBS_observations'])), 64)
        self.assertIn('open non-SRD', json.loads(self.database.metadata['R16_source_reuse'])['route'])
        self.assertTrue(json.loads(self.database.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])


if __name__ == '__main__':
    unittest.main()
