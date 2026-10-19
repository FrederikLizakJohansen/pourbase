"""Original Pd reactions retain source media, revised fits and physical formulas."""
from dataclasses import replace
import json
import math
import unittest
import numpy as np
import pourbase as pb
from pourbase.engine import transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature

G = 'gibbs_energy_of_formation'
RTL = 8.31446261815324 * 298.15 * math.log(10)


class PalladiumSourceRoutesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()
        cls.derivations = json.loads(cls.db.metadata['R11g_palladium_derivations'])

    def test_all_eight_reactions_reconstruct_with_their_original_inputs(self):
        self.assertEqual(len(self.derivations), 8)
        for d in self.derivations:
            record = self.db.species_records((d['record_id'],))[0]
            source = ('pourbase_R11g_local_Pd_formation_G' if d['NH3_input'] else
                      'R11g_local_hydrolysis_2023' if d['source_id'].startswith('HummelThoenen') else
                      'R11g_local_hydrolysis_2002')
            value = next(v for v in record.reported if v.source.source_id == source)
            inputs = (len(d['source_step_log10K']) * -26500 if d['NH3_input'] else
                      (3 if 'oh-3' in record.record_id else 2) * -237129)
            self.assertAlmostEqual(-(value.value - 176500 - inputs) / RTL, d['source_log10K'])
            self.assertEqual(value.status, 'source_verified_estimate')
            self.assertIsNone(value.uncertainty)
            self.assertEqual((value.temperature_K, value.pressure_bar), (298.15, 1))

    def test_substantive_hydrolysis_revision_keeps_old_observations_and_explicit_policy_reason(self):
        for rid, older, newer in [('r11g-pd-pd-oh-2-aqueous', -4, -4.6),
                                  ('r11g-pd-pd-oh-3-q-1-aqueous', -15.5, -16.6)]:
            record = self.db.species_records((rid,))[0]
            self.assertEqual(len(record.reported), 2)
            selected = self.db.selections[(rid, G)].chosen
            self.assertEqual(selected.source_id, 'R11g_local_hydrolysis_2023')
            self.assertTrue(self.db.selections[(rid, G)].needs_review == (abs(newer - older) * RTL > 5000))
            override = next(o for o in self.db.policy.overrides if o.record_id == rid)
            self.assertIn('controlling phase', override.reason)
            self.assertIn('revision', override.reason)
        # The original-publication tie-break assumes repeated evaluations by the same authors.
        unreviewed = replace(self.db.policy, overrides=tuple(o for o in self.db.policy.overrides
                                                           if not o.record_id.startswith('r11g-')))
        self.assertEqual(pb.ThermodynamicDatabase(self.db.path, policy=unreviewed).selections[
            ('r11g-pd-pd-oh-3-q-1-aqueous', G)].chosen.source_id, 'R11g_local_hydrolysis_2002')

    def test_original_ammine_steps_keep_finite_medium_and_original_widths(self):
        rows = [d for d in self.derivations if d['NH3_input']]
        self.assertEqual([d['source_log10K'] for d in rows], [9.6, 18.5, 26, 32.8])
        for n, d in enumerate(rows, 1):
            self.assertEqual(d['source_step_log10K'], [9.6, 8.9, 7.5, 6.8][:n])
            self.assertEqual(d['source_step_width'], .1)
            self.assertIsNone(d['source_reaction_width'])
            self.assertIn('finite-medium', d['scientific_qualification'])
            self.assertIn('specific interactions', d['scientific_qualification'])
        basis = json.loads(self.db.metadata['source_reuse_R11g_original_palladium'])
        self.assertIn('not a measured I=0', basis['Rasmussen_source']['standard_state'])
        with self.db.connect() as c:
            ref = c.execute("SELECT * FROM ligands WHERE ligand_id='ammonia-nh3'").fetchone()
        self.assertEqual((ref['formula_ascii'], ref['charge'], ref['gibbs_energy_J_mol']), ('NH3', 0, -26500))

    def test_full_hydroxo_formula_and_native_water_notation_agree(self):
        system = self.db.load_system('Pd')
        s = next(s for s in system.species if s.record_id == 'r11g-pd-pd-oh-3-q-1-aqueous')
        self.assertEqual((s.formula_ascii, s.charge, s.core_oxygen_count,
                          s.core_hydrogen_count, s.electrons_per_metal, s.protons_per_metal),
                         ('Pd(OH)3', -1, 3, 3, 2, 3))
        native_G = s.gibbs_energy_J_mol + 237129
        self.assertAlmostEqual(-(native_G - 176500 + 2 * 237129) / RTL, -16.6)
        cfg = pb.PourbaixConditions()
        expected = s.gibbs_energy_J_mol + 3 * 237129 - 3 * RTL * 7 - 2 * 96485.33212 * .2
        expected += RTL * cfg.aqueous_activities.log10_activity_for(s.record_id, s.species, s.formula_ascii)
        self.assertAlmostEqual(float(transformed_gibbs_J_mol_metal(s, self.db.reference_state,
                                                               cfg, 7, .2)), expected, places=3)

    def test_ammine_activity_response_keeps_hydrogens_in_neutral_ligand(self):
        system = self.db.load_system('Pd', ligand_ids=('ammonia-nh3',))
        for n in range(1, 5):
            s = next(s for s in system.species if s.record_id == f'r11g-pd-pd-nh3-{n}-q+2-aqueous')
            self.assertEqual((s.ligand_count, s.ligand_charge, s.core_hydrogen_count,
                              s.electrons_per_metal, s.protons_per_metal), (n, 0, 0, 2, 0))
            energies = []
            for lognh in (-7, -5):
                cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
                    pb.LigandActivity('ammonia-nh3', log10_free_activity=lognh),)))
                energies.append(float(transformed_gibbs_J_mol_metal(s, self.db.reference_state, cfg, 7, 0)))
            self.assertAlmostEqual(energies[1] - energies[0], -2 * n * RTL)

    def test_dilute_closed_pd_balance_preserves_thermal_and_crystalline_gap_scope(self):
        cfg = pb.PourbaixConditions(pH_points=7, eh_points=9,
            ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('ammonia-nh3', log10_free_activity=-5),
                pb.LigandActivity('chloride-cl', log10_free_activity=-3))))
        for model in (pb.IdealActivityCoefficientModel(), pb.DaviesActivityCoefficientModel(.01)):
            m = pb.MassBalanceEngine(self.db, activity_coefficient_model=model).calculate(
                'Pd', cfg, pb.TotalMetalConcentration(1e-7))
            np.testing.assert_allclose(m.dissolved_metal_mol_L + 1e-7 * m.precipitated_metal_fraction,
                                       1e-7, rtol=1e-11, atol=1e-15)
        thermal = at_temperature(self.db, 323.15).load_system('Pd', ligand_ids=('ammonia-nh3',))
        self.assertFalse(any(s.record_id.startswith('r11g-') for s in thermal.species))
        gap = self.db.species_records(('gfe-pd-pdo2-q+0-solid-solid',))[0]
        self.assertIsNone(gap.thermochemistry.gibbs_energy_J_mol.value)
        self.assertNotIn('r11g-pd-pd-oh-2-amorphous', {s.record_id for s in self.db.load_system('Pd').species})
