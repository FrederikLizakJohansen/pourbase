"""The stable species along a path through pH and potential, and the boundaries it crosses.

A path through points ``(pH, E)`` describes, for example, a potential sweep at fixed pH, an acid
or base titration at fixed potential, or both changing together. It joins its points with
straight segments, or with a smooth Catmull-Rom curve through all of them. For fixed-activity
diagrams the stable species follows from Eq. 2 at every sampled point and each crossing is
located by bisection between samples; for mass-balance diagrams it follows the calculated grid.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .engine import transformed_gibbs_J_mol_metal
from .equilibria import BoundaryEquation
from .models import ThermodynamicSpecies


@dataclass(frozen=True)
class Crossing:
    fraction: float  # position along the path, 0 at the start and 1 at the end
    pH: float
    eh_V: float
    before: ThermodynamicSpecies
    after: ThermodynamicSpecies
    boundary: BoundaryEquation | None


@dataclass(frozen=True)
class PhasePath:
    fraction: np.ndarray
    pH: np.ndarray
    eh_V: np.ndarray
    species: tuple[ThermodynamicSpecies, ...]
    stable_species_index: np.ndarray
    crossings: tuple[Crossing, ...]


def path_curve(vertices, smooth: bool = False, points: int = 401) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``(position, pH, Eh)`` sampled along a path through ``vertices``; ``position`` runs from 0 to 1.

    Each segment receives samples in proportion to its length, with pH and potential scaled by
    14 pH units and 3 V. ``smooth`` joins the points with a Catmull-Rom curve.
    """
    vertices = np.asarray(vertices, dtype=np.float64)
    if vertices.ndim != 2 or vertices.shape[1] != 2 or len(vertices) < 2:
        raise ValueError("a path needs at least two (pH, Eh) points")
    if points < 2:
        raise ValueError("a path needs at least two samples")
    scaled = vertices / np.array([14.0, 3.0])
    lengths = np.linalg.norm(np.diff(scaled, axis=0), axis=1)
    total = lengths.sum()
    knots = np.concatenate(([0.0], np.cumsum(lengths) / total)) if total > 0 else np.linspace(0, 1, len(vertices))
    position = np.linspace(0.0, 1.0, points)
    segment = np.clip(np.searchsorted(knots, position, side="right") - 1, 0, len(vertices) - 2)
    width = np.where(knots[segment + 1] > knots[segment], knots[segment + 1] - knots[segment], 1.0)
    t = (position - knots[segment]) / width
    p1, p2 = vertices[segment], vertices[segment + 1]
    if not smooth or len(vertices) == 2:
        curve = p1 + (p2 - p1) * t[:, None]
    else:
        padded = np.vstack((2 * vertices[0] - vertices[1], vertices, 2 * vertices[-1] - vertices[-2]))
        p0, p3 = padded[segment], padded[segment + 3]
        t = t[:, None]
        curve = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t**2
                       + (-p0 + 3 * p1 - 3 * p2 + p3) * t**3)
    return position, curve[:, 0], curve[:, 1]


def phase_path(calculation, *vertices: tuple[float, float], smooth: bool = False, points: int = 401) -> PhasePath:
    """Stable species along the path through ``vertices``, each ``(pH, Eh in V vs SHE)``."""
    diagram = calculation.diagram
    species = diagram.system.species
    vertices = tuple(vertices)
    fraction, pH, eh = path_curve(vertices, smooth, points)
    energies = getattr(diagram, "transformed_gibbs_J_mol_metal", None)
    exact = energies is not None and not calculation.is_mass_balance
    reference = calculation.database.reference_state

    def stable_at(pH_values, eh_values):
        if exact:
            stack = np.stack([transformed_gibbs_J_mol_metal(item, reference, diagram.conditions,
                                                            pH_values, eh_values) for item in species])
            return np.argmin(stack, axis=0)
        columns = np.abs(diagram.pH[None, :] - np.atleast_1d(pH_values)[:, None]).argmin(axis=1)
        rows = np.abs(diagram.eh_V[None, :] - np.atleast_1d(eh_values)[:, None]).argmin(axis=1)
        return diagram.stable_species_index[rows, columns]

    def at(position: float) -> tuple[float, float]:  # between samples the path is taken as straight
        return float(np.interp(position, fraction, pH)), float(np.interp(position, fraction, eh))

    stable = np.asarray(stable_at(pH, eh))
    boundaries = {frozenset((item.left_record_id, item.right_record_id)): item for item in calculation.boundaries}
    crossings = []
    for index in np.nonzero(stable[1:] != stable[:-1])[0]:
        low, high = fraction[index], fraction[index + 1]
        if exact:  # bisect to the point where the stable species changes
            first = stable[index]
            for _ in range(40):
                middle = (low + high) / 2
                x, y = at(middle)
                point = stable_at(np.array([x]), np.array([y]))[0]
                low, high = (middle, high) if point == first else (low, middle)
        position = (low + high) / 2
        x, y = at(position)
        before, after = species[int(stable[index])], species[int(stable[index + 1])]
        crossings.append(Crossing(float(position), x, y, before, after,
                                  boundaries.get(frozenset((before.record_id, after.record_id)))))
    return PhasePath(fraction, pH, eh, species, stable, tuple(crossings))
