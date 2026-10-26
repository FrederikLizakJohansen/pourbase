"""One-population sulfurous-acid water convention with retained source versions."""
from dataclasses import replace
import json
import unittest

import pourbase as pb
from pourbase.constants import GAS_CONSTANT_J_MOL_K, LN_10
from pourbase.engine import standard_transformed_gibbs_J_mol_metal

RID = 'gfe-s-so2-q+0-aqueous-aq'
G = 'gibbs_energy_of_formation'
SID = 'R11j3i1_local_SO2_water_representation'


class SulfurousAcidWaterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()

    def test_raw_versions_and_unknown_combined_confidence_remain_visible(self):
        rows = json.loads(self.db.metadata['R11j3i1_water_converted_observations'])
        self.assertEqual(len(rows), 2)
        for row in rows:
            ev = row['evidence']
            year = ev['raw_source_year']
            self.assertAlmostEqual(ev['raw_original_value'], -539.188 if year == 1992 else -539.187)
            self.assertEqual(ev['raw_original_uncertainty'], 4.072)
            self.assertEqual((ev['raw_printed_page'], ev['raw_pdf_page']), (68, 86) if year == 1992 else (138, 178))
            self.assertEqual(row['value'], -302059 if year == 1992 else -302058)
            self.assertIsNone(row['uncertainty'])
            self.assertIsNone(ev['water_anchor']['uncertainty'])
            self.assertEqual(row['status'], 'source_verified_estimate')
            selection = self.db.selections[RID, G]
            self.assertEqual(next(x.evidence_class for x in selection.candidates if x.value_id == row['value_id']), 'E')
            self.assertNotEqual(selection.chosen.value_id, row['value_id'])

    def test_formal_and_canonical_balanced_energies_are_invariant(self):
        phase = next(x for x in self.db.load_system('S').species if x.record_id == RID)
        for row in json.loads(self.db.metadata['R11j3i1_water_converted_observations']):
            canonical = replace(phase, gibbs_energy_J_mol=row['value'])
            formal = replace(phase, formula_ascii='H2SO3', core_oxygen_count=3, core_hydrogen_count=2,
                gibbs_energy_J_mol=row['evidence']['raw_original_value'] * 1000)
            self.assertEqual((formal.electrons_per_metal, formal.protons_per_metal), (4, 4))
            self.assertEqual((canonical.electrons_per_metal, canonical.protons_per_metal), (4, 4))
            for pH, potential in [(0, -1), (7, 0), (14, 1)]:
                self.assertAlmostEqual(float(standard_transformed_gibbs_J_mol_metal(formal, self.db.reference_state, pb.PourbaixConditions(), pH, potential)),
                    float(standard_transformed_gibbs_J_mol_metal(canonical, self.db.reference_state, pb.PourbaixConditions(), pH, potential)))

    def test_matching_source_protonation_constant_is_preserved(self):
        water = self.db.reference_state.water_gibbs_energy_J_mol
        self.assertEqual(water, -237129)
        for row in json.loads(self.db.metadata['R11j3i1_water_converted_observations']):
            hs = -528685 if row['evidence']['raw_source_year'] == 1992 else -528684
            delta = row['value'] + water - hs
            self.assertEqual(delta, -10503)
            self.assertAlmostEqual(-delta / (GAS_CONSTANT_J_MOL_K * 298.15 * LN_10), 1.84, places=4)

    def test_one_population_and_existing_preference_are_preserved(self):
        with self.db.connect() as c:
            self.assertEqual(c.execute("SELECT count(*) FROM species WHERE formula_ascii='H2SO3'").fetchone()[0], 0)
            self.assertEqual(c.execute('SELECT count(*) FROM ligands').fetchone()[0], 31)
        self.assertEqual(self.db.selections[RID, G].chosen.value, -300676)
        self.assertNotEqual(self.db.selections[RID, G].chosen.source_id, SID)
        context = json.loads(self.db.metadata['R11j3i1_SO2_water_convention'])
        self.assertEqual(context['water_activity'], 1)
        self.assertFalse(context['identity_reference_numerical_data_imported'])
        self.assertIn('analytical', context['source_neutral_population'])
        review = json.loads(self.db.metadata['R11j3i1_sulfurous_acid_review'])
        self.assertTrue(review['scientific_identity_hold_resolved'])
        self.assertEqual((review['new_observations'], review['new_species'], review['newly_available_properties']), (2, 0, 0))
        self.assertEqual(self.db.policy.fingerprint, '586e3da17300')
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])


if __name__ == '__main__':
    unittest.main()
