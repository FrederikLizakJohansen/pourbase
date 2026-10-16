"""Typed evidence records read from the database for display and export."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class SourceReference:
    source_id: str
    citation: str | None
    url: str | None
    locator: str | None


@dataclass(frozen=True, slots=True)
class PropertyValue:
    """One recommended property with its status, uncertainty and source."""

    value: float | None
    status: str | None
    uncertainty: float | None
    source: SourceReference | None


@dataclass(frozen=True, slots=True)
class Thermochemistry:
    temperature_K: float
    pressure_bar: float
    gibbs_energy_J_mol: PropertyValue
    entropy_J_mol_K: PropertyValue
    formation_enthalpy_J_mol: PropertyValue


@dataclass(frozen=True, slots=True)
class ReportedValue:
    """A value reported or retained from a source, recommended or not."""

    value_id: str
    property: str
    value: float | None
    unit: str
    status: str
    selected_as_recommended: bool
    uncertainty: float | None
    source: SourceReference | None
    supersedes_value_id: str | None
    temperature_K: float | None = None
    pressure_bar: float | None = None


@dataclass(frozen=True, slots=True)
class ComputationalFallback:
    """A labelled Materials Project estimate for a missing experimental Gibbs energy."""

    requested_mp_id: str
    canonical_mp_id: str
    formula: str
    spacegroup_symbol: str | None
    spacegroup_number: str | None
    selection_basis: str
    mapping_confidence: str
    temperature_K: float
    gibbs_energy_eV_atom: float
    gibbs_energy_J_mol: float
    model: str
    database_version: str
    source_url: str
    notes: str | None


@dataclass(frozen=True, slots=True)
class PhaseIdentity:
    status: str
    identified_phase: str | None
    spacegroup_symbol: str | None
    spacegroup_number: str | None
    possible_phases: str | None
    evidence_summary: str | None
    source_url: str | None
    notes: str | None


@dataclass(frozen=True, slots=True)
class RecordWarning:
    type: str
    message: str
    source: SourceReference | None


@dataclass(frozen=True, slots=True)
class SpeciesRecord:
    """Everything the database holds about one species."""

    record_id: str
    system: str
    symbol: str
    species: str
    formula_ascii: str
    phase: str
    phase_detail: str
    charge: float
    metal_oxidation_state: float | None
    thermochemistry: Thermochemistry
    reported: tuple[ReportedValue, ...]
    fallback: ComputationalFallback | None
    phase_identity: PhaseIdentity | None
    warnings: tuple[RecordWarning, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)
