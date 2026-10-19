"""Database-derived metal speciation views for mass-balanced diagrams."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from .grid import nearest_index
from .mass_balance import MassBalancedPourbaixDiagram
from .models import ThermodynamicSpecies


FloatArray = npt.NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class SpeciationProfile:
    """Metal fractions along pH at one U, derived from curated Gibbs records."""

    U_V: float
    pH: FloatArray
    species: tuple[ThermodynamicSpecies, ...]
    metal_fraction: FloatArray

    def __post_init__(self) -> None:
        if self.metal_fraction.shape != (len(self.species), self.pH.size):
            raise ValueError("speciation profile has the wrong shape")
        if np.any(self.metal_fraction < 0) or np.any(self.metal_fraction > 1):
            raise ValueError("speciation fractions must lie between zero and one")
        if not np.allclose(self.metal_fraction.sum(axis=0), 1.0, atol=1e-10):
            raise ValueError("speciation fractions must conserve total metal")


def _metal_fractions(
    diagram: MassBalancedPourbaixDiagram, rows: slice | int, columns: slice | int
) -> FloatArray:
    """Fraction of the total metal held by each species on part of the grid."""
    concentration = diagram.aqueous_concentration_mol_L[:, rows, columns]
    solid = diagram.precipitating_solid_index[rows, columns]
    precipitated = diagram.precipitated_metal_fraction[rows, columns]
    fractions = np.zeros((len(diagram.system.species), *np.shape(solid)), dtype=np.float64)
    fractions[diagram.aqueous_species_indices] = concentration / diagram.total_metal.total_metal_mol_L
    for index, species in enumerate(diagram.system.species):
        if not species.is_aqueous:
            fractions[index] = np.where(solid == index, precipitated, 0.0)
    return fractions


def metal_fraction_grid(diagram: MassBalancedPourbaixDiagram) -> FloatArray:
    """Fraction of the total metal held by each species at every grid point."""
    fractions = _metal_fractions(diagram, slice(None), slice(None))
    fractions.setflags(write=False)
    return fractions


def dissolved_blend_weights(diagram: MassBalancedPourbaixDiagram) -> FloatArray:
    """Weights for coloring a closed-balance diagram by its dissolved fractions.

    Where no solid precipitates, the weights are the fractions of the dissolved species (they sum
    to one). Where a solid precipitates, it is a separate phase and takes the whole weight, so
    every edge between solid and solution stays sharp.
    """
    fractions = np.array(_metal_fractions(diagram, slice(None), slice(None)))
    solid = diagram.precipitating_solid_index
    precipitating = solid >= 0
    one_hot = np.zeros_like(fractions)
    np.put_along_axis(one_hot, np.where(precipitating, solid, 0)[None, :, :], 1.0, axis=0)
    weights = np.where(precipitating[None, :, :], one_hot, fractions)
    weights.setflags(write=False)
    return weights


def speciation_profile(diagram: MassBalancedPourbaixDiagram, U_V: float) -> SpeciationProfile:
    """Metal fractions along pH at the grid U nearest to ``U_V``."""
    row = nearest_index(diagram.U_V, U_V, "U_V")
    fractions = _metal_fractions(diagram, row, slice(None))
    active = fractions.max(axis=1) > 1e-12
    profile = fractions[active]
    profile.setflags(write=False)
    return SpeciationProfile(
        U_V=float(diagram.U_V[row]),
        pH=diagram.pH,
        species=tuple(item for index, item in enumerate(diagram.system.species) if active[index]),
        metal_fraction=profile,
    )


def speciation_at(
    diagram: MassBalancedPourbaixDiagram, pH: float, U_V: float
) -> tuple[dict[str, object], ...]:
    """Sourced metal fractions at one point, largest first, including a precipitated solid."""
    row = nearest_index(diagram.U_V, U_V, "U_V")
    column = nearest_index(diagram.pH, pH, "pH")
    fractions = _metal_fractions(diagram, row, column)
    total = diagram.total_metal.total_metal_mol_L
    rows = [
        {
            "record_id": species.record_id,
            "species": species.species,
            "phase": species.phase,
            "metal_fraction": float(fraction),
            "metal_concentration_mol_L": float(fraction) * total,
            "gibbs_source_id": species.source_id,
            "gibbs_status": species.gibbs_status.value,
        }
        for species, fraction in zip(diagram.system.species, fractions)
        if fraction > 1e-15
    ]
    return tuple(sorted(rows, key=lambda item: item["metal_fraction"], reverse=True))


def plot_speciation_profile(
    profile: SpeciationProfile, *, ax: object | None = None, title: str | None = None
) -> object:
    """Plot sourced species fractions along pH at a fixed U."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise ImportError("Plotting requires Matplotlib") from error
    if ax is None:
        _, ax = plt.subplots(figsize=(8.2, 4.8), constrained_layout=True)
    for species, fraction in zip(profile.species, profile.metal_fraction):
        ax.plot(profile.pH, fraction, label=species.species, linewidth=1.8)
    ax.set(
        xlabel="pH",
        ylabel="fraction of total metal",
        ylim=(0.0, 1.02),
        title=title or f"Metal speciation at U = {profile.U_V:g} V vs SHE",
    )
    ax.legend(fontsize=7, loc="best")
    ax.grid(alpha=0.2)
    return ax
