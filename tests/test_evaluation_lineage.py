"""Selection uses reviewed evaluation histories while retaining legacy choices."""
from dataclasses import replace
import json
import unittest
from unittest.mock import patch

import pourbase as pb
from pourbase.records import EvaluationLineage
from pourbase.selection import SELECTOR_VERSION, describe

G = 'gibbs_energy_of_formation'


def row(vid, year=1992, author='Grenthe', evaluation=None, derivation='published', reprint=None,
        uncertainty=1., citation=None, status='verified'):
    lineage = None if evaluation is None else dict(version=1, evaluation_id=evaluation,
                                                  derivation_id=derivation, reprint_of_value_id=reprint)
    return dict(value_id=vid, record_id='test-oxide', property=G, value=-1000.,
                uncertainty=uncertainty, status=status, source_id=vid,
                citation=citation or f'{author}, I. et al. ({year}). OECD Nuclear Energy Agency NEA-TDB.',
                source_locator=json.dumps({'evaluation_lineage': lineage}) if lineage else 'Table 1, p. 5')


class Evidence:
    def __init__(self, rows):
        self.rows = rows

    def _rows(self, sql, parameters=()):
        return [dict(record_id='test-oxide', symbol='Sr')] if sql.startswith('SELECT record_id, symbol') else self.rows


class EvaluationLineageTests(unittest.TestCase):
    def choose(self, *rows):
        return pb.select(Evidence(rows))[('test-oxide', G)].chosen

    def test_independent_same_author_revision_reaches_recency(self):
        chosen = self.choose(row('original', evaluation='NEA1992'),
                             row('revision', 2020, evaluation='NEA2020'))
        self.assertEqual(chosen.value_id, 'revision')
        self.assertEqual(chosen.evaluation_lineage.evaluation_id, 'NEA2020')

    def test_actual_reprint_across_authors_prefers_original(self):
        self.assertEqual(self.choose(row('original', evaluation='same'),
                                    row('reprint', 2003, author='Guillaumont', evaluation='same',
                                        reprint='original')).value_id, 'original')

    def test_reviewed_equal_lineage_prefers_earliest_publication(self):
        self.assertEqual(self.choose(row('original', evaluation='same'),
                                    row('later', 2003, author='Guillaumont', evaluation='same')).value_id, 'original')

    def test_changed_uncertainty_is_independent_when_reviewed_as_revision(self):
        self.assertEqual(self.choose(row('original', evaluation='old', uncertainty=None),
                                    row('revision', 2020, evaluation='reassessed', uncertainty=10.)).value_id,
                         'revision')

    def test_revised_inputs_have_a_distinct_derivation(self):
        self.assertEqual(self.choose(row('old-inputs', evaluation='same', derivation='anchors1992'),
                                    row('new-inputs', 2020, evaluation='same', derivation='anchors2020')).value_id,
                         'new-inputs')

    def test_third_independent_candidate_competes_with_original(self):
        self.assertEqual(self.choose(row('original', evaluation='first'),
                                    row('reprint', 2020, evaluation='first', reprint='original'),
                                    row('independent', 2010, author='Other', evaluation='second')).value_id,
                         'independent')

    def test_unannotated_legacy_choices_remain(self):
        self.assertEqual(self.choose(row('original'), row('later', 2020)).value_id, 'original')

    def test_class_priority_and_overrides_still_apply(self):
        rows = [row('NEA', evaluation='old'), row('NBS', 2023, evaluation='new',
                citation='Wagman, D. D. et al. (2023). The NBS Tables of Chemical Thermodynamic Properties.')]
        self.assertEqual(self.choose(*rows).value_id, 'NEA')
        policy = pb.SelectionPolicy.default().with_override('test-oxide', G, 'NBS', 'reviewed test')
        self.assertEqual(pb.select(Evidence(rows), policy)[('test-oxide', G)].chosen.value_id, 'NBS')

    def test_reprint_link_is_validated_against_ineligible_original(self):
        self.assertEqual(self.choose(row('original', evaluation='same', status='superseded_source_value'),
                                    row('copy', 2003, evaluation='same', reprint='original')).value_id, 'copy')

    def test_bad_links_cannot_silently_change_selection(self):
        examples = [
            [row('copy', evaluation='same', reprint='missing')],
            [row('a', evaluation='same', reprint='b'), row('b', 2003, evaluation='same', reprint='a')],
            [row('a', evaluation='first'), row('b', 2003, evaluation='different', reprint='a')],
            [row('a', evaluation='same'), row('b', 2003, evaluation='same', derivation='different', reprint='a')],
        ]
        for rows in examples:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                self.choose(*rows)
        a, b = row('a', evaluation='same'), row('b', evaluation='same', reprint='a')
        b['record_id'] = 'other-species'
        with self.assertRaises(ValueError):
            self.choose(a, b)
        b['record_id'] = a['record_id']; b['property'] = 'absolute_entropy'
        with self.assertRaises(ValueError):
            self.choose(a, b)

    def test_invalid_provenance_is_explicit_and_legacy_locators_are_readable(self):
        for loc in (None, 'Table 1, p. 5', '{}', '[]'):
            self.assertIsNone(EvaluationLineage.from_locator(loc))
        for data in (None, {}, dict(version=2), dict(version=True),
                     dict(version=1, evaluation_id='', derivation_id='published'),
                     dict(version=1, evaluation_id='same', derivation_id='published', reprint_of_value_id='')):
            with self.subTest(data=data), self.assertRaises(ValueError):
                EvaluationLineage.from_locator(json.dumps({'evaluation_lineage': data}))

    def test_selector_behavior_is_part_of_result_identity(self):
        policy = pb.SelectionPolicy.default()
        before = policy.fingerprint
        self.assertEqual(describe(policy)['selector_version'], SELECTOR_VERSION)
        with patch('pourbase.selection.SELECTOR_VERSION', 'future-selector'):
            self.assertNotEqual(policy.fingerprint, before)
        self.assertEqual(policy.fingerprint, before)

    def test_bundled_lineage_is_exposed_in_selected_evidence_and_exports(self):
        db = pb.ThermodynamicDatabase.bundled()
        rid = 'r11j3b-ba-bao-crystalline'
        record = db.species_records((rid,))[0]
        chosen = db.selections[rid, G].chosen
        reported = next(x for x in record.reported if x.value_id == chosen.value_id)
        self.assertEqual(reported.evaluation_lineage, chosen.evaluation_lineage)
        self.assertEqual(record.as_dict()['reported'][0]['evaluation_lineage']['evaluation_id'],
                         record.reported[0].evaluation_lineage.evaluation_id)
        self.assertEqual(json.loads(db.metadata['R11j3f2_explicit_evaluation_lineage'])['lineage_annotations'], 10)


if __name__ == '__main__':
    unittest.main()
