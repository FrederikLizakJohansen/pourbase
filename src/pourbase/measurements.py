"""Measured conditions placed on a diagram: the predicted species at each point and how firmly it is predicted."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .models import ThermodynamicSpecies
from .uncertainty import DEFAULT_ASSUMED_UNCERTAINTY_J_MOL, stability_margin


@dataclass(frozen=True)
class MeasuredPoint:
    label: str
    pH: float
    eh_V: float  # V vs SHE


@dataclass(frozen=True)
class PointAssessment:
    point: MeasuredPoint
    inside: bool  # within the pH and potential window of the diagram
    species: ThermodynamicSpecies | None
    runner_up: ThermodynamicSpecies | None = None
    margin_J_mol_metal: float | None = None
    margin_uncertainty_J_mol_metal: float | None = None

    @property
    def within_uncertainty(self) -> bool:
        """True when the runner-up lies within one combined standard uncertainty (Eq. 12, k = 1)."""
        return (self.margin_J_mol_metal is not None and self.margin_uncertainty_J_mol_metal is not None
                and self.margin_J_mol_metal < self.margin_uncertainty_J_mol_metal)


def assess_points(calculation, points, assumed_uncertainty_J_mol: float = DEFAULT_ASSUMED_UNCERTAINTY_J_MOL
                  ) -> tuple[PointAssessment, ...]:
    """The predicted species at each measured point; fixed-activity diagrams add the margin to the runner-up."""
    diagram = calculation.diagram
    results = []
    for point in points:
        inside = bool(diagram.pH[0] <= point.pH <= diagram.pH[-1] and diagram.eh_V[0] <= point.eh_V <= diagram.eh_V[-1])
        if not inside:
            results.append(PointAssessment(point, False, None))
            continue
        if calculation.is_mass_balance:
            row = int(np.abs(diagram.eh_V - point.eh_V).argmin())
            column = int(np.abs(diagram.pH - point.pH).argmin())
            species = diagram.system.species[int(diagram.stable_species_index[row, column])]
            results.append(PointAssessment(point, True, species))
            continue
        margin = stability_margin(diagram, point.pH, point.eh_V, assumed_uncertainty_J_mol)
        results.append(PointAssessment(point, True, margin.species, margin.runner_up, margin.margin_J_mol_metal,
                                       margin.margin_uncertainty_J_mol_metal))
    return tuple(results)
