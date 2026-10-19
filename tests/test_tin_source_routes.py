"""Tin source routes retain hydration, evidence status and phase distinctions."""
from dataclasses import replace
import json
import math
import unittest

import numpy as np
import pourbase as pb
from pourbase.engine import transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature

G = 'gibbs_energy_of_formation'
RID = 'r11f-sn-casn-oh-6-burtite'
RTL = 8.31446261815324 * 298.15 * math.log(10)


class TinSourceRoutesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()
        cls.derivations = json.loads(cls.db.metadata['R11f_tin_derivations'])

    def test_historical_reactions_reconstruct_and_keep_preferred_nea_values(self):
        self.assertEqual(len(self.derivations), 4)
        self.assertEqual(sorted(d['source_log10K_width'] for d in self.derivations), [.3, .3, .3, 1.6])
        for d in self.derivations:
            record = self.db.species_records((d['record_id'],))[0]
            local = next(v for v in record.reported if v.source.source_id ==
                         'pourbase_R11f_historical_tin_G_variants')
            anchor = d['anchor']['value_J_mol']
            water = self.db.reference_state.water_gibbs_energy_J_mol
            if d['equation'].startswith('Gsolid'):
                logk = (local.value - anchor + 2 * water) / RTL
            else:
                logk = -(local.value - d['anchor_coefficient'] * anchor
                         - d['water_input']['coefficient'] * water) / RTL
            self.assertAlmostEqual(logk, d['source_log10K'])
            self.assertIsNone(local.uncertainty)
            self.assertFalse(local.selected_as_recommended)
            self.assertEqual(self.db.selections[(record.record_id, G)].chosen.value_id,
                             d['old_preferred_value_id'])
            self.assertIn('further sublicensees', local.source.locator)

    def test_native_water_components_match_existing_full_hydroxo_formulas(self):
        water = self.db.reference_state.water_gibbs_energy_J_mol
        for suffix, removed, formula in [('5-q-1-aq', 2, 'Sn(OH)5'),
                                         ('6-q-2-aqueous-aq', 3, 'Sn(OH)6')]:
            d = next(d for d in self.derivations if suffix in d['record_id'])
            record = self.db.species_records((d['record_id'],))[0]
            self.assertEqual(record.formula_ascii, formula)
            native = d['value_J_mol'] - removed * water
            native_master = d['anchor']['value_J_mol'] - 2 * water
            self.assertAlmostEqual(native - native_master - water, -RTL * d['source_log10K'])

    def test_burtite_original_triplet_keeps_status_intervals_and_nominal_composition(self):
        record = self.db.species_records((RID,))[0]
        values = {v.property: v for v in record.reported}
        self.assertEqual(record.formula_ascii, 'CaSn(OH)6')
        for prop, value, width, status in [(G, -1885800, 7600, 'source_verified_estimate'),
                ('enthalpy_of_formation', -2149900, 6900, 'verified'),
                ('absolute_entropy', 215.7, None, 'source_verified_estimate')]:
            v = values[prop]
            self.assertEqual((v.value, v.uncertainty, v.status), (value, width, status))
            self.assertTrue(v.selected_as_recommended)
            self.assertIn('adsorbedwater', v.source.locator)
        basis = json.loads(self.db.metadata['source_reuse_R11f_tin_original_results'])
        self.assertIn('CC BY-NC-ND', basis['Haase_source']['article_licence'])
        self.assertIn('three original numerical results', basis['Haase_source']['numerical_fact_review'])

    def test_burtite_full_formula_energy_and_calcium_response_keep_thermal_scope(self):
        system = self.db.load_system('Sn', ligand_ids=('calcium-ca2',))
        s = next(s for s in system.species if s.record_id == RID)
        self.assertEqual((s.core_oxygen_count, s.core_hydrogen_count,
                          s.electrons_per_metal, s.protons_per_metal), (6, 6, 4, 6))
        energies = []
        for logca in (-3, -1):
            cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('calcium-ca2', log10_free_activity=logca),)))
            energy = float(transformed_gibbs_J_mol_metal(s, self.db.reference_state, cfg, 7, .2))
            expected = -1885800 + 6 * 237129 - (-553580 + RTL * logca) - 6 * RTL * 7 - 4 * 96485.33212 * .2
            self.assertAlmostEqual(energy, expected, places=3)
            energies.append(energy)
        self.assertAlmostEqual(energies[1] - energies[0], -2 * RTL)
        for temperature in (323.15, 373.15):
            self.assertNotIn(RID, {s.record_id for s in at_temperature(self.db, temperature)
                                  .load_system('Sn', ligand_ids=('calcium-ca2',)).species})

    def test_gas_free_closed_tin_balance_and_distinct_precipitate_equilibrium(self):
        cfg = pb.PourbaixConditions(pH_min=13, pH_max=14, pH_points=3,
            eh_min_V=.4, eh_max_V=.6, eh_points=3,
            ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('calcium-ca2', log10_free_activity=-1),)))
        system = self.db.load_system('Sn', ligand_ids=('calcium-ca2',))
        gas_free = replace(system, species=tuple(s for s in system.species if not s.is_gas))
        for model in (pb.IdealActivityCoefficientModel(), pb.DaviesActivityCoefficientModel(.1)):
            result = pb.MassBalanceEngine(self.db, activity_coefficient_model=model).calculate_system(
                gas_free, cfg, pb.TotalMetalConcentration(.05))
            np.testing.assert_allclose(result.dissolved_metal_mol_L + .05 * result.precipitated_metal_fraction,
                                       .05, rtol=1e-11, atol=1e-15)
            self.assertGreater(float(np.max(result.precipitated_metal_fraction)), 0)
            self.assertEqual({result.system.species[int(i)].record_id
                              for i in np.unique(result.precipitating_solid_index) if i >= 0}, {RID})
        sn6 = self.db.selections[('gfe-sn-sn-oh-6-q-2-aqueous-aq', G)].chosen.value
        k = -(-1885800 + 553580 - sn6) / RTL
        self.assertAlmostEqual(k, 3.43, delta=.02)
        self.assertGreater(abs(k - 9.7), 6)  # Historical fresh precipitate is a distinct branch.
