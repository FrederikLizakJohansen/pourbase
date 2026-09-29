"""Transparent Boltzmann-like smoothing of fixed-activity Pourbaix grids."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from .constants import GAS_CONSTANT_J_MOL_K
from .engine import PourbaixDiagram
from .models import ThermodynamicSpecies


FloatArray = npt.NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class BoltzmannSmoothedDiagram:
    """Soft-min view of one fixed-activity diagram.

    The weights compare transformed Gibbs energies normalized per mole of metal.
    They visualize energetic competition between entries. They do not represent
    conserved phase amounts or equilibrium mole fractions.
    """

    diagram: PourbaixDiagram
    thermal_scale: float
    weights: FloatArray
    soft_minimum_gibbs_J_mol_metal: FloatArray
    dominant_weight: FloatArray
    mixing_entropy_J_mol_K: FloatArray

    def __post_init__(self) -> None:
        if not math.isfinite(self.thermal_scale) or self.thermal_scale <= 0:
            raise ValueError("thermal_scale must be positive and finite")
        grid_shape = (self.diagram.eh_V.size, self.diagram.pH.size)
        if self.weights.shape != (len(self.diagram.system.species), *grid_shape):
            raise ValueError("weights shape does not match the source diagram")
        for name, value in (
            ("soft minimum", self.soft_minimum_gibbs_J_mol_metal),
            ("dominant weight", self.dominant_weight),
            ("mixing entropy", self.mixing_entropy_J_mol_K),
        ):
            if value.shape != grid_shape:
                raise ValueError(f"{name} shape does not match the source diagram")

    @property
    def effective_thermal_energy_J_mol(self) -> float:
        return (
            self.thermal_scale
            * GAS_CONSTANT_J_MOL_K
            * self.diagram.conditions.temperature_K
        )

    @property
    def interpretation(self) -> str:
        return (
            "Boltzmann-like soft-min weights over transformed Gibbs energies per "
            "mole of metal; these are energetic-competition weights, not phase "
            "fractions or a closed mass-balance result. The blend depends on the "
            "set of species supplied to the calculation."
        )

    def weights_at(
        self, pH: float, eh_V: float
    ) -> tuple[tuple[ThermodynamicSpecies, float], ...]:
        """Return species and descending soft-min weight at one grid point."""
        if not math.isfinite(pH) or not math.isfinite(eh_V):
            raise ValueError("pH and eh_V must be finite")
        if not self.diagram.pH[0] <= pH <= self.diagram.pH[-1]:
            raise ValueError("pH lies outside the diagram")
        if not self.diagram.eh_V[0] <= eh_V <= self.diagram.eh_V[-1]:
            raise ValueError("eh_V lies outside the diagram")
        pH_index = int(np.abs(self.diagram.pH - pH).argmin())
        eh_index = int(np.abs(self.diagram.eh_V - eh_V).argmin())
        pairs = tuple(
            (species, float(self.weights[index, eh_index, pH_index]))
            for index, species in enumerate(self.diagram.system.species)
        )
        return tuple(sorted(pairs, key=lambda item: item[1], reverse=True))


def boltzmann_smooth(
    diagram: PourbaixDiagram, thermal_scale: float = 1.0
) -> BoltzmannSmoothedDiagram:
    """Return stable softmax weights ``exp(-(G-Gmin)/(scale*R*T))``.

    Subtracting the grid minimum gives the same normalized weights as the direct
    Boltzmann expression and prevents numerical overflow.
    """
    if not math.isfinite(thermal_scale) or thermal_scale <= 0:
        raise ValueError("thermal_scale must be positive and finite")
    energy_stack = diagram.transformed_gibbs_J_mol_metal
    if energy_stack is None:
        raise ValueError(
            "the source diagram does not contain its transformed Gibbs grid"
        )
    effective_rt = (
        thermal_scale * GAS_CONSTANT_J_MOL_K * diagram.conditions.temperature_K
    )
    delta = energy_stack - diagram.minimum_transformed_gibbs_J_mol_metal[None, :, :]
    unnormalized = np.exp(-delta / effective_rt)
    partition = np.sum(unnormalized, axis=0, keepdims=True)
    weights = np.asarray(unnormalized / partition, dtype=np.float64)
    soft_minimum = np.asarray(
        diagram.minimum_transformed_gibbs_J_mol_metal
        - effective_rt * np.log(partition[0]),
        dtype=np.float64,
    )
    dominant_weight = np.asarray(np.max(weights, axis=0), dtype=np.float64)
    log_weights = np.zeros_like(weights)
    np.log(weights, out=log_weights, where=weights > 0)
    mixing_entropy = np.asarray(
        -GAS_CONSTANT_J_MOL_K * np.sum(weights * log_weights, axis=0),
        dtype=np.float64,
    )
    for array in (weights, soft_minimum, dominant_weight, mixing_entropy):
        array.setflags(write=False)
    return BoltzmannSmoothedDiagram(
        diagram=diagram,
        thermal_scale=thermal_scale,
        weights=weights,
        soft_minimum_gibbs_J_mol_metal=soft_minimum,
        dominant_weight=dominant_weight,
        mixing_entropy_J_mol_K=mixing_entropy,
    )
