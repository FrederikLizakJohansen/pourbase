"""Silicate reaction bases, protonation states and source conditions remain explicit."""
import json
import math
import unittest
from dataclasses import replace

import numpy as np
import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K
from pourbase.temperature import at_temperature

G = 'gibbs_energy_of_formation'
H = 'enthalpy_of_formation'
S = 'absolute_entropy'
H2 = 'r11j-si-h2sio4-q-2-aqueous'
T4 = 'r11j-si-h4si4o12-q-4-aqueous'
LID = 'silicate-h2sio4'


class SilicateSourceRoutesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()

    def test_original_editions_and_updated_entropy_remain_distinct(self):
        record = self.db.species_records((H2,))[0]
        entropy = {x.source.source_id: (x.value, x.uncertainty)
                   for x in record.reported if x.property == S}
        self.assertEqual(entropy, {
            'NEA_1992_R11j_selected_silicates': (-1.487, 51.592),
            'NEA_2003_R11j_selected_silicates': (-1.488, 51.592),
            'NEA_OECD_20261025_ancillary_R14e2': (-10.453, 50.402)})
        self.assertEqual(self.db.selections[(H2, S)].chosen.value, -10.453)
        self.assertEqual(self.db.selections[(H2, H)].chosen.uncertainty, 15051)
        ligand = next(x for x in self.db.available_ligands() if x.ligand_id == LID)
        # The established free-component reference retains its original evaluation.
        self.assertEqual(ligand.gibbs_energy_J_mol, -1175651)
        self.assertEqual(self.db.selections[(H2, G)].chosen.value, -1177088)

    def test_local_associations_reconstruct_with_their_own_protonation_basis(self):
        details = json.loads(self.db.metadata['R11j_silicate_observations'])
        for d in details:
            if 'source_log10K' not in d or d['record_id'] == T4:
                continue
            x = d['inputs']
            rtl = d['R_J_mol_K'] * d['temperature_K'] * math.log(10)
            self.assertAlmostEqual((x['metal_G_J_mol'] + x['ligand_G_J_mol'] -
                                    d['value_J_mol']) / rtl, d['source_log10K'])
            if 'cah2sio4' in d['record_id'] or 'mgh2sio4' in d['record_id']:
                self.assertEqual(x['ligand_G_J_mol'], -1175651)
            else:
                self.assertEqual(x['ligand_G_J_mol'], -1252304)
            self.assertIsNone(d['total_uncertainty'])

    def test_tetramer_water_normalization_and_per_silicon_energy(self):
        for d in json.loads(self.db.metadata['R11j_silicate_observations']):
            if d['record_id'] != T4 or 'source_log10K' not in d:
                continue
            x = d['inputs']; rtl = d['R_J_mol_K'] * 298.15 * math.log(10)
            # Four full orthosilicic-acid units release four water units.
            logk = (4*x['H4SiO4_G_J_mol'] - 4*x['water_G_J_mol'] - d['value_J_mol']) / rtl
            self.assertAlmostEqual(logk, d['source_log10K'])
        species = {s.record_id: s for s in self.db.load_system('Si').species}
        self.assertEqual((species[T4].formula_ascii, species[T4].metal_count,
                          species[T4].charge, species[T4].electrons_per_metal,
                          species[T4].protons_per_metal), ('H4Si4O12', 4, -4, 4, 5))
        self.assertEqual((species[H2].charge, species[H2].protons_per_metal), (-2, 6))
        self.assertNotIn((T4, H), self.db.selections)
        self.assertNotIn((T4, S), self.db.selections)

    def test_distinct_neutral_complexes_require_explicit_free_dihydrogen_silicate(self):
        for symbol in ('Ca', 'Mg'):
            rid = f'r11j-{symbol.lower()}-{symbol.lower()}h2sio4-q+0-aqueous'
            self.assertNotIn(rid, {s.record_id for s in self.db.load_system(symbol).species})
            species = next(s for s in self.db.load_system(symbol, ligand_ids=(LID,)).species
                           if s.record_id == rid)
            self.assertEqual((species.charge, species.ligand_charge,
                              species.core_oxygen_count, species.core_hydrogen_count,
                              species.electrons_per_metal), (0, -2, 0, 0, 2))
            self.assertEqual(self.db.selections[(rid, G)].chosen.evidence_class, 'E')
            self.assertNotIn((rid, H), self.db.selections)
        # Existing aluminium override and the Miron protonation reference are retained.
        self.assertEqual(self.db.selections[(
            'gfe-al-alh3sio4-q+2-aqueous-aq', G)].chosen.source_id,
            'Miron_R04_2017_gfe-al-alh3sio4-q+2-aqueous-aq_gf')

    def test_closed_silicon_inventory_excludes_tetramer_and_conserves_metal(self):
        system = self.db.load_system('Si')
        system = replace(system, species=tuple(s for s in system.species if not s.is_gas))
        diagram = pb.MassBalanceEngine(self.db).calculate_system(
            system, pb.PourbaixConditions(pH_points=11, U_points=13),
            pb.TotalMetalConcentration(1e-6))
        self.assertNotIn(T4, {diagram.system.species[i].record_id
                              for i in diagram.aqueous_species_indices})
        np.testing.assert_allclose(diagram.dissolved_metal_mol_L +
                                   1e-6*diagram.precipitated_metal_fraction, 1e-6,
                                   rtol=1e-11, atol=1e-15)
        for temperature in (323.15, 373.15):
            shifted = next(s for s in at_temperature(self.db, temperature).load_system('Si').species
                           if s.record_id == H2)
            expected = -1177088 - (temperature-298.15)*(-1386070+1177088)/298.15
            self.assertAlmostEqual(shifted.gibbs_energy_J_mol, expected)

    def test_condition_hold_and_separate_reuse_routes_remain_explicit(self):
        basis = json.loads(self.db.metadata['source_reuse_R11j_silicates'])
        self.assertIn('20C', basis['holds']['alkaline_aluminium'])
        self.assertIn('1.2M', basis['holds']['alkaline_aluminium'])
        self.assertIn('No298.15K observation admitted', basis['holds']['alkaline_aluminium'])
        self.assertIn('further sublicensees', basis['NEA_terms'])
        self.assertIn('isolated-original-numerical-facts', basis['original_fact_terms'])
        self.assertIn('mixed-source set', basis['reference_scope'])
        with self.db.connect() as c:
            self.assertEqual(c.execute("SELECT count(*) FROM species WHERE formula_ascii='AlH4SiO7'").fetchone()[0], 0)
