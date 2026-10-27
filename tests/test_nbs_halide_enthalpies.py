"""Retain source enthalpies with explicit missing-G and full formula units."""
import json
import unittest

import pourbase as pb

G = 'gibbs_energy_of_formation'
H = 'enthalpy_of_formation'
S = 'absolute_entropy'
SID = 'R16d2b_open_NBS_crystalline_bromides_iodides'


class NBSHalideEnthalpyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = pb.ThermodynamicDatabase.bundled()

    def test_H_only_evidence_is_reported_as_missing_G_in_component_scope(self):
        rid = 'r16d2b-te-nbs-record813'
        record = self.db.species_records((rid,))[0]
        self.assertIsNone(record.thermochemistry.gibbs_energy_J_mol.value)
        self.assertIsNone(record.thermochemistry.entropy_J_mol_K.value)
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, -190400)
        self.assertEqual(len(record.reported), 1)
        self.assertIsNone(record.reported[0].uncertainty)
        evidence = json.loads(record.reported[0].source.locator)
        self.assertEqual((evidence['logical_csv_record'], evidence['source_state']), (813, 'cr'))
        self.assertNotIn(rid, {x.record_id for x in self.db.load_system('Te').missing_gibbs})
        scoped = self.db.load_system('Te', ligand_ids=('bromide-br',))
        self.assertNotIn(rid, {x.record_id for x in scoped.species})
        self.assertIn(rid, {x.record_id for x in scoped.missing_gibbs})
        with self.assertRaises(pb.IncompleteSystemError):
            scoped.require_complete()

    def test_fractional_hydrate_keeps_full_formula_and_enthalpy(self):
        rid = 'r16d2b-ba-nbs-record10044'
        record = self.db.species_records((rid,))[0]
        self.assertEqual(record.formula_ascii, 'BaI2(H2O)2.5')
        self.assertEqual(record.thermochemistry.formation_enthalpy_J_mol.value, -1363600)
        with self.db.connect() as c:
            row = c.execute('SELECT * FROM species WHERE record_id=?', (rid,)).fetchone()
            self.assertEqual((row['metal_count'], row['core_oxygen_count'], row['core_hydrogen_count'], row['atom_count']), (1, 2.5, 5, 10.5))
            self.assertEqual((row['ligand_id'], row['ligand_count'], row['electron_coefficient_per_metal']), ('iodide-i', 2, 2))
        self.assertEqual(record.phase_identity.status, 'unresolved')

    def test_polyhalide_formal_state_is_distinct_from_reaction_electrons(self):
        for rid, ligand in [('r16d2b-na-nbs-record11030', 'iodide-i'), ('r16d2b-k-nbs-record12381', 'iodide-i'), ('r16d2b-rb-nbs-record13514', 'bromide-br')]:
            with self.db.connect() as c:
                row = c.execute('SELECT * FROM species WHERE record_id=?', (rid,)).fetchone()
                self.assertEqual((row['metal_oxidation_state'], row['electron_coefficient_per_metal'], row['ligand_count'], row['ligand_id']), (1, 3, 3, ligand))
            self.assertNotIn((rid, G), self.db.selections)
            self.assertEqual(self.db.selections[rid, H].chosen.evidence_class, 'B')
            source = self.db.species_records((rid,))[0].reported[0].source
            self.assertIn('polyhalide', json.loads(source.locator)['polyhalide_balance'])

    def test_existing_NEA_alternatives_and_fixed_references_remain(self):
        observations = json.loads(self.db.metadata['R16d2b_NBS_halide_observations'])
        self.assertEqual(len(observations), 88)
        review = json.loads(self.db.metadata['R16d2b_NBS_halide_source_review'])
        existing = [x for x in review['records'] if x['admitted_properties'] and not x['new_species']]
        self.assertEqual({x['source_formula'] for x in existing}, {'SnBr2', 'SnI2', 'NiBr2', 'NiI2', 'FeBr3', 'FeI2', 'ZrBr4', 'ZrI4'})
        for x in existing:
            rid = x['record_id']
            self.assertNotEqual(self.db.selections[rid, H].chosen.source_id, SID)
            self.assertTrue(any(r.source.source_id == SID for r in self.db.species_records((rid,))[0].reported))
        self.assertEqual(self.db.policy.fingerprint, '5bbebf8f20e9')
        with self.db.connect() as c:
            self.assertEqual(c.execute('SELECT count(*) FROM ligands').fetchone()[0], 31)
        self.assertTrue(json.loads(self.db.metadata['source_permission_NEA_TDB'])['downstream_acknowledgment_required'])

    def test_source_empty_rows_create_no_empty_records(self):
        review = json.loads(self.db.metadata['R16d2b_NBS_halide_source_review'])
        self.assertEqual((review['source_rows'], review['new_observations'], review['new_species']), (90, 88, 80))
        empty = [x for x in review['records'] if x['disposition'] == 'no_numerical_GHS_value']
        self.assertEqual({x['source_formula'] for x in empty}, {'BiBr3', 'SnI4'})
        self.assertTrue(all(x['record_id'] is None and not x['new_species'] for x in empty))
        tin = next(x for x in empty if x['source_formula'] == 'SnI4')
        self.assertEqual(tin['matched_record_ids'], ['nea02a-sn-sni4-crystalline-tetraiodide'])
        self.assertIsNotNone(self.db.species_records((tin['matched_record_ids'][0],))[0].thermochemistry.gibbs_energy_J_mol.value)


if __name__ == '__main__':
    unittest.main()
