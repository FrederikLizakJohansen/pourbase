"""Eu routes retain full formulas, reaction alternatives and hydration holds."""
import json
import math
import unittest
import numpy as np
import pourbase as pb
from pourbase.engine import transformed_gibbs_J_mol_metal
from pourbase.temperature import at_temperature
from pourbase.user_data import formula_counts

G = 'gibbs_energy_of_formation'
RTL = 8.31446261815324 * 298.15 * math.log(10)
CARB = 'r11h-eu-euohco3-crystalline'
SIL = 'r11h-eu-euh3sio4-q+2-aqueous'


class EuropiumSourceRoutesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()
        cls.derivations = json.loads(cls.db.metadata['R11h_europium_derivations'])

    def test_six_original_reactions_reconstruct_and_preserve_prior_choices(self):
        self.assertEqual(len(self.derivations), 6)
        for d in self.derivations:
            record = self.db.species_records((d['record_id'],))[0]
            value = next(x for x in record.reported if x.value_id.endswith(':r11h-' + d['variant']))
            reaction = value.value - d['Eu_input']['value_J_mol'] - sum(
                x['coefficient'] * x['value_J_mol'] for x in d['other_inputs'])
            self.assertAlmostEqual(reaction / RTL * (-1 if 'silicate' in d['variant'] else 1),
                                   d['source_log10K'])
            self.assertEqual(value.status, 'source_verified_estimate')
            self.assertIsNone(value.uncertainty)
            self.assertEqual((value.temperature_K, value.pressure_bar), (298.15, 1))
        for rid, source in [('gfe-eu-eu-oh-3-q+0-solid-crystalline',
                             'Jordan_2024_EuIII_Hydrolysis_EuOH3_cr'),
                            ('gfe-eu-euf3-q+0-solid-crystalline-trifluoride',
                             'EuF3_R05_Migdisov2009_Table2_NBS_reference_gf')]:
            self.assertEqual(self.db.selections[(rid, G)].chosen.source_id, source)

    def test_hydroxycarbonate_keeps_oh_in_core_and_reconstructs_acid_dissolution(self):
        s = next(s for s in self.db.load_system('Eu', ligand_ids=('carbonate-co3',)).species
                 if s.record_id == CARB)
        self.assertEqual((s.formula_ascii, s.core_oxygen_count, s.core_hydrogen_count,
                          s.ligand_count, s.ligand_charge, s.electrons_per_metal,
                          s.protons_per_metal), ('EuOHCO3', 1, 1, 1, -2, 3, 1))
        self.assertEqual(sum(formula_counts(s.formula_ascii).values()), 7)
        logkw = (-157244 + 237129) / RTL
        acid_logk = -(-574100 - 527810 - 237129 - s.gibbs_energy_J_mol) / RTL
        self.assertAlmostEqual(acid_logk, -21.7 + logkw)
        cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
            pb.LigandActivity('carbonate-co3', log10_free_activity=-5),)))
        expected = s.gibbs_energy_J_mol + 237129 + 527810 + 5 * RTL - 7 * RTL
        self.assertAlmostEqual(float(transformed_gibbs_J_mol_metal(s, self.db.reference_state,
                                                               cfg, 7, 0)), expected)

    def test_eu_specific_and_pooled_silicate_variants_keep_original_reference_basis(self):
        rows = [d for d in self.derivations if d['record_id'] == SIL]
        self.assertEqual([d['source_log10K'] for d in rows], [7.31, 7.8])
        self.assertEqual([d['source_reaction_width'] for d in rows], [.2, .5])
        record = self.db.species_records((SIL,))[0]
        self.assertEqual(len(record.reported), 2)
        self.assertEqual(self.db.selections[(SIL, G)].chosen.source_id,
                         'R11h_local_Eu_silicate_specific_2023')
        s = next(s for s in self.db.load_system('Eu', ligand_ids=('silicate-h3sio4',)).species
                 if s.record_id == SIL)
        self.assertEqual((s.core_oxygen_count, s.core_hydrogen_count, s.ligand_charge,
                          s.charge, s.electrons_per_metal, s.protons_per_metal), (0, 0, -1, 2, 3, 0))
        self.assertEqual(sum(formula_counts(s.formula_ascii).values()), 9)
        native_complex = s.gibbs_energy_J_mol + 237129
        native_ligand = -1252304 + 237129
        self.assertAlmostEqual(-(native_complex + 574100 - native_ligand) / RTL, 7.31)

    def test_precise_holds_and_source_qualifications_remain_separate(self):
        basis = json.loads(self.db.metadata['source_reuse_R11h_original_europium'])
        self.assertIn('not obtained', basis['holds']['amorphous_hydroxide'])
        self.assertIn('n not established', basis['holds']['simple_carbonate'])
        self.assertIn('2023 rejects', basis['holds']['old_silicate'])
        with self.db.connect() as c:
            new = list(c.execute("SELECT record_id, formula_ascii FROM species WHERE record_id LIKE 'r11h-%'"))
        self.assertEqual({r['record_id'] for r in new}, {CARB, SIL})
        self.assertNotIn('Eu2(CO3)3', {r['formula_ascii'] for r in new})

    def test_buffered_europium_balance_and_temperature_scope(self):
        # The isolated release and concurrent workspace expose their current potential-axis names.
        point_name = 'U_points' if 'U_points' in pb.PourbaixConditions.__dataclass_fields__ else 'eh_points'
        cfg = pb.PourbaixConditions(pH_points=7, **{point_name: 9},
            ligand_activities=pb.LigandActivityModel((
                pb.LigandActivity('carbonate-co3', log10_free_activity=-5),
                pb.LigandActivity('silicate-h3sio4', log10_free_activity=-5))))
        for model in (pb.IdealActivityCoefficientModel(), pb.DaviesActivityCoefficientModel(.01)):
            m = pb.MassBalanceEngine(self.db, activity_coefficient_model=model).calculate(
                'Eu', cfg, pb.TotalMetalConcentration(1e-6))
            np.testing.assert_allclose(m.dissolved_metal_mol_L + 1e-6 * m.precipitated_metal_fraction,
                                       1e-6, rtol=1e-11, atol=1e-15)
        thermal = at_temperature(self.db, 323.15).load_system(
            'Eu', ligand_ids=('carbonate-co3', 'silicate-h3sio4'))
        self.assertFalse(any(s.record_id.startswith('r11h-') for s in thermal.species))
