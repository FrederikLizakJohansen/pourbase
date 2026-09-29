"""Activity-coefficient models for aqueous mass-balance calculations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class ActivityCoefficientModel(Protocol):
    """Interface for species activity coefficients at controlled solution conditions."""

    def log10_coefficient(self, charge: float) -> float:
        """Return ``log10(gamma)`` for one aqueous species charge."""

    def coefficient(self, charge: float) -> float:
        """Return the dimensionless activity coefficient for one species charge."""

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable model description."""


def _validated_charge(charge: float) -> float:
    value = float(charge)
    if not math.isfinite(value):
        raise ValueError("aqueous species charge must be finite")
    return value


@dataclass(frozen=True, slots=True)
class IdealActivityCoefficientModel:
    """Unit activity coefficients for an ideal dilute aqueous mixture."""

    def log10_coefficient(self, charge: float) -> float:
        _validated_charge(charge)
        return 0.0

    def coefficient(self, charge: float) -> float:
        _validated_charge(charge)
        return 1.0

    def as_dict(self) -> dict[str, object]:
        return {
            "kind": "ideal_activity_coefficients",
            "ionic_strength_mol_L": 0.0,
            "concentration_basis": "molarity",
        }


@dataclass(frozen=True, slots=True)
class DaviesActivityCoefficientModel:
    """Davies coefficients at fixed background ionic strength and 298.15 K.

    Ionic strength is supplied on a molarity basis. At this model's dilute range it
    approximates the molality basis used by the original Davies expression. The
    selected metal's contribution to ionic strength is not solved because the
    current chemical system has no explicit supporting-electrolyte counterions.
    """

    ionic_strength_mol_L: float
    debye_huckel_A: float = 0.509

    maximum_ionic_strength_mol_L = 0.1
    empirical_linear_coefficient = 0.3
    reference_temperature_K = 298.15
    source_url = (
        "https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/"
        "tdb2_2020-09-02_11-51-54_735.pdf"
    )

    def __post_init__(self) -> None:
        if not math.isfinite(self.ionic_strength_mol_L):
            raise ValueError("ionic_strength_mol_L must be finite")
        if not 0.0 <= self.ionic_strength_mol_L <= self.maximum_ionic_strength_mol_L:
            raise ValueError(
                "Davies ionic strength must lie between 0 and "
                f"{self.maximum_ionic_strength_mol_L:g} mol L^-1"
            )
        if not math.isfinite(self.debye_huckel_A) or self.debye_huckel_A <= 0:
            raise ValueError("debye_huckel_A must be positive and finite")

    def log10_coefficient(self, charge: float) -> float:
        value = _validated_charge(charge)
        root_ionic_strength = math.sqrt(self.ionic_strength_mol_L)
        correction = (
            root_ionic_strength / (1.0 + root_ionic_strength)
            - self.empirical_linear_coefficient * self.ionic_strength_mol_L
        )
        return -self.debye_huckel_A * value**2 * correction

    def coefficient(self, charge: float) -> float:
        return 10.0 ** self.log10_coefficient(charge)

    def as_dict(self) -> dict[str, object]:
        return {
            "kind": "davies_fixed_ionic_strength",
            "ionic_strength_mol_L": self.ionic_strength_mol_L,
            "concentration_basis": "molarity_dilute_approximation",
            "debye_huckel_A": self.debye_huckel_A,
            "reference_temperature_K": self.reference_temperature_K,
            "maximum_ionic_strength_mol_L": self.maximum_ionic_strength_mol_L,
            "ionic_strength_is_self_consistent": False,
            "source_url": self.source_url,
        }
