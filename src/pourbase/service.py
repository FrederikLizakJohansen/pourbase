"""Shared calculation adapter for the command line and desktop application."""

from __future__ import annotations

import base64
import csv
import io
import math
from collections.abc import Mapping
from typing import Any

import numpy as np

from .activity_coefficients import (
    DaviesActivityCoefficientModel,
    IdealActivityCoefficientModel,
)
from .boltzmann import boltzmann_smooth
from .constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from .database import ThermodynamicDatabase
from .engine import PourbaixEngine
from .conversions import ConcentrationConversion, convert_concentration
from .equilibria import boundary_equations, plating_potentials
from .mass_balance import MassBalanceEngine
from .materials_project import (
    OfficialMaterialsProjectClient,
    OfficialMaterialsProjectComparator,
)
from .models import (
    AqueousActivityModel,
    GasFugacityModel,
    GibbsEnergyPolicy,
    LigandActivity,
    LigandActivityModel,
    PourbaixConditions,
    TotalMetalConcentration,
)
from .plotting import (
    plot_boltzmann_diagram,
    plot_diagram,
    plot_mass_balance_summary,
    plot_official_materials_project_comparison,
)
from .speciation import plot_speciation_profile, speciation_at, speciation_profile
from .sweeps import ConcentrationSweepEngine, plot_concentration_sweep


PERIODIC_CATEGORY_LABELS = {
    "dissolved_or_gas": "Dissolved aqueous species or gas",
    "solid_oxide": "Solid oxide",
    "hydroxide_or_oxyhydroxide": "Solid hydroxide or oxyhydroxide",
    "elemental_solid": "Elemental solid",
    "elemental_liquid": "Elemental liquid",
    "other_solid": "Other solid compound",
    "incomplete": "Calculation withheld because Gibbs data are incomplete",
    "reference_component": "Reference component",
    "deferred_noble_gas": "Noble gas outside practical aqueous scope",
    "restricted_radioactive": "Deferred for radiological evidence review",
    "outside_current_scope": "Not yet curated",
}


def _energy_policy(payload: Mapping[str, Any]) -> GibbsEnergyPolicy:
    return GibbsEnergyPolicy(
        str(payload.get("energy_policy", GibbsEnergyPolicy.EXPERIMENTAL_ONLY.value))
    )


def _ligand_model(raw: object) -> LigandActivityModel | None:
    if raw in (None, [], ()):
        return None
    if not isinstance(raw, list):
        raise ValueError("ligands must be a JSON list")
    assignments = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise ValueError("each ligand setting must be a JSON object")
        assignments.append(
            LigandActivity(
                ligand_id=str(item["ligand_id"]),
                log10_free_activity=(
                    float(item["log10_free_activity"])
                    if item.get("log10_free_activity") is not None
                    else None
                ),
                total_unbound_mol_L=(
                    float(item["total_unbound_mol_L"])
                    if item.get("total_unbound_mol_L") is not None
                    else None
                ),
                acid_pKa=(
                    float(item["acid_pKa"])
                    if item.get("acid_pKa") is not None
                    else None
                ),
            )
        )
    return LigandActivityModel(tuple(assignments))


def _gas_fugacity_model(payload: Mapping[str, Any]) -> GasFugacityModel:
    overrides = payload.get("gas_fugacity_overrides", {})
    if not isinstance(overrides, Mapping):
        raise ValueError("gas_fugacity_overrides must be a JSON object")
    return GasFugacityModel(
        default_log10_fugacity=float(payload.get("log10_gas_fugacity", 0.0)),
        overrides={str(key): float(value) for key, value in overrides.items()},
    )


def _concentration_input(
    payload: Mapping[str, Any], symbol: str, mode: str
) -> ConcentrationConversion:
    """Resolve modern unit-aware input while retaining the initial JSON API."""
    if "concentration_value" in payload:
        return convert_concentration(
            symbol,
            float(payload["concentration_value"]),
            str(payload.get("concentration_unit", "log10_molar")),
            solution_density_kg_L=float(payload.get("solution_density_kg_L", 1.0)),
        )
    if mode == "mass_balance":
        return convert_concentration(
            symbol, float(payload.get("total_metal_mol_L", 1e-6)), "molar"
        )
    return convert_concentration(
        symbol, float(payload.get("log10_activity", -6.0)), "log10_molar"
    )


def _periodic_category(species: Any) -> str:
    """Classify one stable species for the periodic-table overview."""
    if species.phase in {"aqueous", "gas", "gaseous"}:
        return "dissolved_or_gas"
    if species.phase == "liquid":
        return "elemental_liquid"
    if species.phase != "solid":
        return "other_solid"
    is_oxide = (
        species.core_oxygen_count > 0
        and species.core_hydrogen_count == 0
        and species.ligand_count == 0
    )
    if is_oxide:
        return "solid_oxide"
    if (
        species.core_oxygen_count > 0
        and species.core_hydrogen_count > 0
        and species.ligand_count == 0
    ):
        return "hydroxide_or_oxyhydroxide"
    if (
        species.core_oxygen_count == 0
        and species.core_hydrogen_count == 0
        and species.ligand_count == 0
    ):
        return "elemental_solid"
    return "other_solid"


def calculate_periodic_table(
    payload: Mapping[str, Any], database: ThermodynamicDatabase
) -> dict[str, Any]:
    """Evaluate every supported single-metal system at one pH/potential point."""
    pH = float(payload.get("periodic_pH", payload.get("probe_pH", 0.0)))
    potential = float(payload.get("periodic_potential_V", 1.6))
    reference = str(payload.get("potential_reference", "RHE")).upper()
    if not math.isfinite(pH) or not -2.0 <= pH <= 16.0:
        raise ValueError("periodic-table pH must be between -2 and 16")
    if not math.isfinite(potential) or not -3.0 <= potential <= 5.0:
        raise ValueError("periodic-table potential must be between -3 and 5 V")
    if reference not in {"SHE", "RHE"}:
        raise ValueError("potential_reference must be SHE or RHE")
    allow_incomplete = bool(payload.get("allow_incomplete", False))
    energy_policy = _energy_policy(payload)
    reference_state = database.reference_state
    temperature_K = reference_state.temperature_K
    nernst_slope = GAS_CONSTANT_J_MOL_K * temperature_K * LN_10 / FARADAY_C_MOL
    potential_she = potential if reference == "SHE" else potential - nernst_slope * pH
    if "concentration_value" in payload:
        unit = str(payload.get("concentration_unit", "log10_molar"))
    else:
        unit = "log10_molar"
    engine = PourbaixEngine(database)
    pending: list[dict[str, Any]] = []
    stable_records: list[str] = []
    stable_by_id: dict[str, Any] = {}
    for symbol, system_name in database.available_systems():
        concentration = _concentration_input(payload, symbol, "fixed_activity")
        system_conditions = PourbaixConditions(
            temperature_K=reference_state.temperature_K,
            pressure_bar=reference_state.pressure_bar,
            aqueous_activities=AqueousActivityModel(
                default_log10_activity=concentration.log10_standard_activity
            ),
            gas_fugacities=_gas_fugacity_model(payload),
        )
        system = database.load_system(symbol, energy_policy=energy_policy)
        missing = [
            item
            for item in system.excluded
            if item.reason == "recommended_gibbs_energy_unavailable"
        ]
        if missing and not allow_incomplete:
            pending.append(
                {
                    "symbol": symbol,
                    "system": system_name,
                    "status": "incomplete",
                    "category": "incomplete",
                    "molar_concentration": concentration.molar_concentration,
                    "log10_activity": concentration.log10_standard_activity,
                    "missing_record_ids": [item.record_id for item in missing],
                    "excluded_record_count": len(system.excluded),
                }
            )
            continue
        energies = sorted(
            [
                (
                    float(
                        np.asarray(
                            engine.transformed_gibbs_J_mol_metal(
                                species,
                                reference_state,
                                system_conditions,
                                pH,
                                potential_she,
                            )
                        ).item()
                    ),
                    species,
                )
                for species in system.species
            ],
            key=lambda item: item[0],
        )
        stable_energy, stable = energies[0]
        stable_records.append(stable.record_id)
        stable_by_id[stable.record_id] = stable
        pending.append(
            {
                "symbol": symbol,
                "system": system_name,
                "status": (
                    "calculated_with_fallback"
                    if any(
                        species.gibbs_status == "materials_project_sisso_300K_fallback"
                        for species in system.species
                    )
                    else ("calculated_with_gaps" if missing else "calculated")
                ),
                "stable_record_id": stable.record_id,
                "stable_species": stable.species,
                "formula_ascii": stable.formula_ascii,
                "phase": stable.phase,
                "phase_detail": stable.phase_detail,
                "gibbs_status": stable.gibbs_status,
                "gibbs_source_id": stable.source_id,
                "molar_concentration": concentration.molar_concentration,
                "log10_activity": concentration.log10_standard_activity,
                "energy_margin_J_mol_metal": (
                    energies[1][0] - stable_energy if len(energies) > 1 else None
                ),
                "missing_record_ids": [item.record_id for item in missing],
                "excluded_record_count": len(system.excluded),
            }
        )

    details_by_id = {
        item["record_id"]: item for item in database.species_details(stable_records)
    }
    counts = {key: 0 for key in PERIODIC_CATEGORY_LABELS}
    results = []
    for item in pending:
        record_id = item.get("stable_record_id")
        if record_id is None:
            counts["incomplete"] += 1
            results.append(item)
            continue
        details = details_by_id[str(record_id)]
        stable = stable_by_id[str(record_id)]
        category = _periodic_category(stable)
        phase_identity = details["phase_identity"] or {}
        identified_phase = phase_identity.get("identified_phase")
        possible_phases = phase_identity.get("possible_phases")
        if identified_phase:
            structure_label = str(identified_phase)
        elif possible_phases:
            structure_label = f"possible: {possible_phases}"
        elif stable.phase_detail and stable.phase_detail.lower() != "solid":
            structure_label = stable.phase_detail
        else:
            structure_label = "structure unresolved"
        counts[category] += 1
        results.append(
            {
                **item,
                "category": category,
                "structure_label": structure_label,
                "phase_identity": details["phase_identity"],
                "gibbs_source": (
                    {
                        "source_id": f"Materials Project {details['computational_fallback']['canonical_mp_id']}",
                        "citation": details["computational_fallback"]["model"],
                        "url": details["computational_fallback"]["source_url"],
                        "locator": f"{details['computational_fallback']['temperature_K']:g} K SISSO estimate",
                    }
                    if stable.gibbs_status == "materials_project_sisso_300K_fallback"
                    else details["thermochemistry"]["gibbs_source"]
                ),
                "warnings": details["warnings"],
            }
        )

    coverage = database.element_coverage()
    result_by_symbol = {item["symbol"]: item for item in results}
    full_results = []
    coverage_status_counts: dict[str, int] = {}
    for coverage_item in coverage:
        symbol = str(coverage_item["symbol"])
        coverage_status = str(coverage_item["coverage_status"])
        coverage_status_counts[coverage_status] = coverage_status_counts.get(coverage_status, 0) + 1
        if symbol in result_by_symbol:
            full_results.append({
                **result_by_symbol[symbol],
                "atomic_number": coverage_item["atomic_number"],
                "coverage_status": coverage_status,
                "coverage_reason": coverage_item["reason"],
            })
        else:
            counts[coverage_status] = counts.get(coverage_status, 0) + 1
            full_results.append({
                **coverage_item,
                "status": coverage_status,
                "category": coverage_status,
                "stable_species": None,
                "missing_record_ids": [],
                "warnings": [],
            })

    return {
        "conditions": {
            "pH": pH,
            "input_potential_V": potential,
            "input_reference": reference,
            "potential_V_vs_SHE": potential_she,
            "potential_V_vs_RHE": potential_she + nernst_slope * pH,
            "rhe_to_she_offset_V": -nernst_slope * pH,
            "temperature_K": temperature_K,
            "concentration_input_unit": unit,
            "concentration_input_value": float(
                payload.get("concentration_value", payload.get("log10_activity", -6.0))
            ),
            "solution_density_kg_L": float(payload.get("solution_density_kg_L", 1.0)),
            "allow_incomplete": allow_incomplete,
            "energy_policy": energy_policy.value,
        },
        "category_labels": PERIODIC_CATEGORY_LABELS,
        "category_counts": counts,
        "periodic_position_count": len(full_results),
        "supported_system_count": len(results),
        "calculated_system_count": sum(
            item["status"].startswith("calculated") for item in results
        ),
        "coverage_status_counts": coverage_status_counts,
        "elements": full_results,
        "method": (
            "Each supported single-metal system is evaluated directly at the selected "
            "pH and SHE-converted potential using its transformed Gibbs energies."
        ),
    }


def calculate(
    payload: Mapping[str, Any], database: ThermodynamicDatabase
) -> tuple[Any, dict[str, Any]]:
    """Calculate one requested diagram and return it with JSON-ready metadata."""
    symbol = str(payload.get("symbol", "Fe")).strip()
    mode = str(payload.get("mode", "fixed_activity"))
    concentration = _concentration_input(payload, symbol, mode)
    overrides = payload.get("activity_overrides", {})
    if not isinstance(overrides, Mapping):
        raise ValueError("activity_overrides must be a JSON object")
    conditions = PourbaixConditions(
        temperature_K=298.15,
        pressure_bar=1.0,
        pH_min=float(payload.get("pH_min", 0.0)),
        pH_max=float(payload.get("pH_max", 14.0)),
        eh_min_V=float(payload.get("eh_min_V", -1.5)),
        eh_max_V=float(payload.get("eh_max_V", 1.5)),
        pH_points=int(payload.get("pH_points", 281)),
        eh_points=int(payload.get("eh_points", 301)),
        aqueous_activities=AqueousActivityModel(
            default_log10_activity=concentration.log10_standard_activity,
            overrides={str(key): float(value) for key, value in overrides.items()},
        ),
        gas_fugacities=_gas_fugacity_model(payload),
        ligand_activities=_ligand_model(payload.get("ligands")),
    )
    allow_incomplete = bool(payload.get("allow_incomplete", False))
    energy_policy = _energy_policy(payload)
    raw_boltzmann_scale = payload.get("boltzmann_scale")
    if mode != "fixed_activity" and raw_boltzmann_scale not in (None, ""):
        raise ValueError(
            "Boltzmann smoothing applies to fixed-activity diagrams. "
            "Mass-balance mode already reports conserved species amounts."
        )
    if mode == "fixed_activity":
        diagram = PourbaixEngine(database).calculate(
            symbol, conditions, allow_incomplete=allow_incomplete,
            energy_policy=energy_policy,
        )
    elif mode == "mass_balance":
        coefficient_name = str(payload.get("activity_coefficient_model", "ideal"))
        if coefficient_name == "davies":
            coefficient_model = DaviesActivityCoefficientModel(
                ionic_strength_mol_L=float(payload.get("ionic_strength_mol_L", 0.01))
            )
        elif coefficient_name == "ideal":
            coefficient_model = IdealActivityCoefficientModel()
        else:
            raise ValueError("activity_coefficient_model must be ideal or davies")
        diagram = MassBalanceEngine(database, coefficient_model).calculate(
            symbol,
            conditions,
            TotalMetalConcentration(concentration.molar_concentration),
            allow_incomplete=allow_incomplete,
            energy_policy=energy_policy,
        )
    else:
        raise ValueError("mode must be fixed_activity or mass_balance")

    probe_pH = float(payload.get("probe_pH", 7.0))
    probe_eh = float(payload.get("probe_eh_V", 0.0))
    probe_species = diagram.species_at(probe_pH, probe_eh)
    probe: dict[str, Any] = {
        "pH": probe_pH,
        "eh_V": probe_eh,
        "record_id": probe_species.record_id,
        "species": probe_species.species,
        "phase": probe_species.phase,
    }
    if mode == "mass_balance":
        state = diagram.state_at(probe_pH, probe_eh)
        probe.update(
            dissolved_metal_mol_L=state.dissolved_metal_mol_L,
            precipitated_metal_mol_L=state.precipitated_metal_mol_L,
            precipitated_fraction=state.precipitated_fraction,
            aqueous_concentrations_mol_L={
                item.species: concentration
                for item, concentration in state.aqueous_concentrations_mol_L
            },
        )
        probe["speciation"] = list(speciation_at(diagram, probe_pH, probe_eh))
    stable_ids = {item.record_id for item in diagram.stable_species}
    exclusion_by_id = {
        item.record_id: {"reason": item.reason, "status": item.status}
        for item in diagram.system.excluded
    }
    details = database.species_details(
        [item.record_id for item in diagram.system.species]
        + [item.record_id for item in diagram.system.excluded]
    )
    effective_by_id = {item.record_id: item for item in diagram.system.species}
    included_details = [
        {
            **item,
            "stable_on_grid": item["record_id"] in stable_ids,
            "calculation_gibbs_energy_J_mol": effective_by_id[item["record_id"]].gibbs_energy_J_mol,
            "calculation_gibbs_status": effective_by_id[item["record_id"]].gibbs_status,
            "calculation_gibbs_source_id": effective_by_id[item["record_id"]].source_id,
        }
        for item in details
        if item["record_id"] not in exclusion_by_id
    ]
    excluded_details = [
        {**item, "exclusion": exclusion_by_id[item["record_id"]]}
        for item in details
        if item["record_id"] in exclusion_by_id
    ]
    result = {
        "symbol": diagram.system.symbol,
        "system": diagram.system.system,
        "mode": mode,
        "energy_policy": energy_policy.value,
        "fallback_record_ids": [
            item.record_id for item in diagram.system.species
            if item.gibbs_status == "materials_project_sisso_300K_fallback"
        ],
        "concentration_input": concentration.as_dict(),
        "conditions": conditions.as_dict(),
        "stable_species": [
            {
                "record_id": item.record_id,
                "species": item.species,
                "phase": item.phase,
                "gibbs_status": item.gibbs_status,
                "source_id": item.source_id,
            }
            for item in diagram.stable_species
        ],
        "excluded_species": [
            {
                "record_id": item.record_id,
                "species": item.species,
                "reason": item.reason,
                "status": item.status,
            }
            for item in diagram.system.excluded
        ],
        "substances": {
            "included": included_details,
            "excluded": excluded_details,
        },
        "probe": probe,
    }
    if mode == "fixed_activity":
        result["boundaries"] = [
            item.as_dict() for item in boundary_equations(diagram, database)
        ]
        plating = plating_potentials(diagram, database)
        result["plating_potentials"] = [item.as_dict() for item in plating]
        result["plating_limit_V_vs_SHE"] = (
            plating[0].potential_V_vs_SHE if plating else None
        )
        raw_scale = raw_boltzmann_scale
        if raw_scale not in (None, ""):
            smoothed = boltzmann_smooth(diagram, float(raw_scale))
            result["boltzmann_smoothing"] = {
                "thermal_scale": smoothed.thermal_scale,
                "effective_thermal_energy_J_mol": (
                    smoothed.effective_thermal_energy_J_mol
                ),
                "interpretation": smoothed.interpretation,
            }
    else:
        result["boundaries"] = []
        result["boundary_note"] = (
            "Mass-balanced boundaries are numerical equilibria that include metal "
            "inventory and precipitation; pairwise fixed-activity equations do not apply."
        )
    return diagram, result


def render_png(
    diagram: Any,
    mode: str,
    *,
    label_domains: bool = True,
    show_legend: bool = True,
    show_boundaries: bool = True,
    show_water: bool = True,
    plating_potential_V: float | None = None,
    plating_label: str | None = None,
    boltzmann_scale: float | None = None,
) -> bytes:
    """Render a diagram to a PNG byte string."""
    import matplotlib.pyplot as plt

    if mode == "mass_balance":
        figure, _ = plot_mass_balance_summary(
            diagram,
            title=f"{diagram.system.system} — experimental data",
            label_domains=label_domains,
            show_legend=show_legend,
            show_boundaries=show_boundaries,
            show_water=show_water,
        )
    else:
        plotter = plot_diagram
        plotted = diagram
        if boltzmann_scale is not None:
            plotter = plot_boltzmann_diagram
            plotted = boltzmann_smooth(diagram, boltzmann_scale)
        axis = plotter(
            plotted,
            title=(
                f"{diagram.system.system} - experimental data"
                + (
                    f"; Boltzmann-like soft-min, scale {boltzmann_scale:g}"
                    if boltzmann_scale is not None
                    else ""
                )
            ),
            label_domains=label_domains,
            show_legend=show_legend,
            show_boundaries=show_boundaries,
            show_water=show_water,
        )
        if plating_potential_V is not None:
            axis.axhline(
                plating_potential_V,
                color="green",
                linestyle="-.",
                linewidth=1.2,
                label=plating_label or "direct plating equilibrium",
            )
            if show_legend:
                axis.legend(fontsize=7, loc="upper right", framealpha=0.9)
        figure = axis.figure
    output = io.BytesIO()
    figure.savefig(output, format="png", dpi=150)
    plt.close(figure)
    return output.getvalue()


def render_grid_csv(diagram: Any) -> bytes:
    """Export every calculated pH/Eh cell with its winning database record."""
    output = io.StringIO()
    fieldnames = ["pH", "Eh_V_vs_SHE", "record_id", "species", "phase"]
    if hasattr(diagram, "dissolved_metal_mol_L"):
        fieldnames.extend(["dissolved_metal_mol_L", "precipitated_metal_fraction"])
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for eh_index, eh in enumerate(diagram.eh_V):
        for pH_index, pH in enumerate(diagram.pH):
            species = diagram.system.species[
                int(diagram.stable_species_index[eh_index, pH_index])
            ]
            row: dict[str, object] = {
                "pH": float(pH),
                "Eh_V_vs_SHE": float(eh),
                "record_id": species.record_id,
                "species": species.species,
                "phase": species.phase,
            }
            if hasattr(diagram, "dissolved_metal_mol_L"):
                row["dissolved_metal_mol_L"] = float(
                    diagram.dissolved_metal_mol_L[eh_index, pH_index]
                )
                row["precipitated_metal_fraction"] = float(
                    diagram.precipitated_metal_fraction[eh_index, pH_index]
                )
            writer.writerow(row)
    return output.getvalue().encode("utf-8")


def render_speciation_png(diagram: Any, eh_V: float) -> bytes:
    """Render a pH-dependent species-fraction profile for a mass balance."""
    import matplotlib.pyplot as plt

    profile = speciation_profile(diagram, eh_V)
    axis = plot_speciation_profile(profile)
    output = io.BytesIO()
    axis.figure.savefig(output, format="png", dpi=150)
    plt.close(axis.figure)
    return output.getvalue()


def calculate_with_image(
    payload: Mapping[str, Any], database: ThermodynamicDatabase
) -> dict[str, Any]:
    diagram, result = calculate(payload, database)
    plating_rows = result.get("plating_potentials", [])
    show_plating = bool(payload.get("show_plating", False)) and bool(plating_rows)
    plating_row = plating_rows[0] if show_plating else None
    result["image_png_base64"] = base64.b64encode(
        render_png(
            diagram,
            str(result["mode"]),
            label_domains=bool(payload.get("show_labels", True)),
            show_legend=bool(payload.get("show_legend", True)),
            show_boundaries=bool(payload.get("show_boundaries", True)),
            show_water=bool(payload.get("show_water", True)),
            plating_potential_V=(
                float(plating_row["potential_V_vs_SHE"])
                if plating_row is not None
                else None
            ),
            plating_label=(
                f"{plating_row['ion_species']} / metal plating"
                if plating_row is not None
                else None
            ),
            boltzmann_scale=(
                float(payload["boltzmann_scale"])
                if payload.get("boltzmann_scale") not in (None, "")
                else None
            ),
        )
    ).decode("ascii")
    if result["mode"] == "mass_balance":
        result["speciation_png_base64"] = base64.b64encode(
            render_speciation_png(diagram, float(payload.get("probe_eh_V", 0.0)))
        ).decode("ascii")
    return result


def calculate_sweep_with_image(
    payload: Mapping[str, Any], database: ThermodynamicDatabase
) -> dict[str, Any]:
    """Calculate and render a fixed-activity concentration sweep."""
    symbol = str(payload.get("symbol", "Fe")).strip()
    conditions = PourbaixConditions(
        temperature_K=298.15,
        pressure_bar=1.0,
        pH_min=float(payload.get("pH_min", 0.0)),
        pH_max=float(payload.get("pH_max", 14.0)),
        eh_min_V=float(payload.get("eh_min_V", -1.5)),
        eh_max_V=float(payload.get("eh_max_V", 1.5)),
        pH_points=int(payload.get("pH_points", 141)),
        eh_points=int(payload.get("eh_points", 151)),
        aqueous_activities=AqueousActivityModel(default_log10_activity=-6.0),
        gas_fugacities=_gas_fugacity_model(payload),
        ligand_activities=_ligand_model(payload.get("ligands")),
    )
    sweep = ConcentrationSweepEngine(database).calculate(
        symbol,
        conditions,
        float(payload.get("sweep_log10_min", -10.0)),
        float(payload.get("sweep_log10_max", 0.0)),
        int(payload.get("sweep_points", 7)),
        allow_incomplete=bool(payload.get("allow_incomplete", False)),
        energy_policy=_energy_policy(payload),
    )
    probe_pH = float(payload.get("probe_pH", 7.0))
    probe_eh = float(payload.get("probe_eh_V", 0.0))
    figure, _ = plot_concentration_sweep(
        sweep,
        probe_pH=probe_pH,
        probe_eh_V=probe_eh,
        show_water=bool(payload.get("show_water", True)),
    )
    import matplotlib.pyplot as plt

    output = io.BytesIO()
    figure.savefig(output, format="png", dpi=150)
    plt.close(figure)
    stable = sweep.stable_species
    return {
        "symbol": sweep.system.symbol,
        "system": sweep.system.system,
        "energy_policy": _energy_policy(payload).value,
        "log10_activity_levels": [float(value) for value in sweep.log10_activities],
        "pH_range": [float(sweep.pH[0]), float(sweep.pH[-1]), int(sweep.pH.size)],
        "eh_V_range": [
            float(sweep.eh_V[0]),
            float(sweep.eh_V[-1]),
            int(sweep.eh_V.size),
        ],
        "probe_pH": probe_pH,
        "probe_eh_V": probe_eh,
        "stable_species": [
            {
                "record_id": item.record_id,
                "species": item.species,
                "phase": item.phase,
                "gibbs_source_id": item.source_id,
                "gibbs_status": item.gibbs_status,
            }
            for item in stable
        ],
        "image_png_base64": base64.b64encode(output.getvalue()).decode("ascii"),
        "interpretation": (
            "Each horizontal 3D slice is an independently calculated fixed-activity "
            "diagram. The projections show the stable record at the selected pH or Eh."
        ),
    }


def calculate_materials_project_comparison(
    payload: Mapping[str, Any], database: ThermodynamicDatabase
) -> dict[str, Any]:
    """Fetch an official MP diagram and compare it with the experimental grid."""
    if str(payload.get("mode", "fixed_activity")) != "fixed_activity":
        raise ValueError("Materials Project comparison requires fixed-activity mode")
    if payload.get("ligands") not in (None, [], ()):
        raise ValueError(
            "Materials Project comparison currently supports ligand-free systems"
        )
    if payload.get("activity_overrides") not in (None, {}):
        raise ValueError(
            "Materials Project comparison currently uses one shared aqueous activity"
        )
    api_key = str(payload.get("mp_api_key", "")).strip()
    if not api_key:
        raise ValueError("Enter a Materials Project API key")
    experimental, experimental_result = calculate(payload, database)
    client = OfficialMaterialsProjectClient(api_key)
    comparison = OfficialMaterialsProjectComparator(
        PourbaixEngine(database), client
    ).compare(
        experimental.system.symbol,
        experimental.conditions,
        filter_solids=bool(payload.get("mp_filter_solids", True)),
        use_gibbs_300K=bool(payload.get("mp_use_gibbs_300K", False)),
        allow_incomplete=bool(payload.get("allow_incomplete", False)),
        energy_policy=_energy_policy(payload),
    )
    official = comparison.materials_project
    probe_pH = float(payload.get("probe_pH", 7.0))
    probe_eh = float(payload.get("probe_eh_V", 0.0))
    experimental_probe = comparison.experimental.species_at(probe_pH, probe_eh)
    mp_probe = official.phase_at(probe_pH, probe_eh)
    stable_ids = {item.phase_id for item in official.stable_phases}
    changed_pairs = [
        {
            "experimental_species": experimental_species,
            "materials_project_phase": mp_phase,
            "grid_cells": cells,
            "grid_fraction": cells / comparison.same_thermodynamic_species.size,
        }
        for experimental_species, mp_phase, cells in comparison.changed_phase_pairs()
    ]
    figure, _ = plot_official_materials_project_comparison(
        comparison,
        title=f"{experimental.system.system}: experiment and Materials Project",
    )
    import matplotlib.pyplot as plt

    output = io.BytesIO()
    figure.savefig(output, format="png", dpi=150)
    plt.close(figure)
    return {
        "symbol": official.symbol,
        "system": experimental.system.system,
        "conditions": experimental.conditions.as_dict(),
        "concentration_input": experimental_result["concentration_input"],
        "equivalent_domain_fraction": comparison.equivalent_domain_fraction,
        "different_domain_fraction": 1.0 - comparison.equivalent_domain_fraction,
        "water_window_equivalent_domain_fraction": (
            comparison.water_window_equivalent_domain_fraction
        ),
        "probe": {
            "pH": probe_pH,
            "eh_V": probe_eh,
            "experimental_record_id": experimental_probe.record_id,
            "experimental_species": experimental_probe.species,
            "materials_project_phase_id": mp_probe.phase_id,
            "materials_project_phase": mp_probe.label,
            "equivalent": (
                comparison.same_thermodynamic_species[
                    int(np.abs(official.eh_V - probe_eh).argmin()),
                    int(np.abs(official.pH - probe_pH).argmin()),
                ].item()
            ),
        },
        "materials_project": {
            "database_version": official.database_version,
            "mp_api_version": official.mp_api_version,
            "pymatgen_version": official.pymatgen_version,
            "filter_solids": official.filter_solids,
            "use_gibbs_300K": official.use_gibbs_300K,
            "method": "MPRester.get_pourbaix_entries + pymatgen PourbaixDiagram",
            "documentation_url": (
                "https://docs.materialsproject.org/methodology/"
                "materials-methodology/aqueous-stability-pourbaix"
            ),
        },
        "materials_project_phases": [
            {**item.as_dict(), "stable_on_grid": item.phase_id in stable_ids}
            for item in official.phases
        ],
        "changed_phase_pairs": changed_pairs,
        "reviewed_phase_matches": list(
            database.materials_project_comparisons(official.symbol)
        ),
        "comparison_definition": (
            "Domains are equivalent when solid O/M and H/M composition matches, "
            "or when aqueous proton/electron coefficients and metal molecularity match."
        ),
        "image_png_base64": base64.b64encode(output.getvalue()).decode("ascii"),
        "credential_handling": (
            "The API key was used for this request and was not stored or returned."
        ),
    }
