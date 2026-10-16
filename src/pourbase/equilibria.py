"""Adjacent phase reactions and activity-conditioned boundary equations.

Two species i and j are in equilibrium where G~_i = G~_j (Eq. 1). Writing
b_i = G~_i(pH = 0, E = 0) for the pH- and potential-independent part, the boundary is

    E = (b_j - b_i) / ((e_j - e_i) F) - (h_j - h_i) / (e_j - e_i) * (RT ln 10 / F) pH   (3)

when the electron coefficients differ, and the vertical line

    pH = (b_j - b_i) / ((h_j - h_i) RT ln 10)                                           (4)

when only the proton coefficients differ. Pairs are taken from neighbouring cells of the
calculated grid, so every reported equation belongs to a boundary that appears in the diagram.
"""


from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from .constants import FARADAY_C_MOL
from .database import ThermodynamicDatabase
from .engine import PourbaixDiagram, PourbaixEngine
from .models import ThermodynamicSpecies


@dataclass(frozen=True, slots=True)
class BoundaryEquation:
    """One equilibrium between adjacent domains under the diagram conditions."""

    left_record_id: str
    right_record_id: str
    left_species: str
    right_species: str
    reaction: str
    kind: str
    eh_intercept_V: float | None
    eh_slope_V_per_pH: float | None
    vertical_pH: float | None
    equation: str
    source_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "left_record_id": self.left_record_id,
            "right_record_id": self.right_record_id,
            "left_species": self.left_species,
            "right_species": self.right_species,
            "reaction": self.reaction,
            "kind": self.kind,
            "eh_intercept_V": self.eh_intercept_V,
            "eh_slope_V_per_pH": self.eh_slope_V_per_pH,
            "vertical_pH": self.vertical_pH,
            "equation": self.equation,
            "source_ids": list(self.source_ids),
        }


@dataclass(frozen=True, slots=True)
class PlatingPotential:
    """Activity-conditioned aqueous-ion/metal equilibrium at pH 0."""

    metal_record_id: str
    ion_record_id: str
    ion_species: str
    potential_V_vs_SHE: float
    reaction: str
    source_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "metal_record_id": self.metal_record_id,
            "ion_record_id": self.ion_record_id,
            "ion_species": self.ion_species,
            "potential_V_vs_SHE": self.potential_V_vs_SHE,
            "reaction": self.reaction,
            "source_ids": list(self.source_ids),
        }


def adjacent_species_pairs(indices: np.ndarray) -> tuple[tuple[int, int], ...]:
    """Return unique pairs whose grid cells share an edge."""
    pairs: set[tuple[int, int]] = set()
    for first, second in (
        (indices[:, :-1], indices[:, 1:]),
        (indices[:-1, :], indices[1:, :]),
    ):
        mask = first != second
        for left, right in zip(first[mask], second[mask]):
            pair = tuple(sorted((int(left), int(right))))
            pairs.add(pair)
    return tuple(sorted(pairs))


def _coefficient(value: float) -> str:
    fraction = Fraction(value).limit_denominator(24)
    if fraction == 1:
        return ""
    return f"{fraction} "


def _reaction(left: ThermodynamicSpecies, right: ThermodynamicSpecies) -> str:
    """Balance a component reaction per mole of metal, including free ligand."""
    left_scale = 1.0 / left.metal_count
    right_scale = 1.0 / right.metal_count
    oxygen_delta = (
        right.core_oxygen_count * right_scale
        - left.core_oxygen_count * left_scale
    )
    hydrogen_delta = (
        right.core_hydrogen_count * right_scale
        - left.core_hydrogen_count * left_scale
        - 2.0 * oxygen_delta
    )
    left_water, right_water = max(oxygen_delta, 0.0), max(-oxygen_delta, 0.0)
    left_proton, right_proton = max(hydrogen_delta, 0.0), max(-hydrogen_delta, 0.0)
    amounts: dict[str, float] = {}
    charges: dict[str, float] = {}
    for species, scale in ((left, -left_scale), (right, right_scale)):
        for component in species.components:
            key = component.ligand_id
            if key in charges and charges[key] != component.charge:
                raise ValueError(f"Inconsistent charge for buffered component {key}")
            amounts[key] = amounts.get(key, 0.0) + scale * component.count
            charges[key] = component.charge
    left_ligands = tuple((max(value, 0.0), key) for key, value in sorted(amounts.items()))
    right_ligands = tuple((max(-value, 0.0), key) for key, value in sorted(amounts.items()))
    left_charge = (left.charge * left_scale + left_proton
                   + sum(amount * charges[key] for amount, key in left_ligands))
    right_charge = (right.charge * right_scale + right_proton
                    + sum(amount * charges[key] for amount, key in right_ligands))
    left_electron, right_electron = (
        max(left_charge - right_charge, 0.0),
        max(right_charge - left_charge, 0.0),
    )
    def side(
        scale: float,
        species: ThermodynamicSpecies,
        water: float,
        proton: float,
        ligands: tuple[tuple[float, str], ...],
        electron: float,
    ) -> str:
        terms = [f"{_coefficient(scale)}{species.species}"]
        for amount, name in ((water, "H2O"), (proton, "H+"), *ligands, (electron, "e-")):
            if not math.isclose(amount, 0.0, abs_tol=1e-10):
                terms.append(f"{_coefficient(amount)}{name}")
        return " + ".join(terms)

    return (
        side(left_scale, left, left_water, left_proton, left_ligands, left_electron)
        + " ⇌ "
        + side(right_scale, right, right_water, right_proton, right_ligands, right_electron)
    )


def _one_boundary(
    diagram: PourbaixDiagram,
    database: ThermodynamicDatabase,
    left: ThermodynamicSpecies,
    right: ThermodynamicSpecies,
) -> BoundaryEquation:
    engine = PourbaixEngine(database)
    reference = database.reference_state

    def difference(pH: float, eh: float) -> float:
        return float(
            engine.transformed_gibbs_J_mol_metal(
                left, reference, diagram.conditions, pH, eh
            )
            - engine.transformed_gibbs_J_mol_metal(
                right, reference, diagram.conditions, pH, eh
            )
        )

    intercept = difference(0.0, 0.0)
    pH_coefficient = difference(1.0, 0.0) - intercept
    eh_coefficient = difference(0.0, 1.0) - intercept
    linear_check = difference(2.0, 0.0) - intercept - 2.0 * pH_coefficient
    sources = tuple(sorted({left.source_id, right.source_id}))
    reaction = _reaction(left, right)
    if not math.isclose(linear_check, 0.0, abs_tol=1e-5):
        return BoundaryEquation(
            left.record_id, right.record_id, left.species, right.species,
            reaction, "numerical", None, None, None,
            "Numerical boundary; pH-dependent ligand protonation makes it non-linear",
            sources,
        )
    if not math.isclose(eh_coefficient, 0.0, abs_tol=1e-10):
        eh_intercept = -intercept / eh_coefficient
        slope = -pH_coefficient / eh_coefficient
        equation = (f"Eh = {eh_intercept:+.4f} V vs SHE" if abs(slope) < 5e-7
                    else f"Eh = {eh_intercept:+.4f} {slope:+.4f}·pH V vs SHE")
        return BoundaryEquation(
            left.record_id, right.record_id, left.species, right.species,
            reaction, "nernst", eh_intercept, slope, None, equation, sources,
        )
    if not math.isclose(pH_coefficient, 0.0, abs_tol=1e-10):
        pH = -intercept / pH_coefficient
        return BoundaryEquation(
            left.record_id, right.record_id, left.species, right.species,
            reaction, "acid_base", None, None, pH, f"pH = {pH:.3f}", sources,
        )
    return BoundaryEquation(
        left.record_id, right.record_id, left.species, right.species,
        reaction, "degenerate", None, None, None,
        "No pH or Eh dependence under these conditions", sources,
    )


def boundary_equations(
    diagram: PourbaixDiagram, database: ThermodynamicDatabase
) -> tuple[BoundaryEquation, ...]:
    """Build equations only for phase pairs adjacent on the calculated grid."""
    return tuple(
        _one_boundary(diagram, database, diagram.system.species[left], diagram.system.species[right])
        for left, right in adjacent_species_pairs(diagram.stable_species_index)
    )


def plating_potentials(
    diagram: PourbaixDiagram, database: ThermodynamicDatabase
) -> tuple[PlatingPotential, ...]:
    """Return direct simple-cation/elemental-metal equilibria at configured activity."""
    metals = [
        item for item in diagram.system.species
        if not item.is_aqueous and item.is_ligand_free
        and math.isclose(item.charge, 0.0, abs_tol=1e-12)
        and math.isclose(item.core_oxygen_count, 0.0, abs_tol=1e-12)
        and math.isclose(item.core_hydrogen_count, 0.0, abs_tol=1e-12)
    ]
    ions = [
        item for item in diagram.system.species
        if item.is_aqueous and item.is_ligand_free
        and math.isclose(item.core_oxygen_count, 0.0, abs_tol=1e-12)
        and math.isclose(item.core_hydrogen_count, 0.0, abs_tol=1e-12)
        and item.electrons_per_metal > 0
    ]
    if not metals:
        return ()
    metal = min(metals, key=lambda item: item.gibbs_energy_J_mol / item.metal_count)
    reference = database.reference_state
    values = []
    for ion in ions:
        ion_energy = float(PourbaixEngine.transformed_gibbs_J_mol_metal(
            ion, reference, diagram.conditions, 0.0, 0.0
        ))
        metal_energy = float(PourbaixEngine.transformed_gibbs_J_mol_metal(
            metal, reference, diagram.conditions, 0.0, 0.0
        ))
        potential = (ion_energy - metal_energy) / (
            ion.electrons_per_metal * FARADAY_C_MOL
        )
        values.append(PlatingPotential(
            metal.record_id, ion.record_id, ion.species, potential,
            _reaction(ion, metal), tuple(sorted({metal.source_id, ion.source_id})),
        ))
    return tuple(sorted(values, key=lambda item: item.potential_V_vs_SHE))
