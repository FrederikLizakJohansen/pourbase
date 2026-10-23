"""Reaction direction and evaluation coherence of corrected radium estimates."""
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
SID = 'R11q_Langmuir1985_sign_corrected_thermal_estimates'
CARB = 'r11l-ra-raco3-crystalline-estimate'
SULF = 'r11l-ra-raso4-crystalline'


class RadiumSolidEnthalpyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()

    def test_positive_dissolution_enthalpies_reconstruct_from_formation_values(self):
        for rid, anion_h, kcal in ((CARB, -677140, 2.8), (SULF, -909270, 9.4)):
            rows = {r.property: r for r in self.db.species_records((rid,))[0].reported
                    if r.source.source_id == SID}
            self.assertEqual(set(rows), {H, S})
            self.assertAlmostEqual(-527600 + anion_h - rows[H].value, kcal * 4184)
            self.assertTrue(all(r.status == 'source_verified_estimate' and r.uncertainty is None
                                for r in rows.values()))
        self.assertEqual(self.db.selections[SULF, H].chosen.value, -1471100)
        self.assertEqual(self.db.selections[SULF, S].chosen.value, 138)
        for prop in (H, S):
            self.assertEqual(self.db.selections[CARB, prop].chosen.source_id, SID)
            self.assertEqual(self.db.selections[CARB, prop].chosen.evidence_class, 'E')

    def test_entropy_reconstructs_original_logk_and_preserves_modern_g(self):
        rtl = GAS_CONSTANT_J_MOL_K * 298.15 * math.log(10)
        details = json.loads(self.db.metadata['R11q_radium_solid_thermal_observations'])
        for d in details:
            reaction_s = 54 + d['anion_S_J_mol_K'] - d['derived_S_J_mol_K']
            reaction_g = d['corrected_dissolution_H_J_mol'] - 298.15 * reaction_s
            self.assertAlmostEqual(-reaction_g / rtl, d['source_log10K'])
            self.assertEqual(d['correction_pdf_pages'], [324, 325])
        historic = next(d for d in details if d['record_id'] == CARB)
        current = self.db.selections[CARB, G].chosen
        self.assertEqual(current.source_id, 'R11p_Matyskin2023_CC_BY_carbonate_adaptation')
        self.assertGreater(abs(current.value - historic['source_original_G_J_mol']), 4000)

    def test_scoped_reuse_and_modern_thermal_holds_remain_explicit(self):
        basis = json.loads(self.db.metadata['source_reuse_R11q_radium_solid_thermal'])
        self.assertIn('individual-original-numerical-facts', basis['reuse_route'])
        self.assertIn('non-SRD', basis['NBS_terms'])
        holds = json.loads(self.db.metadata['R11q_radium_solid_thermal_holds'])
        self.assertEqual(holds['R11l5_status'], 'completed_authoritative_sign_correction_and_local_HS_adaptation')
        self.assertIn('remains held', holds['R11l3'])
        self.assertIn('remains open', holds['R11p2'])
        for t in (323.15, 373.15):
            self.assertNotIn(CARB, {s.record_id for s in at_temperature(self.db, t).load_system(
                'Ra', ligand_ids=('carbonate-co3',)).species})
