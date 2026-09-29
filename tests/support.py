"""Shared test setup: import the package from the checkout."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class FakeMPComposition:
    def __init__(self, formula: str, amounts: dict[str, float]) -> None:
        self.reduced_formula = formula
        self.amounts = amounts

    def get(self, element: str, default: float = 0.0) -> float:
        return self.amounts.get(element, default)


class FakeMPEntry:
    """The subset of a pymatgen PourbaixEntry that the evaluation reads."""

    def __init__(self, entry_id, name, phase_type, formula, amounts, energy, npH, nPhi) -> None:
        self.entry_id, self.name, self.phase_type = entry_id, name, phase_type
        self.composition = FakeMPComposition(formula, amounts)
        self.normalization_factor = 1.0 / amounts["Fe"]
        self.normalized_energy, self.npH, self.nPhi = energy, npH, nPhi

    def normalized_energy_at_conditions(self, pH, eh_V):
        return self.normalized_energy + self.npH * self.normalization_factor * 0.0591 * pH + (
            self.nPhi * self.normalization_factor * eh_V
        )
