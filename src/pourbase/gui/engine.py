"""Computation layer of the desktop GUI, independent of Qt.

:class:`Parameters` holds every user setting and converts it into the request mapping read by
:func:`pourbase.service.calculate`. :class:`Engine` caches the most recent results so that
changes to display settings reuse the calculated grid.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import closing
from dataclasses import asdict, dataclass, field, fields, replace
from typing import Any, Callable

import numpy as np

from ..database import ThermodynamicDatabase
from ..service import calculate, calculate_periodic_table
from ..speciation import speciation_at
from ..engine import PourbaixEngine
from ..models import AqueousActivityModel
from ..sweeps import ConcentrationSweep

MODES = {
    "fixed_activity": "Fixed activity",
    "mass_balance": "Mass balance (closed total metal)",
}
CONCENTRATION_UNITS = {
    "log10_molar": "log₁₀ (mol/L)",
    "molar": "mol/L",
    "ppm": "ppm (mg/L)",
    "wt_percent": "wt %",
}
RESOLUTIONS = {
    "Preview": (141, 151),
    "Standard": (281, 301),
    "High": (561, 601),
}

# Settings that change the calculated grid; the remaining settings only affect the display
CALCULATION_FIELDS = (
    "symbol", "mode", "concentration_value", "concentration_unit", "solution_density_kg_L",
    "davies", "ionic_strength_mol_L", "log10_gas_fugacity", "allow_incomplete",
    "use_mp_fallbacks", "pH_min", "pH_max", "eh_min_V", "eh_max_V", "resolution", "ligands",
)
LIGAND_MODES = {
    "free": "Free activity (log₁₀ a)",
    "total": "Unbound pool (mol/L)",
}


@dataclass
class LigandSetting:
    """One buffered ligand reservoir as entered in the GUI."""

    enabled: bool = False
    mode: str = "free"
    log10_free_activity: float = -2.0
    total_unbound_mol_L: float = 0.01
    use_pKa: bool = False
    acid_pKa: float = 7.0

    def to_payload(self, ligand_id: str) -> dict[str, Any]:
        if self.mode == "free":
            return {"ligand_id": ligand_id, "log10_free_activity": self.log10_free_activity}
        return {
            "ligand_id": ligand_id,
            "total_unbound_mol_L": self.total_unbound_mol_L,
            "acid_pKa": self.acid_pKa if self.use_pKa else None,
        }


@dataclass
class Parameters:
    symbol: str = "Fe"
    mode: str = "fixed_activity"
    concentration_value: float = -6.0
    concentration_unit: str = "log10_molar"
    solution_density_kg_L: float = 1.0
    davies: bool = False
    ionic_strength_mol_L: float = 0.01
    log10_gas_fugacity: float = 0.0
    allow_incomplete: bool = False
    use_mp_fallbacks: bool = False
    pH_min: float = 0.0
    pH_max: float = 14.0
    eh_min_V: float = -1.5
    eh_max_V: float = 1.5
    resolution: str = "Standard"
    probe_pH: float = 7.0
    probe_eh_V: float = 0.0
    ligands: dict[str, LigandSetting] = field(default_factory=dict)

    def calculation_key(self) -> tuple:
        values = []
        for name in CALCULATION_FIELDS:
            value = getattr(self, name)
            if name == "ligands":
                value = json.dumps(self.ligand_payload(), sort_keys=True)
            values.append(value)
        return tuple(values)

    def ligand_payload(self) -> list[dict[str, Any]]:
        return [
            setting.to_payload(ligand_id)
            for ligand_id, setting in sorted(self.ligands.items())
            if setting.enabled
        ]

    def to_payload(self) -> dict[str, Any]:
        pH_points, eh_points = RESOLUTIONS[self.resolution]
        payload: dict[str, Any] = {
            "symbol": self.symbol,
            "mode": self.mode,
            "concentration_value": self.concentration_value,
            "concentration_unit": self.concentration_unit,
            "solution_density_kg_L": self.solution_density_kg_L,
            "log10_gas_fugacity": self.log10_gas_fugacity,
            "allow_incomplete": self.allow_incomplete,
            "energy_policy": (
                "experimental_then_mp" if self.use_mp_fallbacks else "experimental_only"
            ),
            "pH_min": self.pH_min,
            "pH_max": self.pH_max,
            "eh_min_V": self.eh_min_V,
            "eh_max_V": self.eh_max_V,
            "pH_points": pH_points,
            "eh_points": eh_points,
            "probe_pH": min(max(self.probe_pH, self.pH_min), self.pH_max),
            "probe_eh_V": min(max(self.probe_eh_V, self.eh_min_V), self.eh_max_V),
            "ligands": self.ligand_payload(),
        }
        if self.mode == "mass_balance":
            payload["activity_coefficient_model"] = "davies" if self.davies else "ideal"
            payload["ionic_strength_mol_L"] = self.ionic_strength_mol_L
        return payload

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> Parameters:
        names = {item.name for item in fields(cls)}
        values = {key: value for key, value in values.items() if key in names}
        ligand_names = {item.name for item in fields(LigandSetting)}
        values["ligands"] = {
            str(ligand_id): LigandSetting(
                **{key: value for key, value in setting.items() if key in ligand_names}
            )
            for ligand_id, setting in dict(values.get("ligands") or {}).items()
            if isinstance(setting, dict)
        }
        parameters = cls(**values)
        if parameters.resolution not in RESOLUTIONS:
            parameters.resolution = "Standard"
        return parameters

    def python_code(self) -> str:
        """Return the equivalent package call for the current settings."""
        policy = (
            "GibbsEnergyPolicy.EXPERIMENTAL_THEN_MP"
            if self.use_mp_fallbacks else "GibbsEnergyPolicy.EXPERIMENTAL_ONLY"
        )
        pH_points, eh_points = RESOLUTIONS[self.resolution]
        lines = [
            "from pourbase import *",
            "",
            "database = ThermodynamicDatabase.bundled()",
            f"level = convert_concentration({self.symbol!r}, {self.concentration_value!r}, "
            f"{self.concentration_unit!r}, solution_density_kg_L={self.solution_density_kg_L!r})",
            "conditions = PourbaixConditions(",
            f"    pH_min={self.pH_min!r}, pH_max={self.pH_max!r}, pH_points={pH_points},",
            f"    eh_min_V={self.eh_min_V!r}, eh_max_V={self.eh_max_V!r}, eh_points={eh_points},",
            "    aqueous_activities=AqueousActivityModel(",
            "        default_log10_activity=level.log10_standard_activity",
            "    ),",
            f"    gas_fugacities=GasFugacityModel(default_log10_fugacity={self.log10_gas_fugacity!r}),",
        ]
        ligands = self.ligand_payload()
        if ligands:
            lines.append("    ligand_activities=LigandActivityModel((")
            for item in ligands:
                arguments = ", ".join(
                    f"{key}={value!r}" for key, value in item.items() if value is not None
                )
                lines.append(f"        LigandActivity({arguments}),")
            lines.append("    )),")
        lines.append(")")
        if self.mode == "mass_balance":
            model = (
                f"DaviesActivityCoefficientModel(ionic_strength_mol_L={self.ionic_strength_mol_L!r})"
                if self.davies else "IdealActivityCoefficientModel()"
            )
            lines += [
                f"diagram = MassBalanceEngine(database, {model}).calculate(",
                f"    {self.symbol!r}, conditions, TotalMetalConcentration(level.molar_concentration),",
            ]
        else:
            lines.append(f"diagram = PourbaixEngine(database).calculate({self.symbol!r}, conditions,")
        lines += [
            f"    allow_incomplete={self.allow_incomplete!r}, energy_policy={policy},",
            ")",
            "plot_diagram(diagram)",
        ]
        return "\n".join(lines)


MAX_SWEEP_POINTS = 101  # log10 activity levels
MAX_SWEEP_GRID_POINTS = 801  # pH or Eh grid points


class SweepCancelled(Exception):
    """Raised when a running sweep is superseded by newer settings."""


@dataclass(frozen=True)
class SweepSettings:
    """Sweep range and the number of slices along each axis of the (log a, pH, Eh) volume."""

    log10_min: float = -10.0
    log10_max: float = 0.0
    points: int = 21
    pH_points: int = 141
    eh_points: int = 151


def compact_diagram(diagram: Any) -> Any:
    """A copy holding only what the sweep views draw: small indices, no Gibbs stack."""
    shape = diagram.stable_species_index.shape
    return replace(
        diagram,
        stable_species_index=diagram.stable_species_index.astype(np.int16),
        minimum_transformed_gibbs_J_mol_metal=np.broadcast_to(np.float64(0.0), shape),
        transformed_gibbs_J_mol_metal=None,
    )


class Engine:
    """Calculates diagrams, sweeps and periodic-table screens, caching recent results."""

    SWEEP_CACHE_SIZE = 8

    def __init__(self, database: ThermodynamicDatabase | None = None) -> None:
        self.database = database or ThermodynamicDatabase.bundled()
        self._key: tuple | None = None
        self._diagram: Any = None
        self._result: dict[str, Any] | None = None
        self._sweeps: dict[tuple, ConcentrationSweep] = {}
        self._sweep_lock = threading.Lock()
        with closing(sqlite3.connect(f"file:{self.database.path}?mode=ro", uri=True)) as connection:
            rows = connection.execute(
                "SELECT symbol, ligand_id, species FROM species WHERE ligand_id IS NOT NULL"
            ).fetchall()
        self.ligand_species: dict[str, dict[str, list[str]]] = {}
        for symbol, ligand_id, species in rows:
            self.ligand_species.setdefault(symbol, {}).setdefault(ligand_id, []).append(species)
        self.ligands = self.database.available_ligands()

    @staticmethod
    def sweep_parameters(parameters: Parameters, settings: SweepSettings) -> Parameters:
        """The fixed-activity parameters of a sweep; the sweep sets its own grid."""
        return Parameters.from_dict(
            {**parameters.to_dict(), "mode": "fixed_activity", "resolution": "Standard"}
        )

    @staticmethod
    def sweep_payload(parameters: Parameters, settings: SweepSettings) -> dict[str, Any]:
        payload = Engine.sweep_parameters(parameters, settings).to_payload()
        payload.update(pH_points=settings.pH_points, eh_points=settings.eh_points)
        return payload

    def sweep_key(self, parameters: Parameters, settings: SweepSettings) -> tuple:
        return (*self.sweep_parameters(parameters, settings).calculation_key(), settings)

    def cached_sweep(self, parameters: Parameters, settings: SweepSettings) -> ConcentrationSweep | None:
        with self._sweep_lock:
            return self._sweeps.get(self.sweep_key(parameters, settings))

    def sweep(
        self,
        parameters: Parameters,
        settings: SweepSettings,
        progress: Callable[[float], bool] | None = None,
    ) -> ConcentrationSweep:
        """Fixed-activity diagrams over a range of aqueous metal activities.

        Levels are calculated one at a time and stored compactly, so a sweep of
        ``MAX_SWEEP_POINTS`` levels stays small. ``progress`` receives the completed fraction;
        returning ``False`` cancels with :class:`SweepCancelled`.
        """
        key = self.sweep_key(parameters, settings)
        cached = self.cached_sweep(parameters, settings)
        if cached is not None:
            return cached
        if not 2 <= settings.points <= MAX_SWEEP_POINTS:
            raise ValueError(f"sweep points must be between 2 and {MAX_SWEEP_POINTS}")
        if settings.log10_min >= settings.log10_max:
            raise ValueError("minimum activity must be smaller than maximum activity")
        for name in ("pH_points", "eh_points"):
            if not 2 <= getattr(settings, name) <= MAX_SWEEP_GRID_POINTS:
                raise ValueError(f"{name} must be between 2 and {MAX_SWEEP_GRID_POINTS}")
        fixed = self.sweep_parameters(parameters, settings)
        payload = self.sweep_payload(parameters, settings)
        base, _ = calculate(payload, self.database)
        engine = PourbaixEngine(self.database)
        levels = np.linspace(settings.log10_min, settings.log10_max, settings.points)
        diagrams = []
        for number, level in enumerate(levels):
            if progress is not None and progress(number / len(levels)) is False:
                raise SweepCancelled()
            conditions = replace(
                base.conditions,
                log10_aqueous_activity=float(level),
                aqueous_activities=AqueousActivityModel(default_log10_activity=float(level)),
            )
            diagrams.append(compact_diagram(engine.calculate(
                fixed.symbol, conditions, allow_incomplete=fixed.allow_incomplete,
                energy_policy=payload["energy_policy"],
            )))
        levels.setflags(write=False)
        sweep = ConcentrationSweep(levels, tuple(diagrams))
        with self._sweep_lock:
            self._sweeps[key] = sweep
            while len(self._sweeps) > self.SWEEP_CACHE_SIZE:
                self._sweeps.pop(next(iter(self._sweeps)))
        return sweep

    def systems(self) -> tuple[tuple[str, str], ...]:
        return self.database.available_systems()

    def compute(self, parameters: Parameters) -> tuple[Any, dict[str, Any]]:
        """Return the diagram and its metadata; recalculates only when the grid changes."""
        key = parameters.calculation_key()
        if key != self._key:
            self._diagram, self._result = calculate(parameters.to_payload(), self.database)
            self._key = key
        assert self._result is not None
        return self._diagram, self._result

    @staticmethod
    def probe(diagram: Any, pH: float, eh_V: float) -> dict[str, Any]:
        """Return the stable species and, for a mass balance, the inventory at one point."""
        species = diagram.species_at(pH, eh_V)
        probe: dict[str, Any] = {"pH": pH, "eh_V": eh_V, "species": species}
        if hasattr(diagram, "state_at"):
            state = diagram.state_at(pH, eh_V)
            probe.update(
                dissolved_metal_mol_L=state.dissolved_metal_mol_L,
                precipitated_fraction=state.precipitated_fraction,
                speciation=speciation_at(diagram, pH, eh_V),
            )
        return probe

    def periodic_table(
        self, parameters: Parameters, pH: float, potential_V: float, reference: str
    ) -> dict[str, Any]:
        return calculate_periodic_table(
            {
                "periodic_pH": pH,
                "periodic_potential_V": potential_V,
                "potential_reference": reference,
                "concentration_value": parameters.concentration_value,
                "concentration_unit": parameters.concentration_unit,
                "solution_density_kg_L": parameters.solution_density_kg_L,
                "allow_incomplete": parameters.allow_incomplete,
                "energy_policy": (
                    "experimental_then_mp"
                    if parameters.use_mp_fallbacks else "experimental_only"
                ),
            },
            self.database,
        )
