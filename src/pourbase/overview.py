"""The stable species of every element at one pH and potential."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum

from .database import ThermodynamicDatabase
from .models import ExclusionReason
from .engine import transformed_gibbs_J_mol_metal, validate_reference_conditions
from .grid import nernst_slope_V
from .models import (
    AqueousActivityModel,
    EvidenceStatus,
    GasFugacityModel,
    GibbsEnergyPolicy,
    PourbaixConditions,
    ThermodynamicSpecies, LigandActivity, LigandActivityModel,
)
from .conversions import convert_concentration
from .records import RecordWarning, SourceReference


class ElementStatus(str, Enum):
    CALCULATED = "calculated"
    CALCULATED_WITH_GAPS = "calculated_with_gaps"
    CALCULATED_WITH_FALLBACK = "calculated_with_fallback"
    INCOMPLETE = "incomplete"
    REFERENCE_COMPONENT = "reference_component"
    DEFERRED_NOBLE_GAS = "deferred_noble_gas"
    RESTRICTED_RADIOACTIVE = "restricted_radioactive"
    OUTSIDE_CURRENT_SCOPE = "outside_current_scope"

    @property
    def is_calculated(self) -> bool:
        return self in (self.CALCULATED, self.CALCULATED_WITH_GAPS, self.CALCULATED_WITH_FALLBACK)

    @property
    def is_provisional(self) -> bool:
        """Calculated with species left out or with Materials Project estimates."""
        return self in (self.CALCULATED_WITH_GAPS, self.CALCULATED_WITH_FALLBACK)

    @property
    def has_system(self) -> bool:
        """The element has species in the database, calculated here or not."""
        return self.is_calculated or self is self.INCOMPLETE


class Category(str, Enum):
    DISSOLVED_OR_GAS = "dissolved_or_gas"
    SOLID_OXIDE = "solid_oxide"
    HYDROXIDE = "hydroxide_or_oxyhydroxide"
    ELEMENTAL_SOLID = "elemental_solid"
    ELEMENTAL_LIQUID = "elemental_liquid"
    OTHER_SOLID = "other_solid"
    INCOMPLETE = "incomplete"
    REFERENCE_COMPONENT = "reference_component"
    DEFERRED_NOBLE_GAS = "deferred_noble_gas"
    RESTRICTED_RADIOACTIVE = "restricted_radioactive"
    OUTSIDE_CURRENT_SCOPE = "outside_current_scope"

    @property
    def label(self) -> str:
        return CATEGORY_LABELS[self]

    @classmethod
    def of(cls, species: ThermodynamicSpecies) -> Category:
        if species.phase in ("aqueous", "gas"):
            return cls.DISSOLVED_OR_GAS
        if species.phase == "liquid":
            return cls.ELEMENTAL_LIQUID
        if not species.is_ligand_free:
            return cls.OTHER_SOLID
        if species.core_oxygen_count and not species.core_hydrogen_count:
            return cls.SOLID_OXIDE
        if species.core_oxygen_count:
            return cls.HYDROXIDE
        return cls.OTHER_SOLID if species.core_hydrogen_count else cls.ELEMENTAL_SOLID


CATEGORY_LABELS = {
    Category.DISSOLVED_OR_GAS: "Dissolved aqueous species or gas",
    Category.SOLID_OXIDE: "Solid oxide",
    Category.HYDROXIDE: "Solid hydroxide or oxyhydroxide",
    Category.ELEMENTAL_SOLID: "Elemental solid",
    Category.ELEMENTAL_LIQUID: "Elemental liquid",
    Category.OTHER_SOLID: "Other solid compound",
    Category.INCOMPLETE: "Calculation withheld because Gibbs data are incomplete",
    Category.REFERENCE_COMPONENT: "Reference component",
    Category.DEFERRED_NOBLE_GAS: "Noble gas outside practical aqueous scope",
    Category.RESTRICTED_RADIOACTIVE: "Deferred for radiological evidence review",
    Category.OUTSIDE_CURRENT_SCOPE: "Not yet curated",
}


@dataclass(frozen=True)
class ElementResult:
    atomic_number: int
    symbol: str
    system: str | None
    status: ElementStatus
    category: Category
    reason: str | None = None
    stable: ThermodynamicSpecies | None = None
    energy_margin_J_mol_metal: float | None = None
    missing_record_ids: tuple[str, ...] = ()
    gibbs_source: SourceReference | None = None
    structure_label: str | None = None
    warnings: tuple[RecordWarning, ...] = ()


@dataclass(frozen=True)
class PeriodicScreen:
    pH: float
    input_potential_V: float
    reference: str
    potential_V_vs_SHE: float
    concentration: float
    concentration_unit: str
    elements: tuple[ElementResult, ...]

    @property
    def category_counts(self) -> Counter:
        return Counter(item.category for item in self.elements)

    @property
    def supported_count(self) -> int:
        return sum(item.status.has_system for item in self.elements)

    @property
    def calculated_count(self) -> int:
        return sum(item.status.is_calculated for item in self.elements)

    def element(self, symbol: str) -> ElementResult:
        return next(item for item in self.elements if item.symbol == symbol)


def screen_periodic_table(
    database: ThermodynamicDatabase | None = None,
    *,
    pH: float = 7.0,
    potential_V: float = 0.0,
    reference: str = "SHE",
    concentration: float = -6.0,
    concentration_unit: str = "log10_molar",
    solution_density_kg_L: float = 1.0,
    log10_gas_fugacity: float = 0.0,
    allow_incomplete: bool = True,
    energy_policy: GibbsEnergyPolicy | str = GibbsEnergyPolicy.EXPERIMENTAL_ONLY,
    ligands: tuple[LigandActivity, ...] = (),
    temperature_K: float = 298.15,
) -> PeriodicScreen:
    """The lowest-energy species of every element at one pH and potential.

    ``ligands`` are buffered ligand reservoirs; their complexes take part for every element that
    forms them. Species without a recommended Gibbs energy are left out unless
    ``allow_incomplete`` is False, which marks such elements as incomplete instead. ``temperature_K``
    extrapolates the Gibbs energies as in :mod:`pourbase.temperature`.
    """
    from .temperature import at_temperature

    database = at_temperature(database or ThermodynamicDatabase.bundled(), temperature_K)
    reference = reference.upper()
    if reference not in ("SHE", "RHE"):
        raise ValueError("reference must be SHE or RHE")
    if not -2.0 <= pH <= 16.0:
        raise ValueError("pH must be between -2 and 16")
    state = database.reference_state
    potential_she = potential_V - (nernst_slope_V(state.temperature_K) * pH if reference == "RHE" else 0.0)
    energy_policy = GibbsEnergyPolicy(energy_policy)
    gases = GasFugacityModel(log10_gas_fugacity)
    systems = dict(database.available_systems())
    ligands = tuple(ligands)
    known = {item.ligand_id for item in database.available_ligands()}
    ligand_ids = tuple(item.ligand_id for item in ligands if item.ligand_id in known)
    ligand_model = LigandActivityModel(tuple(item for item in ligands if item.ligand_id in known)) if ligand_ids else None
    calculated: dict[str, tuple] = {}
    for symbol in systems:
        system = database.load_system(symbol, ligand_ids=ligand_ids, energy_policy=energy_policy)
        missing = tuple(item.record_id for item in system.missing_gibbs)
        if missing and not allow_incomplete:
            calculated[symbol] = (ElementStatus.INCOMPLETE, None, None, missing)
            continue
        conditions = PourbaixConditions(
            temperature_K=state.temperature_K, pressure_bar=state.pressure_bar,
            aqueous_activities=AqueousActivityModel(convert_concentration(
                symbol, concentration, concentration_unit, solution_density_kg_L=solution_density_kg_L,
            ).log10_standard_activity),
            gas_fugacities=gases,
            ligand_activities=ligand_model,
        )
        validate_reference_conditions(conditions, state)
        energies = sorted(
            (float(transformed_gibbs_J_mol_metal(item, state, conditions, pH, potential_she)), index)
            for index, item in enumerate(system.species)
        )
        if any(item.gibbs_status is EvidenceStatus.MATERIALS_PROJECT_FALLBACK for item in system.species):
            status = ElementStatus.CALCULATED_WITH_FALLBACK
        else:
            without_entropy = any(item.reason is ExclusionReason.TEMPERATURE_DATA_UNAVAILABLE
                                  for item in system.excluded)
            status = (ElementStatus.CALCULATED_WITH_GAPS if missing or without_entropy
                      else ElementStatus.CALCULATED)
        margin = energies[1][0] - energies[0][0] if len(energies) > 1 else None
        calculated[symbol] = (status, system.species[energies[0][1]], margin, missing)

    records = {
        item.record_id: item
        for item in database.species_records(
            entry[1].record_id for entry in calculated.values() if entry[1] is not None
        )
    }
    elements = []
    for coverage in database.element_coverage():
        symbol = str(coverage["symbol"])
        if symbol not in calculated:
            status = ElementStatus(coverage["coverage_status"])
            elements.append(ElementResult(
                int(coverage["atomic_number"]), symbol, None, status, Category(status.value),
                reason=coverage["reason"],
            ))
            continue
        status, stable, margin, missing = calculated[symbol]
        if stable is None:
            elements.append(ElementResult(
                int(coverage["atomic_number"]), symbol, systems[symbol], status, Category.INCOMPLETE,
                reason=coverage["reason"], missing_record_ids=missing,
            ))
            continue
        record = records[stable.record_id]
        if stable.gibbs_status is EvidenceStatus.MATERIALS_PROJECT_FALLBACK and record.fallback:
            source = SourceReference(
                stable.source_id, record.fallback.model, record.fallback.source_url,
                f"{record.fallback.temperature_K:g} K SISSO estimate",
            )
        else:
            source = record.thermochemistry.gibbs_energy_J_mol.source
        identity = record.phase_identity
        if identity and identity.identified_phase:
            structure = identity.identified_phase
        elif identity and identity.possible_phases:
            structure = f"possible: {identity.possible_phases}"
        else:
            structure = stable.phase_detail if stable.phase_detail.lower() not in ("", "solid") else None
        elements.append(ElementResult(
            int(coverage["atomic_number"]), symbol, systems[symbol], status, Category.of(stable),
            reason=coverage["reason"], stable=stable, energy_margin_J_mol_metal=margin,
            missing_record_ids=missing, gibbs_source=source, structure_label=structure,
            warnings=record.warnings,
        ))
    return PeriodicScreen(
        pH, potential_V, reference, potential_she, concentration, concentration_unit, tuple(elements),
    )
