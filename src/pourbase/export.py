"""Figures and CSV grids for calculated diagrams."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

import numpy as np

from .boltzmann import boltzmann_smooth
from .constants import GAS_CONSTANT_J_MOL_K
from .mass_balance import MassBalancedPourbaixDiagram
from .plotting import plot_boltzmann_diagram, plot_diagram, plot_mass_balance_summary


def grid_csv(diagram: Any) -> str:
    """Every grid point with its stable species, and the metal inventory for a mass balance."""
    pH, eh = np.meshgrid(diagram.pH, diagram.eh_V)
    index = diagram.stable_species_index.ravel()
    species = diagram.system.species
    columns = [
        pH.ravel(), eh.ravel(),
        np.array([item.record_id for item in species])[index],
        np.array([item.species for item in species])[index],
        np.array([item.phase for item in species])[index],
    ]
    header = ["pH", "Eh_V_vs_SHE", "record_id", "species", "phase"]
    if isinstance(diagram, MassBalancedPourbaixDiagram):
        columns += [diagram.dissolved_metal_mol_L.ravel(), diagram.precipitated_metal_fraction.ravel()]
        header += ["dissolved_metal_mol_L", "precipitated_metal_fraction"]
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(zip(*columns))
    return output.getvalue()


def diagram_figure(
    diagram: Any,
    *,
    labels: bool = True,
    legend: bool = True,
    boundaries: bool = True,
    water: bool = True,
    plating_potential_V: float | None = None,
    blend_width_kJ_mol: float | None = None,
    boltzmann_scale: float | None = None,
) -> Any:
    """A Matplotlib figure of a fixed-activity or mass-balance diagram.

    ``blend_width_kJ_mol`` draws soft-minimum weights (Eq. 8) of that width; ``boltzmann_scale``
    gives the width in units of RT and is kept for compatibility.
    """
    options = dict(label_domains=labels, show_legend=legend, show_boundaries=boundaries, show_water=water)
    title = f"{diagram.system.system}, experimental data"
    if isinstance(diagram, MassBalancedPourbaixDiagram):
        figure, _ = plot_mass_balance_summary(diagram, title=title, **options)
        return figure
    if boltzmann_scale is not None and blend_width_kJ_mol is None:
        blend_width_kJ_mol = boltzmann_scale * GAS_CONSTANT_J_MOL_K * diagram.conditions.temperature_K / 1000
    if blend_width_kJ_mol is not None:
        axis = plot_boltzmann_diagram(
            boltzmann_smooth(diagram, blend_width_kJ_mol * 1000),
            title=f"{title}; soft minimum, width {blend_width_kJ_mol:g} kJ/mol", **options,
        )
    else:
        axis = plot_diagram(diagram, title=title, **options)
    if plating_potential_V is not None:
        axis.axhline(plating_potential_V, color="green", linestyle="-.", linewidth=1.2,
                     label="direct plating equilibrium")
        if legend:
            axis.legend(fontsize=7, loc="upper right", framealpha=0.9)
    return axis.figure


def save_figure(figure: Any, path: str | Path, dpi: int = 300) -> Path:
    import matplotlib.pyplot as plt

    path = Path(path)
    figure.savefig(path, dpi=dpi)
    plt.close(figure)
    return path
