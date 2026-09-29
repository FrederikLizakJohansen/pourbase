"""Fixed-activity single-metal Pourbaix calculations."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from .constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10, REFERENCE_STATE_ABSOLUTE_TOLERANCE
from .database import ThermodynamicDatabase
from .exceptions import UnsupportedConditionError
from .grid import grid_axes, nearest_index, readonly, water_lines
from .models import (
    GibbsEnergyPolicy,
    MetalSystem,
    PourbaixConditions,
    ReferenceState,
    ThermodynamicSpecies,
)

FloatArray = npt.NDArray[np.float64]
IntegerArray = npt.NDArray[np.integer]


@dataclass(frozen=True, slots=True)
class PourbaixDiagram:
    """Stable species on a pH/Eh grid.

    ``transformed_gibbs_J_mol_metal`` holds the energy of every species at every grid
    point and ``minimum_transformed_gibbs_J_mol_metal`` the lowest one; both are None
    for diagrams calculated with ``store_energies=False``.
    """

    system: MetalSystem
    conditions: PourbaixConditions
    pH: FloatArray
    eh_V: FloatArray
    stable_species_index: IntegerArray
    her_V: FloatArray
    oer_V: FloatArray
    minimum_transformed_gibbs_J_mol_metal: FloatArray | None = None
    transformed_gibbs_J_mol_metal: FloatArray | None = None

    def __post_init__(self) -> None:
        shape = (self.eh_V.size, self.pH.size)
        if self.stable_species_index.shape != shape:
            raise ValueError("stable_species_index shape does not match the calculation axes")
        if self.minimum_transformed_gibbs_J_mol_metal is not None and (
            self.minimum_transformed_gibbs_J_mol_metal.shape != shape
        ):
            raise ValueError("minimum Gibbs grid shape does not match the calculation axes")
        if self.transformed_gibbs_J_mol_metal is not None and (
            self.transformed_gibbs_J_mol_metal.shape != (len(self.system.species), *shape)
        ):
            raise ValueError("transformed Gibbs stack shape does not match the species and axes")

    @property
    def stable_species(self) -> tuple[ThermodynamicSpecies, ...]:
        return tuple(self.system.species[int(index)] for index in np.unique(self.stable_species_index))

    @property
    def aqueous_activity_assignments(self) -> tuple[tuple[str, str, float], ...]:
        """``(record_id, species, log10 activity)`` of every aqueous species."""
        model = self.conditions.aqueous_activities
        return tuple(
            (item.record_id, item.species, model.log10_activity_for(item.record_id, item.species, item.formula_ascii))
            for item in self.system.species if item.is_aqueous
        )

    @property
    def gas_fugacity_assignments(self) -> tuple[tuple[str, str, float], ...]:
        """``(record_id, species, log10(f / 1 bar))`` of every gas species."""
        model = self.conditions.gas_fugacities
        return tuple(
            (item.record_id, item.species, model.log10_fugacity_for(item.record_id, item.species, item.formula_ascii))
            for item in self.system.species if item.is_gas
        )

    def species_at(self, pH: float, eh_V: float) -> ThermodynamicSpecies:
        """The stable species at the grid point nearest to a coordinate."""
        row = nearest_index(self.eh_V, eh_V, "eh_V")
        column = nearest_index(self.pH, pH, "pH")
        return self.system.species[int(self.stable_species_index[row, column])]


def validate_reference_conditions(conditions: PourbaixConditions, reference: ReferenceState) -> None:
    """The data describe one temperature and pressure; reject extrapolation."""
    for value, expected, name, unit in (
        (conditions.temperature_K, reference.temperature_K, "Temperature", "K"),
        (conditions.pressure_bar, reference.pressure_bar, "Pressure", "bar"),
    ):
        if not math.isclose(value, expected, rel_tol=0.0, abs_tol=REFERENCE_STATE_ABSOLUTE_TOLERANCE):
            raise UnsupportedConditionError(f"{name} extrapolation is unavailable; use {expected:g} {unit}")


def standard_transformed_gibbs_J_mol_metal(
    species: ThermodynamicSpecies,
    reference: ReferenceState,
    conditions: PourbaixConditions,
    pH: npt.ArrayLike,
    eh_V: npt.ArrayLike,
) -> FloatArray:
    """Transformed Gibbs energy per mole of metal at unit activity of the species."""
    pH_grid, eh_grid = np.broadcast_arrays(np.asarray(pH, dtype=np.float64), np.asarray(eh_V, dtype=np.float64))
    rt_ln_10 = GAS_CONSTANT_J_MOL_K * conditions.temperature_K * LN_10
    baseline = (
        species.gibbs_energy_J_mol - species.core_oxygen_count * reference.water_gibbs_energy_J_mol
    ) / species.metal_count
    if not species.is_ligand_free:
        ligands = conditions.ligand_activities
        if ligands is None or species.ligand_id not in ligands.ligand_ids:
            raise UnsupportedConditionError(
                f"Ligand species {species.record_id} requires an activity for {species.ligand_id}"
            )
        assert species.ligand_gibbs_energy_J_mol is not None
        ligand_potential = species.ligand_gibbs_energy_J_mol + rt_ln_10 * ligands.assignment_for(
            species.ligand_id
        ).log10_activity(pH_grid)
        baseline = baseline - species.ligand_count / species.metal_count * ligand_potential
    return (
        baseline
        - species.protons_per_metal * rt_ln_10 * pH_grid
        - species.electrons_per_metal * FARADAY_C_MOL * eh_grid
    )


def transformed_gibbs_J_mol_metal(
    species: ThermodynamicSpecies,
    reference: ReferenceState,
    conditions: PourbaixConditions,
    pH: npt.ArrayLike,
    eh_V: npt.ArrayLike,
) -> FloatArray:
    """Transformed Gibbs energy per mole of metal at the configured activity or fugacity."""
    energy = standard_transformed_gibbs_J_mol_metal(species, reference, conditions, pH, eh_V)
    identifiers = (species.record_id, species.species, species.formula_ascii)
    if species.is_gas:
        log10_activity = conditions.gas_fugacities.log10_fugacity_for(*identifiers)
    elif species.is_aqueous:
        log10_activity = conditions.aqueous_activities.log10_activity_for(*identifiers)
    else:
        return np.asarray(energy, dtype=np.float64)
    rt_ln_10 = GAS_CONSTANT_J_MOL_K * conditions.temperature_K * LN_10
    return np.asarray(energy + rt_ln_10 * log10_activity / species.metal_count, dtype=np.float64)


class PourbaixEngine:
    """Fixed-activity diagrams at the database reference state."""

    transformed_gibbs_J_mol_metal = staticmethod(transformed_gibbs_J_mol_metal)
    standard_transformed_gibbs_J_mol_metal = staticmethod(standard_transformed_gibbs_J_mol_metal)

    def __init__(self, database: ThermodynamicDatabase) -> None:
        self.database = database

    def calculate(
        self,
        symbol: str,
        conditions: PourbaixConditions,
        *,
        allow_incomplete: bool = False,
        energy_policy: GibbsEnergyPolicy | str = GibbsEnergyPolicy.EXPERIMENTAL_ONLY,
        store_energies: bool = True,
    ) -> PourbaixDiagram:
        """Calculate a diagram; complete data are required unless ``allow_incomplete``."""
        ligand_ids = conditions.ligand_activities.ligand_ids if conditions.ligand_activities else ()
        system = self.database.load_system(symbol, ligand_ids=ligand_ids, energy_policy=energy_policy)
        return self.calculate_system(
            system, conditions, allow_incomplete=allow_incomplete, store_energies=store_energies
        )

    def calculate_system(
        self,
        system: MetalSystem,
        conditions: PourbaixConditions,
        *,
        allow_incomplete: bool = False,
        store_energies: bool = True,
    ) -> PourbaixDiagram:
        """Calculate a previously loaded or transformed system."""
        reference = self.database.reference_state
        validate_reference_conditions(conditions, reference)
        if not allow_incomplete:
            system.require_complete()
        pH, eh_V = grid_axes(conditions)
        pH_grid, eh_grid = np.meshgrid(pH, eh_V)
        energies = np.stack([
            transformed_gibbs_J_mol_metal(species, reference, conditions, pH_grid, eh_grid)
            for species in system.species
        ])
        stable = np.argmin(energies, axis=0)
        her_V, oer_V = water_lines(pH, conditions.temperature_K, reference.water_gibbs_energy_J_mol)
        if not store_energies:
            dtype = np.int16 if len(system.species) < 2**15 else np.intp
            return PourbaixDiagram(system, conditions, pH, eh_V, readonly(stable, dtype), her_V, oer_V)
        minimum = np.take_along_axis(energies, stable[np.newaxis], axis=0)[0]
        return PourbaixDiagram(
            system, conditions, pH, eh_V, readonly(stable), her_V, oer_V,
            minimum_transformed_gibbs_J_mol_metal=readonly(minimum),
            transformed_gibbs_J_mol_metal=readonly(energies),
        )
