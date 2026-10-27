"""The counts and the NEA acknowledgement in README.md and CONTRIBUTING.md match the database."""

from __future__ import annotations

import subprocess
import sys
import unittest

from support import ROOT


class ReadmeCountsTest(unittest.TestCase):
    def test_counts_are_current(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "update_counts.py"), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)


if __name__ == "__main__":
    unittest.main()
