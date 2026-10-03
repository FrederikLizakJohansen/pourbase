"""Potential scales for displaying diagrams calculated against the SHE, independent of Qt.

Fixed reference electrodes shift the potential axis. The RHE scale moves with pH, so a
diagram is resampled onto it, and points outside the calculated SHE window stay empty.
"""

from __future__ import annotations

import numpy as np

from ..constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10

# Potentials of the reference electrodes against the SHE at 25 °C, in V
REFERENCE_ELECTRODES_V = {
    "SHE": 0.0,
    "RHE": None,
    "Ag/AgCl (sat. KCl)": 0.197,
    "Ag/AgCl (3 M KCl)": 0.210,
    "SCE (sat. KCl)": 0.241,
    "Hg/HgO (1 M KOH)": 0.098,
}


def nernst_slope_V(temperature_K: float = 298.15) -> float:
    return GAS_CONSTANT_J_MOL_K * temperature_K * LN_10 / FARADAY_C_MOL


def axis_label(scale: str) -> str:
    return f"E (V vs {scale})"


def to_scale(eh_V, pH, scale: str, temperature_K: float = 298.15):
    """Potentials against the SHE expressed on ``scale``."""
    offset = REFERENCE_ELECTRODES_V[scale]
    if offset is None:
        return np.asarray(eh_V) + nernst_slope_V(temperature_K) * np.asarray(pH)
    return np.asarray(eh_V) - offset


def from_scale(potential_V, pH, scale: str, temperature_K: float = 298.15):
    """Potentials on ``scale`` expressed against the SHE."""
    offset = REFERENCE_ELECTRODES_V[scale]
    if offset is None:
        return np.asarray(potential_V) - nernst_slope_V(temperature_K) * np.asarray(pH)
    return np.asarray(potential_V) + offset


def resample(pH: np.ndarray, eh_V: np.ndarray, scale: str, temperature_K: float = 298.15
             ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``(potential axis, source row per point, valid)`` for showing an SHE grid on ``scale``.

    Index a grid with ``grid[rows, columns]`` (columns from ``np.arange(pH.size)``) to move
    it onto the new axis; ``valid`` is False where the point lies outside the SHE window.
    """
    if REFERENCE_ELECTRODES_V[scale] is not None:
        rows = np.broadcast_to(np.arange(eh_V.size)[:, np.newaxis], (eh_V.size, pH.size))
        return to_scale(eh_V, 0.0, scale), rows, np.ones(rows.shape, dtype=bool)
    axis = eh_V.copy()
    source = from_scale(axis[:, np.newaxis], pH[np.newaxis, :], scale, temperature_K)
    step = (eh_V[-1] - eh_V[0]) / max(eh_V.size - 1, 1)
    rows = np.rint((source - eh_V[0]) / step).astype(int)
    valid = (rows >= 0) & (rows < eh_V.size)
    return axis, np.clip(rows, 0, eh_V.size - 1), valid
