"""Full-formula NEA oligomers, mixed solids and retained policy alternatives."""
from dataclasses import replace
import json
import unittest
import numpy as np
import pourbase as pb
from pourbase.constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature

SID = 'NEA_OECD_20261025_ancillary_R14e2'

class NEARemainingAncillaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()

    def test_own_phosphate_evaluation_and_source_uncertainties(self):
        rid = 'gfe-p-po4-q-3-aqueous-aq'
        record = self.db.species_records((rid,))[0]
        rows = [r for r in record.reported if r.source and r.source.source_id == SID]
        self.assertEqual({r.property: (r.value, r.uncertainty) for r in rows}, {
            'gibbs_energy_of_formation': (-1025491, 1576),
            'enthalpy_of_formation': (-1284400, 4085), 'absolute_entropy': (-220.970, 12.846)})
        for row in rows:
            ev = json.loads(row.source.locator)
            self.assertEqual((ev['printed_page'], ev['pdf_page']), (44, 86))
            self.assertIn('1992', ev['original_evaluation'])
            self.assertFalse(ev['table_cell_is_bold_CODATA_copy'])
            self.assertIn('95%', ev['uncertainty_convention'])
            self.assertEqual(self.db.selections[rid, row.property].chosen.evidence_class, 'A')
        self.assertGreater(len(record.reported), 3)

    def test_silicate_trimer_is_kept_as_a_trimer(self):
        rid = 'r14e2-si-h3si3o9-q-3-cyclic-aqueous'
        record = self.db.species_records((rid,))[0]
        self.assertEqual((record.formula_ascii, record.charge), ('H3Si3O9', -3))
        phase = next(s for s in self.db.load_system('Si').species if s.record_id == rid)
        self.assertEqual((phase.metal_count, phase.core_oxygen_count, phase.core_hydrogen_count,
                          phase.protons_per_metal, phase.electrons_per_metal), (3, 9, 3, 5, 4))
        cfg = pb.PourbaixConditions()
        expected = (-3053100 - 9 * self.db.reference_state.water_gibbs_energy_J_mol) / 3
        expected -= 5 * GAS_CONSTANT_J_MOL_K * 298.15 * LN_10 * 7 + 4 * FARADAY_C_MOL
        self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(
            phase, self.db.reference_state, cfg, 7, 1)), expected, places=7)

    def test_G_only_oligomers_have_no_inferred_thermal_properties(self):
        for rid in ['r14e2-si-h4si2o7-q-2-aqueous', 'r14e2-si-h5si2o7-q-1-aqueous',
                    'r14e2-si-h3si3o9-q-3-cyclic-aqueous', 'r14e2-si-h5si3o10-q-3-linear-aqueous',
                    'r11j-si-h4si4o12-q-4-aqueous', 'r14e2-si-h5si4o12-q-3-aqueous']:
            record = self.db.species_records((rid,))[0]
            self.assertIsNone(record.thermochemistry.formation_enthalpy_J_mol.value)
            self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
            self.assertNotIn(rid, {s.record_id for s in at_temperature(self.db, 323.15).load_system('Si').species})

    def test_independent_new_silicate_G_survives_existing_override(self):
        rid = 'gfe-si-h3sio4-q-1-aqueous-aq'
        selection = self.db.selections[rid, 'gibbs_energy_of_formation']
        self.assertEqual(selection.chosen.value, -1252304)
        self.assertTrue(selection.basis.startswith('override:'))
        candidate = next(c for c in selection.candidates if c.source_id == SID)
        self.assertEqual((candidate.value, candidate.evidence_class), (-1253236, 'A'))
        self.assertEqual(self.db.policy.fingerprint, '544b421b7f1c')

    def test_fluorapatite_uses_both_references_and_full_formula_unit(self):
        rid = 'r14e2-ca-fluorapatite'
        self.assertNotIn(rid, {s.record_id for s in self.db.load_system('Ca', ligand_ids=('phosphate-po4',)).species})
        phase = next(s for s in self.db.load_system('Ca', ligand_ids=('phosphate-po4', 'fluoride-f')).species if s.record_id == rid)
        self.assertEqual((phase.metal_count, phase.core_oxygen_count, phase.core_hydrogen_count,
                          phase.protons_per_metal, phase.electrons_per_metal), (5, 0, 0, 0, 2))
        self.assertEqual({c.ligand_id: c.count for c in phase.components}, {'phosphate-po4': 3, 'fluoride-f': 1})
        cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity('phosphate-po4', log10_free_activity=-6),
            pb.LigandActivity('fluoride-f', log10_free_activity=-3))))
        rt = GAS_CONSTANT_J_MOL_K * 298.15 * LN_10
        expected = (phase.gibbs_energy_J_mol - sum(c.count * (c.gibbs_energy_J_mol +
                    rt * (-6 if c.ligand_id == 'phosphate-po4' else -3)) for c in phase.components)) / 5
        self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(
            phase, self.db.reference_state, cfg, 7, 0)), expected, places=7)

    def test_borate_half_formula_and_structural_water_are_retained(self):
        system = self.db.load_system('B', ligand_ids=('calcium-ca2',))
        for rid, formula, oxygen, hydrogen, g in [
            ('r14e2-b-colemanite', 'CaB3O4(OH)3(H2O)', 8, 5, -3167438),
            ('r14e2-b-inyoite', 'CaB3O3(OH)5(H2O)4', 12, 13, -4116064)]:
            record = self.db.species_records((rid,))[0]
            phase = next(s for s in system.species if s.record_id == rid)
            self.assertEqual(record.formula_ascii, formula)
            self.assertEqual((phase.metal_count, phase.core_oxygen_count, phase.core_hydrogen_count,
                              phase.components[0].count, phase.protons_per_metal), (3, oxygen, hydrogen, 1, 11 / 3))
            self.assertAlmostEqual(phase.gibbs_energy_J_mol, g)

    def test_closed_Si_excludes_oligomers_and_mixed_solid_primary_balances(self):
        for sym, lids in [('Si', ()), ('B', ('calcium-ca2',)), ('Ca', ('phosphate-po4', 'fluoride-f'))]:
            cfg = pb.PourbaixConditions(pH_points=7, U_points=9,
                ligand_activities=pb.LigandActivityModel(tuple(pb.LigandActivity(l, log10_free_activity=-3)
                                                             for l in lids)) if lids else None)
            system = self.db.load_system(sym, ligand_ids=lids)
            system = replace(system, species=tuple(s for s in system.species if not s.is_gas))
            for model in [pb.IdealActivityCoefficientModel(), pb.DaviesActivityCoefficientModel(.01)]:
                result = pb.MassBalanceEngine(self.db, activity_coefficient_model=model).calculate_system(
                    system, cfg, pb.TotalMetalConcentration(1e-3))
                np.testing.assert_allclose(result.dissolved_metal_mol_L + 1e-3 * result.precipitated_metal_fraction,
                                           1e-3, rtol=1e-10, atol=1e-15)
                if sym == 'Si':
                    polynuclear = {s.record_id for s in system.species if s.is_aqueous and s.metal_count != 1}
                    self.assertEqual(len(polynuclear), 6)
                    self.assertFalse(polynuclear & {s.record_id for s in result.system.species})
                    excluded = {s.record_id: s.reason for s in result.system.excluded}
                    self.assertTrue(all(excluded[rid] == pb.ExclusionReason.POLYNUCLEAR_AQUEOUS
                                        for rid in polynuclear))

    def test_phase_and_source_holds_remain_separate(self):
        glass = self.db.species_records(('r14e2-si-vitreous',))[0]
        self.assertIsNone(glass.phase_identity.spacegroup_symbol)
        self.assertEqual(glass.phase_identity.identified_phase, 'SiO2(vit)')
        self.assertIsNotNone(self.db.species_records(('r09-si-amor-sl',))[0])
        self.assertEqual(len(json.loads(self.db.metadata['R14e2_NEA2024_observations'])), 60)
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])
        self.assertEqual(json.loads(self.db.metadata['R16_Thermoddem_rights_review'])['rights']['bulk_data_status'], 'held_redistribution_rights')

if __name__ == '__main__':
    unittest.main()
