"""Open NBS salt observations and specialized-model scope."""
from contextlib import closing
from dataclasses import replace
import json
import unittest

import numpy as np
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal


class SpecializedPHREEQCSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_nbs_standard_enthalpy_uses_the_298K_column(self):
        record = self.database.species_records(('r13-mg-nbs-record8880',))[0]
        thermo = record.thermochemistry
        self.assertEqual((thermo.gibbs_energy_J_mol.value, thermo.formation_enthalpy_J_mol.value,
                          thermo.entropy_J_mol_K.value), (-591790, -641320, 89.62))
        for row in record.reported:
            self.assertEqual((row.temperature_K, row.pressure_bar), (298.15, 1))
            self.assertIsNone(row.uncertainty)
            locator = json.loads(row.source.locator)
            self.assertEqual(locator['logical_csv_record'], 8880)
            self.assertEqual(locator['csv_column_zero_based'], {
                'gibbs_energy_of_formation': 8, 'enthalpy_of_formation': 7,
                'absolute_entropy': 10}[row.property])
            self.assertEqual(self.database.selections[record.record_id, row.property].chosen.evidence_class, 'B')

    def test_magnesium_hydrate_water_is_counted_once(self):
        rid = 'r13-mg-nbs-record8909'
        self.assertNotIn(rid, {s.record_id for s in self.database.load_system('Mg').species})
        phase = next(s for s in self.database.load_system('Mg', ligand_ids=('chloride-cl',)).species
                     if s.record_id == rid)
        self.assertEqual((phase.metal_count, phase.components[0].count, phase.core_oxygen_count,
                          phase.core_hydrogen_count, phase.protons_per_metal), (1, 2, 6, 12, 0))
        self.assertEqual(replace(phase, electron_coefficient_per_metal=None).electrons_per_metal, 2)
        rtln = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        for chloride in [-6, -3, 0]:
            cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('chloride-cl', log10_free_activity=chloride),)))
            expected = (-2114640 - 6 * self.database.reference_state.water_gibbs_energy_J_mol
                        - 2 * (phase.components[0].gibbs_energy_J_mol + rtln * chloride))
            for pH, potential in [(0, -1), (7, 0), (14, 1)]:
                self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(
                    phase, self.database.reference_state, cfg, pH, potential)),
                    expected - 2 * FARADAY_C_MOL * potential, places=7)

    def test_source_enthalpy_only_hydrates_keep_gibbs_and_entropy_missing(self):
        for logical_record in [9242, 9243, 9244, 9245]:
            rid = f'r13-ca-nbs-record{logical_record}'
            record = self.database.species_records((rid,))[0]
            self.assertEqual({r.property for r in record.reported}, {'enthalpy_of_formation'})
            self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
            self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
            excluded = self.database.load_system('Ca', ligand_ids=('chloride-cl',)).excluded
            self.assertEqual(next(r.reason for r in excluded if r.record_id == rid),
                             pb.ExclusionReason.GIBBS_ENERGY_UNAVAILABLE)
        record = self.database.species_records(('r13-ca-nbs-record9245',))[0]
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, -2607900)
        self.assertEqual(record.phase_identity.status, 'unresolved')

    def test_mixed_sulfate_requires_both_reservoirs_and_keeps_source_gap(self):
        rid = 'r13-ca-nbs-record12054'
        for components in [(), ('sulfate-so4',), ('sodium-na',)]:
            self.assertNotIn(rid, {s.record_id for s in self.database.load_system(
                'Ca', ligand_ids=components).species})
        system = self.database.load_system('Ca', ligand_ids=('sulfate-so4', 'sodium-na'))
        self.assertEqual(next(r.reason for r in system.excluded if r.record_id == rid),
                         pb.ExclusionReason.GIBBS_ENERGY_UNAVAILABLE)
        record = self.database.species_records((rid,))[0]
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, -2829200)

    def test_primary_balances_preserve_external_chloride_scope(self):
        cfg = pb.PourbaixConditions(pH_points=7, U_points=9,
            ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('chloride-cl', log10_free_activity=-3),)))
        for symbol in ['K', 'Mg', 'Ca']:
            system = self.database.load_system(symbol, ligand_ids=('chloride-cl',))
            system = replace(system, species=tuple(s for s in system.species if not s.is_gas))
            result = pb.MassBalanceEngine(self.database).calculate_system(
                system, cfg, pb.TotalMetalConcentration(1e-4))
            np.testing.assert_allclose(result.dissolved_metal_mol_L
                + 1e-4 * result.precipitated_metal_fraction, 1e-4, rtol=1e-11, atol=1e-15)

    def test_model_parameters_and_source_holds_are_separate_from_observations(self):
        review = json.loads(self.database.metadata['R13_PHREEQC_specialized_review'])
        self.assertEqual(review['inventory']['main_specialized_files'], 5)
        self.assertEqual(review['inventory']['specialized_reaction_blocks'], 4524)
        self.assertEqual(review['inventory']['scoped_noncomment_lines'], 15298)
        self.assertEqual(review['inventory']['native_numbers_imported'], 0)
        self.assertIn('convergence', next(k for k in review['inventory']['dispositions'] if 'arbitrary' in k))
        self.assertIn('JANAF', review['USGS_candidate_exclusions'])
        self.assertEqual(len(review['admitted_phase_rows']), 12)
        self.assertTrue(review['prior_reviews_carried'])
        with closing(self.database.connect()) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM reported_thermochemistry "
                "WHERE source_id='R13_NBS_PDR_salt_properties'").fetchone()[0], 26)
