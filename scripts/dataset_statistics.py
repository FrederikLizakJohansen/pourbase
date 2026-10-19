#!/usr/bin/env python3
"""Write STATISTICS.md and its figures from the bundled database.

Run from the repository root::

    python scripts/dataset_statistics.py
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle


REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))
import pourbase as pb  # noqa: E402
DATABASE = REPOSITORY / "src" / "pourbase" / "data" / "pourbase.sqlite"
INPUTS = REPOSITORY / "data" / "statistics"
MP_THERMOCHEMISTRY = PAPER_DATA = INPUTS
GENERATED = FIGURES = REPOSITORY / "docs" / "statistics"
STATISTICS = REPOSITORY / "STATISTICS.md"

INK = "#333331"
SPINE = "#8a8a82"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
GREEN = "#1baf7a"
PURPLE = "#4a3aa7"
PALE = "#e3e2dc"
COLORS = [BLUE, ORANGE, GREEN, PURPLE]

plt.rcParams.update(
    {
        "font.size": 8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": SPINE,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "text.color": INK,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.dpi": 180,
    }
)


def scalar(
    connection: sqlite3.Connection, query: str, parameters: tuple[Any, ...] = ()
) -> Any:
    return connection.execute(query, parameters).fetchone()[0]


def rows(connection: sqlite3.Connection, query: str) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(query)]


def collect_statistics() -> dict[str, Any]:
    with closing(pb.ThermodynamicDatabase(DATABASE).connect()) as connection:
        connection.row_factory = sqlite3.Row
        metadata = dict(connection.execute("SELECT key,value FROM metadata"))
        phases = rows(
            connection,
            """SELECT s.phase,COUNT(*) AS species,
                      SUM(t.gibbs_energy_J_mol IS NOT NULL) AS gibbs,
                      SUM(t.entropy_J_mol_K IS NOT NULL) AS entropy,
                      SUM(t.formation_enthalpy_J_mol IS NOT NULL) AS enthalpy
               FROM species AS s JOIN selected_thermochemistry AS t USING(record_id)
               GROUP BY s.phase ORDER BY species DESC""",
        )
        properties = [
            {
                "property": "Gibbs energy",
                "available": scalar(
                    connection,
                    "SELECT COUNT(*) FROM selected_thermochemistry WHERE gibbs_energy_J_mol IS NOT NULL",
                ),
            },
            {
                "property": "Entropy",
                "available": scalar(
                    connection,
                    "SELECT COUNT(*) FROM selected_thermochemistry WHERE entropy_J_mol_K IS NOT NULL",
                ),
            },
            {
                "property": "Formation enthalpy",
                "available": scalar(
                    connection,
                    "SELECT COUNT(*) FROM selected_thermochemistry WHERE formation_enthalpy_J_mol IS NOT NULL",
                ),
            },
        ]
        gibbs_status = {
            row["gibbs_status"]: row["count"]
            for row in rows(
                connection,
                """SELECT gibbs_status,COUNT(*) AS count FROM selected_thermochemistry
                   GROUP BY gibbs_status ORDER BY count DESC""",
            )
        }
        coverage = rows(
            connection,
            """SELECT e.atomic_number,e.symbol,e.coverage_status,e.reason,
                      COUNT(s.record_id) AS species
               FROM element_coverage AS e
               LEFT JOIN species AS s ON s.symbol=e.symbol
               GROUP BY e.atomic_number,e.symbol,e.coverage_status,e.reason
               ORDER BY e.atomic_number""",
        )
        systems = rows(
            connection,
            """WITH warning_counts AS (
                     SELECT record_id,COUNT(*) AS warnings FROM warnings GROUP BY record_id
                   )
               SELECT s.symbol,s.system,COUNT(*) AS species,
                      SUM(s.phase='aqueous') AS aqueous,
                      SUM(s.phase='solid') AS solid,
                      SUM(s.phase='gas') AS gas,
                      SUM(s.phase='liquid') AS liquid,
                      SUM(t.gibbs_energy_J_mol IS NOT NULL) AS gibbs,
                      SUM(t.entropy_J_mol_K IS NOT NULL) AS entropy,
                      SUM(t.formation_enthalpy_J_mol IS NOT NULL) AS enthalpy,
                      COALESCE(SUM(w.warning_count),0) AS warnings
               FROM species AS s
               JOIN selected_thermochemistry AS t USING(record_id)
               LEFT JOIN (
                   SELECT record_id,COUNT(*) AS warning_count
                   FROM warnings GROUP BY record_id
               ) AS w USING(record_id)
               GROUP BY s.symbol,s.system ORDER BY s.symbol""",
        )
        totals = {
            "species": scalar(connection, "SELECT COUNT(*) FROM species"),
            "supported_systems": scalar(
                connection,
                "SELECT COUNT(*) FROM element_coverage WHERE coverage_status='supported'",
            ),
            "all_elements_documented": scalar(
                connection, "SELECT COUNT(*) FROM element_coverage"
            ),
            "reported_thermochemistry": scalar(
                connection, "SELECT COUNT(*) FROM reported_thermochemistry"
            ),
            "recommended_values": scalar(
                connection,
                "SELECT COUNT(gibbs_value_id) + COUNT(entropy_value_id) + COUNT(formation_enthalpy_value_id) FROM selected_thermochemistry",
            ),
            "source_records": scalar(connection, "SELECT COUNT(*) FROM sources"),
            "distinct_citations": scalar(
                connection, "SELECT COUNT(DISTINCT citation) FROM sources"
            ),
            "warnings": scalar(connection, "SELECT COUNT(*) FROM warnings"),
            "phase_records": scalar(connection, "SELECT COUNT(*) FROM phases"),
            "resolved_phase_records": scalar(
                connection,
                "SELECT COUNT(*) FROM phases WHERE identity_status LIKE 'resolved%'",
            ),
            "mp_matches": scalar(
                connection, "SELECT COUNT(*) FROM materials_project_matches"
            ),
            "mp_energy_rows": scalar(
                connection, "SELECT COUNT(*) FROM materials_project_energies"
            ),
            "computational_fallbacks": scalar(
                connection, "SELECT COUNT(*) FROM computational_fallbacks"
            ),
            "ligands": scalar(connection, "SELECT COUNT(*) FROM ligands"),
        }
        warning_types = rows(
            connection,
            """SELECT warning_type,COUNT(*) AS count FROM warnings
               GROUP BY warning_type ORDER BY count DESC""",
        )
        phase_identity = rows(
            connection,
            """SELECT identity_status,COUNT(*) AS count FROM phases
               GROUP BY identity_status ORDER BY count DESC""",
        )

    mp_metadata_path = MP_THERMOCHEMISTRY / "mp-thermochemistry-metadata.json"
    mp_metadata = json.loads(mp_metadata_path.read_text())
    return {
        "metadata": metadata,
        "totals": totals,
        "phases": phases,
        "properties": properties,
        "gibbs_status": gibbs_status,
        "element_coverage": coverage,
        "systems": systems,
        "warning_types": warning_types,
        "phase_identity": phase_identity,
        "materials_project_comparison": mp_metadata,
    }


def write_statistics(stats: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "dataset-summary.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False) + "\n"
    )
    fields = [
        "symbol",
        "system",
        "species",
        "aqueous",
        "solid",
        "gas",
        "liquid",
        "gibbs",
        "entropy",
        "enthalpy",
        "warnings",
    ]
    with (GENERATED / "per-system-statistics.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(stats["systems"])



PERIODIC_POSITIONS: dict[str, tuple[int, int]] = {}


def _place(row: int, symbols: list[str | None]) -> None:
    for column, symbol in enumerate(symbols, start=1):
        if symbol is not None:
            PERIODIC_POSITIONS[symbol] = (column, row)


_place(1, ["H"] + [None] * 16 + ["He"])
_place(2, ["Li", "Be"] + [None] * 10 + ["B", "C", "N", "O", "F", "Ne"])
_place(3, ["Na", "Mg"] + [None] * 10 + ["Al", "Si", "P", "S", "Cl", "Ar"])
_place(
    4,
    [
        "K",
        "Ca",
        "Sc",
        "Ti",
        "V",
        "Cr",
        "Mn",
        "Fe",
        "Co",
        "Ni",
        "Cu",
        "Zn",
        "Ga",
        "Ge",
        "As",
        "Se",
        "Br",
        "Kr",
    ],
)
_place(
    5,
    [
        "Rb",
        "Sr",
        "Y",
        "Zr",
        "Nb",
        "Mo",
        "Tc",
        "Ru",
        "Rh",
        "Pd",
        "Ag",
        "Cd",
        "In",
        "Sn",
        "Sb",
        "Te",
        "I",
        "Xe",
    ],
)
_place(
    6,
    [
        "Cs",
        "Ba",
        None,
        "Hf",
        "Ta",
        "W",
        "Re",
        "Os",
        "Ir",
        "Pt",
        "Au",
        "Hg",
        "Tl",
        "Pb",
        "Bi",
        "Po",
        "At",
        "Rn",
    ],
)
_place(
    7,
    [
        "Fr",
        "Ra",
        None,
        "Rf",
        "Db",
        "Sg",
        "Bh",
        "Hs",
        "Mt",
        "Ds",
        "Rg",
        "Cn",
        "Nh",
        "Fl",
        "Mc",
        "Lv",
        "Ts",
        "Og",
    ],
)
_place(
    8,
    [
        None,
        None,
        "La",
        "Ce",
        "Pr",
        "Nd",
        "Pm",
        "Sm",
        "Eu",
        "Gd",
        "Tb",
        "Dy",
        "Ho",
        "Er",
        "Tm",
        "Yb",
        "Lu",
    ],
)
_place(
    9,
    [
        None,
        None,
        "Ac",
        "Th",
        "Pa",
        "U",
        "Np",
        "Pu",
        "Am",
        "Cm",
        "Bk",
        "Cf",
        "Es",
        "Fm",
        "Md",
        "No",
        "Lr",
    ],
)


def style_axis(axis: Any) -> None:
    for name in ("left", "bottom"):
        axis.spines[name].set_color(SPINE)
    axis.tick_params(colors=INK)


def plot_dataset_overview(stats: dict[str, Any]) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    figure = plt.figure(figsize=(9.5, 6.4), layout="constrained")
    grid = figure.add_gridspec(2, 3, height_ratios=[1.9, 1.0])
    periodic = figure.add_subplot(grid[0, :])
    phase_axis = figure.add_subplot(grid[1, 0])
    property_axis = figure.add_subplot(grid[1, 1])
    evidence_axis = figure.add_subplot(grid[1, 2])

    coverage = {row["symbol"]: row for row in stats["element_coverage"]}
    maximum = max(row["species"] for row in stats["element_coverage"])
    cmap = LinearSegmentedColormap.from_list(
        "species_coverage", ["#eef3f8", "#78aadd", "#174b8a"]
    )
    norm = Normalize(vmin=1, vmax=maximum)
    status_colors = {
        "reference_component": "#b9e5e0",
        "restricted_radioactive": "#b8b8b1",
        "deferred_noble_gas": "#dddcd6",
        "outside_current_scope": "#f5f4ef",
    }
    for symbol, (column, row) in PERIODIC_POSITIONS.items():
        item = coverage[symbol]
        count = int(item["species"])
        color = (
            cmap(norm(count))
            if item["coverage_status"] == "supported"
            else status_colors[item["coverage_status"]]
        )
        periodic.add_patch(
            Rectangle(
                (column - 0.46, row - 0.43),
                0.92,
                0.86,
                facecolor=color,
                edgecolor="white" if item["coverage_status"] == "supported" else SPINE,
                linewidth=0.6,
            )
        )
        periodic.text(
            column,
            row - 0.08,
            symbol,
            ha="center",
            va="center",
            fontsize=7,
            weight="bold",
        )
        if count:
            periodic.text(
                column, row + 0.22, str(count), ha="center", va="center", fontsize=5.5
            )
    for row, text in ((6, "57-71"), (7, "89-103")):
        periodic.add_patch(
            Rectangle(
                (3 - 0.46, row - 0.43),
                0.92,
                0.86,
                facecolor="#f5f4ef",
                edgecolor=SPINE,
                linewidth=0.6,
            )
        )
        periodic.text(3, row, text, ha="center", va="center", fontsize=5.5)
    periodic.text(
        2.25, 8, "lanthanides", ha="right", va="center", fontsize=6.5, color=SPINE
    )
    periodic.text(
        2.25, 9, "actinides", ha="right", va="center", fontsize=6.5, color=SPINE
    )
    periodic.set_xlim(0.45, 18.55)
    periodic.set_ylim(9.5, 0.45)
    periodic.set_aspect("equal")
    periodic.axis("off")
    periodic.set_title(
        "(a)  Elemental systems and number of species", loc="left", pad=4
    )
    colorbar = figure.colorbar(
        plt.cm.ScalarMappable(norm=norm, cmap=cmap),
        ax=periodic,
        orientation="horizontal",
        fraction=0.035,
        pad=0.015,
        aspect=55,
    )
    colorbar.set_label("species in a supported system", fontsize=7)
    colorbar.ax.tick_params(labelsize=6)
    periodic.legend(
        handles=[
            Patch(
                facecolor=status_colors["reference_component"],
                edgecolor=SPINE,
                label="reference component",
            ),
            Patch(
                facecolor=status_colors["outside_current_scope"],
                edgecolor=SPINE,
                label="documented outside scope",
            ),
            Patch(
                facecolor=status_colors["restricted_radioactive"],
                edgecolor=SPINE,
                label="restricted / deferred",
            ),
        ],
        loc="lower center",
        bbox_to_anchor=(0.5, -0.05),
        ncols=3,
        fontsize=6.5,
        handlelength=1.2,
        columnspacing=1.5,
    )

    phase_colors = {"aqueous": BLUE, "solid": ORANGE, "gas": GREEN, "liquid": PURPLE}
    phase_names = [item["phase"] for item in reversed(stats["phases"])]
    phase_counts = [item["species"] for item in reversed(stats["phases"])]
    y = np.arange(len(phase_names))
    phase_axis.barh(
        y, phase_counts, color=[phase_colors[name] for name in phase_names], height=0.62
    )
    phase_axis.set_yticks(y, phase_names)
    phase_axis.set_xlabel("species")
    phase_axis.set_title("(b)  Physical phases", loc="left")
    for position, value in zip(y, phase_counts):
        phase_axis.text(value + 4, position, str(value), va="center", fontsize=7)
    phase_axis.set_xlim(0, max(phase_counts) * 1.2)
    style_axis(phase_axis)

    total_species = stats["totals"]["species"]
    property_names = [item["property"] for item in reversed(stats["properties"])]
    property_counts = [item["available"] for item in reversed(stats["properties"])]
    y = np.arange(len(property_names))
    property_axis.barh(y, [total_species] * len(y), color=PALE, height=0.62)
    property_axis.barh(y, property_counts, color=[GREEN, ORANGE, BLUE], height=0.62)
    property_axis.set_yticks(y, property_names)
    property_axis.set_xlabel("species with a recommended value")
    property_axis.set_title("(c)  Thermochemical coverage", loc="left")
    for position, value in zip(y, property_counts):
        property_axis.text(
            value - 8,
            position,
            f"{value}  ({100 * value / total_species:.0f}%)",
            ha="right",
            va="center",
            color="white" if value > 150 else INK,
            fontsize=6.5,
        )
    property_axis.set_xlim(0, total_species)
    style_axis(property_axis)

    status_order = [
        ("verified", "verified", BLUE),
        ("defined_reference_state", "reference state", GREEN),
        ("source_verified_estimate", "source estimate", ORANGE),
        ("not_available", "unavailable", PALE),
        ("terminal_evidence_gap", "open gap", SPINE),
    ]
    left = 0
    for key, label, color in status_order:
        value = stats["gibbs_status"].get(key, 0)
        evidence_axis.barh(
            [0.82],
            [value],
            left=left,
            color=color,
            height=0.16,
            label=f"{label}: {value}",
        )
        left += value
    evidence_axis.set_xlim(0, total_species)
    evidence_axis.set_ylim(0, 1)
    evidence_axis.set_yticks([])
    evidence_axis.set_xlabel("species")
    evidence_axis.set_title("(d)  Gibbs evidence and links", loc="left")
    evidence_axis.legend(
        loc="upper left",
        bbox_to_anchor=(0, 0.73),
        fontsize=6.2,
        ncols=2,
        handlelength=1.2,
        columnspacing=1.0,
    )
    total = stats["totals"]
    evidence_axis.text(
        0.02,
        0.37,
        f"{total['source_records']} source records  /  {total['distinct_citations']} citations\n"
        f"{total['phase_records']} phase records  /  {total['resolved_phase_records']} resolved\n"
        f"{total['mp_matches']} MP phase matches  /  {total['mp_energy_rows']} energy rows",
        transform=evidence_axis.transAxes,
        va="top",
        fontsize=7,
        linespacing=1.45,
    )
    style_axis(evidence_axis)

    for suffix in ("png",):
        figure.savefig(FIGURES / f"dataset-overview.{suffix}", bbox_inches="tight")
    plt.close(figure)


def plot_calculation_showcase() -> None:
    sys.path.insert(0, str(REPOSITORY / "src"))
    from pourbase import (  # noqa: PLC0415
        OfficialMaterialsProjectComparison,
        OfficialMaterialsProjectDiagram,
        OfficialMaterialsProjectPhase,
        AqueousActivityModel,
        PourbaixConditions,
        PourbaixEngine,
        ThermodynamicDatabase,
        plot_official_materials_project_comparison,
    )
    from pourbase.materials_project import (  # noqa: PLC0415
        thermodynamic_species_equivalence_key,
    )

    database = ThermodynamicDatabase(DATABASE)
    metadata = json.loads((PAPER_DATA / "fe-official-mp-metadata.json").read_text())
    conditions = PourbaixConditions(
        pH_min=metadata["pH_range"][0],
        pH_max=metadata["pH_range"][1],
        pH_points=metadata["pH_range"][2],
        U_min_V=metadata["U_V_range"][0],
        U_max_V=metadata["U_V_range"][1],
        U_points=metadata["U_V_range"][2],
        aqueous_activities=AqueousActivityModel(metadata["log10_aqueous_activity"]),
    )
    experimental = PourbaixEngine(database).calculate("Fe", conditions, allow_incomplete=True)
    with (PAPER_DATA / metadata["phase_file"]).open(newline="") as handle:
        cached_rows = list(csv.DictReader(handle))
    phases = tuple(
        OfficialMaterialsProjectPhase(
            phase_id=row["phase_id"],
            label=row["label"],
            formula=row["formula"],
            phase_type=row["phase_type"],
            source_url=row["source_url"],
            metal_count=float(row["metal_count"]),
            oxygen_per_metal=float(row["oxygen_per_metal"]),
            hydrogen_per_metal=float(row["hydrogen_per_metal"]),
            protons_per_metal=float(row["protons_per_metal"]),
            electrons_per_metal=float(row["electrons_per_metal"]),
            baseline_energy_eV_metal=float(row["baseline_energy_eV_metal"]),
            log10_activity=(
                float(row["log10_activity"]) if row["log10_activity"] else None
            ),
        )
        for row in cached_rows
    )
    pH_grid, U_grid = np.meshgrid(experimental.pH, experimental.U_V)
    energy_stack = np.stack(
        [
            phase.baseline_energy_eV_metal
            - 0.0591 * phase.protons_per_metal * pH_grid
            - phase.electrons_per_metal * U_grid
            for phase in phases
        ]
    )
    stable_phase_index = np.argmin(energy_stack, axis=0)
    observed_counts = np.bincount(stable_phase_index.ravel(), minlength=len(phases))
    expected_counts = np.asarray(
        [int(row["stable_grid_points"]) for row in cached_rows], dtype=int
    )
    if not np.array_equal(observed_counts, expected_counts):
        raise RuntimeError(
            "Cached Materials Project grid no longer reproduces its recorded phase counts"
        )
    minimum_energy = np.take_along_axis(
        energy_stack, stable_phase_index[np.newaxis, :, :], axis=0
    )[0]
    official = OfficialMaterialsProjectDiagram(
        symbol="Fe",
        conditions=conditions,
        phases=phases,
        pH=experimental.pH,
        U_V=experimental.U_V,
        stable_phase_index=stable_phase_index,
        minimum_energy_eV_metal=minimum_energy,
        her_V=experimental.her_V,
        oer_V=experimental.oer_V,
        database_version=metadata["materials_project_database_version"],
        mp_api_version=metadata["mp_api_version"],
        pymatgen_version=metadata["pymatgen_version"],
        filter_solids=metadata["filter_solids"],
        use_gibbs_300K=metadata["use_gibbs_300K"],
    )
    same = np.zeros_like(stable_phase_index, dtype=bool)
    experimental_keys = [
        thermodynamic_species_equivalence_key(species)
        for species in experimental.system.species
    ]
    for experimental_index, experimental_key in enumerate(experimental_keys):
        for phase_index, phase in enumerate(phases):
            if experimental_key == phase.equivalence_key:
                same |= (experimental.stable_species_index == experimental_index) & (
                    stable_phase_index == phase_index
                )
    comparison = OfficialMaterialsProjectComparison(
        experimental=experimental,
        materials_project=official,
        same_thermodynamic_species=same,
    )

    figure, axes = plot_official_materials_project_comparison(comparison)
    figure.set_size_inches(9.5, 3.35)
    for axis in axes:
        axis.set_title("", loc="center")
    axes[0].set_title("(a)  Experimental", loc="left", fontsize=8)
    axes[1].set_title("(b)  Materials Project", loc="left", fontsize=8)
    axes[2].set_title(
        "(c)  Different thermodynamic species\n"
        f"{(1 - comparison.equivalent_domain_fraction) * 100:.1f}% full / "
        f"{(1 - comparison.water_window_equivalent_domain_fraction) * 100:.1f}% water window",
        loc="left",
        fontsize=8,
    )
    for axis in axes:
        for label in axis.texts:
            if label.get_text() == "FeOH⁺":
                label.set_position((8.65, -0.50))
            elif label.get_text() == "Fe₃O₄":
                label.set_position((11.25, -0.66))
        axis.title.set_fontsize(8)
        axis.title.set_ha("left")
        axis.title.set_position((0, 1.02))
        style_axis(axis)
    for suffix in ("png",):
        figure.savefig(FIGURES / f"calculation-showcase.{suffix}", bbox_inches="tight")
    plt.close(figure)

    with closing(pb.ThermodynamicDatabase(DATABASE).connect()) as connection:
        experimental_dataset_version = scalar(
            connection, "SELECT value FROM metadata WHERE key='dataset_version'"
        )
    output_metadata = {
        **metadata,
        "experimental_dataset_version": experimental_dataset_version,
        "equivalence_definition": (
            "Solids match by H/O composition per metal; aqueous species match by "
            "proton and electron coefficients per metal."
        ),
        "equivalent_domain_fraction": comparison.equivalent_domain_fraction,
        "water_window_equivalent_domain_fraction": (
            comparison.water_window_equivalent_domain_fraction
        ),
        "stable_experimental_species": [
            species.species for species in experimental.stable_species
        ],
        "stable_materials_project_phases": [
            phase.label for phase in official.stable_phases
        ],
    }
    (GENERATED / "fe-pourbaix-comparison.json").write_text(
        json.dumps(output_metadata, indent=2, ensure_ascii=False) + "\n"
    )
    with (GENERATED / "fe-pourbaix-comparison-changes.csv").open(
        "w", newline=""
    ) as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("experimental_species", "mp_phase", "grid_points"))
        writer.writerows(comparison.changed_phase_pairs())


def _float(row: dict[str, str], key: str) -> float:
    return float(row[key])


def plot_mp_thermochemistry() -> None:
    with (MP_THERMOCHEMISTRY / "mp-thermochemistry-points.csv").open(newline="") as handle:
        points = list(csv.DictReader(handle))
    methods = ["GGA_GGA+U", "GGA_GGA+U_R2SCAN", "r2SCAN"]
    method_colors = dict(zip(methods, (BLUE, ORANGE, GREEN)))
    labels = {
        "GGA_GGA+U": "GGA / GGA+U",
        "GGA_GGA+U_R2SCAN": "GGA / GGA+U / r2SCAN",
        "r2SCAN": "r2SCAN",
    }
    properties = [
        ("enthalpy", "experimental_enthalpy_eV_atom", "Formation enthalpy"),
        ("gibbs", "experimental_gibbs_eV_atom", "Gibbs energy"),
    ]
    figure, axes = plt.subplots(2, 2, figsize=(9.5, 6.0), layout="constrained")
    panel = 0
    for row_index, (_, experimental_key, title) in enumerate(properties):
        comparison_axis, residual_axis = axes[row_index]
        all_values: list[float] = []
        for method in methods:
            selected_rows = [
                item
                for item in points
                if item["calculation_type"] == method and item[experimental_key]
            ]
            x = np.asarray([_float(item, experimental_key) for item in selected_rows])
            y = np.asarray(
                [_float(item, "formation_energy_eV_atom") for item in selected_rows]
            )
            selected = np.asarray(
                [int(item["selected_for_comparison"]) == 1 for item in selected_rows]
            )
            residual = y - x
            all_values.extend(x.tolist())
            all_values.extend(y.tolist())
            comparison_axis.scatter(
                x[~selected],
                y[~selected],
                s=18,
                color=method_colors[method],
                alpha=0.68,
                edgecolors="white",
                linewidths=0.35,
                rasterized=True,
            )
            comparison_axis.scatter(
                x[selected],
                y[selected],
                s=22,
                color=method_colors[method],
                edgecolors=INK,
                linewidths=0.75,
                rasterized=True,
            )
            residual_axis.scatter(
                x[~selected],
                residual[~selected],
                s=18,
                color=method_colors[method],
                alpha=0.68,
                edgecolors="white",
                linewidths=0.35,
                rasterized=True,
            )
            residual_axis.scatter(
                x[selected],
                residual[selected],
                s=22,
                color=method_colors[method],
                edgecolors=INK,
                linewidths=0.75,
                rasterized=True,
            )
            residual_axis.text(
                0.02,
                0.96 - methods.index(method) * 0.075,
                f"{labels[method]}: MAE {np.mean(np.abs(residual)):.3f} eV/atom",
                transform=residual_axis.transAxes,
                va="top",
                fontsize=6.3,
                color=method_colors[method],
            )
        low, high = min(all_values), max(all_values)
        margin = (high - low) * 0.035
        comparison_axis.plot(
            [low - margin, high + margin],
            [low - margin, high + margin],
            "--",
            color=INK,
            linewidth=0.9,
        )
        comparison_axis.set_xlim(low - margin, high + margin)
        comparison_axis.set_ylim(low - margin, high + margin)
        residual_axis.axhline(0, color=INK, linestyle="--", linewidth=0.9)
        comparison_axis.set_xlabel(f"Experimental {title.lower()} / eV atom$^{{-1}}$")
        comparison_axis.set_ylabel("MP formation energy / eV atom$^{-1}$")
        residual_axis.set_xlabel(f"Experimental {title.lower()} / eV atom$^{{-1}}$")
        residual_axis.set_ylabel("MP minus experiment / eV atom$^{-1}$")
        comparison_axis.set_title(
            f"({chr(97 + panel)})  {title}: phase-matched values", loc="left"
        )
        panel += 1
        residual_axis.set_title(
            f"({chr(97 + panel)})  {title}: signed residual", loc="left"
        )
        panel += 1
        style_axis(comparison_axis)
        style_axis(residual_axis)
    handles = [
        Line2D(
            [],
            [],
            marker="o",
            linestyle="",
            markersize=5,
            color=method_colors[method],
            label=labels[method],
        )
        for method in methods
    ]
    handles.append(
        Line2D(
            [],
            [],
            marker="o",
            linestyle="",
            markersize=5,
            markerfacecolor="white",
            markeredgecolor=INK,
            label="selected for diagram comparison",
        )
    )
    figure.legend(
        handles=handles,
        loc="outside upper center",
        ncols=4,
        fontsize=7,
        handlelength=1,
        columnspacing=1.5,
    )
    for suffix in ("png",):
        figure.savefig(FIGURES / f"mp-thermochemistry.{suffix}", bbox_inches="tight")
    plt.close(figure)


TABLES = (
    ("species", "Formula, charge, phase, composition, oxidation state and reaction coefficients"),
    ("selected_thermochemistry", "Derived by the selection policy: one recommended Gibbs energy, entropy and enthalpy per species"),
    ("reported_thermochemistry", "Every retained reported value, recommended or not, with supersession links"),
    ("sources", "Full citations, links, locators and access dates"),
    ("phases", "Phase identity, candidate polymorphs, space group and evidence"),
    ("warnings", "Scientific cautions attached to records"),
    ("computational_fallbacks", "Opt-in Materials Project 300 K estimates for missing solid Gibbs energies"),
    ("materials_project_matches", "Reviewed experimental-phase to Materials Project structure matches"),
    ("materials_project_energies", "Method-specific Materials Project energies with provenance"),
    ("element_coverage", "Status of every chemical element"),
    ("ligands", "Free-ligand reference states for ligand-aware calculations"),
    ("additional_components", "Additional independent buffered references per species, beyond the first ligand"),
    ("metadata", "Dataset version, reference conditions, schema version and value policy"),
)


def write_markdown(stats: dict[str, Any]) -> None:
    total = stats["totals"]
    species = total["species"]
    properties = {item["property"]: item["available"] for item in stats["properties"]}
    methods = stats["materials_project_comparison"]["methods"]
    comparison = json.loads((GENERATED / "fe-pourbaix-comparison.json").read_text())
    with closing(pb.ThermodynamicDatabase(DATABASE).connect()) as connection:
        table_rows = {name: scalar(connection, f'SELECT COUNT(*) FROM "{name}"') for name, _ in TABLES}

    def percent(count: int) -> str:
        return f"{count} ({100 * count / species:.0f} %)"

    lines = [
        "# Dataset statistics",
        "",
        f"pourbase dataset {stats['metadata']['dataset_version']}, generated from the bundled database "
        "by `scripts/dataset_statistics.py`. Machine-readable versions are in "
        "[`docs/statistics`](docs/statistics).",
        "",
        "## Summary",
        "",
        "| | |",
        "|---|---|",
        f"| Species | {species} |",
        f"| Supported elemental systems | {total['supported_systems']} of {total['all_elements_documented']} elements |",
        f"| Recommended Gibbs energies | {percent(properties['Gibbs energy'])} |",
        f"| Recommended entropies | {percent(properties['Entropy'])} |",
        f"| Recommended formation enthalpies | {percent(properties['Formation enthalpy'])} |",
        f"| Reported values retained | {total['reported_thermochemistry']} |",
        f"| Source records | {total['source_records']} ({total['distinct_citations']} distinct citations) |",
        f"| Phase records | {total['phase_records']} ({total['resolved_phase_records']} resolved) |",
        f"| Warnings | {total['warnings']} |",
        f"| Materials Project matches | {total['mp_matches']} phases, {total['mp_energy_rows']} energy rows |",
        f"| Materials Project fallback estimates | {total['computational_fallbacks']} |",
        f"| Ligands | {total['ligands']} |",
        "",
        "Gibbs energies by evidence status:",
        "",
        "| Status | Species |",
        "|---|---|",
        *(f"| `{status}` | {count} |" for status, count in stats["gibbs_status"].items()),
        "",
        "Species by phase:",
        "",
        "| Phase | Species | Gibbs | Entropy | Enthalpy |",
        "|---|---|---|---|---|",
        *(f"| {row['phase']} | {row['species']} | {row['gibbs']} | {row['entropy']} | {row['enthalpy']} |"
          for row in stats["phases"]),
        "",
        "## Database tables",
        "",
        "| Table | Rows | Contents |",
        "|---|---|---|",
        *(f"| `{name}` | {table_rows[name]} | {description} |" for name, description in TABLES),
        "",
        "[`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) defines every column, unit and join.",
        "",
        "## Coverage",
        "",
        "![Dataset overview](docs/statistics/dataset-overview.png)",
        "",
        "Elemental coverage, species by phase, property availability and evidence status.",
        "",
        "## Comparison with Materials Project",
        "",
        "![Experimental and Materials Project formation energies](docs/statistics/mp-thermochemistry.png)",
        "",
        "Phase-matched experimental formation energies against Materials Project DFT formation "
        f"energies (database {stats['materials_project_comparison']['materials_project_database_versions'][0]}). "
        "Mean absolute differences, in eV per atom:",
        "",
        "| Method | Enthalpy (n) | Enthalpy MAE | Gibbs (n) | Gibbs MAE |",
        "|---|---|---|---|---|",
        *(f"| {method} | {methods['enthalpy'][method]['count']} | "
          f"{methods['enthalpy'][method]['mean_absolute_error_eV_atom']:.3f} | "
          f"{methods['gibbs'][method]['count']} | {methods['gibbs'][method]['mean_absolute_error_eV_atom']:.3f} |"
          for method in methods["enthalpy"] if method in methods["gibbs"]),
        "",
        "The enthalpy is the closest comparison with a 0 K DFT formation energy; the Gibbs difference "
        "also includes finite-temperature entropy. These differences are diagnostics, not "
        "experimental error estimates.",
        "",
        "## Example: the iron system",
        "",
        "![Iron Pourbaix diagram compared with Materials Project](docs/statistics/calculation-showcase.png)",
        "",
        f"The experimental Fe diagram at log₁₀ a = {comparison['log10_aqueous_activity']:g} and the official "
        f"Materials Project diagram (database {comparison['materials_project_database_version']}) have the "
        f"same thermodynamic species over {100 * comparison['equivalent_domain_fraction']:.0f} % of the grid "
        f"and {100 * comparison['water_window_equivalent_domain_fraction']:.0f} % of the water-stability window.",
        "",
        "## Systems",
        "",
        "| Element | System | Species | Aqueous | Solid | Gas | Liquid | Gibbs | Entropy | Enthalpy | Warnings |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
        *(f"| {row['symbol']} | {row['system']} | {row['species']} | {row['aqueous']} | {row['solid']} | "
          f"{row['gas']} | {row['liquid']} | {row['gibbs']} | {row['entropy']} | {row['enthalpy']} | {row['warnings']} |"
          for row in stats["systems"]),
        "",
    ]
    STATISTICS.write_text("\n".join(lines))


def main() -> None:
    if not DATABASE.is_file():
        raise FileNotFoundError(DATABASE)
    stats = collect_statistics()
    write_statistics(stats)
    plot_dataset_overview(stats)
    plot_calculation_showcase()
    plot_mp_thermochemistry()
    write_markdown(stats)
    print(f"Wrote {STATISTICS} and {GENERATED}")


if __name__ == "__main__":
    main()
