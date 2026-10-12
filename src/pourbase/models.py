"""Immutable domain objects for thermodynamic data and calculation inputs."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

import numpy as np
import numpy.typing as npt

from .exceptions import IncompleteSystemError


class GibbsEnergyPolicy(str, Enum):
    """Choose which evidence layer may supply a calculation Gibbs energy."""

    EXPERIMENTAL_ONLY = "experimental_only"
    EXPERIMENTAL_THEN_MP = "experimental_then_mp"


class EvidenceStatus(str, Enum):
    """Evidence behind a Gibbs energy record."""

    VERIFIED = "verified"
    SOURCE_VERIFIED_ESTIMATE = "source_verified_estimate"
    DEFINED_REFERENCE_STATE = "defined_reference_state"
    NOT_AVAILABLE = "not_available"
    TERMINAL_EVIDENCE_GAP = "terminal_evidence_gap"
    MATERIALS_PROJECT_FALLBACK = "materials_project_sisso_300K_fallback"
    USER_SUPPLIED = "user_supplied"


class ExclusionReason(str, Enum):
    """Why a database record is left out of a calculation."""

    GIBBS_ENERGY_UNAVAILABLE = "recommended_gibbs_energy_unavailable"
    LIGAND_NOT_SELECTED = "ligand_species_not_selected"
    LIGAND_REFERENCE_UNAVAILABLE = "ligand_reference_unavailable"
    POLYNUCLEAR_AQUEOUS = "mass_balance_nonmonometal_aqueous_unsupported"


@dataclass(frozen=True, slots=True)
class ReferenceState:
    """Reference conditions and water Gibbs energy used by a dataset release."""

    temperature_K: float
    pressure_bar: float
    water_gibbs_energy_J_mol: float

    def __post_init__(self) -> None:
        for name, value in (
            ("temperature_K", self.temperature_K),
            ("pressure_bar", self.pressure_bar),
            ("water_gibbs_energy_J_mol", self.water_gibbs_energy_J_mol),
        ):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.temperature_K <= 0:
            raise ValueError("temperature_K must be positive")
        if self.pressure_bar <= 0:
            raise ValueError("pressure_bar must be positive")


@dataclass(frozen=True, slots=True)
class LigandReference:
    """One free-ligand standard state used by ligand-aware calculations."""

    ligand_id: str
    name: str
    formula_ascii: str
    charge: float
    gibbs_energy_J_mol: float
    source_id: str
    source_citation: str
    source_url: str
    value_status: str

    def __post_init__(self) -> None:
        for name, value in (
            ("ligand_id", self.ligand_id),
            ("name", self.name),
            ("formula_ascii", self.formula_ascii),
            ("source_id", self.source_id),
            ("source_citation", self.source_citation),
            ("source_url", self.source_url),
            ("value_status", self.value_status),
        ):
            if not value:
                raise ValueError(f"{name} must not be empty")
        if not math.isfinite(self.charge) or not math.isfinite(
            self.gibbs_energy_J_mol
        ):
            raise ValueError("ligand charge and Gibbs energy must be finite")


@dataclass(frozen=True, slots=True)
class LigandActivity:
    """A buffered free-ligand activity or monoprotic acid/base reservoir.

    ``log10_free_activity`` fixes the activity of the deprotonated ligand directly.
    ``total_unbound_mol_L`` describes an unbound pool ``HL + L``. Supplying
    ``acid_pKa`` then calculates the deprotonated fraction at each pH. Omitting the
    pKa treats the pool as fully dissociated.
    """

    ligand_id: str
    log10_free_activity: float | None = None
    total_unbound_mol_L: float | None = None
    acid_pKa: float | None = None
    standard_concentration_mol_L: float = 1.0

    def __post_init__(self) -> None:
        ligand_id = self.ligand_id.strip()
        if not ligand_id:
            raise ValueError("ligand_id must not be empty")
        object.__setattr__(self, "ligand_id", ligand_id)
        fixed = self.log10_free_activity is not None
        total = self.total_unbound_mol_L is not None
        if fixed == total:
            raise ValueError(
                "supply exactly one of log10_free_activity and total_unbound_mol_L"
            )
        if fixed and not math.isfinite(float(self.log10_free_activity)):
            raise ValueError("log10_free_activity must be finite")
        if total and (
            not math.isfinite(float(self.total_unbound_mol_L))
            or float(self.total_unbound_mol_L) <= 0
        ):
            raise ValueError("total_unbound_mol_L must be positive and finite")
        if self.acid_pKa is not None and not math.isfinite(self.acid_pKa):
            raise ValueError("acid_pKa must be finite when supplied")
        if self.acid_pKa is not None and fixed:
            raise ValueError("acid_pKa applies to a total unbound ligand pool")
        if (
            not math.isfinite(self.standard_concentration_mol_L)
            or self.standard_concentration_mol_L <= 0
        ):
            raise ValueError("standard_concentration_mol_L must be positive and finite")

    def log10_activity(self, pH: npt.ArrayLike) -> np.ndarray:
        """Buffered activity of the deprotonated ligand at each pH.

        A fixed free activity is returned as given. A total unbound pool c_L with an acid pKa
        gives the free (deprotonated) ligand activity

            log10 a_L = log10(c_L / c0) - log10(1 + 10^(pKa - pH)) .                    (11)
        """
        pH_array = np.asarray(pH, dtype=np.float64)
        if self.log10_free_activity is not None:
            return np.full_like(pH_array, self.log10_free_activity)
        assert self.total_unbound_mol_L is not None
        log_total = math.log10(self.total_unbound_mol_L / self.standard_concentration_mol_L)
        if self.acid_pKa is None:
            return np.full_like(pH_array, log_total)
        return log_total - np.logaddexp(0.0, (self.acid_pKa - pH_array) * math.log(10)) / math.log(10)

    def as_dict(self) -> dict[str, object]:
        return {
            "ligand_id": self.ligand_id,
            "mode": (
                "fixed_free_activity"
                if self.log10_free_activity is not None
                else "buffered_total_unbound"
            ),
            "log10_free_activity": self.log10_free_activity,
            "total_unbound_mol_L": self.total_unbound_mol_L,
            "acid_pKa": self.acid_pKa,
            "standard_concentration_mol_L": self.standard_concentration_mol_L,
        }


@dataclass(frozen=True, slots=True)
class LigandActivityModel:
    """Named buffered ligand reservoirs available to a calculation."""

    assignments: tuple[LigandActivity, ...]

    def __post_init__(self) -> None:
        assignments = tuple(self.assignments)
        if not assignments:
            raise ValueError("at least one ligand assignment is required")
        if any(not isinstance(item, LigandActivity) for item in assignments):
            raise TypeError("assignments must contain LigandActivity objects")
        ids = [item.ligand_id for item in assignments]
        if len(ids) != len(set(ids)):
            raise ValueError("ligand assignments must have unique ligand_id values")
        object.__setattr__(self, "assignments", assignments)

    @property
    def ligand_ids(self) -> tuple[str, ...]:
        return tuple(item.ligand_id for item in self.assignments)

    def assignment_for(self, ligand_id: str) -> LigandActivity:
        for item in self.assignments:
            if item.ligand_id == ligand_id:
                return item
        raise KeyError(ligand_id)

    def as_dict(self) -> dict[str, object]:
        return {
            "kind": "buffered_free_ligand_reservoirs",
            "assignments": [item.as_dict() for item in self.assignments],
            "includes_acid_base_speciation": any(
                item.acid_pKa is not None for item in self.assignments
            ),
            "enforces_total_ligand_balance": False,
        }


@dataclass(frozen=True, slots=True)
class ThermodynamicSpecies:
    """One supported thermodynamic species used by the calculation engine."""

    record_id: str
    system: str
    symbol: str
    species: str
    formula_ascii: str
    phase: str
    phase_detail: str
    charge: float
    metal_count: float
    core_oxygen_count: float
    core_hydrogen_count: float
    ligand_id: str | None
    ligand_count: float
    ligand_charge: float
    gibbs_energy_J_mol: float
    gibbs_status: EvidenceStatus
    source_id: str
    ligand_gibbs_energy_J_mol: float | None = None
    formal_metal_oxidation_state: float | None = None
    electron_coefficient_per_metal: float | None = None
    gibbs_uncertainty_J_mol: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "gibbs_status", EvidenceStatus(self.gibbs_status))
        required_text = {
            "record_id": self.record_id,
            "system": self.system,
            "symbol": self.symbol,
            "species": self.species,
            "formula_ascii": self.formula_ascii,
            "phase": self.phase,
            "gibbs_status": self.gibbs_status,
            "source_id": self.source_id,
        }
        for name, value in required_text.items():
            if not value:
                raise ValueError(f"{name} must not be empty")
        for name, value in (
            ("charge", self.charge),
            ("metal_count", self.metal_count),
            ("core_oxygen_count", self.core_oxygen_count),
            ("core_hydrogen_count", self.core_hydrogen_count),
            ("ligand_count", self.ligand_count),
            ("ligand_charge", self.ligand_charge),
            ("gibbs_energy_J_mol", self.gibbs_energy_J_mol),
        ):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.phase not in {"aqueous", "solid", "liquid", "gas"}:
            raise ValueError(f"Unsupported phase {self.phase!r}")
        if self.metal_count <= 0:
            raise ValueError("metal_count must be positive")
        if self.core_oxygen_count < 0 or self.core_hydrogen_count < 0:
            raise ValueError("core atom counts must be non-negative")
        if self.ligand_count < 0:
            raise ValueError("ligand_count must be non-negative")
        if self.ligand_count and not self.ligand_id:
            raise ValueError("ligand_id is required when ligand_count is non-zero")
        if self.ligand_count and self.ligand_gibbs_energy_J_mol is None:
            raise ValueError(
                "ligand_gibbs_energy_J_mol is required when ligand_count is non-zero"
            )
        if self.ligand_gibbs_energy_J_mol is not None and not math.isfinite(
            self.ligand_gibbs_energy_J_mol
        ):
            raise ValueError("ligand_gibbs_energy_J_mol must be finite when supplied")
        for name, value in (
            ("formal_metal_oxidation_state", self.formal_metal_oxidation_state),
            ("electron_coefficient_per_metal", self.electron_coefficient_per_metal),
        ):
            if value is not None and not math.isfinite(value):
                raise ValueError(f"{name} must be finite when supplied")

    @property
    def is_aqueous(self) -> bool:
        return self.phase == "aqueous"

    @property
    def is_gas(self) -> bool:
        return self.phase == "gas"

    @property
    def is_condensed(self) -> bool:
        """Return whether the species has unit activity as a pure condensed phase."""
        return self.phase in {"solid", "liquid"}

    @property
    def is_ligand_free(self) -> bool:
        return self.ligand_count == 0

    @property
    def metal_oxidation_state(self) -> float:
        """Average formal metal oxidation state."""
        if self.formal_metal_oxidation_state is not None:
            return self.formal_metal_oxidation_state
        return self.electrons_per_metal

    @property
    def electrons_per_metal(self) -> float:
        """Electron coefficient in the metal/water formation reaction."""
        if self.electron_coefficient_per_metal is not None:
            return self.electron_coefficient_per_metal
        return (
            self.charge
            - self.ligand_count * self.ligand_charge
            + 2 * self.core_oxygen_count
            - self.core_hydrogen_count
        ) / self.metal_count

    @property
    def protons_per_metal(self) -> float:
        return (
            2 * self.core_oxygen_count - self.core_hydrogen_count
        ) / self.metal_count


@dataclass(frozen=True, slots=True)
class SpeciesExclusion:
    """A database record omitted from a calculation and the explicit reason."""

    record_id: str
    species: str
    reason: ExclusionReason
    status: str


@dataclass(frozen=True, slots=True)
class MetalSystem:
    """Supported and excluded records for one elemental system."""

    system: str
    symbol: str
    species: tuple[ThermodynamicSpecies, ...]
    excluded: tuple[SpeciesExclusion, ...] = ()

    def __post_init__(self) -> None:
        if not self.system or not self.symbol:
            raise ValueError("system and symbol must not be empty")
        if not self.species:
            raise ValueError(f"No supported species are available for {self.symbol}")
        if any(item.symbol != self.symbol for item in self.species):
            raise ValueError("All species must belong to the same element symbol")
        record_ids = [item.record_id for item in self.species]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("Species record IDs must be unique")

    @property
    def missing_gibbs(self) -> tuple[SpeciesExclusion, ...]:
        """Ligand-free records without a Gibbs energy for this calculation."""
        return tuple(
            item for item in self.excluded if item.reason is ExclusionReason.GIBBS_ENERGY_UNAVAILABLE
        )

    @property
    def is_thermochemically_complete(self) -> bool:
        return not self.missing_gibbs

    def require_complete(self) -> None:
        """Raise :class:`IncompleteSystemError` when a Gibbs energy is missing."""
        if missing := self.missing_gibbs:
            raise IncompleteSystemError(
                f"{self.symbol} has {len(missing)} species without a recommended Gibbs "
                f"energy: {', '.join(item.record_id for item in missing)}"
            )


@dataclass(frozen=True, slots=True)
class AqueousActivityModel:
    """Ideal aqueous activities with an optional override for named species.

    Override selectors are matched in the order supplied by a calculation backend.
    The experimental engine uses record ID, display name, and ASCII formula. The MP
    adapter uses entry ID, entry name, and reduced formula.
    """

    default_log10_activity: float = -6.0
    overrides: Mapping[str, float] = field(default_factory=dict, hash=False)

    def __post_init__(self) -> None:
        if not math.isfinite(self.default_log10_activity):
            raise ValueError("default_log10_activity must be finite")
        if not isinstance(self.overrides, Mapping):
            raise TypeError("overrides must be a mapping of selector to log10 activity")
        normalized: dict[str, float] = {}
        for raw_selector, raw_value in self.overrides.items():
            if not isinstance(raw_selector, str):
                raise TypeError("aqueous activity override selectors must be strings")
            selector = raw_selector.strip()
            if not selector:
                raise ValueError("aqueous activity override selectors must not be empty")
            if selector in normalized:
                raise ValueError(f"duplicate aqueous activity selector {selector!r}")
            value = float(raw_value)
            if not math.isfinite(value):
                raise ValueError(
                    f"aqueous activity override for {selector!r} must be finite"
                )
            normalized[selector] = value
        object.__setattr__(
            self,
            "overrides",
            MappingProxyType(dict(sorted(normalized.items()))),
        )

    def log10_activity_for(self, *identifiers: str | None) -> float:
        """Resolve the first matching identifier or return the global default."""
        for identifier in identifiers:
            if identifier is None:
                continue
            normalized = str(identifier).strip()
            if normalized in self.overrides:
                return self.overrides[normalized]
        return self.default_log10_activity

    def activity_for(self, *identifiers: str | None) -> float:
        """Return the resolved dimensionless activity in linear form."""
        log10_activity = self.log10_activity_for(*identifiers)
        try:
            activity = 10.0**log10_activity
        except OverflowError as error:
            raise ValueError("resolved aqueous activity is outside floating-point range") from error
        if not math.isfinite(activity) or activity <= 0:
            raise ValueError("resolved aqueous activity is outside floating-point range")
        return activity

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable description of the model."""
        return {
            "kind": "ideal_species_activities",
            "default_log10_activity": self.default_log10_activity,
            "overrides": dict(self.overrides),
            "is_total_concentration": False,
        }


@dataclass(frozen=True, slots=True)
class GasFugacityModel:
    """Ideal-gas fugacities relative to the 1 bar standard state.

    Values are supplied as log10(f / 1 bar). Selectors use the same record ID,
    display-name, and formula lookup order as aqueous activity overrides.
    """

    default_log10_fugacity: float = 0.0
    overrides: Mapping[str, float] = field(default_factory=dict, hash=False)

    def __post_init__(self) -> None:
        if not math.isfinite(self.default_log10_fugacity):
            raise ValueError("default_log10_fugacity must be finite")
        if not isinstance(self.overrides, Mapping):
            raise TypeError("gas fugacity overrides must be a mapping")
        normalized: dict[str, float] = {}
        for raw_selector, raw_value in self.overrides.items():
            if not isinstance(raw_selector, str) or not raw_selector.strip():
                raise ValueError("gas fugacity override selectors must be non-empty strings")
            value = float(raw_value)
            if not math.isfinite(value):
                raise ValueError(
                    f"gas fugacity override for {raw_selector!r} must be finite"
                )
            normalized[raw_selector.strip()] = value
        object.__setattr__(
            self, "overrides", MappingProxyType(dict(sorted(normalized.items())))
        )

    def log10_fugacity_for(self, *identifiers: str | None) -> float:
        for identifier in identifiers:
            if identifier is not None and str(identifier).strip() in self.overrides:
                return self.overrides[str(identifier).strip()]
        return self.default_log10_fugacity

    def as_dict(self) -> dict[str, object]:
        return {
            "kind": "ideal_gas_fugacities",
            "standard_fugacity_bar": 1.0,
            "default_log10_fugacity": self.default_log10_fugacity,
            "overrides": dict(self.overrides),
        }


@dataclass(frozen=True, slots=True)
class TotalMetalConcentration:
    """Closed-system metal inventory for a mass-balance calculation.

    The total is expressed as moles of the selected metal per litre of solution and
    includes dissolved metal plus metal assigned to precipitated phases.
    """

    total_metal_mol_L: float
    standard_concentration_mol_L: float = 1.0

    def __post_init__(self) -> None:
        for name, value in (
            ("total_metal_mol_L", self.total_metal_mol_L),
            ("standard_concentration_mol_L", self.standard_concentration_mol_L),
        ):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite")

    @property
    def dimensionless_total(self) -> float:
        """Return total metal concentration relative to its standard state."""
        return self.total_metal_mol_L / self.standard_concentration_mol_L

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable description of the model."""
        return {
            "kind": "closed_metal_inventory",
            "total_metal_mol_L": self.total_metal_mol_L,
            "standard_concentration_mol_L": self.standard_concentration_mol_L,
            "includes_precipitated_metal": True,
            "enforces_charge_balance": False,
        }


@dataclass(frozen=True, slots=True)
class PourbaixConditions:
    """Validated grid and activity conditions of one calculation."""

    temperature_K: float = 298.15
    pressure_bar: float = 1.0
    pH_min: float = 0.0
    pH_max: float = 14.0
    eh_min_V: float = -1.5
    eh_max_V: float = 1.5
    pH_points: int = 281
    eh_points: int = 301
    aqueous_activities: AqueousActivityModel = field(default_factory=AqueousActivityModel)
    gas_fugacities: GasFugacityModel = field(default_factory=GasFugacityModel)
    ligand_activities: LigandActivityModel | None = None

    def __post_init__(self) -> None:
        for name, kind in (
            ("aqueous_activities", AqueousActivityModel),
            ("gas_fugacities", GasFugacityModel),
        ):
            if not isinstance(getattr(self, name), kind):
                raise TypeError(f"{name} must be a {kind.__name__}")
        if self.ligand_activities is not None and not isinstance(
            self.ligand_activities, LigandActivityModel
        ):
            raise TypeError("ligand_activities must be a LigandActivityModel")
        for name in ("temperature_K", "pressure_bar", "pH_min", "pH_max", "eh_min_V", "eh_max_V"):
            if not math.isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be finite")
        if self.temperature_K <= 0 or self.pressure_bar <= 0:
            raise ValueError("temperature and pressure must be positive")
        if self.pH_min >= self.pH_max:
            raise ValueError("pH_min must be smaller than pH_max")
        if self.eh_min_V >= self.eh_max_V:
            raise ValueError("eh_min_V must be smaller than eh_max_V")
        if self.pH_points < 2 or self.eh_points < 2:
            raise ValueError("each grid axis must contain at least two points")

    def as_dict(self) -> dict[str, object]:
        """The calculation conditions as serializable metadata."""
        return {
            "temperature_K": self.temperature_K,
            "pressure_bar": self.pressure_bar,
            "pH_range": [self.pH_min, self.pH_max, self.pH_points],
            "eh_V_range": [self.eh_min_V, self.eh_max_V, self.eh_points],
            "aqueous_activity_model": self.aqueous_activities.as_dict(),
            "gas_fugacity_model": self.gas_fugacities.as_dict(),
            "ligand_activity_model": (
                self.ligand_activities.as_dict() if self.ligand_activities is not None else None
            ),
        }
