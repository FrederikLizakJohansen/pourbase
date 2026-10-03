"""How firmly each species is stable, given the uncertainties of the Gibbs energies.

Both functions work on fixed-activity diagrams calculated with stored energies. A species
without a reported uncertainty takes an assumed one, defined reference states are exact, and
the uncertainty of ligand reference energies is not included.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from .constants import FARADAY_C_MOL
from .engine import PourbaixDiagram
from .grid import nearest_index
from .models import EvidenceStatus, ThermodynamicSpecies

DEFAULT_ASSUMED_UNCERTAINTY_J_MOL = 2000.0


def gibbs_uncertainty_J_mol(species: ThermodynamicSpecies, assumed_J_mol: float) -> tuple[float, bool]:
    """``(uncertainty of ΔfG°, whether it is assumed)`` for one species."""
    if species.gibbs_status is EvidenceStatus.DEFINED_REFERENCE_STATE:
        return 0.0, False
    if species.gibbs_uncertainty_J_mol is not None:
        return species.gibbs_uncertainty_J_mol, False
    return assumed_J_mol, True


def _energies(diagram: PourbaixDiagram) -> npt.NDArray[np.float64]:
    energies = getattr(diagram, "transformed_gibbs_J_mol_metal", None)
    if energies is None:
        raise ValueError("Uncertainty analysis needs a fixed-activity diagram with stored energies")
    return energies


def _sigma_per_metal(diagram: PourbaixDiagram, assumed_J_mol: float) -> tuple[np.ndarray, tuple[str, ...]]:
    values, assumed = [], []
    for item in diagram.system.species:
        sigma, is_assumed = gibbs_uncertainty_J_mol(item, assumed_J_mol)
        values.append(sigma / item.metal_count)
        if is_assumed:
            assumed.append(item.record_id)
    return np.asarray(values), tuple(assumed)


@dataclass(frozen=True)
class StabilityUncertainty:
    """Grid points where another species lies within ``confidence_sigma`` combined uncertainties."""

    confidence_sigma: float
    assumed_uncertainty_J_mol: float
    uncertain: npt.NDArray[np.bool_]
    assumed_record_ids: tuple[str, ...]

    @property
    def uncertain_fraction(self) -> float:
        return float(self.uncertain.mean())


def stability_uncertainty(
    diagram: PourbaixDiagram,
    confidence_sigma: float = 1.0,
    assumed_uncertainty_J_mol: float = DEFAULT_ASSUMED_UNCERTAINTY_J_MOL,
) -> StabilityUncertainty:
    """Mark the points where the stable species could change within the stated uncertainties.

    A point is uncertain when some other species lies above the stable one by less than
    ``confidence_sigma`` times the combined uncertainty of the two, per mole of metal.
    """
    energies = _energies(diagram)
    sigma, assumed = _sigma_per_metal(diagram, assumed_uncertainty_J_mol)
    stable = diagram.stable_species_index
    gap = energies - energies.min(axis=0)
    combined = np.sqrt(sigma[stable][np.newaxis] ** 2 + sigma[:, np.newaxis, np.newaxis] ** 2)
    other = np.arange(len(sigma))[:, np.newaxis, np.newaxis] != stable[np.newaxis]
    uncertain = np.any(other & (gap < confidence_sigma * combined), axis=0)
    uncertain.setflags(write=False)
    return StabilityUncertainty(confidence_sigma, assumed_uncertainty_J_mol, uncertain, assumed)


@dataclass(frozen=True)
class NeighbourBoundary:
    """The next species along one axis and how far away its boundary lies."""

    species: ThermodynamicSpecies
    distance: float


@dataclass(frozen=True)
class StabilityMargin:
    """Why one species is stable at a point, and how firmly.

    ``margin_J_mol_metal`` is the energy above the stable species of the runner-up, the
    species with the next lowest energy; ``margin_uncertainty_J_mol_metal`` is their combined
    uncertainty. Potential distances are exact at the grid point; pH distances follow the grid.
    """

    pH: float
    eh_V: float
    species: ThermodynamicSpecies
    runner_up: ThermodynamicSpecies | None
    margin_J_mol_metal: float | None
    margin_uncertainty_J_mol_metal: float | None
    runner_up_uses_assumed_uncertainty: bool
    higher_potential: NeighbourBoundary | None
    lower_potential: NeighbourBoundary | None
    higher_pH: NeighbourBoundary | None
    lower_pH: NeighbourBoundary | None


def stability_margin(
    diagram: PourbaixDiagram,
    pH: float,
    eh_V: float,
    assumed_uncertainty_J_mol: float = DEFAULT_ASSUMED_UNCERTAINTY_J_MOL,
) -> StabilityMargin:
    """The runner-up species and the nearest boundaries at the grid point nearest to a coordinate."""
    energies = _energies(diagram)
    row = nearest_index(diagram.eh_V, eh_V, "eh_V")
    column = nearest_index(diagram.pH, pH, "pH")
    species = diagram.system.species
    point = energies[:, row, column]
    stable = int(diagram.stable_species_index[row, column])
    sigma, assumed = _sigma_per_metal(diagram, assumed_uncertainty_J_mol)

    runner_up = margin = margin_sigma = None
    if len(species) > 1:
        order = np.argsort(point)
        second = int(order[1] if order[0] == stable else order[0])
        runner_up = species[second]
        margin = float(point[second] - point[stable])
        margin_sigma = float(np.hypot(sigma[stable], sigma[second]))

    # At fixed pH every transformed energy is linear in Eh with slope -n F per mole of metal
    higher = lower = None
    electrons = species[stable].electrons_per_metal
    for index, item in enumerate(species):
        slope = (item.electrons_per_metal - electrons) * FARADAY_C_MOL
        if index == stable or slope == 0:
            continue
        shift = (point[index] - point[stable]) / slope
        crossing = float(diagram.eh_V[row] + shift - eh_V)
        if shift > 0 and (higher is None or crossing < higher.distance):
            higher = NeighbourBoundary(item, crossing)
        elif shift < 0 and (lower is None or crossing > lower.distance):
            lower = NeighbourBoundary(item, crossing)

    line = diagram.stable_species_index[row]
    changed = np.nonzero(line != stable)[0]
    right, left = changed[changed > column], changed[changed < column]
    higher_pH = NeighbourBoundary(species[int(line[right[0]])], float(diagram.pH[right[0]] - pH)) if right.size else None
    lower_pH = NeighbourBoundary(species[int(line[left[-1]])], float(diagram.pH[left[-1]] - pH)) if left.size else None

    return StabilityMargin(
        pH, eh_V, species[stable], runner_up, margin, margin_sigma,
        runner_up is not None and runner_up.record_id in assumed,
        higher, lower, higher_pH, lower_pH,
    )
