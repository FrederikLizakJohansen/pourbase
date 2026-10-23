"""Original selenide cells, neutral reservoirs and separately qualified RuTe2."""
from dataclasses import replace
import json
import unittest

import numpy as np
import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal


class HeraclesSourceRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_original_selected_cells_replace_no_previous_evidence(self):
        record = self.database.species_records(('r10-bi-bi2se3-cr',))[0]
        self.assertEqual((record.thermochemistry.gibbs_energy_J_mol.value,
                          record.thermochemistry.formation_enthalpy_J_mol.value,
                          record.thermochemistry.entropy_J_mol_K.value), (-146618, -145500, 243.5))
        for row in record.reported:
            self.assertEqual((row.temperature_K, row.pressure_bar), (298.15, 1))
            loc = json.loads(row.source.locator)
            self.assertEqual((loc['table'], loc['printed_page'], loc['pdf_page']), ('III-1', 43, 84))
            self.assertIn('95%', loc['confidence'])
            self.assertEqual(self.database.selections[record.record_id, row.property].chosen.evidence_class, 'A')

    def test_unselected_mirror_G_and_entropy_proxies_stay_missing(self):
        for rid, properties in [('r10-ru-ruse2-cr', {'absolute_entropy'}),
                                ('r10-sn-alpha-snse', {'enthalpy_of_formation'}),
                                ('r10-fe-fese2-cr', {'enthalpy_of_formation', 'absolute_entropy'})]:
            record = self.database.species_records((rid,))[0]
            self.assertEqual({r.property for r in record.reported}, properties)
            self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
        lanthanum = self.database.species_records(('r10-la-la2se3-cr',))[0]
        self.assertEqual(lanthanum.charge, 0)
        self.assertEqual(lanthanum.thermochemistry.entropy_J_mol_K.value, 202.2)

    def test_neutral_selenium_reservoir_balances_full_formula(self):
        rid = 'r10-bi-bi2se3-cr'
        self.assertEqual(next(r.reason for r in self.database.load_system('Bi').excluded if r.record_id == rid),
                         pb.ExclusionReason.LIGAND_NOT_SELECTED)
        phase = next(s for s in self.database.load_system('Bi', ligand_ids=('elemental-se-cr',)).species
                     if s.record_id == rid)
        self.assertEqual((phase.metal_count, phase.components[0].count, phase.components[0].charge), (2, 3, 0))
        self.assertEqual((phase.core_oxygen_count, phase.core_hydrogen_count, phase.electrons_per_metal), (0, 0, 0))
        self.assertEqual(replace(phase, electron_coefficient_per_metal=None).electrons_per_metal, 0)
        for loga in [0, -3]:
            cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('elemental-se-cr', log10_free_activity=loga),)))
            expected = (-146618 - 3 * GAS_CONSTANT_J_MOL_K * 298.15 * LN_10 * loga) / 2
            for pH, potential in [(0, -1), (7, 0), (14, 1)]:
                self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(
                    phase, self.database.reference_state, cfg, pH, potential)), expected, places=7)

    def test_gases_need_both_se_reservoir_and_explicit_gas_selection(self):
        rid = 'r10-ge-gese-g'
        for components, gases in [((), False), ((), True), (('elemental-se-cr',), False)]:
            system = self.database.load_system('Ge', ligand_ids=components, include_optional_gases=gases)
            self.assertNotIn(rid, {s.record_id for s in system.species})
        system = self.database.load_system('Ge', ligand_ids=('elemental-se-cr',), include_optional_gases=True)
        self.assertIn(rid, {s.record_id for s in system.species})
        bismuth = self.database.load_system('Bi', ligand_ids=('elemental-se-cr',), include_optional_gases=True)
        self.assertEqual(next(r.reason for r in bismuth.excluded if r.record_id == 'r10-bi-bise-g'),
                         pb.ExclusionReason.GIBBS_ENERGY_UNAVAILABLE)

    def test_rute2_original_extrapolation_has_separate_source_and_phase_hold(self):
        record = self.database.species_records(('r10-ru-rute2-2024-emf',))[0]
        self.assertEqual((record.thermochemistry.gibbs_energy_J_mol.value,
                          record.thermochemistry.formation_enthalpy_J_mol.value,
                          record.thermochemistry.entropy_J_mol_K.value), (-126900, -136600, 94.94))
        self.assertEqual(record.phase_identity.status, 'unresolved')
        for row in record.reported:
            self.assertEqual(row.status, 'source_verified_estimate')
            self.assertIsNone(row.uncertainty)
            self.assertEqual(json.loads(row.source.locator)['experimental_temperature_range_K'], [747, 884])
            self.assertEqual(self.database.selections[record.record_id, row.property].chosen.evidence_class, 'E')

    def test_primary_inventory_balance_and_bibliography_scope(self):
        cfg = pb.PourbaixConditions(pH_points=7, U_points=9,
            ligand_activities=pb.LigandActivityModel((pb.LigandActivity('elemental-se-cr', log10_free_activity=0),)))
        system = self.database.load_system('Ni', ligand_ids=('elemental-se-cr',))
        system = replace(system, species=tuple(s for s in system.species if not s.is_gas))
        result = pb.MassBalanceEngine(self.database).calculate_system(system, cfg, pb.TotalMetalConcentration(1e-4))
        np.testing.assert_allclose(result.dissolved_metal_mol_L + 1e-4 * result.precipitated_metal_fraction,
                                   1e-4, rtol=1e-11, atol=1e-15)
        review = json.loads(self.database.metadata['R10_Heracles_source_review'])
        self.assertEqual(review['bibliography']['property_slots'], 2664)
        self.assertEqual(review['bibliography']['graph_Heracles_records'], 949)
        self.assertTrue(review['bibliography']['graph_edges_are_all_record_level'])
        self.assertEqual(len(review['admitted_phase_rows']), 25)
