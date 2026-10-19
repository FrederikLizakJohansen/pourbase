"""Concentration sweeps and three-dimensional Pourbaix views."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

import numpy as np
import numpy.typing as npt

from .database import ThermodynamicDatabase
from .engine import PourbaixDiagram, PourbaixEngine
from .exceptions import CalculationCancelled
from .grid import phase_boundary_segments
from .models import AqueousActivityModel, GibbsEnergyPolicy, PourbaixConditions, ThermodynamicSpecies
from .plotting import species_colors

MAX_SWEEP_POINTS = 201


FloatArray = npt.NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class ConcentrationSweep:
    """A common pH/U grid evaluated at several default aqueous activities."""

    log10_activities: FloatArray
    diagrams: tuple[PourbaixDiagram, ...]

    def __post_init__(self) -> None:
        if self.log10_activities.ndim != 1 or self.log10_activities.size != len(self.diagrams):
            raise ValueError("activity levels and diagrams must have matching lengths")
        if len(self.diagrams) < 2:
            raise ValueError("a concentration sweep requires at least two levels")
        first = self.diagrams[0]
        for diagram in self.diagrams[1:]:
            if diagram.system.symbol != first.system.symbol:
                raise ValueError("all sweep diagrams must use the same element")
            if not np.array_equal(diagram.pH, first.pH) or not np.array_equal(diagram.U_V, first.U_V):
                raise ValueError("all sweep diagrams must use the same grid")

    @property
    def system(self):
        return self.diagrams[0].system

    @property
    def pH(self) -> FloatArray:
        return self.diagrams[0].pH

    @property
    def U_V(self) -> FloatArray:
        return self.diagrams[0].U_V

    @property
    def stable_species(self) -> tuple[ThermodynamicSpecies, ...]:
        identifiers = {
            item.record_id for diagram in self.diagrams for item in diagram.stable_species
        }
        return tuple(item for item in self.system.species if item.record_id in identifiers)


class ConcentrationSweepEngine:
    """Fixed-activity diagrams over a range of the default aqueous metal activity."""

    def __init__(self, database: ThermodynamicDatabase) -> None:
        self.database = database
        self.engine = PourbaixEngine(database)

    def calculate(
        self,
        symbol: str,
        conditions: PourbaixConditions,
        log10_activity_min: float,
        log10_activity_max: float,
        points: int = 7,
        *,
        allow_incomplete: bool = True,
        energy_policy: GibbsEnergyPolicy | str = GibbsEnergyPolicy.EXPERIMENTAL_ONLY,
        store_energies: bool = False,
        progress: Callable[[float], bool | None] | None = None,
    ) -> ConcentrationSweep:
        """Calculate ``points`` evenly spaced activity levels.

        Diagrams are stored without their energy stacks unless ``store_energies``.
        ``progress`` receives the completed fraction; returning False raises
        :class:`CalculationCancelled`.
        """
        if not math.isfinite(log10_activity_min) or not math.isfinite(log10_activity_max):
            raise ValueError("activity limits must be finite")
        if log10_activity_min >= log10_activity_max:
            raise ValueError("minimum activity must be smaller than maximum activity")
        if not 2 <= points <= MAX_SWEEP_POINTS:
            raise ValueError(f"sweep points must be between 2 and {MAX_SWEEP_POINTS}")
        if conditions.aqueous_activities.overrides:
            raise ValueError("species activity overrides are unavailable during a global sweep")
        ligand_ids = conditions.ligand_activities.ligand_ids if conditions.ligand_activities else ()
        system = self.database.load_system(symbol, ligand_ids=ligand_ids, energy_policy=energy_policy)
        levels = np.linspace(log10_activity_min, log10_activity_max, points)
        diagrams = []
        for number, level in enumerate(levels):
            if progress is not None and progress(number / points) is False:
                raise CalculationCancelled(f"sweep cancelled after {number} of {points} levels")
            level_conditions = replace(
                conditions, aqueous_activities=AqueousActivityModel(default_log10_activity=float(level))
            )
            diagrams.append(self.engine.calculate_system(
                system, level_conditions, allow_incomplete=allow_incomplete, store_energies=store_energies,
            ))
        levels.setflags(write=False)
        return ConcentrationSweep(levels, tuple(diagrams))


def _compact_volume(sweep: ConcentrationSweep) -> tuple[np.ndarray, tuple[ThermodynamicSpecies, ...]]:
    species = sweep.stable_species
    by_record = {item.record_id: index for index, item in enumerate(species)}
    volume = np.empty((len(sweep.diagrams), sweep.U_V.size, sweep.pH.size), dtype=np.intp)
    for level_index, diagram in enumerate(sweep.diagrams):
        for system_index, item in enumerate(diagram.system.species):
            if item.record_id in by_record:
                volume[level_index][diagram.stable_species_index == system_index] = by_record[item.record_id]
    return volume, species


def plot_concentration_sweep(
    sweep: ConcentrationSweep,
    *,
    probe_pH: float = 7.0,
    probe_U_V: float = 0.0,
    show_water: bool = True,
) -> tuple[Any, Any]:
    """Plot stacked 3D boundaries and two orthogonal concentration projections."""
    try:
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap
        from matplotlib.patches import Patch
    except ImportError as error:
        raise ImportError("Plotting requires Matplotlib") from error
    if not sweep.pH[0] <= probe_pH <= sweep.pH[-1]:
        raise ValueError("probe_pH lies outside the sweep")
    if not sweep.U_V[0] <= probe_U_V <= sweep.U_V[-1]:
        raise ValueError("probe_U_V lies outside the sweep")
    volume, species = _compact_volume(sweep)
    colors = species_colors(tuple(item.record_id for item in species))
    cmap = ListedColormap([colors[item.record_id] for item in species])
    figure = plt.figure(figsize=(17, 5.5), constrained_layout=True)
    axis_3d = figure.add_subplot(1, 3, 1, projection="3d")
    for level, compact, diagram in zip(sweep.log10_activities, volume, sweep.diagrams):
        for segment in phase_boundary_segments(compact, sweep.pH, sweep.U_V):
            axis_3d.plot(
                [segment[0][0], segment[1][0]],
                [float(level), float(level)],
                [segment[0][1], segment[1][1]],
                color="black", linewidth=0.45, alpha=0.75,
            )
        if show_water:
            axis_3d.plot(sweep.pH, np.full(sweep.pH.shape, level), diagram.her_V,
                         "--", color="gray", linewidth=0.5)
            axis_3d.plot(sweep.pH, np.full(sweep.pH.shape, level), diagram.oer_V,
                         "--", color="gray", linewidth=0.5)
    axis_3d.set(xlabel="pH", ylabel="log10 aqueous activity", zlabel="U (V vs SHE)",
                title="Stacked phase boundaries")

    U_index = int(np.abs(sweep.U_V - probe_U_V).argmin())
    pH_index = int(np.abs(sweep.pH - probe_pH).argmin())
    axis_ph = figure.add_subplot(1, 3, 2)
    axis_ph.pcolormesh(
        sweep.pH, sweep.log10_activities, volume[:, U_index, :],
        cmap=cmap, vmin=-0.5, vmax=len(species) - 0.5, shading="nearest",
    )
    axis_ph.set(xlabel="pH", ylabel="log10 aqueous activity",
                title=f"pH–activity at U = {sweep.U_V[U_index]:g} V")
    axis_U = figure.add_subplot(1, 3, 3)
    axis_U.pcolormesh(
        sweep.log10_activities, sweep.U_V, volume[:, :, pH_index].T,
        cmap=cmap, vmin=-0.5, vmax=len(species) - 0.5, shading="nearest",
    )
    axis_U.set(xlabel="log10 aqueous activity", ylabel="U (V vs SHE)",
                title=f"U–activity at pH = {sweep.pH[pH_index]:g}")
    figure.legend(
        handles=[Patch(facecolor=colors[item.record_id], label=item.species) for item in species],
        loc="outside lower center", ncol=min(6, len(species)), fontsize=7,
    )
    return figure, (axis_3d, axis_ph, axis_U)
