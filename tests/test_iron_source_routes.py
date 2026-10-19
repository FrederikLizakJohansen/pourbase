"""Iron additions preserve nominal phases, source models and thermal effects."""
import json
import math
import unittest

import pourbase as pb
from pourbase.temperature import at_temperature

G = 'gibbs_energy_of_formation'
H = 'enthalpy_of_formation'
S = 'absolute_entropy'
R2 = 'gfe-fe-fe-oh-3-q+0-solid-ferrihydrite-2-line'
R6 = 'gfe-fe-fe-oh-3-q+0-solid-ferrihydrite-6-line'
SID = 'NEA_2013_R11i_nominal_ferrihydrite_models'


class IronSourceRoutesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()

    def test_nea_adjusted_models_retain_original_alternatives(self):
        for rid, value, interval, original in [(R2, -826700, 2100, -827100),
                                               (R6, -829900, 2000, -830300)]:
            selected = self.db.selections[(rid, H)].chosen
            self.assertEqual((selected.value, selected.uncertainty, selected.source_id),
                             (value, interval, SID))
            self.assertEqual(selected.status, 'source_verified_estimate')
            record = self.db.species_records((rid,))[0]
            self.assertTrue(any(x.property == H and x.value == original for x in record.reported))
        entropy = self.db.selections[(R6, S)].chosen
        self.assertEqual((entropy.value, entropy.uncertainty, entropy.source_id), (130, 10, SID))
        self.assertIn('not normal selected NEA values', self.db.source(SID).locator)

    def test_calculated_solubility_reconstructs_with_source_consistent_ions(self):
        d, = json.loads(self.db.metadata['R11i_ferrihydrite_derivations'])
        record = self.db.species_records((R6,))[0]
        value = next(x for x in record.reported if x.source.source_id ==
                     'R11i_local_NEA2013_six_line_ferrihydrite_G')
        rtl = 8.31446261815324 * 298.15 * math.log(10)
        logk = (value.value - d['Fe3_input']['value_J_mol'] -
                3 * d['OH_input']['value_J_mol']) / rtl
        self.assertAlmostEqual(logk, -38.97)
        self.assertEqual(d['OH_input']['value_J_mol'], -157220)
        self.assertEqual(d['source_log10Ksp_interval'], .64)
        self.assertIsNone(value.uncertainty)
        self.assertFalse(value.selected_as_recommended)
        self.assertIn('calculated', d['source_dependence'])
        for rid, line in [(R2, '2-line'), (R6, '6-line')]:
            self.assertEqual(self.db.selections[(rid, G)].chosen.source_id,
                             f'Ferrihydrite_R05_{line}_gf_NBS-derived-upper-G')

    def test_thermal_shift_follows_adjusted_enthalpy_and_retains_nominal_scope(self):
        for temperature in (323.15, 373.15):
            species = {s.record_id: s for s in at_temperature(self.db, temperature).load_system('Fe').species}
            for rid, old_h in [(R2, -827100), (R6, -830300)]:
                g = self.db.selections[(rid, G)].chosen.value
                old_extrapolation = g - (temperature - 298.15) * (old_h - g) / 298.15
                self.assertAlmostEqual(species[rid].gibbs_energy_J_mol - old_extrapolation,
                                       -400 * (temperature - 298.15) / 298.15)

    def test_native_phase_and_commercial_source_holds_remain_explicit(self):
        basis = json.loads(self.db.metadata['source_reuse_R11i_iron'])
        self.assertIn('do not establish', basis['holds']['ferric_hydroxide_proxies'])
        self.assertIn('phase mismatch', basis['holds']['precipitated_carbonate'])
        self.assertIn('commercial', basis['holds']['trimer'])
        self.assertIn('fixes BrownEkberg2016', basis['holds']['dimer'])
        self.assertEqual(basis['permission_id'], 'NEA-TDB-OECD-2026-10-14')
        self.assertIn('further sublicensees', basis['acknowledgment'])
        with self.db.connect() as c:
            self.assertEqual(c.execute("SELECT count(*) FROM species WHERE record_id LIKE 'r11i-%'").fetchone()[0], 0)
        dimer = self.db.species_records(('gfe-fe-fe2-oh-2-q+4-aqueous-aq',))[0]
        self.assertTrue({G, H, S}.issubset({x.property for x in dimer.reported}))
