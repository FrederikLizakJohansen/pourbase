"""Cumulative calorimetric basis and qualified standard-state AlF adaptations."""
import json
import math
import unittest

import support  # noqa: F401
import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K
from pourbase.temperature import at_temperature

G = 'gibbs_energy_of_formation'
H = 'enthalpy_of_formation'
S = 'absolute_entropy'
AL = 'gfe-al-al-q+3-aqueous-aq'
FIDS = {5: 'r11l-al-alf5-q-2-aqueous', 6: 'r11l-al-alf6-q-3-aqueous'}
SID = 'R11r_LatimerJolly1953_qualified_AlF_thermal'


class AluminiumFluorideThermalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()

    def test_cumulative_enthalpies_and_entropy_reconstruct_the_existing_g_model(self):
        rtl = GAS_CONSTANT_J_MOL_K * 298.15 * math.log(10)
        hs = {}
        for n, calories in ((5, 1650), (6, 100)):
            rid = FIDS[n]
            h = self.db.selections[rid, H].chosen
            s = self.db.selections[rid, S].chosen
            hs[n] = h.value
            self.assertEqual(h.source_id, SID)
            self.assertEqual(h.evidence_class, 'E')
            self.assertIsNone(h.uncertainty)
            reaction_h = h.value + 531000 + n * 332630
            reaction_s = s.value + 321.7 + n * 13.8
            self.assertAlmostEqual(reaction_h, calories * 4.184)
            self.assertAlmostEqual(-(reaction_h - 298.15 * reaction_s) / rtl, 20.29)
            self.assertEqual(self.db.selections[rid, G].chosen.source_id,
                             'R11l_local_Nagra2023_original_models')
        self.assertAlmostEqual(hs[6] - hs[5] + 332630, -1550 * 4.184)

    def test_open_al_enthalpy_keeps_the_previous_evaluation_and_controls_thermal_derivative(self):
        h = self.db.selections[AL, H].chosen
        self.assertEqual((h.value, h.evidence_class), (-531000, 'B'))
        old = next(r for r in self.db.species_records((AL,))[0].reported
                   if r.value_id == AL + ':hf:preferred')
        self.assertEqual((old.value, old.uncertainty), (-538350, 862))
        self.assertFalse(old.selected_as_recommended)
        for t in (323.15, 373.15):
            ion = next(s for s in at_temperature(self.db, t).load_system('Al').species
                       if s.record_id == AL)
            expected = -485000 - (t - 298.15) * (-531000 + 485000) / 298.15
            self.assertAlmostEqual(ion.gibbs_energy_J_mol, expected)

    def test_finite_medium_approximation_and_original_entropy_exclusion_are_explicit(self):
        details = json.loads(self.db.metadata['R11r_aluminium_fluoride_thermal_observations'])
        for d in details['complexes']:
            self.assertEqual(d['source_H_ionic_strength_range'], [.06, .2])
            self.assertEqual(d['source_G_ionic_strength'], .5)
            self.assertTrue(d['source_original_entropy_excluded'])
            self.assertIsNone(d['total_uncertainty'])
            self.assertIn('approximately valid', d['finite_I_interpretation'])
        basis = json.loads(self.db.metadata['source_reuse_R11r_aluminium_fluoride_thermal'])
        self.assertIn('isolated-original-numerical-facts', basis['reuse_route'])
        self.assertIn('non-SRD', basis['NBS_terms'])
        holds = json.loads(self.db.metadata['R11r_aluminium_fluoride_thermal_holds'])
        self.assertIn('not retrieved', holds['R11r2'])
        for t in (323.15, 373.15):
            available = {s.record_id for s in at_temperature(self.db, t).load_system(
                'Al', ligand_ids=('fluoride-f',)).species}
            self.assertFalse(set(FIDS.values()) & available)
