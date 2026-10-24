"""Original hydrosulfide variants, reference conventions and zinc adaptations."""
from dataclasses import replace
import json
import unittest

import numpy as np
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal


class HydrosulfideSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_original_and_revised_values_remain_distinct(self):
        record = self.database.species_records(('r15-au-auhs2-aqueous',))[0]
        rows = {(r.source.source_id, r.property): r for r in record.reported}
        self.assertAlmostEqual(rows['AkinfievZotov2001_R15_original', 'gibbs_energy_of_formation'].value,
                               1829 * 4.184)
        self.assertAlmostEqual(rows['AkinfievZotov2010_R15_revision', 'gibbs_energy_of_formation'].value,
                               3487 * 4.184)
        self.assertEqual(len(rows), 6)
        for prop in ['gibbs_energy_of_formation', 'absolute_entropy', 'enthalpy_of_formation']:
            choice = self.database.selections[record.record_id, prop].chosen
            self.assertEqual(choice.source_id, 'AkinfievZotov2001_R15_original')
            self.assertEqual(choice.evidence_class, 'E')
        self.assertTrue(all(r.uncertainty is None and r.temperature_K == 298.15 and
                            r.pressure_bar == 1 for r in record.reported))

    def test_disputed_2010_gold_enthalpy_stays_held(self):
        record = self.database.species_records(('r15-au-auhs-aqueous',))[0]
        self.assertEqual(len(record.reported), 5)
        self.assertFalse(any(r.property == 'enthalpy_of_formation' and
                             r.source.source_id == 'AkinfievZotov2010_R15_revision'
                             for r in record.reported))
        self.assertAlmostEqual(record.thermochemistry.formation_enthalpy_J_mol.value, 9122 * 4.184)
        holds = json.loads(self.database.metadata['R15_source_and_model_holds'])
        self.assertIn('11032', holds['R15c'])
        self.assertIn('55263', holds['R15c'])

    def test_derived_2001_silver_enthalpy_is_held(self):
        record = self.database.species_records(('r15-ag-aghs-aqueous',))[0]
        self.assertEqual(len(record.reported), 5)
        self.assertFalse(any(r.property == 'enthalpy_of_formation' and
                             r.source.source_id == 'AkinfievZotov2001_R15_original'
                             for r in record.reported))
        self.assertAlmostEqual(record.thermochemistry.formation_enthalpy_J_mol.value, 2722 * 4.184)
        self.assertEqual(self.database.selections[record.record_id, 'enthalpy_of_formation'].chosen.source_id,
                         'AkinfievZotov2010_R15_revision')
        self.assertEqual(self.database.selections[record.record_id, 'gibbs_energy_of_formation'].chosen.source_id,
                         'AkinfievZotov2001_R15_original')
        self.assertIn('4769', json.loads(self.database.metadata['R15_source_and_model_holds'])['R15g'])

    def test_new_zinc_anchor_uses_open_NBS_298K_enthalpy(self):
        record = self.database.species_records(('gfe-zn-zn-q+2-aqueous-aq',))[0]
        enthalpy = next(r for r in record.reported if r.property == 'enthalpy_of_formation')
        self.assertEqual((enthalpy.value, enthalpy.status, enthalpy.uncertainty), (-153890, 'verified', None))
        locator = json.loads(enthalpy.source.locator)
        self.assertEqual((locator['logical_csv_record'], locator['csv_column_zero_based']), (4023, 7))
        self.assertEqual(locator['source_state'], 'ao')
        self.assertEqual(locator['reuse']['doi'], '10.18434/M32124')

    def test_zinc_regression_retains_its_anchor_basis_and_extrapolation(self):
        record = self.database.species_records(('r15-zn-znhs2-aqueous',))[0]
        rtln = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        self.assertAlmostEqual(record.thermochemistry.gibbs_energy_J_mol.value,
                               -147060 + 2 * 12080 - rtln * 9.30)
        self.assertAlmostEqual(record.thermochemistry.formation_enthalpy_J_mol.value,
                               -153890 + 2 * (-17600) - 13700)
        self.assertAlmostEqual(record.thermochemistry.entropy_J_mol_K.value,
                               -112.1 + 2 * 62.8 + (-13700 + rtln * 9.30) / 298.15)
        for row in record.reported:
            locator = json.loads(row.source.locator)
            self.assertEqual((locator['printed_page'], locator['log10_beta_quoted_width']), (1249, .17))
            self.assertIn('extrapolated', locator['fit_range'])
            self.assertIsNone(row.uncertainty)
        rows = self.database.species_records(('r15-zn-znhs3-aqueous',))[0].reported
        self.assertEqual(json.loads(rows[0].source.locator)['log10_beta_quoted_width'], .05)

    def test_canonical_zinc_charges_and_dehydrated_formula(self):
        system = self.database.load_system('Zn', ligand_ids=('sulfide-s',))
        expected = {'r15-zn-znhs2-aqueous': (0, 2, 2), 'r15-zn-znhs3-aqueous': (-1, 3, 3),
                    'r15-zn-zns-hs-aqueous': (-1, 2, 1)}
        for phase in system.species:
            if phase.record_id not in expected:
                continue
            charge, sulfurs, hydrogens = expected.pop(phase.record_id)
            self.assertEqual((phase.charge, phase.components[0].count,
                              phase.core_oxygen_count, phase.core_hydrogen_count),
                             (charge, sulfurs, 0, hydrogens))
            self.assertEqual(replace(phase, electron_coefficient_per_metal=None).electrons_per_metal, 2)
        self.assertFalse(expected)
        holds = json.loads(self.database.metadata['R15_source_and_model_holds'])
        self.assertIn('16/23/30', holds['R15a'])
        self.assertIn('omitted', holds['R15b'])

    def test_HS_activity_conversion_uses_current_sulfide_reference(self):
        system = self.database.load_system('Ag', ligand_ids=('sulfide-s',))
        phase = next(s for s in system.species if s.record_id == 'r15-ag-aghs2-aqueous')
        reference = phase.components[0].gibbs_energy_J_mol
        self.assertEqual(reference, 120695)
        rtln = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        pka = (reference - 12080) / rtln
        self.assertAlmostEqual(pka, 19.028524733842467)
        for pH in [0, 7, 14]:
            cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('sulfide-s', log10_free_activity=-3 + pH - pka),)))
            expected = phase.gibbs_energy_J_mol - 2 * (12080 - 3 * rtln) - FARADAY_C_MOL * .2
            self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(
                phase, self.database.reference_state, cfg, pH, .2)), expected, places=7)

    def test_one_acid_pool_and_supported_primary_balances(self):
        pka = json.loads(self.database.metadata['R15_chemistry_support'])['pKa_HS_from_current_references']
        ligand = pb.LigandActivity('sulfide-s', total_unbound_mol_L=1e-3, acid_pKa=pka)
        log_activity = ligand.log10_activity(np.array([-300, 0, 7, 14, 300]))
        self.assertTrue(np.isfinite(log_activity).all())
        free = 10.0 ** log_activity
        np.testing.assert_allclose(free + (1e-3 - free), 1e-3)
        cfg = pb.PourbaixConditions(pH_min=9, pH_max=14, pH_points=7, U_points=9,
            ligand_activities=pb.LigandActivityModel((ligand,)))
        for sym in ['Ag', 'Cu', 'Au', 'Zn']:
            system = self.database.load_system(sym, ligand_ids=('sulfide-s',))
            self.assertTrue(any(s.record_id.startswith('r15-') for s in system.species))
            self.assertFalse(any(s.record_id.startswith('r15-') for s in self.database.load_system(sym).species))
            system = replace(system, species=tuple(s for s in system.species if not s.is_gas))
            for model in [pb.IdealActivityCoefficientModel(), pb.DaviesActivityCoefficientModel(.01)]:
                result = pb.MassBalanceEngine(self.database, activity_coefficient_model=model).calculate_system(
                    system, cfg, pb.TotalMetalConcentration(1e-6))
                np.testing.assert_allclose(result.dissolved_metal_mol_L + 1e-6 * result.precipitated_metal_fraction,
                                           1e-6, rtol=1e-10, atol=1e-15)

    def test_reuse_routes_and_existing_NEA_reference_are_separate(self):
        review = json.loads(self.database.metadata['R15_hydrosulfide_source_review'])
        self.assertEqual((review['original2001_observations'], review['revised2010_observations'],
                          review['local_PSI_Zn_observations'], review['new_open_NBS_Zn2_H']), (17, 11, 9, 1))
        self.assertEqual(len(json.loads(self.database.metadata['R15_hydrosulfide_observations'])), 38)
        self.assertIn('individual original numerical-facts', review['licence']['original_facts']['route'])
        self.assertIn('No open licence', review['licence']['original_facts']['original_licence'])
        chemistry = json.loads(self.database.metadata['R15_chemistry_support'])
        self.assertFalse(chemistry['runtime_changes_required'])
        self.assertTrue(chemistry['all_existing_Ni_HS_rows_and_reference_preserved'])
        self.assertIn('NEA2003', chemistry['reference_ligand']['source_id'])
        self.assertTrue(json.loads(self.database.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])


if __name__ == '__main__':
    unittest.main()
