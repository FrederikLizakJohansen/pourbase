"""Qualified endmember adaptation of the openly licensed 2023 carbonate study."""
import json
import math
import unittest

import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K

CARB = 'r11l-ra-raco3-crystalline-estimate'
G = 'gibbs_energy_of_formation'
SID = 'R11p_Matyskin2023_CC_BY_carbonate_adaptation'


class ExperimentalRadiumCarbonateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()

    def test_conditional_estimate_reconstructs_published_solubility_and_keeps_alternatives(self):
        record = self.db.species_records((CARB,))[0]
        value = self.db.selections[CARB, G].chosen
        rtl = GAS_CONSTANT_J_MOL_K * 298.15 * math.log(10)
        self.assertEqual(value.source_id, SID)
        self.assertEqual(value.evidence_class, 'E')
        self.assertAlmostEqual((value.value + 561500 + 527810) / rtl, -7.52)
        self.assertIsNone(value.uncertainty)
        self.assertEqual(len(record.reported), 3)
        for old in (-1136686.4788710426, -1132062.9911739891):
            self.assertTrue(any(abs(r.value - old) < 1e-7 for r in record.reported))

    def test_fit_and_systematic_intervals_keep_their_meanings(self):
        d, = json.loads(self.db.metadata['R11p_radium_carbonate_observations'])
        self.assertEqual(d['fit_variants'], ['Davies', 'ESIT'])
        self.assertEqual(d['independent_observations'], 1)
        self.assertEqual(d['source_fit_standard_uncertainty_log10K'], .02)
        self.assertEqual(d['source_systematic_adjusted_standard_uncertainty_log10K'], .04)
        self.assertAlmostEqual(d['systematic_adjusted_partial_sigma_J_mol'],
                               2 * d['fit_partial_sigma_J_mol'])
        self.assertIsNone(d['total_uncertainty'])
        self.assertEqual(d['source_bath_temperature_C'], 25.1)
        self.assertEqual(d['source_table_temperature_C'], 25.)
        self.assertIn('Ba/Ra<=0.1', d['phase_interpretation'])
        self.assertIn('No enthalpy-based', d['temperature_interpretation'])

    def test_main_article_licence_and_separate_holds_are_recorded(self):
        basis = json.loads(self.db.metadata['source_reuse_R11p_experimental_radium_carbonate'])
        self.assertEqual(basis['licence_url'], 'https://creativecommons.org/licenses/by/4.0/')
        self.assertEqual(basis['supplement']['licence'], 'CC BY-NC4.0')
        self.assertEqual(basis['supplement']['status'], 'read_only_context_no_import_or_redistribution')
        holds = json.loads(self.db.metadata['R11p_radium_carbonate_holds'])
        self.assertIn('R11p1', holds['exact_composition_and_mixing'])
        self.assertIn('R11p2', holds['temperature'])
        self.assertIn('R11p3', holds['independent_refit'])
        self.assertIn('held', holds['R11l3'])
        for prop in ('enthalpy_of_formation', 'absolute_entropy'):
            self.assertNotIn((CARB, prop), self.db.selections)
