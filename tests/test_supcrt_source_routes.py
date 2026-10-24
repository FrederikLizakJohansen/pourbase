"""Original mineral evaluations, formula scales and independent reservoirs."""
from contextlib import closing
from dataclasses import replace
import json
import unittest

import numpy as np
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal


class SUPCRTSourceRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_original_standard_cells_keep_property_specific_intervals(self):
        record = self.database.species_records(('r12-mg-enstatite',))[0]
        thermo = record.thermochemistry
        self.assertEqual((thermo.gibbs_energy_J_mol.value, thermo.formation_enthalpy_J_mol.value,
                          thermo.entropy_J_mol_K.value), (-1458300, -1545600, 66.3))
        self.assertEqual((thermo.gibbs_energy_J_mol.uncertainty,
                          thermo.formation_enthalpy_J_mol.uncertainty), (1600, 1500))
        for row in record.reported:
            self.assertEqual((row.temperature_K, row.pressure_bar), (298.15, 1))
            locator = json.loads(row.source.locator)
            self.assertEqual((locator['table'], locator['printed_page'], locator['pdf_page']),
                             ('2', 34, 40))
            self.assertTrue(locator['ancestry_reference_numbers'])
            self.assertIn('public-domain', locator['reuse']['reuse_basis'])
            self.assertEqual(self.database.selections[record.record_id, row.property].chosen.evidence_class, 'B')

    def test_nickel_polymorphs_use_complete_two_metal_formula_units(self):
        phases = self.database.load_system('Ni', ligand_ids=('silica-sio2-component',)).species
        a, b = [next(s for s in phases if s.record_id == rid)
                for rid in ['r12-ni-liebenbergite', 'r12-ni-ni2sio4-spinel']]
        self.assertEqual((a.metal_count, a.components[0].count, a.core_oxygen_count), (2, 1, 2))
        self.assertEqual((a.electrons_per_metal, a.protons_per_metal), (2, 2))
        self.assertEqual(replace(a, electron_coefficient_per_metal=None).electrons_per_metal, 2)
        self.assertEqual(b.gibbs_energy_J_mol - a.gibbs_energy_J_mol, 8000)
        cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity('silica-sio2-component', log10_free_activity=-3),)))
        difference = (standard_transformed_gibbs_J_mol_metal(b, self.database.reference_state, cfg, 7, 0)
                      - standard_transformed_gibbs_J_mol_metal(a, self.database.reference_state, cfg, 7, 0))
        self.assertAlmostEqual(float(difference), 4000)
        self.assertNotIn(a.record_id, {s.record_id for s in self.database.load_system('Ni').species})

    def test_diopside_needs_calcium_and_physical_silicic_acid(self):
        rid = 'r12-mg-diopside'
        for components in [(), ('calcium-ca2',), ('silica-sio2-component',)]:
            self.assertNotIn(rid, {s.record_id for s in self.database.load_system(
                'Mg', ligand_ids=components).species})
        phase = next(s for s in self.database.load_system('Mg', ligand_ids=(
            'calcium-ca2', 'silica-sio2-component')).species if s.record_id == rid)
        self.assertEqual((phase.metal_count, phase.electrons_per_metal, phase.protons_per_metal), (1, 2, 4))
        rtln = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        for calcium, silica in [(-6, -3), (-3, -6), (0, 0)]:
            cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('calcium-ca2', log10_free_activity=calcium),
                pb.LigandActivity('silica-sio2-component', log10_free_activity=silica))))
            for pH, potential in [(0, -1), (7, 0), (14, 1)]:
                # Mg + Ca2+ + 2H4SiO4 = diopside + 2H2O + 4H+ + 2e-.
                expected = (-3026800 - (-553580 + rtln * calcium)
                    - 2 * (-1316600 + rtln * silica)
                    + 2 * self.database.reference_state.water_gibbs_energy_J_mol
                    - 4 * rtln * pH - 2 * FARADAY_C_MOL * potential)
                self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(
                    phase, self.database.reference_state, cfg, pH, potential)), expected, places=7)

    def test_named_aluminium_and_silica_phases_are_distinct(self):
        records = self.database.species_records(('r11v-al-kaolinite', 'r12-al-dickite', 'r12-al-halloysite'))
        self.assertEqual({r.formula_ascii for r in records}, {'Al2Si2O5(OH)4'})
        self.assertEqual({r.phase_identity.status for r in records}, {'resolved'})
        self.assertEqual(len({r.thermochemistry.gibbs_energy_J_mol.value for r in records}), 3)
        for rid in ['r12-si-coesite', 'r12-si-stishovite', 'r12-ni-ni2sio4-spinel']:
            record = self.database.species_records((rid,))[0]
            self.assertTrue(any(w.type == 'r12_metastable_pressure_phase_scope' for w in record.warnings))
        coesite = self.database.species_records(('r12-si-coesite',))[0]
        self.assertEqual(coesite.thermochemistry.gibbs_energy_J_mol.value, -852500)

    def test_primary_inventory_is_conserved_with_buffered_secondary_elements(self):
        for symbol, components in [('Ni', ('silica-sio2-component',)),
                                   ('Mg', ('calcium-ca2', 'silica-sio2-component')),
                                   ('Al', ('sodium-na', 'silica-sio2-component'))]:
            cfg = pb.PourbaixConditions(pH_points=7, U_points=9,
                ligand_activities=pb.LigandActivityModel(tuple(pb.LigandActivity(
                    key, log10_free_activity=-3) for key in components)))
            system = self.database.load_system(symbol, ligand_ids=components)
            system = replace(system, species=tuple(s for s in system.species if not s.is_gas))
            result = pb.MassBalanceEngine(self.database).calculate_system(
                system, cfg, pb.TotalMetalConcentration(1e-4))
            np.testing.assert_allclose(result.dissolved_metal_mol_L
                + 1e-4 * result.precipitated_metal_fraction, 1e-4, rtol=1e-11, atol=1e-15)

    def test_inventory_reuse_and_adjacent_extension_scopes_are_separate(self):
        review = json.loads(self.database.metadata['R12_SUPCRT_version_review'])
        self.assertEqual(review['inventory']['variants'], 8)
        self.assertEqual(review['inventory']['record_representations'], 11350)
        self.assertEqual(review['inventory']['property_slots'], 34050)
        self.assertEqual(review['named_SUPCRT_phase_routes'], 20)
        self.assertEqual(len(review['adjacent_original_USGS_phases']), 5)
        self.assertEqual(len(review['admitted_phase_rows']), 25)
        self.assertIn('R06', json.loads(self.database.metadata['R12_source_and_scientific_holds']))
        with closing(self.database.connect()) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM reported_thermochemistry "
                "WHERE source_id='R12_USGS1995_silicates'").fetchone()[0], 75)
