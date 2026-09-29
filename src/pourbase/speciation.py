"""Database-derived metal speciation views for mass-balanced diagrams."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from .mass_balance import MassBalancedPourbaixDiagram
from .models import ThermodynamicSpecies


FloatArray = npt.NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class SpeciationProfile:
    """Metal fractions along pH at one Eh, derived from curated Gibbs records."""

    eh_V: float
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


def metal_fraction_grid(diagram: MassBalancedPourbaixDiagram) -> FloatArray:
    """Return one metal-inventory fraction grid per included species."""
    fractions = np.zeros(
        (len(diagram.system.species), diagram.eh_V.size, diagram.pH.size),
        dtype=np.float64,
    )
    total = diagram.total_metal.total_metal_mol_L
    for local_index, system_index in enumerate(diagram.aqueous_species_indices):
        fractions[int(system_index)] = (
            diagram.aqueous_concentration_mol_L[local_index] / total
        )
    for system_index, species in enumerate(diagram.system.species):
        if species.is_aqueous:
            continue
        fractions[system_index] = np.where(
            diagram.precipitating_solid_index == system_index,
            diagram.precipitated_metal_fraction,
            0.0,
        )
    fractions.setflags(write=False)
    return fractions


def speciation_profile(
    diagram: MassBalancedPourbaixDiagram, eh_V: float
) -> SpeciationProfile:
    """Extract pH-dependent metal fractions at the nearest calculated Eh."""
    if not math.isfinite(eh_V) or not diagram.eh_V[0] <= eh_V <= diagram.eh_V[-1]:
        raise ValueError("eh_V lies outside the diagram")
    eh_index = int(np.abs(diagram.eh_V - eh_V).argmin())
    fractions = metal_fraction_grid(diagram)[:, eh_index, :]
    active = np.max(fractions, axis=1) > 1e-12
    profile_fractions = np.asarray(fractions[active], dtype=np.float64)
    profile_fractions.setflags(write=False)
    return SpeciationProfile(
        eh_V=float(diagram.eh_V[eh_index]),
        pH=diagram.pH,
        species=tuple(
            item for index, item in enumerate(diagram.system.species) if active[index]
        ),
        metal_fraction=profile_fractions,
    )


def speciation_at(
    diagram: MassBalancedPourbaixDiagram, pH: float, eh_V: float
) -> tuple[dict[str, object], ...]:
    """Return sourced metal fractions at one point, including precipitated solids."""
    if not diagram.pH[0] <= pH <= diagram.pH[-1]:
        raise ValueError("pH lies outside the diagram")
    if not diagram.eh_V[0] <= eh_V <= diagram.eh_V[-1]:
        raise ValueError("eh_V lies outside the diagram")
    pH_index = int(np.abs(diagram.pH - pH).argmin())
    eh_index = int(np.abs(diagram.eh_V - eh_V).argmin())
    fractions = metal_fraction_grid(diagram)[:, eh_index, pH_index]
    rows = []
    for index, species in enumerate(diagram.system.species):
        fraction = float(fractions[index])
        if fraction <= 1e-15:
            continue
        rows.append({
            "record_id": species.record_id,
            "species": species.species,
            "phase": species.phase,
            "metal_fraction": fraction,
            "metal_concentration_mol_L": (
                fraction * diagram.total_metal.total_metal_mol_L
            ),
            "gibbs_source_id": species.source_id,
            "gibbs_status": species.gibbs_status,
        })
    return tuple(sorted(rows, key=lambda item: float(item["metal_fraction"]), reverse=True))


def plot_speciation_profile(
    profile: SpeciationProfile, *, ax: object | None = None, title: str | None = None
) -> object:
    """Plot sourced species fractions along pH at a fixed Eh."""
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
        title=title or f"Metal speciation at Eh = {profile.eh_V:g} V vs SHE",
    )
    ax.legend(fontsize=7, loc="best")
    ax.grid(alpha=0.2)
    return ax
