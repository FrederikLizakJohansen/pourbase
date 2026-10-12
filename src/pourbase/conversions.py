"""Concentration-unit helpers for the public API and desktop application.

A metal concentration entered as log10(c / mol L^-1), mol/L, ppm (mg of metal per litre) or
weight percent of metal is converted to molarity with the atomic weight M_M (g/mol) and the
solution density rho (kg/L):

    c = 10^x,   c = ppm / (1000 M_M),   c = 10 rho wt% / M_M                             (10)

In fixed-activity mode a = c / (1 mol/L) is assigned to every aqueous species of the element; in
mass-balance mode c is the conserved total c_T.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


# Conventional atomic weights (g mol-1), rounded for practical solution preparation.
# Source: CIAAW standard atomic weights, https://ciaaw.org/atomic-weights.htm
ATOMIC_WEIGHT_G_MOL: dict[str, float] = {
    "Ag": 107.8682, "Al": 26.9815385, "As": 74.921595, "Au": 196.96657,
    "B": 10.81, "Ba": 137.327, "Be": 9.0121831, "Bi": 208.98040,
    "Br": 79.904, "C": 12.011, "Ca": 40.078, "Cd": 112.414,
    "Ce": 140.116, "Cl": 35.45, "Co": 58.933194, "Cr": 51.9961,
    "Cs": 132.90545196, "Cu": 63.546, "F": 18.998403163,
    "Dy": 162.500, "Er": 167.259, "Eu": 151.964,
    "Fe": 55.845, "Ga": 69.723, "Gd": 157.25, "Ge": 72.630, "Hf": 178.49,
    "I": 126.90447, "In": 114.818,
    "Hg": 200.592, "Ho": 164.93033, "Ir": 192.217, "K": 39.0983,
    "La": 138.90547, "Li": 6.94, "Lu": 174.9668, "Mg": 24.305,
    "Mn": 54.938043, "Mo": 95.95, "N": 14.007, "Na": 22.98976928,
    "Nb": 92.90637, "Nd": 144.242, "Ni": 58.6934,
    "P": 30.973761998, "Pb": 207.2, "Pd": 106.42, "Pr": 140.90766,
    "Pt": 195.084,
    "Rb": 85.4678,
    "Os": 190.23, "Re": 186.207, "Rh": 102.90549, "Ru": 101.07,
    "S": 32.06, "Sb": 121.760, "Sc": 44.955908, "Se": 78.971,
    "Si": 28.085, "Sn": 118.710, "Sr": 87.62,
    "Sm": 150.36, "Ta": 180.94788, "Tb": 158.92535, "Te": 127.60,
    "Ti": 47.867, "Tl": 204.38, "Tm": 168.93422,
    "V": 50.9415, "W": 183.84,
    "Y": 88.90584, "Yb": 173.045, "Zn": 65.38, "Zr": 91.224,
}


@dataclass(frozen=True, slots=True)
class ConcentrationConversion:
    """One user concentration expressed as molarity and log10 standard activity."""

    symbol: str
    input_value: float
    input_unit: str
    molar_concentration: float
    log10_standard_activity: float
    solution_density_kg_L: float
    assumptions: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "input_value": self.input_value,
            "input_unit": self.input_unit,
            "molar_concentration": self.molar_concentration,
            "log10_standard_activity": self.log10_standard_activity,
            "solution_density_kg_L": self.solution_density_kg_L,
            "assumptions": list(self.assumptions),
            "atomic_weight_g_mol": ATOMIC_WEIGHT_G_MOL[self.symbol],
        }


def convert_concentration(
    symbol: str,
    value: float,
    unit: str,
    *,
    solution_density_kg_L: float = 1.0,
) -> ConcentrationConversion:
    """Convert log10(M), mol/L, ppm metal, or wt% metal to molarity."""
    symbol = symbol.strip()[:1].upper() + symbol.strip()[1:].lower()
    if symbol not in ATOMIC_WEIGHT_G_MOL:
        raise ValueError(f"No atomic weight is available for {symbol}")
    if not math.isfinite(value):
        raise ValueError("concentration value must be finite")
    if not math.isfinite(solution_density_kg_L) or solution_density_kg_L <= 0:
        raise ValueError("solution density must be positive and finite")
    atomic_weight = ATOMIC_WEIGHT_G_MOL[symbol]
    assumptions: list[str] = []
    normalized = unit.strip().lower()
    if normalized in {"log10_molar", "log10(molar)", "log10_m"}:
        try:
            molar = 10.0**value
        except OverflowError as error:
            raise ValueError("converted concentration is outside floating-point range") from error
        canonical_unit = "log10_molar"
    elif normalized in {"molar", "mol_l", "mol/l"}:
        molar = value
        canonical_unit = "molar"
    elif normalized in {"ppm", "mg_l", "mg/l"}:
        molar = value / 1000.0 / atomic_weight
        canonical_unit = "ppm"
        assumptions.append("ppm is interpreted as mg of elemental metal per litre of solution")
    elif normalized in {"wt_percent", "wt%", "weight_percent"}:
        molar = (value / 100.0) * solution_density_kg_L * 1000.0 / atomic_weight
        canonical_unit = "wt_percent"
        assumptions.append("wt% is the mass fraction of elemental metal in the complete solution")
        assumptions.append("the supplied solution density converts solution mass to volume")
    else:
        raise ValueError("concentration unit must be log10_molar, molar, ppm, or wt_percent")
    if not math.isfinite(molar) or molar <= 0:
        raise ValueError("converted concentration must be positive and finite")
    return ConcentrationConversion(
        symbol=symbol,
        input_value=value,
        input_unit=canonical_unit,
        molar_concentration=molar,
        log10_standard_activity=math.log10(molar / 1.0),
        solution_density_kg_L=solution_density_kg_L,
        assumptions=tuple(assumptions),
    )


def express_concentration(
    symbol: str, molar: float, unit: str, *, solution_density_kg_L: float = 1.0
) -> float:
    """A molar metal concentration expressed in ``unit``; the inverse of :func:`convert_concentration`."""
    grams_per_litre = molar * ATOMIC_WEIGHT_G_MOL[symbol]
    values = {
        "log10_molar": math.log10(molar),
        "molar": molar,
        "ppm": grams_per_litre * 1000.0,
        "wt_percent": grams_per_litre / (10.0 * solution_density_kg_L),
    }
    if unit not in values:
        raise ValueError("concentration unit must be log10_molar, molar, ppm, or wt_percent")
    return values[unit]


def metal_molarity_from_mass(
    symbol: str, mass_g: float, solution_volume_L: float
) -> float:
    """Return molarity from grams of elemental metal and final solution volume."""
    symbol = symbol.strip()[:1].upper() + symbol.strip()[1:].lower()
    if symbol not in ATOMIC_WEIGHT_G_MOL:
        raise ValueError(f"No atomic weight is available for {symbol}")
    if not math.isfinite(mass_g) or mass_g <= 0:
        raise ValueError("metal mass must be positive and finite")
    if not math.isfinite(solution_volume_L) or solution_volume_L <= 0:
        raise ValueError("solution volume must be positive and finite")
    return mass_g / ATOMIC_WEIGHT_G_MOL[symbol] / solution_volume_L
