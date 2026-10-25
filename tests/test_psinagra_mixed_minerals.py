"""Original USGS mineral alternatives and complete buffered reactions."""
from dataclasses import replace
import json
import unittest

import numpy as np
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal


class PSINagraMixedMineralTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_original_evaluations_and_shared_dolomite_alternatives(self):
        for rid, values in [('r11v-mg-dolomite-ordered', (-2161300, -2324500, 155.2)),
                            ('r11v-al-kaolinite', (-3797500, -4119000, 200.4))]:
            record = self.database.species_records((rid,))[0]
            # Keep checking the original evaluation after newer source selections.
            original_rows = [row for row in record.reported if row.source and
                             row.source.source_id == 'R11v_USGS1995_mixed_minerals']
            self.assertEqual({row.property: row.value for row in original_rows}, dict(zip(
                ['gibbs_energy_of_formation', 'enthalpy_of_formation', 'absolute_entropy'], values)))
            self.assertEqual(record.phase_identity.status, 'resolved')
            for row in original_rows:
                self.assertEqual((row.temperature_K, row.pressure_bar), (298.15, 1))
                self.assertIn('USGS', row.source.locator)
                selection = self.database.selections[rid, row.property]
                candidate = next(c for c in selection.candidates if c.value_id == row.value_id)
                self.assertEqual(candidate.evidence_class, 'B')
        dolomite = self.database.species_records(('r11v-mg-dolomite-ordered',))[0]
        original = {row.property: row for row in dolomite.reported
                    if row.source.source_id == 'R11v_HemingwayRobie1994_dolomite_original'}
        self.assertEqual(original['gibbs_energy_of_formation'].value, -2161700)
        self.assertEqual(original['enthalpy_of_formation'].uncertainty, 1100)
        self.assertTrue(all(not row.selected_as_recommended for row in original.values()))
        self.assertEqual(len(dolomite.reported), 8)

    def test_ordered_dolomite_requires_both_reservoirs_and_charge_balance(self):
        rid = 'r11v-mg-dolomite-ordered'
        for components in [(), ('calcium-ca2',), ('carbonate-co3',)]:
            self.assertNotIn(rid, {s.record_id for s in self.database.load_system(
                'Mg', ligand_ids=components).species})
        phase = next(s for s in self.database.load_system(
            'Mg', ligand_ids=('calcium-ca2', 'carbonate-co3')).species if s.record_id == rid)
        self.assertEqual([(c.ligand_id, c.count, c.charge) for c in phase.components],
                         [('calcium-ca2', 1, 2), ('carbonate-co3', 2, -2)])
        self.assertEqual((phase.metal_count, phase.core_oxygen_count, phase.core_hydrogen_count,
                          phase.electrons_per_metal, phase.protons_per_metal), (1, 0, 0, 2, 0))
        self.assertEqual(replace(phase, electron_coefficient_per_metal=None).electrons_per_metal, 2)
        rtln = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        for calcium, carbonate in [(-6, -3), (-3, -6), (0, 0)]:
            cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('calcium-ca2', log10_free_activity=calcium),
                pb.LigandActivity('carbonate-co3', log10_free_activity=carbonate))))
            expected = -2163402 - (-553580 + rtln * calcium) - 2 * (-527810 + rtln * carbonate)
            for potential in [-1, 0, 1]:
                self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(
                    phase, self.database.reference_state, cfg, 7, potential)),
                    expected - 2 * FARADAY_C_MOL * potential, places=7)

    def test_kaolinite_uses_physical_silicic_acid_and_full_formula_unit(self):
        phase = next(s for s in self.database.load_system('Al', ligand_ids=(
            'silica-sio2-component',)).species if s.record_id == 'r11v-al-kaolinite')
        self.assertEqual((phase.metal_count, phase.core_oxygen_count, phase.core_hydrogen_count,
                          phase.electrons_per_metal, phase.protons_per_metal), (2, 5, 4, 3, 3))
        rtln = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        for silica in [-6, -3, 0]:
            cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('silica-sio2-component', log10_free_activity=silica),)))
            for pH, potential in [(0, -1), (7, 0), (14, 1)]:
                # 2Al + 2H4SiO4 + H2O = kaolinite + 6H+ + 6e-.
                expected = ((-3797500 - 2 * (-1316600 + rtln * silica)
                             - self.database.reference_state.water_gibbs_energy_J_mol
                             - 6 * rtln * pH) / 2 - 3 * FARADAY_C_MOL * potential)
                self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(
                    phase, self.database.reference_state, cfg, pH, potential)), expected, places=7)

    def test_closed_primary_inventory_with_prescribed_secondary_activities(self):
        for symbol, components in [('Mg', ('calcium-ca2', 'carbonate-co3')),
                                   ('Al', ('silica-sio2-component',))]:
            cfg = pb.PourbaixConditions(pH_points=7, U_points=9,
                ligand_activities=pb.LigandActivityModel(tuple(pb.LigandActivity(
                    key, log10_free_activity=-3) for key in components)))
            system = self.database.load_system(symbol, ligand_ids=components)
            system = replace(system, species=tuple(s for s in system.species if not s.is_gas))
            result = pb.MassBalanceEngine(self.database).calculate_system(
                system, cfg, pb.TotalMetalConcentration(1e-4))
            np.testing.assert_allclose(result.dissolved_metal_mol_L
                + 1e-4 * result.precipitated_metal_fraction, 1e-4, rtol=1e-11, atol=1e-15)

    def test_open_source_scope_keeps_disordered_phase_and_other_holds(self):
        review = json.loads(self.database.metadata['R11v_PSI_Nagra_completion'])
        self.assertEqual(review['mirror_scope']['total_property_slots'], 3830)
        self.assertEqual(review['mirror_scope']['reactions'], 440)
        self.assertIn('public-domain', review['reuse']['reuse_basis'])
        holds = json.loads(self.database.metadata['R11v_source_and_scientific_holds'])
        self.assertIn('Disordered dolomite', holds['R11v1'])
        self.assertTrue(review['prior_reviews_carried'])
        with self.database.connect() as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM species WHERE record_id=?",
                ('r11v-mg-dolomite-disordered',)).fetchone()[0], 0)
