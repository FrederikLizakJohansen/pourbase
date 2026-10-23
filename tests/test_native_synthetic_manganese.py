"""Native bicarbonate conversion and synthetic MnCO3 evaluation ancestry."""
import json
import math
import unittest

import support  # noqa: F401
import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K

G = 'gibbs_energy_of_formation'
H = 'enthalpy_of_formation'
RID = 'r11m-mn-mnco3-precipitated'
SID = 'R11s_USGS1991_Nordstrom1990_synthetic_MnCO3_adaptation'


class NativeSyntheticManganeseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()
        cls.details, = json.loads(cls.db.metadata['R11s_native_synthetic_manganese_observations'])

    def test_selected_alternative_reconstructs_original_ksp_and_keeps_prior_values(self):
        v = self.db.selections[RID, G].chosen
        rtl = GAS_CONSTANT_J_MOL_K * 298.15 * math.log(10)
        self.assertEqual((v.source_id, v.evidence_class), (SID, 'E'))
        self.assertAlmostEqual((v.value + 228100 + 527810) / rtl, -10.39)
        self.assertIsNone(v.uncertainty)
        rows = self.db.species_records((RID,))[0].reported
        self.assertEqual(len(rows), 3)
        self.assertTrue(any(abs(r.value + 814575.8542830301) < 1e-7 for r in rows))
        self.assertEqual(self.db.selections[RID, H].chosen.value, -883200)

    def test_native_reaction_uses_the_source_bicarbonate_reference(self):
        n = self.details['native_conversion']
        a, b, c, d, e = n['source_coefficients']
        t = 298.15
        ka = a + b*t + c/t + d*math.log10(t) + e/t**2
        self.assertAlmostEqual(ka, -10.328854378506376)
        self.assertEqual(round(ka + 10.39, 5), .06115)
        rtl = GAS_CONSTANT_J_MOL_K * t * math.log(10)
        self.assertAlmostEqual(n['source_equivalent_bicarbonate_G_J_mol'], -527810 + rtl*ka)
        self.assertAlmostEqual(n['rounded_reference_residual_J_mol'], -2.8010571827180684)
        self.assertNotEqual(n['native_rounded_K_with_current_bicarbonate_G_J_mol'],
                            self.db.selections[RID, G].chosen.value)

    def test_source_missing_enthalpy_and_exact_specimen_scope_remain_explicit(self):
        self.assertIsNone(self.details['source_reaction_H'])
        self.assertEqual((self.details['source_pdf_page'], self.details['source_row']), (36, 190))
        self.assertIn('Exact powder identity', self.details['material_category'])
        self.assertNotIn((RID, 'absolute_entropy'), self.db.selections)
        holds = json.loads(self.db.metadata['R11s_native_synthetic_manganese_holds'])
        self.assertEqual(holds['R11m1_status'], 'completed_source_category_and_native_reference_reconciliation')
        self.assertIn('remains unresolved', holds['R11s1'])
        self.assertIn('unavailable', holds['R11s2'])
        basis = json.loads(self.db.metadata['source_reuse_R11s_native_synthetic_manganese'])
        self.assertIn('USGS', basis['USGS_rights'])
        self.assertIn('non-SRD', basis['NBS_terms'])
