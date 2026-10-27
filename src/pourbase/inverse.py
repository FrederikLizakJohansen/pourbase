"""Inverse questions: where a species or a kind of species is stable, and which elements satisfy a criterion.

A target is a set of species: one species, or a kind in the sense of Pourbaix's corrosion
diagrams. At each point the target holds with margin ``M`` when its lowest transformed Gibbs
energy (Eq. 1) lies at least ``M`` below that of every species outside it,

    min_{j ∉ T} G_j − min_{i ∈ T} G_i ≥ M,

so ``M = 0`` reproduces the stability region of Eq. 2. With ``k_sigma`` the margin is instead
required to exceed ``k`` combined standard uncertainties of the two competing species (Eq. 12).
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from .models import EvidenceStatus, ThermodynamicSpecies

KINDS = {
    "immunity": "Metal stable (immunity)",
    "passivation": "Solid compound stable (passivation)",
    "corrosion": "Dissolved (corrosion)",
    "solid": "Any solid or liquid stable",
}


def target_members(species: tuple[ThermodynamicSpecies, ...], target: str) -> np.ndarray:
    """Boolean mask of the species in ``target``: a kind from ``KINDS`` or a record ID."""
    if target == "immunity":
        return np.array([item.gibbs_status is EvidenceStatus.DEFINED_REFERENCE_STATE and item.is_condensed
                         for item in species])
    if target == "passivation":
        return np.array([item.is_condensed and item.gibbs_status is not EvidenceStatus.DEFINED_REFERENCE_STATE
                         for item in species])
    if target == "corrosion":
        return np.array([item.is_aqueous for item in species])
    if target == "solid":
        return np.array([item.is_condensed for item in species])
    members = np.array([item.record_id == target for item in species])
    if not members.any():
        raise ValueError(f"{target!r} is neither a kind ({', '.join(KINDS)}) nor a species of this system")
    return members


@dataclass(frozen=True)
class StabilityRegion:
    target: str
    pH: np.ndarray
    U_V: np.ndarray
    margin_J_mol_metal: np.ndarray  # (U, pH): the margin; negative where the target is not stable
    satisfied: np.ndarray  # (U, pH) boolean
    min_margin_J_mol: float
    k_sigma: float | None

    @property
    def fraction(self) -> float:
        return float(self.satisfied.mean())

    @property
    def pH_range(self) -> tuple[float, float] | None:
        columns = np.nonzero(self.satisfied.any(axis=0))[0]
        return (float(self.pH[columns[0]]), float(self.pH[columns[-1]])) if columns.size else None

    @property
    def U_range(self) -> tuple[float, float] | None:
        rows = np.nonzero(self.satisfied.any(axis=1))[0]
        return (float(self.U_V[rows[0]]), float(self.U_V[rows[-1]])) if rows.size else None


def stability_region(calculation, target: str, min_margin_J_mol: float = 0.0, k_sigma: float | None = None,
                     assumed_uncertainty_J_mol: float = 2000.0) -> StabilityRegion:
    """Where ``target`` is stable with at least ``min_margin_J_mol`` (or ``k_sigma`` uncertainties) to spare."""
    from .uncertainty import gibbs_uncertainty_J_mol

    diagram = calculation.diagram
    species = diagram.system.species
    members = target_members(species, target)
    energies = getattr(diagram, "transformed_gibbs_J_mol_metal", None)
    if energies is None or calculation.is_mass_balance:
        satisfied = members[diagram.stable_species_index]
        margin = np.where(satisfied, np.nan, -np.inf)
        return StabilityRegion(target, diagram.pH, diagram.U_V, margin, satisfied, 0.0, None)
    if members.all() or not members.any():
        satisfied = np.full(diagram.stable_species_index.shape, bool(members.all()))
        return StabilityRegion(target, diagram.pH, diagram.U_V, np.where(satisfied, np.inf, -np.inf), satisfied,
                               min_margin_J_mol, k_sigma)
    inside = np.where(members[:, None, None], energies, np.inf)
    outside = np.where(members[:, None, None], np.inf, energies)
    best_in, best_out = inside.min(axis=0), outside.min(axis=0)
    margin = best_out - best_in
    if k_sigma is None:
        satisfied = margin >= max(min_margin_J_mol, 0.0) if min_margin_J_mol > 0 else margin > 0
    else:
        sigma = np.array([gibbs_uncertainty_J_mol(item, assumed_uncertainty_J_mol)[0] / item.metal_count
                          for item in species])
        combined = np.hypot(sigma[inside.argmin(axis=0)], sigma[outside.argmin(axis=0)])
        satisfied = (margin > 0) & (margin >= k_sigma * combined)
    return StabilityRegion(target, diagram.pH, diagram.U_V, margin, satisfied, min_margin_J_mol, k_sigma)


@dataclass(frozen=True)
class WindowResult:
    symbol: str
    fraction: float | None  # share of the window where the criterion holds; None when not calculated
    minimum_margin_J_mol_metal: float | None  # smallest margin over the window
    note: str = ""


def screen_window(database, kind: str, pH: tuple[float, float], U_V: tuple[float, float],
                  min_margin_J_mol: float = 0.0, points: int = 21, **scenario) -> dict[str, WindowResult]:
    """For every element, the share of a pH–potential window where ``kind`` holds.

    ``scenario`` takes ``Scenario`` fields such as ``concentration``,
    ``ligands`` or ``temperature_K``; the diagrams are fixed-activity.
    """
    from .scenario import Mode, Scenario, calculate

    if kind not in KINDS:
        raise ValueError(f"kind must be one of {', '.join(KINDS)}")
    if not (pH[0] < pH[1] and U_V[0] < U_V[1]):
        raise ValueError("the window needs a lower and a higher pH and potential")
    results = {}
    for symbol, _name in database.available_systems():
        base = Scenario(symbol, mode=Mode.FIXED_ACTIVITY, pH_min=pH[0], pH_max=pH[1], U_min_V=U_V[0],
                        U_max_V=U_V[1], pH_points=points, U_points=points)
        try:
            calculation = calculate(replace(base, **scenario), database)
            region = stability_region(calculation, kind, min_margin_J_mol)
        except Exception as error:  # an element outside the model is reported, not fatal
            results[symbol] = WindowResult(symbol, None, None, str(error))
            continue
        finite = region.margin_J_mol_metal[np.isfinite(region.margin_J_mol_metal)]
        results[symbol] = WindowResult(symbol, region.fraction, float(finite.min()) if finite.size else None)
    return results
