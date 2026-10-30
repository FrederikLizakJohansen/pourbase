"""Reproducible figures comparing experimental and Materials Project energies."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import numpy as np

from .database import ThermodynamicDatabase


PROPERTY_FIELDS = {
    "enthalpy": (
        "experimental_enthalpy_eV_atom",
        "Experimental formation enthalpy (eV/atom)",
        "Formation enthalpy",
    ),
    "gibbs": (
        "experimental_gibbs_eV_atom",
        "Experimental formation energy ΔfG° at 298.15 K (eV/atom)",
        "Formation energy ΔfG°",
    ),
}


def comparison_metrics(
    rows: Iterable[Mapping[str, object]], property_name: str
) -> dict[str, dict[str, float | int]]:
    """Calculate transparent per-method residual metrics in eV/atom."""
    try:
        field = PROPERTY_FIELDS[property_name][0]
    except KeyError as error:
        raise ValueError("property_name must be enthalpy or gibbs") from error
    residuals: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        experimental = row.get(field)
        calculated = row.get("formation_energy_eV_atom")
        if experimental is None or calculated is None:
            continue
        residuals[str(row["calculation_type"])].append(
            float(calculated) - float(experimental)
        )
    result: dict[str, dict[str, float | int]] = {}
    for method, values in sorted(residuals.items()):
        array = np.asarray(values, dtype=np.float64)
        result[method] = {
            "count": int(array.size),
            "mean_signed_error_eV_atom": float(np.mean(array)),
            "mean_absolute_error_eV_atom": float(np.mean(np.abs(array))),
            "root_mean_square_error_eV_atom": float(np.sqrt(np.mean(array**2))),
        }
    return result


def plot_mp_thermochemistry_comparison(
    rows: Iterable[Mapping[str, object]],
    property_name: str,
) -> tuple[Any, Any]:
    """Return scatter and residual panels for one experimental property."""
    try:
        field, experimental_label, short_label = PROPERTY_FIELDS[property_name]
    except KeyError as error:
        raise ValueError("property_name must be enthalpy or gibbs") from error
    usable = [
        row for row in rows
        if row.get(field) is not None and row.get("formation_energy_eV_atom") is not None
    ]
    if not usable:
        raise ValueError(f"no paired Materials Project and experimental {property_name} rows")

    import matplotlib.pyplot as plt

    methods = sorted({str(row["calculation_type"]) for row in usable})
    palette = plt.get_cmap("tab10")
    colors = {method: palette(index % palette.N) for index, method in enumerate(methods)}
    figure, axes = plt.subplots(1, 2, figsize=(11.5, 5.0), constrained_layout=True)
    all_values: list[float] = []
    for method in methods:
        group = [row for row in usable if row["calculation_type"] == method]
        experimental = np.asarray([float(row[field]) for row in group])
        calculated = np.asarray([float(row["formation_energy_eV_atom"]) for row in group])
        selected = np.asarray([bool(row["selected_for_comparison"]) for row in group])
        all_values.extend(experimental.tolist())
        all_values.extend(calculated.tolist())
        axes[0].scatter(
            experimental, calculated, s=32, color=colors[method], alpha=0.8,
            edgecolors=np.where(selected, "black", "none"), linewidths=0.7,
            label=f"{method} (n={len(group)})",
        )
        axes[1].scatter(
            experimental, calculated - experimental, s=32,
            color=colors[method], alpha=0.8,
            edgecolors=np.where(selected, "black", "none"), linewidths=0.7,
            label=method,
        )
    lower, upper = min(all_values), max(all_values)
    padding = max((upper - lower) * 0.04, 0.05)
    axes[0].plot(
        [lower - padding, upper + padding], [lower - padding, upper + padding],
        color="black", linestyle="--", linewidth=1.0, label="identity",
    )
    axes[0].set_xlim(lower - padding, upper + padding)
    axes[0].set_ylim(lower - padding, upper + padding)
    axes[0].set_xlabel(experimental_label)
    axes[0].set_ylabel("Materials Project formation energy (eV/atom)")
    axes[0].set_title(f"MP energy compared with experimental {short_label.lower()}")
    axes[0].legend(fontsize=7)
    axes[1].axhline(0.0, color="black", linestyle="--", linewidth=1.0)
    axes[1].set_xlabel(experimental_label)
    axes[1].set_ylabel("MP minus experiment (eV/atom)")
    axes[1].set_title("Signed residual")
    axes[1].legend(fontsize=7)
    figure.suptitle(
        "Phase-matched Materials Project and experimental thermochemistry",
        fontsize=12,
    )
    return figure, axes


def write_mp_thermochemistry_bundle(
    database: ThermodynamicDatabase, output_dir: str | Path
) -> dict[str, object]:
    """Write the comparison figures, plotted rows, metrics, and method notes."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = database.materials_project_thermochemistry()
    fieldnames = tuple(rows[0].keys()) if rows else ()
    with (output / "mp-thermochemistry-points.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    import matplotlib.pyplot as plt

    properties: dict[str, object] = {}
    for property_name in PROPERTY_FIELDS:
        figure, _ = plot_mp_thermochemistry_comparison(rows, property_name)
        stem = f"mp-{property_name}-comparison"
        figure.savefig(output / f"{stem}.png", dpi=300)
        figure.savefig(output / f"{stem}.pdf")
        plt.close(figure)
        properties[property_name] = comparison_metrics(rows, property_name)

    versions = sorted({str(row["database_version"]) for row in rows})
    retrieved = sorted({str(row["retrieved_on"]) for row in rows})
    metadata: dict[str, object] = {
        "materials_project_database_versions": versions,
        "retrieval_dates": retrieved,
        "phase_matched_records": len({str(row["record_id"]) for row in rows}),
        "materials_project_energy_rows": len(rows),
        "methods": properties,
        "residual_definition": "Materials Project formation energy minus experimental value",
        "normalization": "eV per atom; experimental J/mol values divided by Faraday constant and formula atom count",
        "selected_marker": "points with a black edge are the curated calculation selected for diagram comparison",
    }
    (output / "mp-thermochemistry-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    (output / "README.md").write_text(
        """# Materials Project thermochemistry figures

These figures compare phase-matched experimental formation values with Materials
Project calculated formation energies. The CSV contains every plotted point. The
JSON file records database versions, retrieval dates, normalization, and residual
metrics. A black point edge marks the calculation selected for Pourbaix comparison.

Formation enthalpy is the closest direct comparison with the 0 K DFT formation
energy. The Gibbs panel is also provided because Gibbs energies drive the
experimental Pourbaix diagrams; its residual includes finite-temperature entropy
effects as well as differences between experiment and calculation.

Materials Project data are used under CC BY 4.0. Cite Materials Project and retain
the database version and MP identifiers in the CSV when reusing these figures.

Suggested Materials Project citations:

- Horton et al., Nature Materials (2025), https://doi.org/10.1038/s41563-025-02272-0
- Jain et al., APL Materials 1, 011002 (2013), https://doi.org/10.1063/1.4812323

For Pourbaix-diagram comparisons, also cite Persson et al., Physical Review B 85,
235438 (2012), https://doi.org/10.1103/PhysRevB.85.235438, and Singh et al.,
Chemistry of Materials 29, 10159-10167 (2017),
https://doi.org/10.1021/acs.chemmater.7b03980.
""",
        encoding="utf-8",
    )
    return metadata
