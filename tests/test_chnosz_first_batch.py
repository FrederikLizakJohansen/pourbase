"""CHNOSZ source variants preserve units, phases, corrections and reaction basis."""
import json
import math
import unittest

import pourbase as pb
from pourbase.engine import transformed_gibbs_J_mol_metal

G = 'gibbs_energy_of_formation'
H = 'enthalpy_of_formation'
S = 'absolute_entropy'


class CHNOSZFirstBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()

    def test_original_hydrosulfide_cells_and_missing_enthalpy(self):
        for symbol, gibbs, entropy in [('Pd', -11724, 52.919), ('Pt', -14980, 45.303)]:
            rid = f'chnosz-initial-{symbol.lower()}-hs4-q-2'
            record = self.db.species_records((rid,))[0]
            rows = {r.property: r for r in record.reported}
            self.assertAlmostEqual(rows[G].value, gibbs * 4.184)
            self.assertAlmostEqual(rows[S].value, entropy * 4.184)
            self.assertNotIn(H, rows)
            self.assertIsNone(record.thermochemistry.formation_enthalpy_J_mol.value)
            self.assertTrue(all(r.status == 'source_verified_estimate' for r in rows.values()))
            self.assertTrue(all(r.uncertainty is None for r in rows.values()))
            self.assertIn('Table 4!', rows[G].source.locator)
            self.assertIn('10.17632/v52mgp7mmm.1', rows[G].source.citation)

    def test_hydrosulfide_and_sulfide_references_give_the_same_energy(self):
        rtln = 8.31446261815324 * 298.15 * math.log(10)
        for symbol in ('Pd', 'Pt'):
            rid = f'chnosz-initial-{symbol.lower()}-hs4-q-2'
            species = next(s for s in self.db.load_system(symbol, ligand_ids=('sulfide-s',)).species
                           if s.record_id == rid)
            self.assertEqual((species.ligand_count, species.core_hydrogen_count,
                              species.electrons_per_metal, species.protons_per_metal), (4, 4, 2, -4))
            pka = (species.ligand_gibbs_energy_J_mol - 12080) / rtln
            for pH in (7, 10):
                for loghs in (-6, -4):
                    cfg = pb.PourbaixConditions(ligand_activities=pb.LigandActivityModel((
                        pb.LigandActivity('sulfide-s', log10_free_activity=loghs + pH - pka),)))
                    actual = float(transformed_gibbs_J_mol_metal(
                        species, self.db.reference_state, cfg, pH, 0))
                    expected = species.gibbs_energy_J_mol - 4 * (12080 + rtln * loghs) - 6 * rtln
                    self.assertAlmostEqual(actual, expected)

    def test_indium_enthalpies_use_the_documented_corrected_variant(self):
        with self.db.connect() as con:
            rows = con.execute('SELECT * FROM reported_thermochemistry WHERE source_id=?',
                               ('CHNOSZ_HB24_corrected_In_H',)).fetchall()
        self.assertEqual(len(rows), 11)
        self.assertTrue(all(r['property'] == H and r['status'] == 'source_verified_estimate' for r in rows))
        self.assertTrue(all('−7335cal/mol' in r['source_locator'] for r in rows))
        # Original E2 K31 = -65513.139; this correction is 30689.64 J/mol.
        chloride = next(r for r in rows if r['record_id'] == 'r06-in-incl-q+2-aq')
        self.assertAlmostEqual(chloride['value'], (-65513.139 - 7335) * 4.184)
        self.assertEqual(self.db.policy.fingerprint, '4c1df55bbeff')

    def test_water_subtraction_preserves_the_existing_germanium_species(self):
        record = self.db.species_records(('gfe-ge-hgeo3-q-1-aqueous-aq',))[0]
        rows = {r.property: r for r in record.reported
                if r.source and r.source.source_id == 'CHNOSZ_HB24_Ge_evaluations'}
        self.assertAlmostEqual(rows[G].value, -218500 * 4.184 + 237129)
        self.assertAlmostEqual(rows[H].value, -260500 * 4.184 + 285830)
        self.assertAlmostEqual(rows[S].value, 27.14 * 4.184 - 69.91)
        self.assertEqual(record.thermochemistry.gibbs_energy_J_mol.value, -711470)
        self.assertIn('stored formula + 1 H2O', rows[G].source.locator)

    def test_named_germanium_and_cadmium_phases_remain_distinct(self):
        ids = ('gfe-ge-geo2-q+0-solid-hexagonal', 'chnosz-initial-ge-argutite',
               'chnosz-initial-ge-alpha-ges2', 'r16d4a-cd-nbs-record4401',
               'chnosz-initial-cd-greenockite')
        records = {r.record_id: r for r in self.db.species_records(ids)}
        self.assertEqual(len(records), 5)
        alpha = records['chnosz-initial-ge-alpha-ges2']
        self.assertIsNone(alpha.thermochemistry.gibbs_energy_J_mol.value)
        green = records['chnosz-initial-cd-greenockite']
        self.assertEqual(green.thermochemistry.gibbs_energy_J_mol.value, -146100)
        self.assertEqual(green.thermochemistry.gibbs_energy_J_mol.uncertainty, 1300)
        self.assertEqual(records['r16d4a-cd-nbs-record4401'].thermochemistry.gibbs_energy_J_mol.value,
                         -156500)

    def test_finite_review_keeps_source_holds_separate(self):
        review = json.loads(self.db.metadata['CHNOSZ_20261028_initial_review'])
        self.assertEqual(review['scope_records'], 47)
        self.assertEqual(len(review['decisions']), 47)
        self.assertEqual(sum(x['added_observations'] for x in review['decisions']), 63)
        held = [x for x in review['decisions'] if x['decisions'] and
                set(x['decisions'].values()) == {'held'}]
        self.assertEqual(len(held), 22)
        self.assertTrue(all(x['added_observations'] == 0 for x in held))
        self.assertIn('CC BY4.0', review['rights']['LBP25'])
        self.assertIn('Thermoddem', review['rights']['HB24'])
