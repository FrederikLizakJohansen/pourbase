"""Small Matplotlib layer for experimental Pourbaix results."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from .boltzmann import BoltzmannSmoothedDiagram
from .engine import PourbaixDiagram
from .grid import phase_boundary_segments
from .mass_balance import MassBalancedPourbaixDiagram


def _plot_dependencies() -> tuple[Any, Any, Any]:
    try:
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap
        from matplotlib.patches import Patch
    except ImportError as error:
        raise ImportError("Plotting requires Matplotlib") from error
    return plt, ListedColormap, Patch


def species_colors(record_ids) -> dict[str, Any]:
    """Colors for species keyed by record ID: tab20 over the sorted IDs."""
    plt, _, _ = _plot_dependencies()
    palette = plt.get_cmap("tab20")
    return {record_id: palette(index % palette.N) for index, record_id in enumerate(sorted(set(record_ids)))}


def plot_diagram(
    diagram: PourbaixDiagram | MassBalancedPourbaixDiagram,
    *,
    ax: Any | None = None,
    title: str | None = None,
    colors: Mapping[str, Any] | None = None,
    label_domains: bool = True,
    show_legend: bool = True,
    show_boundaries: bool = True,
    show_water: bool = True,
) -> Any:
    """Plot one phase map and return its Matplotlib axes."""
    plt, ListedColormap, Patch = _plot_dependencies()
    if ax is None:
        _, ax = plt.subplots(figsize=(7.2, 5.4), constrained_layout=True)
    stable_indices = sorted(int(value) for value in np.unique(diagram.stable_species_index))
    stable_species = tuple(diagram.system.species[index] for index in stable_indices)
    colors = colors or species_colors(tuple(item.record_id for item in stable_species))
    compact = np.zeros_like(diagram.stable_species_index)
    for display_index, species_index in enumerate(stable_indices):
        compact[diagram.stable_species_index == species_index] = display_index
    color_map = ListedColormap([colors[item.record_id] for item in stable_species])
    ax.pcolormesh(
        diagram.pH, diagram.eh_V, compact, cmap=color_map, vmin=-0.5,
        vmax=len(stable_species) - 0.5, shading="nearest", rasterized=True,
    )
    if show_boundaries and len(stable_species) > 1:
        from matplotlib.collections import LineCollection

        segments = phase_boundary_segments(compact, diagram.pH, diagram.eh_V)
        if len(segments):
            ax.add_collection(
                LineCollection(
                    segments, colors="black", linewidths=0.65, zorder=3
                )
            )
    if show_water:
        ax.plot(diagram.pH, diagram.her_V, "--", color="black", linewidth=1.0)
        ax.plot(diagram.pH, diagram.oer_V, "--", color="black", linewidth=1.0)
    if label_domains:
        pH_grid, eh_grid = np.meshgrid(diagram.pH, diagram.eh_V)
        for display_index, species in enumerate(stable_species):
            mask = compact == display_index
            target_pH = float(np.mean(pH_grid[mask]))
            target_eh = float(np.mean(eh_grid[mask]))
            locations = np.column_stack(np.nonzero(mask))
            coordinates = np.column_stack((pH_grid[mask], eh_grid[mask]))
            scale_pH = max(float(np.ptp(diagram.pH)), 1.0)
            scale_eh = max(float(np.ptp(diagram.eh_V)), 1.0)
            distances = ((coordinates[:, 0] - target_pH) / scale_pH) ** 2 + (
                (coordinates[:, 1] - target_eh) / scale_eh
            ) ** 2
            row, column = locations[int(np.argmin(distances))]
            ax.text(
                diagram.pH[column], diagram.eh_V[row], species.species,
                ha="center", va="center", fontsize=8,
                bbox={"facecolor": "white", "alpha": 0.72, "edgecolor": "none", "pad": 1.5},
            )
    ax.set(xlabel="pH", ylabel="Eh (V vs SHE)", title=title)
    ax.set_xlim(float(diagram.pH[0]), float(diagram.pH[-1]))
    ax.set_ylim(float(diagram.eh_V[0]), float(diagram.eh_V[-1]))
    if show_legend:
        ax.legend(
            handles=[
                Patch(facecolor=colors[item.record_id], edgecolor="black", label=item.species)
                for item in stable_species
            ],
            fontsize=7, loc="upper right", framealpha=0.9,
        )
    return ax


def plot_uncertainty(
    diagram: PourbaixDiagram,
    *,
    ax: Any,
    confidence_sigma: float = 1.0,
    assumed_uncertainty_kJ_mol: float = 2.0,
    color: Any = "black",
) -> Any:
    """Hatch the points where another species lies within ``confidence_sigma`` combined uncertainties (Eq. 12).

    Species without a reported uncertainty take ``assumed_uncertainty_kJ_mol``. Draws on ``ax``, the
    axes of a diagram plotted with :func:`plot_diagram`, and returns it.
    """
    from .uncertainty import stability_uncertainty

    uncertain = stability_uncertainty(diagram, confidence_sigma, assumed_uncertainty_kJ_mol * 1000).uncertain
    ax.contourf(diagram.pH, diagram.eh_V, uncertain.astype(float), levels=[0.5, 1.5], colors="none",
                hatches=["////"], zorder=3)
    ax.contour(diagram.pH, diagram.eh_V, uncertain.astype(float), levels=[0.5], colors=[color],
               linewidths=0.6, zorder=3)
    return ax


def plot_boltzmann_diagram(
    smoothed: BoltzmannSmoothedDiagram,
    *,
    ax: Any | None = None,
    title: str | None = None,
    colors: Mapping[str, Any] | None = None,
    label_domains: bool = True,
    show_legend: bool = True,
    show_boundaries: bool = True,
    show_water: bool = True,
    minimum_peak_weight: float = 0.01,
) -> Any:
    """Plot a blend of every species' soft-minimum weight (Eq. 8).

    The colors show energetic competition. They are not equilibrium phase
    fractions; use the mass-balance engine when conserved amounts are needed.
    """
    if not 0.0 <= minimum_peak_weight <= 1.0:
        raise ValueError("minimum_peak_weight must lie between zero and one")
    plt, _, Patch = _plot_dependencies()
    if ax is None:
        _, ax = plt.subplots(figsize=(7.2, 5.4), constrained_layout=True)
    diagram = smoothed.diagram
    species = diagram.system.species
    colors = colors or species_colors(tuple(item.record_id for item in species))
    from matplotlib.colors import to_rgba

    rgb_palette = np.asarray(
        [to_rgba(colors[item.record_id])[:3] for item in species], dtype=np.float64
    )
    rgb_grid = np.einsum("ihw,ic->hwc", smoothed.weights, rgb_palette)
    ax.imshow(
        rgb_grid,
        origin="lower",
        extent=(
            float(diagram.pH[0]), float(diagram.pH[-1]),
            float(diagram.eh_V[0]), float(diagram.eh_V[-1]),
        ),
        aspect="auto",
        interpolation="bilinear",
        rasterized=True,
    )
    if show_boundaries and len(diagram.stable_species) > 1:
        from matplotlib.collections import LineCollection

        segments = phase_boundary_segments(
            diagram.stable_species_index, diagram.pH, diagram.eh_V
        )
        if len(segments):
            ax.add_collection(
                LineCollection(segments, colors="black", linewidths=0.65, zorder=3)
            )
    if show_water:
        ax.plot(diagram.pH, diagram.her_V, "--", color="black", linewidth=1.0)
        ax.plot(diagram.pH, diagram.oer_V, "--", color="black", linewidth=1.0)
    stable_indices = sorted(
        int(value) for value in np.unique(diagram.stable_species_index)
    )
    if label_domains:
        pH_grid, eh_grid = np.meshgrid(diagram.pH, diagram.eh_V)
        for species_index in stable_indices:
            item = species[species_index]
            mask = diagram.stable_species_index == species_index
            locations = np.column_stack(np.nonzero(mask))
            coordinates = np.column_stack((pH_grid[mask], eh_grid[mask]))
            target = np.mean(coordinates, axis=0)
            scales = np.asarray([
                max(float(np.ptp(diagram.pH)), 1.0),
                max(float(np.ptp(diagram.eh_V)), 1.0),
            ])
            row, column = locations[int(np.argmin(np.sum(
                ((coordinates - target) / scales) ** 2, axis=1
            )))]
            ax.text(
                diagram.pH[column], diagram.eh_V[row], item.species,
                ha="center", va="center", fontsize=8,
                bbox={"facecolor": "white", "alpha": 0.72,
                      "edgecolor": "none", "pad": 1.5},
            )
    if title is None:
        title = f"{diagram.system.system} - soft minimum (width {smoothed.width_J_mol / 1000:.3g} kJ/mol)"
    ax.set(xlabel="pH", ylabel="Eh (V vs SHE)", title=title)
    ax.set_xlim(float(diagram.pH[0]), float(diagram.pH[-1]))
    ax.set_ylim(float(diagram.eh_V[0]), float(diagram.eh_V[-1]))
    if show_legend:
        peak_weights = np.max(smoothed.weights, axis=(1, 2))
        displayed = [
            (item, float(peak_weights[index]))
            for index, item in enumerate(species)
            if peak_weights[index] >= minimum_peak_weight
        ]
        ax.legend(
            handles=[
                Patch(
                    facecolor=colors[item.record_id], edgecolor="black",
                    label=f"{item.species} (peak {peak:.2f})",
                )
                for item, peak in displayed
            ],
            fontsize=7, loc="upper right", framealpha=0.9,
        )
    return ax


def plot_mass_balance_summary(
    diagram: MassBalancedPourbaixDiagram, *, title: str | None = None,
    label_domains: bool = True, show_legend: bool = True,
    show_boundaries: bool = True, show_water: bool = True,
) -> tuple[Any, Any]:
    """Plot phase domains, precipitated fraction, and dissolved metal."""
    plt, _, _ = _plot_dependencies()
    figure, axes = plt.subplots(
        1, 3, figsize=(15.5, 5.2), sharex=True, sharey=True, constrained_layout=True
    )
    plot_diagram(
        diagram, ax=axes[0], title="Dominant species / precipitating solid",
        label_domains=label_domains, show_legend=show_legend,
        show_boundaries=show_boundaries, show_water=show_water,
    )
    precipitated = axes[1].pcolormesh(
        diagram.pH, diagram.eh_V, diagram.precipitated_metal_fraction,
        cmap="Blues", vmin=0.0, vmax=1.0, shading="nearest", rasterized=True,
    )
    figure.colorbar(precipitated, ax=axes[1], label="precipitated metal fraction")
    floor = np.finfo(np.float64).tiny
    dissolved = axes[2].pcolormesh(
        diagram.pH, diagram.eh_V,
        np.log10(np.maximum(diagram.dissolved_metal_mol_L, floor)),
        cmap="viridis", shading="nearest", rasterized=True,
    )
    figure.colorbar(dissolved, ax=axes[2], label="log10 dissolved metal / mol L⁻¹")
    axes[1].set_title("Precipitated inventory")
    axes[2].set_title("Total dissolved metal")
    for axis in axes[1:]:
        if show_water:
            axis.plot(diagram.pH, diagram.her_V, "--", color="black", linewidth=1.0)
            axis.plot(diagram.pH, diagram.oer_V, "--", color="black", linewidth=1.0)
        axis.set_xlim(float(diagram.pH[0]), float(diagram.pH[-1]))
        axis.set_ylim(float(diagram.eh_V[0]), float(diagram.eh_V[-1]))
        axis.set_xlabel("pH")
    if title:
        figure.suptitle(title)
    return figure, axes


def plot_official_materials_project_diagram(
    diagram: Any,
    *,
    ax: Any | None = None,
    title: str | None = None,
    colors: Mapping[str, Any] | None = None,
    label_domains: bool = True,
    show_legend: bool = True,
) -> Any:
    """Plot a phase map returned by Materials Project's official workflow."""
    plt, ListedColormap, Patch = _plot_dependencies()
    if ax is None:
        _, ax = plt.subplots(figsize=(7.2, 5.4), constrained_layout=True)
    stable_indices = sorted(int(value) for value in np.unique(diagram.stable_phase_index))
    stable_phases = tuple(diagram.phases[index] for index in stable_indices)
    colors = colors or species_colors(tuple(item.phase_id for item in stable_phases))
    compact = np.zeros_like(diagram.stable_phase_index)
    for display_index, phase_index in enumerate(stable_indices):
        compact[diagram.stable_phase_index == phase_index] = display_index
    ax.pcolormesh(
        diagram.pH, diagram.eh_V, compact,
        cmap=ListedColormap([colors[item.phase_id] for item in stable_phases]),
        vmin=-0.5, vmax=len(stable_phases) - 0.5, shading="nearest", rasterized=True,
    )
    if len(stable_phases) > 1:
        from matplotlib.collections import LineCollection

        segments = phase_boundary_segments(compact, diagram.pH, diagram.eh_V)
        if len(segments):
            ax.add_collection(LineCollection(
                segments, colors="black", linewidths=0.65, zorder=3
            ))
    ax.plot(diagram.pH, diagram.her_V, "--", color="black", linewidth=1.0)
    ax.plot(diagram.pH, diagram.oer_V, "--", color="black", linewidth=1.0)
    if label_domains:
        pH_grid, eh_grid = np.meshgrid(diagram.pH, diagram.eh_V)
        for display_index, phase in enumerate(stable_phases):
            mask = compact == display_index
            locations = np.column_stack(np.nonzero(mask))
            coordinates = np.column_stack((pH_grid[mask], eh_grid[mask]))
            target = np.mean(coordinates, axis=0)
            scales = np.asarray([
                max(float(np.ptp(diagram.pH)), 1.0),
                max(float(np.ptp(diagram.eh_V)), 1.0),
            ])
            row, column = locations[int(np.argmin(np.sum(
                ((coordinates - target) / scales) ** 2, axis=1
            )))]
            ax.text(
                diagram.pH[column], diagram.eh_V[row], phase.label,
                ha="center", va="center", fontsize=8,
                bbox={"facecolor": "white", "alpha": 0.72,
                      "edgecolor": "none", "pad": 1.5},
            )
    ax.set(xlabel="pH", ylabel="Eh (V vs SHE)", title=title)
    ax.set_xlim(float(diagram.pH[0]), float(diagram.pH[-1]))
    ax.set_ylim(float(diagram.eh_V[0]), float(diagram.eh_V[-1]))
    if show_legend:
        ax.legend(
            handles=[
                Patch(facecolor=colors[item.phase_id], edgecolor="black", label=item.label)
                for item in stable_phases
            ],
            fontsize=7, loc="upper right", framealpha=0.9,
        )
    return ax


def plot_official_materials_project_comparison(
    comparison: Any, *, title: str | None = None
) -> tuple[Any, Any]:
    """Plot experimental, live official MP, and domain-agreement panels."""
    from .materials_project import thermodynamic_species_equivalence_key

    plt, ListedColormap, Patch = _plot_dependencies()
    figure, axes = plt.subplots(
        1, 3, figsize=(15.5, 5.2), sharex=True, sharey=True,
        constrained_layout=True,
    )
    experimental = comparison.experimental
    official = comparison.materials_project
    experimental_keys = {
        item.record_id: thermodynamic_species_equivalence_key(item)
        for item in experimental.system.species
    }
    all_keys = set(experimental_keys.values()) | {
        item.equivalence_key for item in official.phases
    }
    palette = plt.get_cmap("tab20")
    colors_by_key = {
        key: palette(index % palette.N)
        for index, key in enumerate(sorted(all_keys))
    }
    plot_diagram(
        experimental, ax=axes[0], title="Experimental Gibbs energies",
        colors={key: colors_by_key[value] for key, value in experimental_keys.items()},
        show_legend=False,
    )
    plot_official_materials_project_diagram(
        official, ax=axes[1], title="Official Materials Project workflow",
        colors={item.phase_id: colors_by_key[item.equivalence_key] for item in official.phases},
        show_legend=False,
    )
    changed = (~comparison.same_thermodynamic_species).astype(int)
    axes[2].pcolormesh(
        experimental.pH, experimental.eh_V, changed,
        cmap=ListedColormap(["#f3f3f3", "#d95f02"]),
        vmin=-0.5, vmax=1.5, shading="nearest", rasterized=True,
    )
    axes[2].plot(experimental.pH, experimental.her_V, "--", color="black", linewidth=1.0)
    axes[2].plot(experimental.pH, experimental.oer_V, "--", color="black", linewidth=1.0)
    axes[2].set_title(
        "Different thermodynamic species\n"
        f"{(1 - comparison.equivalent_domain_fraction) * 100:.1f}% of grid"
    )
    axes[2].legend(
        handles=[
            Patch(facecolor="#f3f3f3", edgecolor="black", label="equivalent"),
            Patch(facecolor="#d95f02", edgecolor="black", label="different"),
        ], fontsize=8, loc="upper right",
    )
    for axis in axes:
        axis.set_xlabel("pH")
    axes[0].set_ylabel("Eh (V vs SHE)")
    if title:
        figure.suptitle(title)
    return figure, axes
