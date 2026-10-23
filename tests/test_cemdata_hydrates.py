"""Original hydrate properties, source discrepancies and independent reservoirs."""
from dataclasses import replace
import json
import unittest

import numpy as np
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal


class CemdataHydrateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_original_values_keep_printed_precision_and_estimate_status(self):
        for rid, values in [
            ('r09-al-ettringite13', (-10540600, -11530300, 1960.4)),
            ('r09-fe-fe-friedel-original', (-5900100, -6528000, 1286)),
            ('r09-mg-m075sh', (-3218430, -3507520, 270)),
        ]:
            record = self.database.species_records((rid,))[0]
            self.assertEqual((record.thermochemistry.gibbs_energy_J_mol.value,
                              record.thermochemistry.formation_enthalpy_J_mol.value,
                              record.thermochemistry.entropy_J_mol_K.value), values)
            for observation in record.reported:
                self.assertEqual(observation.status, 'source_verified_estimate')
                self.assertIsNone(observation.uncertainty)
                self.assertEqual((observation.temperature_K, observation.pressure_bar), (298.15, 1))
                locator = json.loads(observation.source.locator)
                self.assertEqual(locator['table'], 'Table 1')
                self.assertIn('manuscript_line', locator)
                self.assertEqual(self.database.selections[rid, observation.property].chosen.evidence_class, 'E')

    def test_undefined_and_inherited_thermal_proxies_are_not_imported(self):
        for rid in ['r09-al-aloham', 'r09-fe-feoohmic', 'r09-si-amor-sl']:
            record = self.database.species_records((rid,))[0]
            self.assertEqual([r.property for r in record.reported], ['gibbs_energy_of_formation'])
            self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
            self.assertIsNone(record.thermochemistry.formation_enthalpy_J_mol.value)
        crystalline = self.database.species_records(('gfe-al-al-oh-3-q+0-solid-gibbsite',))[0]
        self.assertEqual(crystalline.phase_detail, 'gibbsite')

    def test_every_component_is_required_for_mixed_hydrogarnet(self):
        rid = 'r09-fe-c3afs0-84h4-32'
        components = ('calcium-ca2', 'aluminate-aloh4', 'silica-sio2-component')
        for missing in components:
            system = self.database.load_system('Fe', ligand_ids=tuple(l for l in components if l != missing))
            self.assertEqual(next(r.reason for r in system.excluded if r.record_id == rid),
                             pb.ExclusionReason.LIGAND_NOT_SELECTED)
        phase = next(s for s in self.database.load_system('Fe', ligand_ids=components).species if s.record_id == rid)
        self.assertEqual({c.ligand_id: c.count for c in phase.components},
                         {'calcium-ca2': 3, 'aluminate-aloh4': 1, 'silica-sio2-component': .84})
        self.assertAlmostEqual(phase.core_oxygen_count, 6.32)
        self.assertAlmostEqual(phase.core_hydrogen_count, 4.64)
        self.assertAlmostEqual(replace(phase, electron_coefficient_per_metal=None).electrons_per_metal, 3)
        cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity('calcium-ca2', log10_free_activity=-3),)))
        with self.assertRaises(pb.UnsupportedConditionError):
            standard_transformed_gibbs_J_mol_metal(phase, self.database.reference_state, cfg, 7, 0)

    def test_full_hydrate_water_and_electron_balance(self):
        components = ('calcium-ca2', 'sulfate-so4')
        phase = next(s for s in self.database.load_system('Al', ligand_ids=components).species
                     if s.record_id == 'r09-al-ettringite')
        self.assertEqual((phase.metal_count, phase.core_oxygen_count, phase.core_hydrogen_count), (2, 38, 64))
        self.assertEqual(phase.electrons_per_metal, 3)
        for ca, sulfate in [(-6, -3), (-3, -6)]:
            cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('calcium-ca2', log10_free_activity=ca),
                pb.LigandActivity('sulfate-so4', log10_free_activity=sulfate))))
            rt = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
            refs = {c.ligand_id: c.gibbs_energy_J_mol for c in phase.components}
            expected = (-15205940 - 6 * (refs['calcium-ca2'] + rt * ca)
                        - 3 * (refs['sulfate-so4'] + rt * sulfate)
                        - 38 * self.database.reference_state.water_gibbs_energy_J_mol - 12 * rt * 7) / 2
            expected -= 3 * FARADAY_C_MOL * .5
            self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(
                phase, self.database.reference_state, cfg, 7, .5)), expected, places=7)

    def test_hydration_states_and_source_holds_remain_distinct(self):
        records = self.database.species_records(tuple('r09-al-' + name for name in [
            'ettringite', 'ettringite30', 'ettringite13', 'ettringite9']))
        self.assertEqual(len({r.formula_ascii for r in records}), 4)
        self.assertTrue(all('amorphous' in r.phase_detail for r in records if r.record_id.endswith(('13', '9'))))
        review = json.loads(self.database.metadata['R09_Cemdata18_source_review'])
        self.assertEqual(review['finite_inventory']['total_property_slots'], 822)
        self.assertEqual(len(review['accepted_phase_rows']), 53)
        holds = json.loads(self.database.metadata['R09_Cemdata18_source_holds'])
        self.assertIn('nitrite', holds)
        self.assertIn('solid_solution', holds)

    def test_buffered_magnesium_balance_conserves_primary_inventory(self):
        components = ('aluminate-aloh4', 'carbonate-co3', 'silica-sio2-component')
        system = self.database.load_system('Mg', ligand_ids=components)
        system = replace(system, species=tuple(s for s in system.species if not s.is_gas))
        cfg = pb.PourbaixConditions(pH_points=7, U_points=9,
            ligand_activities=pb.LigandActivityModel(tuple(
                pb.LigandActivity(l, log10_free_activity=-3) for l in components)))
        result = pb.MassBalanceEngine(self.database).calculate_system(system, cfg, pb.TotalMetalConcentration(1e-4))
        np.testing.assert_allclose(result.dissolved_metal_mol_L + 1e-4 * result.precipitated_metal_fraction,
                                   1e-4, rtol=1e-11, atol=1e-15)
