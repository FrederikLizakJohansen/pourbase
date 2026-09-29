"""Closed-system metal balance for single-metal Pourbaix calculations."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from .activity_coefficients import (
    ActivityCoefficientModel,
    IdealActivityCoefficientModel,
)
from .constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from .database import ThermodynamicDatabase
from .engine import PourbaixEngine
from .exceptions import IncompleteSystemError, UnsupportedConditionError
from .models import (
    GibbsEnergyPolicy,
    MetalSystem,
    PourbaixConditions,
    SpeciesExclusion,
    ThermodynamicSpecies,
    TotalMetalConcentration,
)


FloatArray = npt.NDArray[np.float64]
IntegerArray = npt.NDArray[np.int_]


def _nearest_grid_index(values: FloatArray, requested: float, name: str) -> int:
    if not math.isfinite(requested):
        raise ValueError(f"{name} must be finite")
    if not values[0] <= requested <= values[-1]:
        raise ValueError(f"{name} lies outside the diagram")
    return int(np.abs(values - requested).argmin())


@dataclass(frozen=True, slots=True)
class MassBalancedState:
    """Equilibrium inventory at one numerical pH/Eh grid point."""

    pH: float
    eh_V: float
    dominant_species: ThermodynamicSpecies
    precipitating_solid: ThermodynamicSpecies | None
    total_metal_mol_L: float
    dissolved_metal_mol_L: float
    precipitated_metal_mol_L: float
    precipitated_fraction: float
    aqueous_concentrations_mol_L: tuple[tuple[ThermodynamicSpecies, float], ...]
    aqueous_activity_coefficients: tuple[tuple[ThermodynamicSpecies, float], ...]
    aqueous_activities: tuple[tuple[ThermodynamicSpecies, float], ...]


@dataclass(frozen=True, slots=True)
class MassBalancedPourbaixDiagram:
    """Predominance and inventory grids from a closed metal balance."""

    system: MetalSystem
    conditions: PourbaixConditions
    total_metal: TotalMetalConcentration
    activity_coefficient_model: ActivityCoefficientModel
    pH: FloatArray
    eh_V: FloatArray
    dominant_species_index: IntegerArray
    precipitating_solid_index: IntegerArray
    aqueous_species_indices: IntegerArray
    aqueous_activity_coefficient: FloatArray
    aqueous_concentration_mol_L: FloatArray
    aqueous_activity: FloatArray
    dissolved_metal_mol_L: FloatArray
    saturation_dissolved_metal_mol_L: FloatArray
    precipitated_metal_fraction: FloatArray
    equilibrium_metal_chemical_potential_J_mol: FloatArray
    her_V: FloatArray
    oer_V: FloatArray

    def __post_init__(self) -> None:
        expected_shape = (self.eh_V.size, self.pH.size)
        for name in (
            "dominant_species_index",
            "precipitating_solid_index",
            "dissolved_metal_mol_L",
            "saturation_dissolved_metal_mol_L",
            "precipitated_metal_fraction",
            "equilibrium_metal_chemical_potential_J_mol",
        ):
            if getattr(self, name).shape != expected_shape:
                raise ValueError(f"{name} has the wrong grid shape")
        expected_aqueous_shape = (self.aqueous_species_indices.size, *expected_shape)
        if self.aqueous_concentration_mol_L.shape != expected_aqueous_shape:
            raise ValueError("aqueous concentration array has the wrong shape")
        if self.aqueous_activity.shape != expected_aqueous_shape:
            raise ValueError("aqueous activity array has the wrong shape")
        if self.aqueous_activity_coefficient.shape != (
            self.aqueous_species_indices.size,
        ):
            raise ValueError("aqueous activity-coefficient array has the wrong shape")
        if np.any(self.dominant_species_index < 0) or np.any(
            self.dominant_species_index >= len(self.system.species)
        ):
            raise ValueError("dominant species index lies outside the system")
        if np.any(self.precipitated_metal_fraction < 0) or np.any(
            self.precipitated_metal_fraction > 1
        ):
            raise ValueError("precipitated fractions must lie between zero and one")
        if np.any(~np.isfinite(self.aqueous_concentration_mol_L)) or np.any(
            self.aqueous_concentration_mol_L < 0
        ):
            raise ValueError("aqueous concentrations must be non-negative and finite")
        if np.any(~np.isfinite(self.aqueous_activity_coefficient)) or np.any(
            self.aqueous_activity_coefficient <= 0
        ):
            raise ValueError("aqueous activity coefficients must be positive and finite")
        if np.any(~np.isfinite(self.aqueous_activity)) or np.any(
            self.aqueous_activity < 0
        ):
            raise ValueError("aqueous activities must be non-negative and finite")
        expected_activity = (
            self.aqueous_activity_coefficient[:, np.newaxis, np.newaxis]
            * self.aqueous_concentration_mol_L
            / self.total_metal.standard_concentration_mol_L
        )
        if not np.allclose(
            self.aqueous_activity,
            expected_activity,
            rtol=1e-12,
            atol=0.0,
        ):
            raise ValueError("aqueous activities are inconsistent with concentrations")
        if np.any(~np.isfinite(self.dissolved_metal_mol_L)) or np.any(
            self.dissolved_metal_mol_L < 0
        ):
            raise ValueError("dissolved metal concentrations must be non-negative and finite")
        if np.any(self.dissolved_metal_mol_L > self.total_metal.total_metal_mol_L):
            raise ValueError("dissolved metal cannot exceed total metal")
        if not np.allclose(
            np.sum(self.aqueous_concentration_mol_L, axis=0),
            self.dissolved_metal_mol_L,
            rtol=1e-12,
            atol=0.0,
        ):
            raise ValueError("aqueous concentrations do not satisfy dissolved metal balance")
        reconstructed_total = self.dissolved_metal_mol_L + (
            self.precipitated_metal_fraction
            * self.total_metal.total_metal_mol_L
        )
        if not np.allclose(
            reconstructed_total,
            self.total_metal.total_metal_mol_L,
            rtol=1e-12,
            atol=0.0,
        ):
            raise ValueError("dissolved and precipitated inventories do not conserve metal")
        for index in self.aqueous_species_indices:
            if not self.system.species[int(index)].is_aqueous:
                raise ValueError("aqueous species index refers to a solid")
        solid_indices = np.unique(self.precipitating_solid_index)
        for index in solid_indices[solid_indices >= 0]:
            if self.system.species[int(index)].is_aqueous:
                raise ValueError("precipitating solid index refers to an aqueous species")

    @property
    def stable_species_index(self) -> IntegerArray:
        """Compatibility alias used by the common phase-map plotting layer."""
        return self.dominant_species_index

    @property
    def stable_species(self) -> tuple[ThermodynamicSpecies, ...]:
        """Return every species that dominates at one or more grid points."""
        indices = sorted(int(value) for value in np.unique(self.dominant_species_index))
        return tuple(self.system.species[index] for index in indices)

    @property
    def aqueous_species(self) -> tuple[ThermodynamicSpecies, ...]:
        """Return aqueous entries in concentration-array order."""
        return tuple(
            self.system.species[int(index)] for index in self.aqueous_species_indices
        )

    def species_at(self, pH: float, eh_V: float) -> ThermodynamicSpecies:
        """Return the dominant species nearest to a requested coordinate."""
        pH_index = _nearest_grid_index(self.pH, pH, "pH")
        eh_index = _nearest_grid_index(self.eh_V, eh_V, "eh_V")
        index = int(self.dominant_species_index[eh_index, pH_index])
        return self.system.species[index]

    def state_at(self, pH: float, eh_V: float) -> MassBalancedState:
        """Return the complete equilibrium inventory nearest to one coordinate."""
        pH_index = _nearest_grid_index(self.pH, pH, "pH")
        eh_index = _nearest_grid_index(self.eh_V, eh_V, "eh_V")
        dominant_index = int(self.dominant_species_index[eh_index, pH_index])
        solid_index = int(self.precipitating_solid_index[eh_index, pH_index])
        dissolved = float(self.dissolved_metal_mol_L[eh_index, pH_index])
        total = self.total_metal.total_metal_mol_L
        return MassBalancedState(
            pH=float(self.pH[pH_index]),
            eh_V=float(self.eh_V[eh_index]),
            dominant_species=self.system.species[dominant_index],
            precipitating_solid=(
                self.system.species[solid_index] if solid_index >= 0 else None
            ),
            total_metal_mol_L=total,
            dissolved_metal_mol_L=dissolved,
            precipitated_metal_mol_L=max(total - dissolved, 0.0),
            precipitated_fraction=float(
                self.precipitated_metal_fraction[eh_index, pH_index]
            ),
            aqueous_concentrations_mol_L=tuple(
                (
                    species,
                    float(self.aqueous_concentration_mol_L[index, eh_index, pH_index]),
                )
                for index, species in enumerate(self.aqueous_species)
            ),
            aqueous_activity_coefficients=tuple(
                (species, float(self.aqueous_activity_coefficient[index]))
                for index, species in enumerate(self.aqueous_species)
            ),
            aqueous_activities=tuple(
                (
                    species,
                    float(self.aqueous_activity[index, eh_index, pH_index]),
                )
                for index, species in enumerate(self.aqueous_species)
            ),
        )


class MassBalanceEngine:
    """Solve aqueous speciation and solid precipitation at fixed total metal.

    Protons and electrons remain open reservoirs controlled by pH and Eh. Water and
    solids have unit activity. The selected metal is conserved across dissolved
    species and precipitated solid. A pluggable model supplies aqueous coefficients.
    """

    def __init__(
        self,
        database: ThermodynamicDatabase,
        activity_coefficient_model: ActivityCoefficientModel | None = None,
    ) -> None:
        self.database = database
        self.phase_engine = PourbaixEngine(database)
        self.activity_coefficient_model = (
            IdealActivityCoefficientModel()
            if activity_coefficient_model is None
            else activity_coefficient_model
        )
        if not isinstance(self.activity_coefficient_model, ActivityCoefficientModel):
            raise TypeError(
                "activity_coefficient_model must implement ActivityCoefficientModel"
            )

    def calculate(
        self,
        symbol: str,
        conditions: PourbaixConditions,
        total_metal: TotalMetalConcentration,
        *,
        allow_incomplete: bool = False,
        energy_policy: GibbsEnergyPolicy | str = GibbsEnergyPolicy.EXPERIMENTAL_ONLY,
    ) -> MassBalancedPourbaixDiagram:
        """Load one elemental system and calculate its closed metal balance."""
        ligand_ids = (
            conditions.ligand_activities.ligand_ids
            if conditions.ligand_activities is not None
            else ()
        )
        return self.calculate_system(
            self.database.load_system(
                symbol, ligand_ids=ligand_ids, energy_policy=energy_policy
            ),
            conditions,
            total_metal,
            allow_incomplete=allow_incomplete,
        )

    def calculate_system(
        self,
        system: MetalSystem,
        conditions: PourbaixConditions,
        total_metal: TotalMetalConcentration,
        *,
        allow_incomplete: bool = False,
    ) -> MassBalancedPourbaixDiagram:
        """Calculate an already loaded or deliberately transformed metal system."""
        if not isinstance(total_metal, TotalMetalConcentration):
            raise TypeError("total_metal must be a TotalMetalConcentration")
        gas_species = tuple(item for item in system.species if item.is_gas)
        if gas_species:
            raise UnsupportedConditionError(
                "Closed element mass balance with a gas phase is not implemented; "
                "use fixed-activity mode with an explicit gas fugacity"
            )
        unsupported_aqueous = tuple(
            item
            for item in system.species
            if item.is_aqueous
            and not math.isclose(item.metal_count, 1.0, rel_tol=0.0, abs_tol=1e-12)
        )
        if unsupported_aqueous:
            system = MetalSystem(
                system=system.system,
                symbol=system.symbol,
                species=tuple(
                    item for item in system.species if item not in unsupported_aqueous
                ),
                excluded=system.excluded
                + tuple(
                    SpeciesExclusion(
                        record_id=item.record_id,
                        species=item.species,
                        reason="mass_balance_nonmonometal_aqueous_unsupported",
                        status=item.gibbs_status,
                    )
                    for item in unsupported_aqueous
                ),
            )
        reference_state = self.database.reference_state
        self.phase_engine._validate_conditions(conditions, reference_state)
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
        activity_model = conditions.aqueous_activities
        assert activity_model is not None
        if activity_model.overrides:
            raise UnsupportedConditionError(
                "Fixed aqueous activity overrides cannot be combined with a total-metal "
                "mass balance; the solver calculates all aqueous activities"
            )

        aqueous_indices = np.asarray(
            [index for index, item in enumerate(system.species) if item.is_aqueous],
            dtype=np.int_,
        )
        solid_indices = np.asarray(
            [index for index, item in enumerate(system.species) if item.is_condensed],
            dtype=np.int_,
        )
        if not aqueous_indices.size:
            raise UnsupportedConditionError(
                f"{system.symbol} has no supported aqueous species for a mass balance"
            )
        pH = np.linspace(conditions.pH_min, conditions.pH_max, conditions.pH_points)
        eh_V = np.linspace(
            conditions.eh_min_V,
            conditions.eh_max_V,
            conditions.eh_points,
        )
        pH_grid, eh_grid = np.meshgrid(pH, eh_V)
        standard_energy = np.stack(
            [
                self.phase_engine.standard_transformed_gibbs_J_mol_metal(
                    species,
                    reference_state,
                    conditions,
                    pH_grid,
                    eh_grid,
                )
                for species in system.species
            ],
            axis=0,
        )
        rt = GAS_CONSTANT_J_MOL_K * conditions.temperature_K
        aqueous_energy = standard_energy[aqueous_indices]
        aqueous_activity_coefficient = np.asarray(
            [
                self.activity_coefficient_model.coefficient(
                    system.species[int(index)].charge
                )
                for index in aqueous_indices
            ],
            dtype=np.float64,
        )
        if np.any(~np.isfinite(aqueous_activity_coefficient)) or np.any(
            aqueous_activity_coefficient <= 0
        ):
            raise ValueError(
                "activity-coefficient model returned a non-positive or non-finite value"
            )
        log_activity_coefficient = np.log(aqueous_activity_coefficient)
        scaled = (
            -aqueous_energy / rt
            - log_activity_coefficient[:, np.newaxis, np.newaxis]
        )
        maximum_scaled = np.max(scaled, axis=0)
        weights = np.exp(scaled - maximum_scaled[np.newaxis, :, :])
        partition = np.sum(weights, axis=0)
        aqueous_fraction = weights / partition[np.newaxis, :, :]
        log_partition = maximum_scaled + np.log(partition)

        total = total_metal.total_metal_mol_L
        standard_concentration = total_metal.standard_concentration_mol_L
        log_dimensionless_total = math.log(total_metal.dimensionless_total)
        aqueous_only_chemical_potential = rt * (
            log_dimensionless_total - log_partition
        )

        grid_shape = pH_grid.shape
        if solid_indices.size:
            solid_energy = standard_energy[solid_indices]
            local_solid_index = np.argmin(solid_energy, axis=0)
            minimum_solid_energy = np.take_along_axis(
                solid_energy,
                local_solid_index[np.newaxis, :, :],
                axis=0,
            )[0]
            stable_solid_index = solid_indices[local_solid_index]
            log_saturation = minimum_solid_energy / rt + log_partition
            precipitating = log_dimensionless_total > log_saturation + 1e-12
            maximum_log_concentration = math.log(
                np.finfo(np.float64).max
            ) - math.log(standard_concentration)
            saturation = standard_concentration * np.exp(
                np.minimum(log_saturation, maximum_log_concentration)
            )
            saturation = np.where(
                log_saturation > maximum_log_concentration,
                np.inf,
                saturation,
            )
            dissolved = np.where(precipitating, saturation, total)
            precipitating_solid_index = np.where(
                precipitating,
                stable_solid_index,
                -1,
            )
            chemical_potential = np.where(
                precipitating,
                minimum_solid_energy,
                aqueous_only_chemical_potential,
            )
        else:
            saturation = np.full(grid_shape, np.inf, dtype=np.float64)
            dissolved = np.full(grid_shape, total, dtype=np.float64)
            precipitating = np.zeros(grid_shape, dtype=np.bool_)
            precipitating_solid_index = np.full(grid_shape, -1, dtype=np.int_)
            chemical_potential = aqueous_only_chemical_potential

        aqueous_concentration = aqueous_fraction * dissolved[np.newaxis, :, :]
        aqueous_activity = (
            aqueous_activity_coefficient[:, np.newaxis, np.newaxis]
            * aqueous_concentration
            / standard_concentration
        )
        precipitated_fraction = np.clip((total - dissolved) / total, 0.0, 1.0)
        predominant_aqueous_local = np.argmax(aqueous_concentration, axis=0)
        dominant_index = aqueous_indices[predominant_aqueous_local]
        dominant_index = np.where(
            precipitating,
            precipitating_solid_index,
            dominant_index,
        )

        nernst_slope = rt * LN_10 / FARADAY_C_MOL
        her_V = -nernst_slope * pH
        oer_standard_V = -reference_state.water_gibbs_energy_J_mol / (
            2 * FARADAY_C_MOL
        )
        oer_V = oer_standard_V - nernst_slope * pH

        arrays = (
            pH,
            eh_V,
            dominant_index,
            precipitating_solid_index,
            aqueous_indices,
            aqueous_activity_coefficient,
            aqueous_concentration,
            aqueous_activity,
            dissolved,
            saturation,
            precipitated_fraction,
            chemical_potential,
            her_V,
            oer_V,
        )
        for array in arrays:
            array.setflags(write=False)
        return MassBalancedPourbaixDiagram(
            system=system,
            conditions=conditions,
            total_metal=total_metal,
            activity_coefficient_model=self.activity_coefficient_model,
            pH=pH,
            eh_V=eh_V,
            dominant_species_index=np.asarray(dominant_index, dtype=np.int_),
            precipitating_solid_index=np.asarray(
                precipitating_solid_index, dtype=np.int_
            ),
            aqueous_species_indices=aqueous_indices,
            aqueous_activity_coefficient=aqueous_activity_coefficient,
            aqueous_concentration_mol_L=np.asarray(
                aqueous_concentration, dtype=np.float64
            ),
            aqueous_activity=np.asarray(aqueous_activity, dtype=np.float64),
            dissolved_metal_mol_L=np.asarray(dissolved, dtype=np.float64),
            saturation_dissolved_metal_mol_L=np.asarray(
                saturation, dtype=np.float64
            ),
            precipitated_metal_fraction=np.asarray(
                precipitated_fraction, dtype=np.float64
            ),
            equilibrium_metal_chemical_potential_J_mol=np.asarray(
                chemical_potential, dtype=np.float64
            ),
            her_V=her_V,
            oer_V=oer_V,
        )


class IdealMassBalanceEngine(MassBalanceEngine):
    """Backward-compatible mass-balance engine with unit activity coefficients."""

    def __init__(self, database: ThermodynamicDatabase) -> None:
        super().__init__(database, IdealActivityCoefficientModel())
