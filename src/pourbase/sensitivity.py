"""Where a diagram is not fixed by the published data.

For every species with several eligible Gibbs energies, another published value shifts its
transformed Gibbs energy (Eq. 1) by the same amount, ``(G_alt - G_used) / m_i``, at every point of
the diagram. A selection of eligible values therefore needs no new calculation: the stored
energies plus one constant per species give the stable species directly.

``selection_sensitivity`` draws random selections, one eligible value per species, and reports
at each grid point the share of selections whose stable species differs from the diagram's. It
also reports, for each species, the share of the diagram that changes when its value alone is
replaced by the eligible value farthest from the one in use.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

import numpy as np

GIBBS = "gibbs_energy_of_formation"


@dataclass(frozen=True)
class AlternativeValue:
    value_J_mol: float
    source_id: str
    citation: str
    evidence_class: str
    in_use: bool


@dataclass(frozen=True)
class SpeciesSensitivity:
    """One species with several eligible Gibbs energies and what replacing its value does."""

    record_id: str
    species: str
    alternatives: tuple[AlternativeValue, ...]
    spread_J_mol: float
    changed_fraction_alone: float


@dataclass(frozen=True)
class SelectionSensitivity:
    pH: np.ndarray
    U_V: np.ndarray
    changed_fraction: np.ndarray  # (U, pH): share of selections with another stable species
    samples: int
    species: tuple[SpeciesSensitivity, ...]

    @property
    def unfixed_fraction(self) -> float:
        """Share of the diagram whose stable species depends on the selection."""
        return float((self.changed_fraction > 0).mean())


def selection_sensitivity(
    diagram,
    selections: Mapping,
    samples: int = 200,
    seed: int = 1,
    classes: set[str] | None = None,
    progress: Callable[[float], bool] | None = None,
) -> SelectionSensitivity:
    """Sensitivity of a fixed-activity ``diagram`` to the choice between eligible Gibbs energies.

    ``selections`` maps ``(record_id, property)`` to the ``Selection`` of
    a policy, for example ``database.selections``. ``classes`` limits the alternatives to some
    evidence classes, such as ``{"A", "B", "C"}``. ``progress(fraction)`` may return False to stop.
    """
    energies = getattr(diagram, "transformed_gibbs_J_mol_metal", None)
    if energies is None:
        raise ValueError("Selection sensitivity needs a fixed-activity diagram with stored energies")
    species = diagram.system.species
    base = diagram.stable_species_index
    offsets: list[np.ndarray] = []
    indices: list[int] = []
    entries: list[SpeciesSensitivity] = []
    for index, item in enumerate(species):
        selection = selections.get((item.record_id, GIBBS))
        if selection is None:
            continue
        candidates = [c for c in selection.candidates if classes is None or c.evidence_class in classes]
        values = sorted({round(c.value, 3) for c in candidates})
        if len(values) < 2:
            continue
        used = selection.chosen.value if selection.chosen is not None else item.gibbs_energy_J_mol
        deltas = np.array([c.value - used for c in candidates]) / item.metal_count
        farthest = deltas[int(np.argmax(np.abs(deltas)))]
        shifted = energies.copy()
        shifted[index] += farthest
        alone = float((np.argmin(shifted, axis=0) != base).mean())
        entries.append(SpeciesSensitivity(
            item.record_id, item.species,
            tuple(AlternativeValue(c.value, c.source_id, c.citation, c.evidence_class,
                                   abs(c.value - used) < 1e-6) for c in candidates),
            max(values) - min(values), alone))
        offsets.append(deltas)
        indices.append(index)
    changed = np.zeros(base.shape)
    if indices:
        rng = np.random.default_rng(seed)
        selected = energies[indices]
        others = np.delete(np.arange(len(species)), indices)
        rest_min = energies[others].min(axis=0) if others.size else np.full(base.shape, np.inf)
        rest_arg = others[energies[others].argmin(axis=0)] if others.size else np.zeros(base.shape, int)
        for sample in range(samples):
            shift = np.array([rng.choice(deltas) for deltas in offsets])
            trial = selected + shift[:, None, None]
            best = trial.argmin(axis=0)
            best_energy = np.take_along_axis(trial, best[None], axis=0)[0]
            stable = np.where(best_energy < rest_min, np.asarray(indices)[best], rest_arg)
            changed += stable != base
            if progress is not None and sample % 10 == 0 and progress(sample / samples) is False:
                break
        changed /= samples
    entries.sort(key=lambda entry: -entry.changed_fraction_alone)
    return SelectionSensitivity(diagram.pH, diagram.U_V, changed, samples if indices else 0, tuple(entries))


def point_outcomes(
    diagram,
    selections: Mapping,
    row: int,
    column: int,
    samples: int = 300,
    seed: int = 1,
    classes: set[str] | None = None,
) -> dict[str, float]:
    """Share of random selections in which each species is stable at one grid point, largest first."""
    energies = diagram.transformed_gibbs_J_mol_metal[:, row, column]
    species = diagram.system.species
    offsets = []
    for item in species:
        selection = selections.get((item.record_id, GIBBS))
        candidates = [c for c in (selection.candidates if selection else ())
                      if classes is None or c.evidence_class in classes]
        if len({round(c.value, 3) for c in candidates}) < 2:
            offsets.append(np.zeros(1))
        else:
            offsets.append(np.array([c.value - item.gibbs_energy_J_mol for c in candidates]) / item.metal_count)
    rng = np.random.default_rng(seed)
    counts = np.zeros(len(species))
    for _sample in range(samples):
        shift = np.array([rng.choice(values) for values in offsets])
        counts[int(np.argmin(energies + shift))] += 1
    order = np.argsort(-counts)
    return {species[index].species: counts[index] / samples for index in order if counts[index]}
