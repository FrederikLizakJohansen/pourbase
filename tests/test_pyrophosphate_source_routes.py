"""Diphosphate identities, source cycles and free-component references stay explicit."""
import json
import math
import unittest
from collections import Counter
from dataclasses import replace

import numpy as np
import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K
from pourbase.engine import transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature
from pourbase.user_data import formula_counts

G = 'gibbs_energy_of_formation'
H = 'enthalpy_of_formation'
S = 'absolute_entropy'
P2 = 'r11k-p-p2o7-q-4-aqueous'
HP = 'r11k-p-hp2o7-q-3-aqueous'
LID = 'pyrophosphate-p2o7'


class PyrophosphateSourceRoutesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()

    def test_source_editions_and_open_nbs_alternatives_remain_distinct(self):
        for rid, g, h, entropy, original_g in [
            (P2, -1935503, -2271100, -117, -1919000),
            (HP, -1989158, -2274800, 46, -1972200),
        ]:
            record = self.db.species_records((rid,))[0]
            self.assertEqual(len(record.reported), 6)
            selected = self.db.selections[(rid, G)].chosen
            self.assertEqual((selected.value, selected.evidence_class, selected.source_id),
                             (g, 'A', 'NEA2003_R11k_pyrophosphate'))
            self.assertEqual(self.db.selections[(rid, H)].chosen.value, h)
            self.assertEqual(self.db.selections[(rid, S)].chosen.value, entropy)
            self.assertTrue(any(x.property == G and x.value == original_g and
                                x.source.source_id == 'R11k_NBS_PDR_pyrophosphate'
                                for x in record.reported))
            for x in record.reported:
                if x.source.source_id == 'R11k_NBS_PDR_pyrophosphate':
                    self.assertIsNone(x.uncertainty)
                    self.assertIn('csv_logical_record', x.source.locator)

    def test_condensation_cycle_retains_full_formula_charge_and_native_rounding(self):
        details = json.loads(self.db.metadata['R11k_pyrophosphate_observations'])
        for d in details:
            if 'combined_log10K' not in d:
                continue
            k = sum(x['coefficient']*x['log10K'] for x in d['reaction_components'])
            self.assertLess(abs(k-d['native_rounded_log10K']), .005)
            x = d['inputs']; rtl = d['R_J_mol_K']*298.15*math.log(10)
            self.assertAlmostEqual((2*x['HPO4_G_J_mol']-x['water_G_J_mol']-d['value'])/rtl, k)
            proton = 1 if d['record_id'] == HP else 0
            lhs = Counter({atom: 2*n for atom, n in formula_counts('HPO4').items()})
            lhs['H'] += proton
            rhs = formula_counts('HP2O7' if proton else 'P2O7') + formula_counts('H2O')
            self.assertEqual(lhs, rhs)
            self.assertEqual(-4+proton, -3 if proton else -4)
            self.assertIsNone(d['total_uncertainty'])
        species = {s.record_id: s for s in self.db.load_system('P').species}
        for rid, protons, charge in [(P2, 7, -4), (HP, 6.5, -3)]:
            s = species[rid]
            self.assertEqual((s.metal_count, s.core_oxygen_count, s.charge,
                              s.electrons_per_metal, s.protons_per_metal),
                             (2, 7, charge, 5, protons))

    def test_free_reference_matches_preferred_ion_and_preserves_the_old_pin(self):
        history = json.loads(self.db.metadata['R11k_pyrophosphate_reference_history'])
        reference = next(x for x in self.db.available_ligands() if x.ligand_id == LID)
        self.assertEqual(reference.gibbs_energy_J_mol, self.db.selections[(P2, G)].chosen.value)
        self.assertEqual(history['previous_pin']['gibbs_energy_J_mol'], -1919000)
        self.assertEqual(history['G_shift_J_mol'], -16503)
        self.assertEqual(history['current_pin_source_interval_J_mol'], 4563)
        ni = self.db.selections[('gfe-ni-ni-q+2-aqueous-aq', G)].chosen.value
        rtl = GAS_CONSTANT_J_MOL_K*298.15*math.log(10)
        for rid, expected in [('nea02c-ni-nip2o7-q-2-aqueous', 8.73),
                              ('nea02c-ni-hnip2o7-q-1-aqueous', 14.54)]:
            actual = (ni+reference.gibbs_energy_J_mol-self.db.selections[(rid, G)].chosen.value)/rtl
            self.assertAlmostEqual(actual, expected, places=3)

    def test_equal_free_component_chemical_potential_restores_transformed_energies(self):
        history = json.loads(self.db.metadata['R11k_pyrophosphate_reference_history'])
        offset = history['log10_activity_offset_for_equivalent_chemical_potential']
        cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity(LID, log10_free_activity=-3),)))
        restored = replace(cfg, ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity(LID, log10_free_activity=-3+offset),)))
        for symbol in ['Ni', 'Zr']:
            for s in self.db.load_system(symbol, ligand_ids=(LID,)).species:
                if s.record_id not in history['affected_species']:
                    continue
                old = replace(s, ligand_gibbs_energy_J_mol=-1919000)
                for ph, potential in [(0, -1), (7, 0), (14, 1)]:
                    old_e = float(transformed_gibbs_J_mol_metal(old, self.db.reference_state, cfg, ph, potential))
                    new_e = float(transformed_gibbs_J_mol_metal(s, self.db.reference_state, cfg, ph, potential))
                    equivalent = float(transformed_gibbs_J_mol_metal(s, self.db.reference_state, restored, ph, potential))
                    self.assertAlmostEqual(new_e-old_e, 16503)
                    self.assertAlmostEqual(equivalent, old_e)

    def test_polynuclear_balance_exclusion_and_mixed_source_temperature_route(self):
        system = self.db.load_system('P')
        system = replace(system, species=tuple(s for s in system.species if not s.is_gas))
        diagram = pb.MassBalanceEngine(self.db).calculate_system(
            system, pb.PourbaixConditions(pH_points=11, U_points=13),
            pb.TotalMetalConcentration(1e-6))
        aqueous = {diagram.system.species[i].record_id for i in diagram.aqueous_species_indices}
        self.assertTrue({P2, HP}.isdisjoint(aqueous))
        np.testing.assert_allclose(diagram.dissolved_metal_mol_L+
                                   1e-6*diagram.precipitated_metal_fraction, 1e-6,
                                   rtol=1e-11, atol=1e-15)
        for temperature in (323.15, 373.15):
            database = at_temperature(self.db, temperature)
            species = {s.record_id: s for s in database.load_system('P').species}
            for rid in (P2, HP):
                g = self.db.selections[(rid, G)].chosen.value
                h = self.db.selections[(rid, H)].chosen.value
                self.assertAlmostEqual(species[rid].gibbs_energy_J_mol,
                                       g-(temperature-298.15)*(h-g)/298.15)
                self.assertEqual(database.formation_entropies()[rid][1],
                                 'ΔfH° and ΔfG°, two sources')

    def test_ionic_entropy_cycle_and_source_specific_reuse_are_preserved(self):
        history = json.loads(self.db.metadata['R11k_pyrophosphate_reference_history'])
        for d, entropy, h, charge, nh in zip(history['formation_cycles'],
                                            [-117, 46], [-2271100, -2274800], [-4, -3], [0, 1]):
            sf = entropy-2*41.09-7*205.152/2-(nh-charge)*130.680/2
            self.assertAlmostEqual(d['NBS_formation_entropy_J_mol_K'], sf)
            self.assertAlmostEqual(d['NBS_G_from_HS_J_mol'], h-298.15*sf)
            self.assertGreater(d['mixed_preferred_NEAG_NBSHS_residual_J_mol'], 15000)
        basis = json.loads(self.db.metadata['source_reuse_R11k_pyrophosphate'])
        self.assertIn('further sublicensees', basis['NEA_terms'])
        self.assertIn('non-SRD', basis['NBS_terms'])
        self.assertIn('without warranty', basis['NBS_terms'])
        self.assertIn('2020', basis['source_updates'])
