from __future__ import annotations

import unittest
from unittest import mock

import numpy as np

import support  # noqa: F401
from mp_fixtures import MP_API, PYMATGEN, FakeRester

from pourbase.materials_project import OfficialMaterialsProjectClient
from pourbase.models import AqueousActivityModel, PourbaixConditions


def conditions(level: float) -> PourbaixConditions:
    return PourbaixConditions(
        pH_points=57, U_points=61,
        aqueous_activities=AqueousActivityModel(default_log10_activity=level),
    )


def ion_share(diagram) -> float:
    ions = [index for index, phase in enumerate(diagram.phases) if phase.phase_type == "aqueous"]
    return float(np.isin(diagram.stable_phase_index, ions).mean())


@unittest.skipUnless(PYMATGEN and MP_API, "pymatgen and mp-api are not installed")
class OfficialClientTests(unittest.TestCase):
    def test_requested_activity_reaches_the_evaluated_entries(self) -> None:
        # pymatgen's PourbaixDiagram resets ion concentrations to its own default; the client
        # must apply the requested activity afterwards.
        with mock.patch("mp_api.client.MPRester", FakeRester):
            client = OfficialMaterialsProjectClient("test-key")
            dilute = client.calculate("Fe", conditions(-8.0))
            concentrated = client.calculate("Fe", conditions(-1.0))
        self.assertEqual(dilute.database_version, "test-db")
        self.assertGreater(ion_share(dilute), ion_share(concentrated))


if __name__ == "__main__":
    unittest.main()
