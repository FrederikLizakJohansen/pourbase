"""Reference conventions and the source corrections requested in sn-codata-entry.md."""

from contextlib import closing
from dataclasses import replace
import unittest

import support  # noqa: F401
import pourbase as pb
from pourbase.temperature import ENTROPY_H2, ENTROPY_O2, ENTROPY_WATER


class ReferenceStateCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = pb.ThermodynamicDatabase.bundled()

    def test_tin_uses_the_nea_entropy_and_keeps_the_rounded_legacy_observation(self):
        record = self.database.species_records(("gfe-sn-sn-q+0-solid-metal",))[0]
        entropy = record.thermochemistry.entropy_J_mol_K
        self.assertEqual((entropy.value, entropy.uncertainty), (51.18, 0.08))
        selection = self.database.selections[record.record_id, "absolute_entropy"]
        self.assertEqual(selection.chosen.source_id, "NEA_OECD_20261014_Sn")
        self.assertEqual(selection.chosen.status, "verified")
        self.assertTrue(any(row.value == 51.2 and row.status == "superseded_source_value"
                            for row in record.reported))
        with closing(self.database.connect()) as connection:
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM reported_thermochemistry r LEFT JOIN reported_thermochemistry p "
                "ON p.value_id=r.supersedes_value_id WHERE r.supersedes_value_id IS NOT NULL "
                "AND p.value_id IS NULL").fetchone()[0], 0)

    def test_nitrogen_uses_a_coherent_open_absolute_entropy_triplet(self):
        rid = "gfe-n-n2-q+0-aqueous-aq"
        values = {}
        for prop in ("gibbs_energy_of_formation", "enthalpy_of_formation", "absolute_entropy"):
            chosen = self.database.selections[rid, prop].chosen
            self.assertTrue(chosen.source_id.startswith("Sander_2023_N2_molal_estimate_"))
            self.assertEqual(chosen.status, "source_verified_estimate")
            values[prop] = chosen.value
        formation_entropy = (values["enthalpy_of_formation"] - values["gibbs_energy_of_formation"]) / 298.15
        self.assertAlmostEqual(values["absolute_entropy"], 191.61 + formation_entropy, places=5)

    def test_reference_enthalpies_are_defined_and_absolute_entropies_are_source_values(self):
        with closing(self.database.connect()) as connection:
            rows = connection.execute(
                "SELECT formation_enthalpy_J_mol,formation_enthalpy_status,entropy_status "
                "FROM selected_thermochemistry WHERE gibbs_status='defined_reference_state'").fetchall()
            self.assertEqual(len(rows), 75)
            self.assertTrue(all(h == 0 and status == "defined_reference_state" for h, status, _ in rows))
            self.assertTrue(all(status in ("accepted", "verified") for _, _, status in rows))
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM reported_thermochemistry WHERE property='absolute_entropy' "
                "AND status='defined_reference_state'").fetchone()[0], 0)

    def test_restricted_citations_are_absent_and_family_removal_preserves_choices(self):
        with closing(self.database.connect()) as connection:
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM sources WHERE citation LIKE '%CODATA Key Values%' "
                "OR source_id='NIST_WebBook_N2_Henry_298K'").fetchone()[0], 0)
        policy = pb.SelectionPolicy.default()
        self.assertFalse(any(item.chosen.evidence_class == "F" for item in self.database.selections.values()))
        germanate = self.database.selections["gfe-ge-hgeo3-q-1-aqueous-aq", "gibbs_energy_of_formation"].chosen
        self.assertEqual((germanate.family, germanate.evidence_class), ("experimental papers", "D"))
        classes = tuple(replace(item, families=("CODATA",) + item.families) if item.name == "A"
                        else replace(item, families=item.families + ("NIST WebBook",)) if item.name == "B"
                        else item for item in policy.classes)
        previous_families = replace(policy, classes=classes, source_text="", family_patterns=(
            ("CODATA", ("CODATA",)), ("NIST WebBook", ("WebBook",)), *policy.family_patterns))
        self.assertEqual(pb.compare_policies(self.database, previous_families, policy), ())

    def test_temperature_entropies_match_open_nbs_cells(self):
        # Open NBS digitization, logical rows 27 (H2 g), 15 (O2 g), 41 (H2O l), column 10.
        self.assertEqual((ENTROPY_H2, ENTROPY_O2, ENTROPY_WATER), (130.684, 205.138, 69.91))


if __name__ == "__main__":
    unittest.main()
