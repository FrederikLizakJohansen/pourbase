"""Independent reservoirs and source conditions for mixed-metal NEA solids."""

from dataclasses import FrozenInstanceError, replace
import math
import unittest

import numpy as np
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import transformed_gibbs_J_mol_metal
from pourbase.equilibria import _reaction


class MixedComponentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def system(self, *components):
        return self.database.load_system('Zr', ligand_ids=components)

    def test_each_independent_reservoir_is_required(self):
        rid = 'nea02g4-zr-ca3-silicate'
        for selected in [(), ('calcium-ca2',), ('silica-sio2-component',)]:
            system = self.system(*selected)
            self.assertEqual(next(x.reason for x in system.excluded if x.record_id == rid),
                             pb.ExclusionReason.LIGAND_NOT_SELECTED)
        phase = next(x for x in self.system('calcium-ca2', 'silica-sio2-component').species
                     if x.record_id == rid)
        self.assertEqual([(c.ligand_id, c.count) for c in phase.components],
                         [('calcium-ca2', 3), ('silica-sio2-component', 2)])
        conditions = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity('calcium-ca2', log10_free_activity=-3),)))
        with self.assertRaises(pb.UnsupportedConditionError):
            transformed_gibbs_J_mol_metal(phase, self.database.reference_state, conditions, 7, 0)

    def test_physical_silicic_acid_reaction_and_full_formula_normalization(self):
        water = self.database.reference_state.water_gibbs_energy_J_mol
        rtln = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        for suffix, cation, nc, ns, nz, oxygen, g, gcat in [
            ('ca3-silicate', 'calcium-ca2', 3, 2, 1, 9, -4769295, -553580),
            ('nasicon-silicate', 'sodium-na', 4, 3, 2, 12, -5944005, -261905),
        ]:
            phase = next(x for x in self.system(cation, 'silica-sio2-component').species
                         if x.record_id == 'nea02g4-zr-' + suffix)
            self.assertEqual((phase.metal_count, phase.electrons_per_metal), (nz, 4))
            # Physical H4SiO4 basis: remove its four O and four H per Si.
            residual_o = oxygen - 4 * ns
            protons = 2 * residual_o + 4 * ns
            for ca, si in [(-6, -3), (-3, -6), (-1, -1)]:
                cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
                    pb.LigandActivity(cation, log10_free_activity=ca),
                    pb.LigandActivity('silica-sio2-component', log10_free_activity=si))))
                for pH, potential in [(0, -1), (7, 0), (14, 1)]:
                    expected = ((g - nc * (gcat + rtln * ca)
                                 - ns * (-1316600 + rtln * si) - residual_o * water
                                 - protons * rtln * pH) / nz
                                - 4 * FARADAY_C_MOL * potential)
                    self.assertAlmostEqual(float(transformed_gibbs_J_mol_metal(
                        phase, self.database.reference_state, cfg, pH, potential)), expected, places=7)

    def test_source_temperature_is_retained_and_not_selected_at_298K(self):
        for suffix in ['na-catapleiite', 'vlasovite', 'elpidite']:
            record = self.database.species_records(('nea02g4-zr-' + suffix,))[0]
            self.assertEqual(len(record.reported), 1)
            row = record.reported[0]
            self.assertEqual((row.temperature_K, row.pressure_bar), (323.15, 1))
            self.assertFalse(row.selected_as_recommended)
            self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
            system = self.system('sodium-na', 'silica-sio2-component')
            self.assertEqual(next(x.reason for x in system.excluded if x.record_id == record.record_id),
                             pb.ExclusionReason.GIBBS_ENERGY_UNAVAILABLE)

    def test_same_evaluation_alternative_keeps_reasoned_preference(self):
        record = self.database.species_records(('nea02g4-zr-nasicon-phosphate',))[0]
        rows = [x for x in record.reported if x.property == 'gibbs_energy_of_formation']
        self.assertEqual({x.value for x in rows}, {-4556968, -4565000})
        self.assertEqual([x.value for x in rows if x.selected_as_recommended], [-4556968])
        selection = self.database.selections[(record.record_id, 'gibbs_energy_of_formation')]
        self.assertEqual(selection.spread_J_mol, 8032)
        self.assertTrue(selection.needs_review)
        self.assertTrue(selection.basis.startswith('override:'))
        self.assertEqual({x.uncertainty for x in rows}, {20222, 20000})

    def test_reaction_and_phase_matching_include_all_components(self):
        system = self.system('sodium-na', 'phosphate-po4')
        phase = next(x for x in system.species if x.record_id == 'nea02g4-zr-nasicon-phosphate')
        metal = next(x for x in system.species if x.formula_ascii == 'Zr' and x.phase == 'solid')
        reaction = _reaction(metal, phase)
        self.assertIn('1/2 NaZr2P3O12', reaction)
        for key in phase.ligand_ids:
            self.assertIn(key, reaction)
        self.assertEqual(phase.protons_per_metal, 0)
        self.assertEqual(phase.electrons_per_metal, 4)
        self.assertNotEqual(pb.thermodynamic_species_equivalence_key(phase),
                            pb.thermodynamic_species_equivalence_key(metal))

    def test_component_validation_and_charge_derived_electrons(self):
        component = pb.BufferedComponent('free-cation', 3, 2, -553580)
        with self.assertRaises(FrozenInstanceError):
            component.count = 2
        for count in [0, -1, math.nan, math.inf]:
            with self.assertRaises(ValueError):
                pb.BufferedComponent('free-cation', count, 2, -553580)
        phase = next(x for x in self.system('calcium-ca2', 'silica-sio2-component').species
                     if x.record_id == 'nea02g4-zr-ca3-silicate')
        self.assertEqual(replace(phase, electron_coefficient_per_metal=None).electrons_per_metal, 4)
        with self.assertRaises(ValueError):
            replace(phase, additional_components=(phase.components[0],))
        with self.assertRaises(TypeError):
            replace(phase, additional_components=('silica-sio2-component',))

    def test_closed_zirconium_inventory_with_open_secondary_buffers(self):
        cfg = pb.PourbaixConditions(pH_points=7, eh_points=9,
            ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('sodium-na', log10_free_activity=-3),
                pb.LigandActivity('silica-sio2-component', log10_free_activity=-3))))
        system = self.system('sodium-na', 'silica-sio2-component')
        system = replace(system, species=tuple(x for x in system.species if not x.is_gas))
        result = pb.MassBalanceEngine(self.database).calculate_system(
            system, cfg, pb.TotalMetalConcentration(1e-4))
        np.testing.assert_allclose(result.dissolved_metal_mol_L
                                   + 1e-4 * result.precipitated_metal_fraction, 1e-4,
                                   rtol=1e-11, atol=1e-15)
        with self.database.connect() as connection:
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM species WHERE formula_ascii = 'Ca2ZrSi3O12'"
            ).fetchone()[0], 0)

    def test_policy_and_user_views_preserve_independent_components(self):
        for database in [pb.with_policy(self.database, self.database.policy),
                         pb.with_user_species(self.database, ())]:
            phase = next(x for x in database.load_system('Zr', ligand_ids=(
                'sodium-na', 'silica-sio2-component')).species
                if x.record_id == 'nea02g4-zr-nasicon-silicate')
            self.assertEqual(len(phase.components), 2)
