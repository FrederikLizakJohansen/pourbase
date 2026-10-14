"""One complete calculation request and its result."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from typing import Any

from .temperature import at_temperature
from .activity_coefficients import DaviesActivityCoefficientModel, IdealActivityCoefficientModel
from .conversions import ConcentrationConversion, convert_concentration
from .database import ThermodynamicDatabase
from .engine import PourbaixDiagram, PourbaixEngine
from .equilibria import BoundaryEquation, PlatingPotential, boundary_equations, plating_potentials
from .mass_balance import MassBalancedPourbaixDiagram, MassBalanceEngine
from .models import (
    AqueousActivityModel,
    EvidenceStatus,
    GasFugacityModel,
    GibbsEnergyPolicy,
    LigandActivity,
    LigandActivityModel,
    PourbaixConditions,
    SpeciesExclusion,
    ThermodynamicSpecies,
    TotalMetalConcentration,
)
from .speciation import speciation_at


class Mode(str, Enum):
    FIXED_ACTIVITY = "fixed_activity"
    MASS_BALANCE = "mass_balance"


@dataclass(frozen=True)
class Scenario:
    """Everything that defines one diagram, in user-facing units.

    ``concentration`` is read in ``concentration_unit`` (log10_molar, molar, ppm or
    wt_percent). In fixed-activity mode it sets the activity of every aqueous metal
    species; in mass-balance mode it sets the conserved total metal.
    ``davies_ionic_strength_mol_L`` selects Davies activity coefficients in mass-balance
    mode; None means ideal. ``activity_overrides`` maps species record IDs, names or
    formulas to their own log10 activity in fixed-activity mode. Species without a recommended
    Gibbs energy are left out and listed in ``Calculation.excluded``; ``allow_incomplete=False``
    raises :class:`IncompleteSystemError` instead. ``temperature_K`` between 273.15 and 373.15 K
    extrapolates every Gibbs energy with its entropy of formation (see :mod:`pourbase.temperature`).
    """

    symbol: str
    mode: Mode = Mode.FIXED_ACTIVITY
    concentration: float = -6.0
    concentration_unit: str = "log10_molar"
    solution_density_kg_L: float = 1.0
    davies_ionic_strength_mol_L: float | None = None
    log10_gas_fugacity: float = 0.0
    ligands: tuple[LigandActivity, ...] = ()
    pH_min: float = 0.0
    pH_max: float = 14.0
    eh_min_V: float = -1.5
    eh_max_V: float = 1.5
    pH_points: int = 281
    eh_points: int = 301
    allow_incomplete: bool = True
    energy_policy: GibbsEnergyPolicy = GibbsEnergyPolicy.EXPERIMENTAL_ONLY
    activity_overrides: tuple[tuple[str, float], ...] = ()
    temperature_K: float = 298.15

    def __post_init__(self) -> None:
        overrides = self.activity_overrides
        if isinstance(overrides, Mapping):
            overrides = overrides.items()
        object.__setattr__(self, "activity_overrides", tuple(sorted((str(k), float(v)) for k, v in overrides)))
        object.__setattr__(self, "mode", Mode(self.mode))
        object.__setattr__(self, "energy_policy", GibbsEnergyPolicy(self.energy_policy))
        object.__setattr__(self, "ligands", tuple(self.ligands))

    @property
    def concentration_conversion(self) -> ConcentrationConversion:
        return convert_concentration(
            self.symbol, self.concentration, self.concentration_unit,
            solution_density_kg_L=self.solution_density_kg_L,
        )

    def conditions(self, log10_activity: float | None = None) -> PourbaixConditions:
        """Calculation conditions; ``log10_activity`` replaces the converted concentration."""
        if log10_activity is None:
            log10_activity = self.concentration_conversion.log10_standard_activity
        return PourbaixConditions(
            pH_min=self.pH_min, pH_max=self.pH_max, eh_min_V=self.eh_min_V, eh_max_V=self.eh_max_V,
            pH_points=self.pH_points, eh_points=self.eh_points, temperature_K=self.temperature_K,
            aqueous_activities=AqueousActivityModel(log10_activity, dict(self.activity_overrides)),
            gas_fugacities=GasFugacityModel(self.log10_gas_fugacity),
            ligand_activities=LigandActivityModel(self.ligands) if self.ligands else None,
        )


@dataclass(frozen=True)
class Probe:
    """The result at one grid point."""

    pH: float
    eh_V: float
    species: ThermodynamicSpecies
    dissolved_metal_mol_L: float | None = None
    precipitated_fraction: float | None = None
    speciation: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True)
class Calculation:
    """A calculated scenario: its diagram and the evidence derived from it."""

    scenario: Scenario
    concentration: ConcentrationConversion
    diagram: PourbaixDiagram | MassBalancedPourbaixDiagram
    database: ThermodynamicDatabase = field(repr=False, compare=False)

    @property
    def is_mass_balance(self) -> bool:
        return self.scenario.mode is Mode.MASS_BALANCE

    @property
    def stable_species(self) -> tuple[ThermodynamicSpecies, ...]:
        return self.diagram.stable_species

    @property
    def excluded(self) -> tuple[SpeciesExclusion, ...]:
        return self.diagram.system.excluded

    @property
    def fallback_species(self) -> tuple[ThermodynamicSpecies, ...]:
        return tuple(
            item for item in self.diagram.system.species
            if item.gibbs_status is EvidenceStatus.MATERIALS_PROJECT_FALLBACK
        )

    @cached_property
    def boundaries(self) -> tuple[BoundaryEquation, ...]:
        """Boundary equations; empty for mass balance, where boundaries are numerical."""
        return () if self.is_mass_balance else boundary_equations(self.diagram, self.database)

    @cached_property
    def plating(self) -> tuple[PlatingPotential, ...]:
        return () if self.is_mass_balance else plating_potentials(self.diagram, self.database)

    def probe(self, pH: float, eh_V: float) -> Probe:
        species = self.diagram.species_at(pH, eh_V)
        if not self.is_mass_balance:
            return Probe(pH, eh_V, species)
        state = self.diagram.state_at(pH, eh_V)
        return Probe(
            pH, eh_V, species, state.dissolved_metal_mol_L, state.precipitated_fraction,
            speciation_at(self.diagram, pH, eh_V),
        )

    def as_dict(self) -> dict[str, Any]:
        """A JSON-serializable summary."""
        return {
            "symbol": self.diagram.system.symbol,
            "system": self.diagram.system.system,
            "mode": self.scenario.mode.value,
            "energy_policy": self.scenario.energy_policy.value,
            "concentration": self.concentration.as_dict(),
            "conditions": self.diagram.conditions.as_dict(),
            "stable_species": [
                {"record_id": item.record_id, "species": item.species, "phase": item.phase,
                 "gibbs_status": item.gibbs_status.value, "source_id": item.source_id}
                for item in self.stable_species
            ],
            "excluded_species": [
                {"record_id": item.record_id, "species": item.species, "reason": item.reason.value}
                for item in self.excluded
            ],
            "boundaries": [item.as_dict() for item in self.boundaries],
            "plating_potentials": [item.as_dict() for item in self.plating],
        }


def calculate(scenario: Scenario, database: ThermodynamicDatabase | None = None) -> Calculation:
    """Calculate a scenario with the bundled database unless another is given."""
    database = at_temperature(database or ThermodynamicDatabase.bundled(), scenario.temperature_K)
    concentration = scenario.concentration_conversion
    conditions = scenario.conditions(concentration.log10_standard_activity)
    if scenario.mode is Mode.MASS_BALANCE:
        coefficients = (
            DaviesActivityCoefficientModel(scenario.davies_ionic_strength_mol_L)
            if scenario.davies_ionic_strength_mol_L is not None
            else IdealActivityCoefficientModel()
        )
        diagram = MassBalanceEngine(database, coefficients).calculate(
            scenario.symbol, conditions, TotalMetalConcentration(concentration.molar_concentration),
            allow_incomplete=scenario.allow_incomplete, energy_policy=scenario.energy_policy,
        )
    else:
        diagram = PourbaixEngine(database).calculate(
            scenario.symbol, conditions,
            allow_incomplete=scenario.allow_incomplete, energy_policy=scenario.energy_policy,
        )
    return Calculation(scenario, concentration, diagram, database)
