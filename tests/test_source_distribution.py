"""Release boundaries preserve usable evidence and expose unresolved JANAF gaps."""
import json
import sqlite3
import unittest
from contextlib import closing

import support  # noqa: F401
import pourbase as pb


class SourceDistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_JANAF_release_has_no_direct_observations_or_dangling_archive_links(self):
        with closing(sqlite3.connect(self.database.path)) as connection:
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM sources WHERE citation LIKE '%NIST-JANAF Thermochemical Tables%'"
            ).fetchone()[0], 0)
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM reported_thermochemistry r "
                "LEFT JOIN reported_thermochemistry parent ON parent.value_id=r.supersedes_value_id "
                "WHERE r.supersedes_value_id IS NOT NULL AND parent.value_id IS NULL"
            ).fetchone()[0], 0)
            # Three old IDs contain JANAF even though their reviewed route is open NBS.
            retained = connection.execute(
                "SELECT citation,url FROM sources WHERE source_id LIKE '%JANAF%'"
            ).fetchall()
            self.assertEqual(len(retained), 3)
            self.assertTrue(all('NBS Tables' in citation and 'M32124' in url
                                for citation, url in retained))

    def test_gap_species_keep_identity_and_explicit_missing_properties(self):
        review = json.loads(self.database.metadata['JANAF_independent_source_release_20261028'])
        self.assertEqual(review['status'], 'independent_source_distribution')
        self.assertFalse(review['archive_distributed'])
        gaps = review['remaining_property_gaps']
        self.assertEqual((len(gaps), sum(map(len, gaps.values()))), (5, 13))
        records = self.database.species_records(tuple(gaps))
        attributes = {
            'gibbs_energy_of_formation': 'gibbs_energy_J_mol',
            'enthalpy_of_formation': 'formation_enthalpy_J_mol',
            'absolute_entropy': 'entropy_J_mol_K',
        }
        for record in records:
            self.assertIsNotNone(record.phase_identity)
            self.assertIn('janaf_redistribution_gap', {warning.type for warning in record.warnings})
            for property_name in gaps[record.record_id]:
                self.assertIsNone(getattr(record.thermochemistry, attributes[property_name]).value)
        self.assertEqual(len(self.database.available_systems()), 75)

    def test_existing_independent_alternatives_supply_the_changed_recommendations(self):
        lead, titanium = self.database.species_records((
            'gfe-pb-pbo2-q+0-solid-plattnerite',
            'gfe-ti-tio-q+0-solid-alpha-tio-vacancy-ordered-monoclinic',
        ))
        preferred = [row for row in lead.reported if row.selected_as_recommended]
        self.assertEqual(len(preferred), 3)
        self.assertTrue(all(row.source.source_id.startswith('USGS_B2131_1995_retained_')
                            for row in preferred))
        entropy = titanium.thermochemistry.entropy_J_mol_K
        self.assertEqual(entropy.source.source_id, 'TiO_fallback_Beyer1982_entropy')
        self.assertEqual(entropy.uncertainty, 0.07)
        self.assertIn('Pressure not explicitly specified', entropy.source.locator)


if __name__ == '__main__':
    unittest.main()
