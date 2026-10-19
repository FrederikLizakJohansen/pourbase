"""Soft-minimum view of fixed-activity Pourbaix grids.

At each grid point every species receives the weight

    w_i = exp[-(G~_i - G~_min) / epsilon] / sum_j exp[-(G~_j - G~_min) / epsilon]          (8)

with G~ from Eq. 1 and a blend width epsilon in J/mol per mole of metal. By default the sums run
over the dissolved species only, and only where a dissolved species is stable: a solid, liquid or
gas is a separate phase that forms when the solution saturates, so wherever one is stable it keeps
the whole weight and every edge involving it stays sharp. As epsilon -> 0 the sharp diagram is
recovered; a larger width blends in the dissolved species within a few epsilon of the minimum.

With epsilon = RT the weights of mononuclear dissolved species are their equilibrium fractions,
since the ratio of two aqueous activities is exp[-(G~_j - G~_i)/RT]; they then reproduce the
fractions of the closed mass balance (:func:`pourbase.speciation.metal_fraction_grid`) wherever no
solid precipitates. Other widths display energy differences.
"""


from __future__ import annotations

import math
import warnings
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from .constants import GAS_CONSTANT_J_MOL_K
from .engine import PourbaixDiagram
from .grid import nearest_index
from .models import ThermodynamicSpecies


FloatArray = npt.NDArray[np.float64]


def thermal_energy_J_mol(diagram: PourbaixDiagram) -> float:
    """RT at the temperature of ``diagram``, the default blend width."""
    return GAS_CONSTANT_J_MOL_K * diagram.conditions.temperature_K


@dataclass(frozen=True, slots=True)
class BoltzmannSmoothedDiagram:
    """Soft-minimum weights of one fixed-activity diagram for a blend width in J/mol.

    ``mixing_entropy_J_mol_K`` is R times the Shannon entropy of the weights, a measure of how
    many species share a point; it is a thermodynamic mixing entropy only where the weights are
    physical fractions (see the module documentation).
    """

    diagram: PourbaixDiagram
    width_J_mol: float
    weights: FloatArray
    soft_minimum_gibbs_J_mol_metal: FloatArray
    dominant_weight: FloatArray
    mixing_entropy_J_mol_K: FloatArray

    def __post_init__(self) -> None:
        if not math.isfinite(self.width_J_mol) or self.width_J_mol <= 0:
            raise ValueError("width_J_mol must be positive and finite")
        grid_shape = (self.diagram.U_V.size, self.diagram.pH.size)
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
    def thermal_scale(self) -> float:
        """The width in units of RT (deprecated; use ``width_J_mol``)."""
        return self.width_J_mol / thermal_energy_J_mol(self.diagram)

    @property
    def effective_thermal_energy_J_mol(self) -> float:
        """The blend width (deprecated name; use ``width_J_mol``)."""
        return self.width_J_mol

    @property
    def interpretation(self) -> str:
        return (
            "Soft-minimum weights over transformed Gibbs energies per mole of metal with a blend "
            f"width of {self.width_J_mol / 1000:.3g} kJ/mol. They display energy differences; "
            "they equal phase fractions only for mononuclear aqueous species at a width of RT "
            "where no solid precipitates."
        )

    def weights_at(
        self, pH: float, U_V: float
    ) -> tuple[tuple[ThermodynamicSpecies, float], ...]:
        """Return species and descending weight at one grid point."""
        row = nearest_index(self.diagram.U_V, U_V, "U_V")
        column = nearest_index(self.diagram.pH, pH, "pH")
        pairs = tuple(
            (species, float(self.weights[index, row, column]))
            for index, species in enumerate(self.diagram.system.species)
        )
        return tuple(sorted(pairs, key=lambda item: item[1], reverse=True))


def boltzmann_smooth(
    diagram: PourbaixDiagram,
    width_J_mol: float | None = None,
    *,
    blend_all_phases: bool = False,
    thermal_scale: float | None = None,
) -> BoltzmannSmoothedDiagram:
    """Soft-minimum weights ``exp(-(G - Gmin) / width)`` of a fixed-activity diagram.

    ``width_J_mol`` defaults to RT. With ``blend_all_phases`` the sums run over every species, so
    solids blend with the solution as well. ``thermal_scale`` gives the width in units of RT and is
    kept for compatibility. Subtracting the grid minimum gives the same normalized weights as the
    direct expression and prevents numerical overflow.
    """
    if thermal_scale is not None:
        warnings.warn("thermal_scale is deprecated; pass width_J_mol (thermal_scale * R * T)",
                      DeprecationWarning, stacklevel=2)
        if width_J_mol is not None:
            raise ValueError("give either width_J_mol or thermal_scale")
        width_J_mol = thermal_scale * thermal_energy_J_mol(diagram)
    if width_J_mol is None:
        width_J_mol = thermal_energy_J_mol(diagram)
    if not math.isfinite(width_J_mol) or width_J_mol <= 0:
        raise ValueError("width_J_mol must be positive and finite")
    energy_stack = diagram.transformed_gibbs_J_mol_metal
    if energy_stack is None:
        raise ValueError("the diagram was calculated without store_energies")
    minimum = diagram.minimum_transformed_gibbs_J_mol_metal
    stable = diagram.stable_species_index
    if blend_all_phases:
        blended = np.ones(len(diagram.system.species), dtype=bool)
        blend_here = np.ones(stable.shape, dtype=bool)
    else:
        blended = np.array([item.is_aqueous for item in diagram.system.species])
        blend_here = blended[stable]
    # Only the blended species carry weight; exp, sum and log run over them alone.
    unnormalized = energy_stack[blended] - minimum
    unnormalized *= -1.0 / width_J_mol
    np.exp(unnormalized, out=unnormalized)
    partition = unnormalized.sum(axis=0)
    unnormalized /= partition
    weights = np.zeros(energy_stack.shape, dtype=np.float64)
    weights[blended] = unnormalized
    weights *= blend_here
    rows, columns = np.nonzero(~blend_here)
    weights[stable[rows, columns], rows, columns] = 1.0
    soft_minimum = np.where(blend_here, minimum - width_J_mol * np.log(partition), minimum)
    dominant_weight = weights.max(axis=0)
    log_weights = np.zeros_like(unnormalized)
    np.log(unnormalized, out=log_weights, where=unnormalized > 0)
    log_weights *= unnormalized
    mixing_entropy = np.where(blend_here, -GAS_CONSTANT_J_MOL_K * log_weights.sum(axis=0), 0.0)
    for array in (weights, soft_minimum, dominant_weight, mixing_entropy):
        array.setflags(write=False)
    return BoltzmannSmoothedDiagram(
        diagram=diagram,
        width_J_mol=float(width_J_mol),
        weights=weights,
        soft_minimum_gibbs_J_mol_metal=soft_minimum,
        dominant_weight=dominant_weight,
        mixing_entropy_J_mol_K=mixing_entropy,
    )
