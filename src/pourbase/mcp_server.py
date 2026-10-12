"""A Model Context Protocol server that gives language-model agents the database and the engine.

    pourbase-mcp [--dataset PATH] [--species CSV] [--policy TOML]

The server speaks MCP over standard input and output, so any MCP client (Claude Code, Claude
Desktop, and other agent frameworks) can start it as a subprocess. Every tool returns JSON-ready
data with record IDs, sources and evidence statuses, so an agent can cite what it reports. The
tools are plain functions of :class:`Tools` and can be called without MCP; the server needs the
optional ``mcp`` dependency (``pip install pourbase[mcp]``).
"""

from __future__ import annotations

import argparse
import dataclasses
import io
import math
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

from .database import ThermodynamicDatabase
from .models import LigandActivity
from .scenario import Mode, Scenario, calculate
from .selection import SelectionPolicy, compare_policies, with_policy
from .uncertainty import stability_margin, stability_uncertainty
from .user_data import open_dataset, with_user_species

INSTRUCTIONS = """\
pourbase holds standard Gibbs energies of formation at 298.15 K and 1 bar for aqueous species,
solids, liquids and gases of the elements, each with its source, locator, evidence status and
uncertainty, and calculates Pourbaix diagrams from them. Start with list_systems, inspect species
with get_species and get_record, and calculate with calculate_diagram, probe_point or
render_diagram. Energies are in kJ/mol, potentials in V vs SHE. Cite the source of every value
you report; values with status 'estimate' or 'user_supplied' are not experimental."""


def _plain(value: Any) -> Any:
    """Dataclasses, enums, tuples and NumPy scalars as JSON-ready values."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {field.name: _plain(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _kJ(value: float | None) -> float | None:
    return None if value is None else round(value / 1000.0, 4)


class Tools:
    """The operations the server offers, on one database."""

    def __init__(self, database: ThermodynamicDatabase | None = None) -> None:
        self.database = database or ThermodynamicDatabase.bundled()

    # ---- database -----------------------------------------------------------------------------

    def list_systems(self) -> dict[str, Any]:
        """The elemental systems with data, the dataset version and the reference state."""
        reference = self.database.reference_state
        return {
            "dataset_version": self.database.data_version,
            "selection_policy": self.database.metadata.get("selection_policy"),
            "reference_state": {"temperature_K": reference.temperature_K, "pressure_bar": reference.pressure_bar,
                                "water_gibbs_energy_kJ_mol": _kJ(reference.water_gibbs_energy_J_mol)},
            "systems": [{"symbol": symbol, "name": name} for symbol, name in self.database.available_systems()],
        }

    def list_ligands(self) -> list[dict[str, Any]]:
        """Ligands that can be buffered in a calculation, with the species they form per element."""
        formed = self.database.ligand_species
        return [{"ligand_id": item.ligand_id, "name": item.name, "formula": item.formula_ascii,
                 "charge": item.charge, "gibbs_energy_kJ_mol": _kJ(item.gibbs_energy_J_mol),
                 "source": item.source_citation,
                 "forms": {symbol: list(by_ligand[item.ligand_id]) for symbol, by_ligand in formed.items()
                           if item.ligand_id in by_ligand}}
                for item in self.database.available_ligands()]

    def get_species(self, symbol: str, include_ligand_species: bool = False) -> list[dict[str, Any]]:
        """Every species of one element with its recommended Gibbs energy, status and source."""
        ligands = [item.ligand_id for item in self.database.available_ligands()] if include_ligand_species else []
        system = self.database.load_system(symbol, ligand_ids=ligands)
        rows = []
        for item in system.species:
            source = self.database.source(item.source_id)
            rows.append({"record_id": item.record_id, "species": item.species, "formula": item.formula_ascii,
                         "phase": item.phase, "charge": item.charge, "ligand_id": item.ligand_id,
                         "gibbs_energy_kJ_mol": _kJ(item.gibbs_energy_J_mol),
                         "uncertainty_kJ_mol": _kJ(item.gibbs_uncertainty_J_mol),
                         "status": item.gibbs_status.value,
                         "source": source.citation if source else item.source_id})
        for item in system.excluded:
            rows.append({"record_id": item.record_id, "species": item.species, "gibbs_energy_kJ_mol": None,
                         "excluded": item.reason.value})
        return rows

    def get_record(self, record_id: str) -> dict[str, Any]:
        """The full evidence record of one species: every reported value, sources, locators, warnings."""
        records = self.database.species_records([record_id])
        if not records:
            raise ValueError(f"No species with record ID {record_id!r}")
        return _plain(records[0])

    def search_species(self, text: str, limit: int = 25) -> list[dict[str, Any]]:
        """Species whose name, formula or record ID contains ``text``."""
        pattern = f"%{text.strip()}%"
        rows = self.database._rows(
            "SELECT record_id, symbol, species, formula_ascii, phase, charge FROM species "
            "WHERE species LIKE ? OR formula_ascii LIKE ? OR record_id LIKE ? ORDER BY symbol, record_id LIMIT ?",
            (pattern, pattern, pattern, int(limit)))
        return [dict(row) for row in rows]

    # ---- calculations -------------------------------------------------------------------------

    def _scenario(self, symbol: str, mode: str, concentration: float, concentration_unit: str,
                  ligands: list[dict[str, Any]] | None, ionic_strength_mol_L: float | None,
                  pH_min: float, pH_max: float, eh_min_V: float, eh_max_V: float,
                  allow_incomplete: bool) -> Scenario:
        return Scenario(
            symbol, mode=Mode(mode), concentration=concentration, concentration_unit=concentration_unit,
            davies_ionic_strength_mol_L=ionic_strength_mol_L,
            ligands=tuple(LigandActivity(**item) for item in (ligands or ())),
            pH_min=pH_min, pH_max=pH_max, eh_min_V=eh_min_V, eh_max_V=eh_max_V,
            allow_incomplete=allow_incomplete,
        )

    def calculate_diagram(self, symbol: str, mode: str = "fixed_activity", concentration: float = -6.0,
                          concentration_unit: str = "log10_molar", ligands: list[dict[str, Any]] | None = None,
                          ionic_strength_mol_L: float | None = None, pH_min: float = 0.0, pH_max: float = 14.0,
                          eh_min_V: float = -1.5, eh_max_V: float = 1.5,
                          allow_incomplete: bool = True) -> dict[str, Any]:
        """Stable species with their share of the diagram, boundary equations, and excluded species.

        ``mode`` is fixed_activity or mass_balance; ``concentration`` is read in
        ``concentration_unit`` (log10_molar, molar, ppm or wt_percent); each ligand is
        {"ligand_id", and "log10_free_activity" or "total_unbound_mol_L" with optional "acid_pKa"}.
        """
        calculation = calculate(self._scenario(symbol, mode, concentration, concentration_unit, ligands,
                                               ionic_strength_mol_L, pH_min, pH_max, eh_min_V, eh_max_V,
                                               allow_incomplete), self.database)
        result = calculation.as_dict()
        diagram = calculation.diagram
        index = diagram.stable_species_index
        shares = {diagram.system.species[int(i)].record_id: float((index == i).mean()) for i in np.unique(index)}
        for item in result["stable_species"]:
            item["share_of_diagram"] = round(shares.get(item["record_id"], 0.0), 4)
        if not calculation.is_mass_balance:
            hatched = stability_uncertainty(diagram).uncertain
            result["share_within_1_sigma_of_another_species"] = round(float(hatched.mean()), 4)
        return _plain(result)

    def probe_point(self, symbol: str, pH: float, eh_V: float, mode: str = "fixed_activity",
                    concentration: float = -6.0, concentration_unit: str = "log10_molar",
                    ligands: list[dict[str, Any]] | None = None, ionic_strength_mol_L: float | None = None,
                    allow_incomplete: bool = True) -> dict[str, Any]:
        """The stable species at one pH and potential, its margin to the runner-up and the nearest boundaries."""
        calculation = calculate(self._scenario(symbol, mode, concentration, concentration_unit, ligands,
                                               ionic_strength_mol_L, 0.0, 14.0, -1.5, 1.5, allow_incomplete),
                                self.database)
        probe = calculation.probe(pH, eh_V)
        source = self.database.source(probe.species.source_id)
        result: dict[str, Any] = {
            "pH": pH, "eh_V": eh_V, "record_id": probe.species.record_id, "species": probe.species.species,
            "phase": probe.species.phase, "gibbs_energy_kJ_mol": _kJ(probe.species.gibbs_energy_J_mol),
            "status": _plain(probe.species.gibbs_status), "source": source.citation if source else None,
            "dissolved_metal_mol_L": probe.dissolved_metal_mol_L,
            "precipitated_fraction": probe.precipitated_fraction, "speciation": _plain(probe.speciation),
        }
        if not calculation.is_mass_balance:
            margin = stability_margin(calculation.diagram, pH, eh_V)
            result.update({
                "runner_up": margin.runner_up.species if margin.runner_up else None,
                "margin_kJ_mol_metal": _kJ(margin.margin_J_mol_metal),
                "margin_uncertainty_kJ_mol_metal": _kJ(margin.margin_uncertainty_J_mol_metal),
                "next_boundary_up": {"species": margin.higher_potential.species.species,
                                     "distance_V": margin.higher_potential.distance}
                if margin.higher_potential else None,
                "next_boundary_down": {"species": margin.lower_potential.species.species,
                                       "distance_V": margin.lower_potential.distance}
                if margin.lower_potential else None,
            })
        return _plain(result)

    def render_diagram(self, symbol: str, mode: str = "fixed_activity", concentration: float = -6.0,
                       concentration_unit: str = "log10_molar", ligands: list[dict[str, Any]] | None = None,
                       ionic_strength_mol_L: float | None = None, allow_incomplete: bool = True) -> bytes:
        """The diagram as a PNG image."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from .export import diagram_figure

        calculation = calculate(self._scenario(symbol, mode, concentration, concentration_unit, ligands,
                                               ionic_strength_mol_L, 0.0, 14.0, -1.5, 1.5, allow_incomplete),
                                self.database)
        figure = diagram_figure(calculation.diagram)
        buffer = io.BytesIO()
        figure.savefig(buffer, format="png", dpi=110, bbox_inches="tight")
        plt.close(figure)
        return buffer.getvalue()

    def compare_policy(self, policy_toml: str, symbol: str | None = None) -> list[dict[str, Any]]:
        """Every recommended Gibbs energy that a selection policy (TOML text) chooses differently from the default."""
        policy = SelectionPolicy.from_toml(policy_toml)
        changes = compare_policies(self.database, SelectionPolicy.default(), policy, ("gibbs_energy_of_formation",))
        symbols = {row["record_id"]: row["symbol"] for row in self.database._rows("SELECT record_id, symbol FROM species")}
        rows = []
        for change in changes:
            if symbol and symbols.get(change.record_id, "").lower() != symbol.strip().lower():
                continue
            rows.append({"record_id": change.record_id,
                         "default_kJ_mol": _kJ(change.first.value), "default_source": change.first.citation,
                         "policy_kJ_mol": _kJ(change.second.value), "policy_source": change.second.citation,
                         "basis": change.second_basis})
        return rows


def build_server(tools: Tools):
    """A FastMCP server exposing ``tools``."""
    from mcp.server.fastmcp import FastMCP, Image

    server = FastMCP("pourbase", instructions=INSTRUCTIONS)
    for name in ("list_systems", "list_ligands", "get_species", "get_record", "search_species",
                 "calculate_diagram", "probe_point", "compare_policy"):
        server.add_tool(getattr(tools, name), name=name)

    def render_diagram(symbol: str, mode: str = "fixed_activity", concentration: float = -6.0,
                       concentration_unit: str = "log10_molar", ligands: list[dict[str, Any]] | None = None,
                       ionic_strength_mol_L: float | None = None, allow_incomplete: bool = True):
        """The diagram as a PNG image."""
        return Image(data=tools.render_diagram(symbol, mode, concentration, concentration_unit, ligands,
                                               ionic_strength_mol_L, allow_incomplete), format="png")

    server.add_tool(render_diagram, name="render_diagram")
    return server


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Model Context Protocol server for pourbase")
    parser.add_argument("--dataset", type=Path, help="a pourbase SQLite file or a species CSV used on its own")
    parser.add_argument("--species", type=Path, help="a CSV of species added to, or replacing, the data")
    parser.add_argument("--policy", type=Path, help="a selection policy (TOML)")
    args = parser.parse_args(argv)
    database: Any = open_dataset(args.dataset) if args.dataset else ThermodynamicDatabase.bundled()
    if args.policy:
        database = with_policy(database, args.policy)
    if args.species:
        database = with_user_species(database, args.species)
    try:
        server = build_server(Tools(database))
    except ImportError as error:
        raise SystemExit("The MCP server needs the mcp package: pip install 'pourbase[mcp]'") from error
    server.run()


if __name__ == "__main__":
    main()
