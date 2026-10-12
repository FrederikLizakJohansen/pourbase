"""pH/Eh grids, water-stability lines and phase boundaries shared by the engines.

A diagram is evaluated at the centres of a regular pH x E grid. Each grid value is the centre of
a rectangular cell, and :func:`phase_boundary_segments` draws a line segment along every cell
edge that separates two different stable species. The drawn lines therefore follow the exact
boundaries of Eqs. 3 and 4 to within half a grid step; the equations themselves come from
:mod:`pourbase.equilibria`. Water is stable between the hydrogen and oxygen lines

    E_H2 = -(RT ln 10 / F) pH,    E_O2 = -G_H2O / (2F) - (RT ln 10 / F) pH .           (5)
"""


from __future__ import annotations

import math

import numpy as np
import numpy.typing as npt

from .constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10, WATER_GIBBS_ENERGY_J_MOL

FloatArray = npt.NDArray[np.float64]


def readonly(array: npt.ArrayLike, dtype: npt.DTypeLike = None) -> np.ndarray:
    result = np.asarray(array, dtype=dtype)
    result.setflags(write=False)
    return result


def grid_axes(conditions) -> tuple[FloatArray, FloatArray]:
    """The pH and Eh axes of a calculation."""
    return (
        readonly(np.linspace(conditions.pH_min, conditions.pH_max, conditions.pH_points)),
        readonly(np.linspace(conditions.eh_min_V, conditions.eh_max_V, conditions.eh_points)),
    )


def nernst_slope_V(temperature_K: float) -> float:
    """RT ln(10) / F in volts per pH unit."""
    return GAS_CONSTANT_J_MOL_K * temperature_K * LN_10 / FARADAY_C_MOL


def water_lines(
    pH: FloatArray, temperature_K: float, water_gibbs_energy_J_mol: float = WATER_GIBBS_ENERGY_J_MOL
) -> tuple[FloatArray, FloatArray]:
    """Hydrogen and oxygen evolution potentials (V vs SHE) along ``pH``."""
    slope = nernst_slope_V(temperature_K)
    oxygen_standard_V = -water_gibbs_energy_J_mol / (2 * FARADAY_C_MOL)
    return readonly(-slope * pH), readonly(oxygen_standard_V - slope * pH)


def nearest_index(values: FloatArray, requested: float, name: str) -> int:
    """Index of the grid value nearest to ``requested``; the value must lie on the grid."""
    if not math.isfinite(requested):
        raise ValueError(f"{name} must be finite")
    if not values[0] <= requested <= values[-1]:
        raise ValueError(f"{name} lies outside the diagram")
    return int(np.abs(values - requested).argmin())


def cell_edges(coordinates: FloatArray) -> FloatArray:
    """Cell edges for monotonically increasing cell-centre coordinates."""
    midpoints = (coordinates[:-1] + coordinates[1:]) / 2.0
    return np.concatenate((
        [coordinates[0] - (coordinates[1] - coordinates[0]) / 2.0],
        midpoints,
        [coordinates[-1] + (coordinates[-1] - coordinates[-2]) / 2.0],
    ))


def phase_boundary_segments(
    regions: np.ndarray, x: FloatArray, y: FloatArray
) -> np.ndarray:
    """Line segments between unlike neighbouring cells, shaped ``(n, 2, 2)``."""
    x_edges, y_edges = cell_edges(x), cell_edges(y)
    rows, columns = np.nonzero(regions[:, 1:] != regions[:, :-1])
    vertical = np.stack((
        np.column_stack((x_edges[columns + 1], y_edges[rows])),
        np.column_stack((x_edges[columns + 1], y_edges[rows + 1])),
    ), axis=1)
    rows, columns = np.nonzero(regions[1:, :] != regions[:-1, :])
    horizontal = np.stack((
        np.column_stack((x_edges[columns], y_edges[rows + 1])),
        np.column_stack((x_edges[columns + 1], y_edges[rows + 1])),
    ), axis=1)
    return np.concatenate((vertical, horizontal)).astype(np.float64)
