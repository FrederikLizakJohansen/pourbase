"""Application state independent of Qt: settings, scenarios and cached results."""

from __future__ import annotations

import threading
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, fields, replace
from typing import Any

from ..database import ThermodynamicDatabase
from ..models import GibbsEnergyPolicy, LigandActivity
from ..overview import PeriodicScreen, screen_periodic_table
from ..scenario import Calculation, Mode, Scenario, calculate
from ..sweeps import ConcentrationSweep, ConcentrationSweepEngine
from ..temperature import at_temperature

MODES = {Mode.FIXED_ACTIVITY.value: "Fixed activity", Mode.MASS_BALANCE.value: "Mass balance (closed total metal)"}
CONCENTRATION_UNITS = {
    "log10_molar": "log₁₀ (mol/L)",
    "molar": "mol/L",
    "ppm": "ppm (mg/L)",
    "wt_percent": "wt %",
}
LIGAND_MODES = {"free": "Free activity (log₁₀ a)", "total": "Unbound pool (mol/L)"}
MAX_GRID_POINTS = 801


@dataclass
class LigandSetting:
    """One buffered ligand reservoir as entered in the GUI."""

    enabled: bool = False
    mode: str = "free"
    log10_free_activity: float = -2.0
    total_unbound_mol_L: float = 0.01
    use_pKa: bool = False
    acid_pKa: float = 7.0

    def activity(self, ligand_id: str) -> LigandActivity:
        if self.mode == "free":
            return LigandActivity(ligand_id, log10_free_activity=self.log10_free_activity)
        return LigandActivity(
            ligand_id, total_unbound_mol_L=self.total_unbound_mol_L,
            acid_pKa=self.acid_pKa if self.use_pKa else None,
        )


@dataclass
class Settings:
    """Everything the user sets for one system; it builds the library :class:`Scenario`."""

    symbol: str = "Fe"
    mode: str = Mode.FIXED_ACTIVITY.value
    concentration: float = -6.0
    concentration_unit: str = "log10_molar"
    solution_density_kg_L: float = 1.0
    davies: bool = False
    ionic_strength_mol_L: float = 0.01
    log10_gas_fugacity: float = 0.0
    allow_incomplete: bool = True
    use_mp_fallbacks: bool = False
    temperature_C: float = 25.0
    pH_min: float = 0.0
    pH_max: float = 14.0
    eh_min_V: float = -1.5
    eh_max_V: float = 1.5
    pH_points: int = 281
    eh_points: int = 301
    probe_pH: float = 7.0
    probe_eh_V: float = 0.0
    ligands: dict[str, LigandSetting] = field(default_factory=dict)
    use_ligands: bool = True

    @property
    def energy_policy(self) -> GibbsEnergyPolicy:
        return GibbsEnergyPolicy.EXPERIMENTAL_THEN_MP if self.use_mp_fallbacks else GibbsEnergyPolicy.EXPERIMENTAL_ONLY

    def ligand_activities(self) -> tuple[LigandActivity, ...]:
        if not self.use_ligands:
            return ()
        return tuple(setting.activity(key) for key, setting in sorted(self.ligands.items()) if setting.enabled)

    def scenario(self) -> Scenario:
        mass_balance = self.mode == Mode.MASS_BALANCE.value
        return Scenario(
            self.symbol, mode=self.mode, concentration=self.concentration,
            concentration_unit=self.concentration_unit, solution_density_kg_L=self.solution_density_kg_L,
            davies_ionic_strength_mol_L=self.ionic_strength_mol_L if mass_balance and self.davies else None,
            log10_gas_fugacity=self.log10_gas_fugacity, ligands=self.ligand_activities(),
            pH_min=self.pH_min, pH_max=self.pH_max, eh_min_V=self.eh_min_V, eh_max_V=self.eh_max_V,
            pH_points=self.pH_points, eh_points=self.eh_points,
            allow_incomplete=self.allow_incomplete, energy_policy=self.energy_policy,
            temperature_K=round(self.temperature_C + 273.15, 6),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> Settings:
        """Restore saved settings; unknown keys are ignored and invalid values reset."""
        known = {item.name for item in fields(cls)}
        ligand_keys = {item.name for item in fields(LigandSetting)}
        values = {key: value for key, value in values.items() if key in known}
        values["ligands"] = {
            str(key): LigandSetting(**{name: item[name] for name in ligand_keys & item.keys()})
            for key, item in dict(values.get("ligands") or {}).items() if isinstance(item, dict)
        }
        try:
            settings = cls(**values)
            settings.scenario().conditions()
        except (TypeError, ValueError):
            return cls()
        return settings

    def scenario_code(self) -> str:
        """The ``pb.Scenario(...)`` expression of these settings."""
        scenario = self.scenario()
        defaults = Scenario(scenario.symbol)
        arguments = [repr(scenario.symbol)]
        for item in fields(Scenario):
            value = getattr(scenario, item.name)
            if item.name in ("symbol", "ligands") or value == getattr(defaults, item.name):
                continue
            arguments.append(f"{item.name}={getattr(value, 'value', value)!r}")
        if scenario.ligands:
            ligands = ", ".join(
                "pb.LigandActivity(" + ", ".join(
                    [repr(ligand.ligand_id)]
                    + [f"{name}={getattr(ligand, name)!r}"
                       for name in ("log10_free_activity", "total_unbound_mol_L", "acid_pKa")
                       if getattr(ligand, name) is not None]
                ) + ")"
                for ligand in scenario.ligands
            )
            arguments.append(f"ligands=({ligands},)")
        return f"pb.Scenario({', '.join(arguments)})"

    def python_code(self) -> str:
        """The equivalent library call with the bundled data and the default policy."""
        return "\n".join((
            "import pourbase as pb",
            "",
            f"calculation = pb.calculate({self.scenario_code()})",
            "pb.plot_diagram(calculation.diagram)",
        ))


def database_code(dataset_path: str | None = None, policy_path: str | None = None,
                  user_species_path: str | None = None) -> list[str]:
    """Lines that open the data the application calculates with."""
    lines = ["import pourbase as pb", ""]
    lines.append(f"database = pb.open_dataset({dataset_path!r})" if dataset_path else "database = pb.open_database()")
    if policy_path:
        lines.append(f"database = pb.with_policy(database, {policy_path!r})")
    if user_species_path:
        lines.append(f"database = pb.with_user_species(database, {user_species_path!r})")
    return lines


def python_code(settings: Settings, display, *, dataset_path: str | None = None, policy_path: str | None = None,
                user_species_path: str | None = None, plot: bool = True) -> str:
    """Python code that reproduces the diagram on screen: data, policy, own species, scenario and view."""
    lines = database_code(dataset_path, policy_path, user_species_path)
    lines.append(f"calculation = pb.calculate({settings.scenario_code()}, database)")
    if not plot:
        return "\n".join(lines)
    if settings.mode == Mode.MASS_BALANCE.value:
        lines.append("figure, axes = pb.plot_mass_balance_summary(calculation.diagram)")
    elif display.boltzmann:
        lines.append(f"ax = pb.plot_boltzmann_diagram(pb.boltzmann_smooth(calculation.diagram, "
                     f"{display.blend_width_kJ_mol * 1000:g}))")
    else:
        lines.append("ax = pb.plot_diagram(calculation.diagram)")
    if display.uncertainty and settings.mode != Mode.MASS_BALANCE.value:
        lines.append(f"pb.plot_uncertainty(calculation.diagram, ax=ax, confidence_sigma={display.uncertainty_sigma:g}, "
                     f"assumed_uncertainty_kJ_mol={display.assumed_uncertainty_kJ_mol:g})")
    if display.potential_scale != "SHE":
        lines.append(f"# The application shows potentials against {display.potential_scale}; "
                     "pourbase calculates against SHE.")
    return "\n".join(lines)


@dataclass(frozen=True)
class SweepSettings:
    """Sweep range and the number of slices along each axis of the (log a, pH, Eh) volume."""

    log10_min: float = -10.0
    log10_max: float = 0.0
    levels: int = 21
    pH_points: int = 141
    eh_points: int = 151

    def scenario(self, settings: Settings) -> Scenario:
        """The fixed-activity scenario swept: the diagram settings on the sweep grid."""
        return replace(
            settings.scenario(), mode=Mode.FIXED_ACTIVITY, davies_ionic_strength_mol_L=None,
            pH_points=self.pH_points, eh_points=self.eh_points,
        )


class Session:
    """The database and recently calculated results, shared by the pages and workers."""

    CACHE_SIZE = {"calculation": 16, "sweep": 6, "screen": 32}

    def __init__(self, database: ThermodynamicDatabase | None = None) -> None:
        self.database = database or ThermodynamicDatabase.bundled()
        self._caches: dict[str, OrderedDict] = {name: OrderedDict() for name in self.CACHE_SIZE}
        self._lock = threading.Lock()

    def _cached(self, kind: str, key: Any, build: Callable[[], Any]) -> Any:
        cache = self._caches[kind]
        with self._lock:
            if key in cache:
                cache.move_to_end(key)
                return cache[key]
        value = build()
        with self._lock:
            cache[key] = value
            while len(cache) > self.CACHE_SIZE[kind]:
                cache.popitem(last=False)
        return value

    def cached(self, kind: str, key: Any) -> Any:
        with self._lock:
            return self._caches[kind].get(key)

    def calculate(self, scenario: Scenario) -> Calculation:
        return self._cached("calculation", scenario, lambda: calculate(scenario, self.database))

    def sweep(
        self, scenario: Scenario, settings: SweepSettings, progress: Callable[[float], bool] | None = None
    ) -> ConcentrationSweep:
        def build() -> ConcentrationSweep:
            return ConcentrationSweepEngine(at_temperature(self.database, scenario.temperature_K)).calculate(
                scenario.symbol, scenario.conditions(), settings.log10_min, settings.log10_max,
                settings.levels, allow_incomplete=scenario.allow_incomplete,
                energy_policy=scenario.energy_policy, progress=progress,
            )
        return self._cached("sweep", (scenario, settings), build)

    def screen(self, **arguments: Any) -> PeriodicScreen:
        key = tuple(sorted(arguments.items()))
        return self._cached("screen", key, lambda: screen_periodic_table(self.database, **arguments))

