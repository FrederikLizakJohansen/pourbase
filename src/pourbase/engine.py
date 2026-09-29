"""Validated single-metal Pourbaix calculation engine."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from .constants import (
    FARADAY_C_MOL,
    GAS_CONSTANT_J_MOL_K,
    LN_10,
    REFERENCE_STATE_ABSOLUTE_TOLERANCE,
)
from .database import ThermodynamicDatabase
from .exceptions import IncompleteSystemError, UnsupportedConditionError
from .models import (
    GibbsEnergyPolicy,
    MetalSystem,
    PourbaixConditions,
    ReferenceState,
    ThermodynamicSpecies,
)


FloatArray = npt.NDArray[np.float64]
IntegerArray = npt.NDArray[np.int_]


@dataclass(frozen=True, slots=True)
class PourbaixDiagram:
    """Numerical result of one equilibrium grid calculation."""

    system: MetalSystem
    conditions: PourbaixConditions
    pH: FloatArray
    eh_V: FloatArray
    stable_species_index: IntegerArray
    minimum_transformed_gibbs_J_mol_metal: FloatArray
    her_V: FloatArray
    oer_V: FloatArray
    transformed_gibbs_J_mol_metal: FloatArray | None = None

    def __post_init__(self) -> None:
        expected_shape = (self.eh_V.size, self.pH.size)
        if self.stable_species_index.shape != expected_shape:
            raise ValueError(
                "stable_species_index shape does not match the calculation axes"
            )
        if self.minimum_transformed_gibbs_J_mol_metal.shape != expected_shape:
            raise ValueError(
                "minimum Gibbs grid shape does not match the calculation axes"
            )
        if self.transformed_gibbs_J_mol_metal is not None:
            expected_stack_shape = (len(self.system.species), *expected_shape)
            if self.transformed_gibbs_J_mol_metal.shape != expected_stack_shape:
                raise ValueError(
                    "transformed Gibbs stack shape does not match the species and axes"
                )

    @property
    def stable_species(self) -> tuple[ThermodynamicSpecies, ...]:
        indices = sorted(int(value) for value in np.unique(self.stable_species_index))
        return tuple(self.system.species[index] for index in indices)

    @property
    def aqueous_activity_assignments(self) -> tuple[tuple[str, str, float], ...]:
        """Return ``(record_id, species, log10 activity)`` for aqueous entries."""
        activity_model = self.conditions.aqueous_activities
        assert activity_model is not None
        return tuple(
            (
                species.record_id,
                species.species,
                activity_model.log10_activity_for(
                    species.record_id,
                    species.species,
                    species.formula_ascii,
                ),
            )
            for species in self.system.species
            if species.is_aqueous
        )

    @property
    def gas_fugacity_assignments(self) -> tuple[tuple[str, str, float], ...]:
        """Return ``(record_id, species, log10(f/1 bar))`` for gas entries."""
        fugacity_model = self.conditions.gas_fugacities
        assert fugacity_model is not None
        return tuple(
            (
                species.record_id,
                species.species,
                fugacity_model.log10_fugacity_for(
                    species.record_id, species.species, species.formula_ascii
                ),
            )
            for species in self.system.species
            if species.is_gas
        )

    def species_at(self, pH: float, eh_V: float) -> ThermodynamicSpecies:
        """Return the grid species nearest to a requested coordinate."""
        if not math.isfinite(pH) or not math.isfinite(eh_V):
            raise ValueError("pH and eh_V must be finite")
        if not self.pH[0] <= pH <= self.pH[-1]:
            raise ValueError("pH lies outside the diagram")
        if not self.eh_V[0] <= eh_V <= self.eh_V[-1]:
            raise ValueError("eh_V lies outside the diagram")
        pH_index = int(np.abs(self.pH - pH).argmin())
        eh_index = int(np.abs(self.eh_V - eh_V).argmin())
        species_index = int(self.stable_species_index[eh_index, pH_index])
        return self.system.species[species_index]


class PourbaixEngine:
    """Compute evidence-aware diagrams at the database reference state."""

    def __init__(self, database: ThermodynamicDatabase) -> None:
        self.database = database

    @staticmethod
    def transformed_gibbs_J_mol_metal(
        species: ThermodynamicSpecies,
        reference_state: ReferenceState,
        conditions: PourbaixConditions,
        pH: npt.ArrayLike,
        eh_V: npt.ArrayLike,
    ) -> FloatArray:
        """Evaluate transformed Gibbs energy with the configured aqueous activity."""
        transformed = PourbaixEngine.standard_transformed_gibbs_J_mol_metal(
            species,
            reference_state,
            conditions,
            pH,
            eh_V,
        )
        if species.is_gas:
            fugacity_model = conditions.gas_fugacities
            assert fugacity_model is not None
            log10_fugacity = fugacity_model.log10_fugacity_for(
                species.record_id,
                species.species,
                species.formula_ascii,
            )
            fugacity_term = (
                GAS_CONSTANT_J_MOL_K
                * conditions.temperature_K
                * LN_10
                * log10_fugacity
                / species.metal_count
            )
            return np.asarray(transformed + fugacity_term, dtype=np.float64)
        if not species.is_aqueous:
            return transformed
        activity_model = conditions.aqueous_activities
        assert activity_model is not None
        log10_activity = activity_model.log10_activity_for(
            species.record_id,
            species.species,
            species.formula_ascii,
        )
        activity_term = (
            GAS_CONSTANT_J_MOL_K
            * conditions.temperature_K
            * LN_10
            * log10_activity
            / species.metal_count
        )
        return np.asarray(transformed + activity_term, dtype=np.float64)

    @staticmethod
    def standard_transformed_gibbs_J_mol_metal(
        species: ThermodynamicSpecies,
        reference_state: ReferenceState,
        conditions: PourbaixConditions,
        pH: npt.ArrayLike,
        eh_V: npt.ArrayLike,
    ) -> FloatArray:
        """Evaluate transformed Gibbs energy at unit metal-species activity."""
        pH_array = np.asarray(pH, dtype=np.float64)
        eh_array = np.asarray(eh_V, dtype=np.float64)
        pH_grid, eh_grid = np.broadcast_arrays(pH_array, eh_array)
        rt_ln_10 = GAS_CONSTANT_J_MOL_K * conditions.temperature_K * LN_10
        baseline = (
            species.gibbs_energy_J_mol / species.metal_count
            - (species.core_oxygen_count / species.metal_count)
            * reference_state.water_gibbs_energy_J_mol
        )
        if not species.is_ligand_free:
            ligand_model = conditions.ligand_activities
            if ligand_model is None or species.ligand_id is None:
                raise UnsupportedConditionError(
                    f"Ligand species {species.record_id} requires a ligand activity model"
                )
            try:
                assignment = ligand_model.assignment_for(species.ligand_id)
            except KeyError as error:
                raise UnsupportedConditionError(
                    f"Ligand species {species.record_id} requires an activity for "
                    f"{species.ligand_id}"
                ) from error
            if assignment.log10_free_activity is not None:
                ligand_log10_activity = np.full_like(
                    pH_grid, assignment.log10_free_activity, dtype=np.float64
                )
            else:
                assert assignment.total_unbound_mol_L is not None
                ligand_log10_activity = np.full_like(
                    pH_grid,
                    math.log10(
                        assignment.total_unbound_mol_L
                        / assignment.standard_concentration_mol_L
                    ),
                    dtype=np.float64,
                )
                if assignment.acid_pKa is not None:
                    exponent = (assignment.acid_pKa - pH_grid) * LN_10
                    ligand_log10_activity -= np.logaddexp(0.0, exponent) / LN_10
            assert species.ligand_gibbs_energy_J_mol is not None
            ligand_chemical_potential = (
                species.ligand_gibbs_energy_J_mol
                + rt_ln_10 * ligand_log10_activity
            )
            baseline = baseline - (
                species.ligand_count
                / species.metal_count
                * ligand_chemical_potential
            )
        return np.asarray(
            baseline
            - species.protons_per_metal * rt_ln_10 * pH_grid
            - species.electrons_per_metal * FARADAY_C_MOL * eh_grid,
            dtype=np.float64,
        )

    def _validate_conditions(
        self, conditions: PourbaixConditions, reference_state: ReferenceState
    ) -> None:
        if not math.isclose(
            conditions.temperature_K,
            reference_state.temperature_K,
            rel_tol=0.0,
            abs_tol=REFERENCE_STATE_ABSOLUTE_TOLERANCE,
        ):
            raise UnsupportedConditionError(
                "Temperature extrapolation is unavailable; use "
                f"{reference_state.temperature_K:g} K"
            )
        if not math.isclose(
            conditions.pressure_bar,
            reference_state.pressure_bar,
            rel_tol=0.0,
            abs_tol=REFERENCE_STATE_ABSOLUTE_TOLERANCE,
        ):
            raise UnsupportedConditionError(
                "Pressure extrapolation is unavailable; use "
                f"{reference_state.pressure_bar:g} bar"
            )

    def calculate(
        self,
        symbol: str,
        conditions: PourbaixConditions,
        *,
        allow_incomplete: bool = False,
        energy_policy: GibbsEnergyPolicy | str = GibbsEnergyPolicy.EXPERIMENTAL_ONLY,
    ) -> PourbaixDiagram:
        """Calculate a diagram, requiring complete ligand-free data by default."""
        ligand_ids = (
            conditions.ligand_activities.ligand_ids
            if conditions.ligand_activities is not None
            else ()
        )
        system = self.database.load_system(
            symbol, ligand_ids=ligand_ids, energy_policy=energy_policy
        )
        return self.calculate_system(
            system,
            conditions,
            allow_incomplete=allow_incomplete,
        )

    def calculate_system(
        self,
        system: MetalSystem,
        conditions: PourbaixConditions,
        *,
        allow_incomplete: bool = False,
    ) -> PourbaixDiagram:
        """Calculate a previously loaded or deliberately transformed system."""
        reference_state = self.database.reference_state
        self._validate_conditions(conditions, reference_state)
        if not allow_incomplete and not system.is_thermochemically_complete:
            missing = [
                item.record_id
                for item in system.excluded
                if item.reason == "recommended_gibbs_energy_unavailable"
            ]
            raise IncompleteSystemError(
                f"{system.symbol} has {len(missing)} ligand-free species without a "
                f"recommended Gibbs energy: {', '.join(missing)}. "
                "Pass allow_incomplete=True for exploratory use."
            )
        pH = np.linspace(conditions.pH_min, conditions.pH_max, conditions.pH_points)
        eh_V = np.linspace(
            conditions.eh_min_V, conditions.eh_max_V, conditions.eh_points
        )
        pH_grid, eh_grid = np.meshgrid(pH, eh_V)
        energy_stack = np.stack(
            [
                self.transformed_gibbs_J_mol_metal(
                    species, reference_state, conditions, pH_grid, eh_grid
                )
                for species in system.species
            ],
            axis=0,
        )
        stable_index = np.argmin(energy_stack, axis=0)
        minimum_gibbs = np.take_along_axis(
            energy_stack, stable_index[np.newaxis, :, :], axis=0
        )[0]
        nernst_slope = (
            GAS_CONSTANT_J_MOL_K * conditions.temperature_K * LN_10 / FARADAY_C_MOL
        )
        her_V = -nernst_slope * pH
        oer_standard_V = -reference_state.water_gibbs_energy_J_mol / (2 * FARADAY_C_MOL)
        oer_V = oer_standard_V - nernst_slope * pH

        for array in (
            pH, eh_V, energy_stack, stable_index, minimum_gibbs, her_V, oer_V
        ):
            array.setflags(write=False)
        return PourbaixDiagram(
            system=system,
            conditions=conditions,
            pH=pH,
            eh_V=eh_V,
            stable_species_index=stable_index,
            minimum_transformed_gibbs_J_mol_metal=minimum_gibbs,
            her_V=her_V,
            oer_V=oer_V,
            transformed_gibbs_J_mol_metal=energy_stack,
        )
