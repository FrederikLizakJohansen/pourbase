"""Live official Materials Project Pourbaix diagrams and grid comparisons."""

from __future__ import annotations

import math
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Any
from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

from .constants import REFERENCE_STATE_ABSOLUTE_TOLERANCE
from .engine import PourbaixDiagram, PourbaixEngine
from .exceptions import MaterialsProjectUnavailableError, UnsupportedConditionError
from .grid import grid_axes, readonly, water_lines
from .models import GibbsEnergyPolicy, PourbaixConditions, ThermodynamicSpecies


FloatArray = npt.NDArray[np.float64]
IntegerArray = npt.NDArray[np.int_]
BooleanArray = npt.NDArray[np.bool_]
PhaseKey = (tuple[str, float, float, float]
            | tuple[str, float, float, float, tuple[tuple[str, float], ...]])


def _rounded(value: float) -> float:
    return round(float(value), 8)


@dataclass(frozen=True, slots=True)
class OfficialMaterialsProjectPhase:
    """One stable entry returned by MP's official aqueous workflow."""

    phase_id: str
    label: str
    formula: str
    phase_type: str
    source_url: str
    metal_count: float
    oxygen_per_metal: float
    hydrogen_per_metal: float
    protons_per_metal: float
    electrons_per_metal: float
    baseline_energy_eV_metal: float
    log10_activity: float | None

    def __post_init__(self) -> None:
        if self.phase_type not in {"solid", "aqueous"}:
            raise ValueError(f"Unsupported MP phase type {self.phase_type!r}")
        if not self.phase_id or not self.label or not self.formula or not self.source_url:
            raise ValueError("MP phase identifiers, label, formula, and source are required")
        if not math.isfinite(self.metal_count) or self.metal_count <= 0:
            raise ValueError("MP phase metal count must be positive and finite")
        if self.phase_type == "solid" and self.log10_activity is not None:
            raise ValueError("MP solid phases cannot have an aqueous activity")

    @property
    def equivalence_key(self) -> PhaseKey:
        if self.phase_type == "solid":
            return (
                "solid", _rounded(self.oxygen_per_metal),
                _rounded(self.hydrogen_per_metal), 0.0,
            )
        return (
            "aqueous", _rounded(self.protons_per_metal),
            _rounded(self.electrons_per_metal), _rounded(self.metal_count),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "phase_id": self.phase_id,
            "label": self.label,
            "formula": self.formula,
            "phase_type": self.phase_type,
            "source_url": self.source_url,
            "metal_count": self.metal_count,
            "oxygen_per_metal": self.oxygen_per_metal,
            "hydrogen_per_metal": self.hydrogen_per_metal,
            "protons_per_metal": self.protons_per_metal,
            "electrons_per_metal": self.electrons_per_metal,
            "baseline_energy_eV_metal": self.baseline_energy_eV_metal,
            "log10_activity": self.log10_activity,
        }


@dataclass(frozen=True, slots=True)
class OfficialMaterialsProjectDiagram:
    """Official MP single-element Pourbaix result evaluated on the requested grid."""

    symbol: str
    conditions: PourbaixConditions
    phases: tuple[OfficialMaterialsProjectPhase, ...]
    pH: FloatArray
    eh_V: FloatArray
    stable_phase_index: IntegerArray
    minimum_energy_eV_metal: FloatArray
    her_V: FloatArray
    oer_V: FloatArray
    database_version: str
    mp_api_version: str
    pymatgen_version: str
    filter_solids: bool
    use_gibbs_300K: bool

    def __post_init__(self) -> None:
        expected = (self.eh_V.size, self.pH.size)
        if self.stable_phase_index.shape != expected:
            raise ValueError("MP phase grid has the wrong shape")
        if self.minimum_energy_eV_metal.shape != expected:
            raise ValueError("MP energy grid has the wrong shape")
        if not self.phases:
            raise ValueError("MP diagram must contain phases")

    @property
    def stable_phases(self) -> tuple[OfficialMaterialsProjectPhase, ...]:
        indices = sorted(int(value) for value in np.unique(self.stable_phase_index))
        return tuple(self.phases[index] for index in indices)

    def phase_at(self, pH: float, eh_V: float) -> OfficialMaterialsProjectPhase:
        if not self.pH[0] <= pH <= self.pH[-1]:
            raise ValueError("pH lies outside the diagram")
        if not self.eh_V[0] <= eh_V <= self.eh_V[-1]:
            raise ValueError("Eh lies outside the diagram")
        pH_index = int(np.abs(self.pH - pH).argmin())
        eh_index = int(np.abs(self.eh_V - eh_V).argmin())
        return self.phases[int(self.stable_phase_index[eh_index, pH_index])]


def thermodynamic_species_equivalence_key(species: ThermodynamicSpecies) -> PhaseKey:
    """Create the composition/reaction key used for cross-dataset domain matching."""
    if not species.is_ligand_free:
        return (
            species.phase,
            _rounded(species.core_oxygen_count / species.metal_count),
            _rounded(species.core_hydrogen_count / species.metal_count),
            _rounded(species.charge / species.metal_count),
            tuple(sorted((item.ligand_id, _rounded(item.count / species.metal_count))
                         for item in species.components)),
        )
    if species.phase in {"solid", "liquid"}:
        return (
            species.phase,
            _rounded(species.core_oxygen_count / species.metal_count),
            _rounded(species.core_hydrogen_count / species.metal_count),
            0.0,
        )
    if species.phase == "gas":
        return (
            "gas",
            _rounded(species.core_oxygen_count / species.metal_count),
            _rounded(species.core_hydrogen_count / species.metal_count),
            _rounded(species.metal_count),
        )
    return (
        "aqueous", _rounded(species.protons_per_metal),
        _rounded(species.electrons_per_metal), _rounded(species.metal_count),
    )


@dataclass(frozen=True, slots=True)
class OfficialMaterialsProjectComparison:
    """Experimental and official MP diagrams evaluated on one common grid."""

    experimental: PourbaixDiagram
    materials_project: OfficialMaterialsProjectDiagram
    same_thermodynamic_species: BooleanArray

    def __post_init__(self) -> None:
        expected = self.experimental.stable_species_index.shape
        if self.materials_project.stable_phase_index.shape != expected:
            raise ValueError("Experimental and MP grids must have the same shape")
        if self.same_thermodynamic_species.shape != expected:
            raise ValueError("Comparison mask has the wrong shape")

    @property
    def equivalent_domain_fraction(self) -> float:
        return float(np.mean(self.same_thermodynamic_species))

    @property
    def water_window_equivalent_domain_fraction(self) -> float:
        _, eh_grid = np.meshgrid(self.experimental.pH, self.experimental.eh_V)
        inside = (eh_grid >= self.experimental.her_V[np.newaxis, :]) & (
            eh_grid <= self.experimental.oer_V[np.newaxis, :]
        )
        return float(np.mean(self.same_thermodynamic_species[inside]))

    def changed_phase_pairs(self) -> tuple[tuple[str, str, int], ...]:
        changed = ~self.same_thermodynamic_species
        if not np.any(changed):
            return ()
        experimental_indices = self.experimental.stable_species_index[changed]
        mp_indices = self.materials_project.stable_phase_index[changed]
        pairs, counts = np.unique(
            np.column_stack((experimental_indices, mp_indices)), axis=0,
            return_counts=True,
        )
        rows = []
        for pair, count in zip(pairs, counts, strict=True):
            rows.append((
                self.experimental.system.species[int(pair[0])].species,
                self.materials_project.phases[int(pair[1])].label,
                int(count),
            ))
        return tuple(sorted(rows, key=lambda row: row[2], reverse=True))


def evaluate_official_materials_project_entries(
    symbol: str,
    conditions: PourbaixConditions,
    stable_entries: Sequence[Any],
    *,
    database_version: str,
    mp_api_version: str,
    pymatgen_version: str,
    filter_solids: bool,
    use_gibbs_300K: bool,
) -> OfficialMaterialsProjectDiagram:
    """Evaluate corrected pymatgen Pourbaix entries on the experimental grid."""
    if not stable_entries:
        raise MaterialsProjectUnavailableError(
            f"Materials Project returned no stable Pourbaix entries for {symbol}"
        )
    ordered_entries = sorted(
        stable_entries, key=lambda item: (str(item.phase_type), item.name, str(item.entry_id))
    )
    phases = []
    activity_model = conditions.aqueous_activities
    for index, entry in enumerate(ordered_entries):
        normalization = float(entry.normalization_factor)
        metal_count = float(entry.composition.get(symbol, 0.0))
        if metal_count <= 0:
            raise MaterialsProjectUnavailableError(
                f"MP entry {entry.entry_id} contains no {symbol}"
            )
        phase_type = "aqueous" if str(entry.phase_type).lower() == "ion" else "solid"
        phase_id = str(entry.entry_id or f"mp-entry-{index}")
        material_id = phase_id
        for suffix in ("-GGA+U", "-GGA", "-R2SCAN", "-r2SCAN"):
            if material_id.endswith(suffix):
                material_id = material_id[: -len(suffix)]
                break
        phases.append(OfficialMaterialsProjectPhase(
            phase_id=phase_id,
            label=str(entry.name),
            formula=str(entry.composition.reduced_formula),
            phase_type=phase_type,
            source_url=(
                "https://docs.materialsproject.org/methodology/materials-methodology/aqueous-stability-pourbaix"
                if phase_type == "aqueous"
                else f"https://materialsproject.org/materials/{material_id}"
            ),
            metal_count=metal_count,
            oxygen_per_metal=float(entry.composition.get("O", 0.0)) / metal_count,
            hydrogen_per_metal=float(entry.composition.get("H", 0.0)) / metal_count,
            protons_per_metal=-float(entry.npH) * normalization,
            electrons_per_metal=-float(entry.nPhi) * normalization,
            baseline_energy_eV_metal=float(entry.normalized_energy),
            log10_activity=(
                activity_model.log10_activity_for(
                    phase_id, str(entry.name), str(entry.composition.reduced_formula)
                )
                if phase_type == "aqueous" else None
            ),
        ))
    pH, eh_V = grid_axes(conditions)
    pH_grid, eh_grid = np.meshgrid(pH, eh_V)
    energy_stack = np.stack([
        np.asarray(entry.normalized_energy_at_conditions(pH_grid, eh_grid), dtype=np.float64)
        for entry in ordered_entries
    ])
    stable_index = np.argmin(energy_stack, axis=0)
    minimum_energy = np.take_along_axis(
        energy_stack, stable_index[np.newaxis, :, :], axis=0
    )[0]
    her_V, oer_V = water_lines(pH, conditions.temperature_K)
    return OfficialMaterialsProjectDiagram(
        symbol=symbol, conditions=conditions, phases=tuple(phases),
        pH=readonly(pH, np.float64), eh_V=readonly(eh_V, np.float64),
        stable_phase_index=readonly(stable_index, np.int_),
        minimum_energy_eV_metal=readonly(minimum_energy, np.float64),
        her_V=readonly(her_V, np.float64), oer_V=readonly(oer_V, np.float64),
        database_version=database_version, mp_api_version=mp_api_version,
        pymatgen_version=pymatgen_version, filter_solids=filter_solids,
        use_gibbs_300K=use_gibbs_300K,
    )


def apply_aqueous_activities(entries: Sequence[Any], conditions: PourbaixConditions) -> None:
    """Set each MP ion entry's concentration from the requested aqueous activities.

    pymatgen stores an ion's concentration per formula unit of its element, so the activity is
    scaled by the entry's normalization factor, as pymatgen's ``PourbaixDiagram`` does with
    ``conc_dict``. Call this after constructing a ``PourbaixDiagram``: the constructor resets
    every ion concentration to its own ``conc_dict``.
    """
    activity_model = conditions.aqueous_activities
    for entry in entries:
        if str(entry.phase_type).lower() == "ion":
            entry.concentration = activity_model.activity_for(
                str(entry.entry_id), str(entry.name), str(entry.composition.reduced_formula),
            ) * float(entry.normalization_factor)


class OfficialMaterialsProjectClient:
    """Fetch an official MP diagram using a caller-supplied API key."""

    def __init__(self, api_key: str) -> None:
        key = api_key.strip()
        if not key:
            raise ValueError("A Materials Project API key is required")
        self._api_key = key

    @staticmethod
    def _validate_conditions(conditions: PourbaixConditions) -> None:
        if not math.isclose(
            conditions.temperature_K, 298.15, rel_tol=0.0,
            abs_tol=REFERENCE_STATE_ABSOLUTE_TOLERANCE,
        ):
            raise UnsupportedConditionError("The official MP workflow uses 298.15 K")
        if not math.isclose(
            conditions.pressure_bar, 1.0, rel_tol=0.0,
            abs_tol=REFERENCE_STATE_ABSOLUTE_TOLERANCE,
        ):
            raise UnsupportedConditionError("The official MP comparison uses 1 bar")

    def calculate(
        self,
        symbol: str,
        conditions: PourbaixConditions,
        *,
        filter_solids: bool = True,
        use_gibbs_300K: bool = False,
    ) -> OfficialMaterialsProjectDiagram:
        self._validate_conditions(conditions)
        normalized_symbol = symbol.strip()[:1].upper() + symbol.strip()[1:].lower()
        if not normalized_symbol:
            raise ValueError("symbol must not be empty")
        try:
            from mp_api.client import MPRester
            from pymatgen.analysis.pourbaix_diagram import PourbaixDiagram as MPPourbaixDiagram
            mp_api_version = version("mp-api")
            pymatgen_version = version("pymatgen")
        except (ImportError, PackageNotFoundError) as error:
            raise MaterialsProjectUnavailableError(
                "Live MP diagrams require mp-api and pymatgen"
            ) from error
        try:
            with MPRester(
                self._api_key, mute_progress_bars=True, notify_db_version=False
            ) as rester:
                entries = rester.get_pourbaix_entries(
                    [normalized_symbol], use_gibbs=300 if use_gibbs_300K else None
                )
                database_version = str(rester.db_version)
            # Every filtered entry is evaluated on the grid: which entries are stable depends on
            # the ion activities, and the constructor evaluates them at its default conc_dict.
            candidate_entries = MPPourbaixDiagram(entries, filter_solids=filter_solids).all_entries
            apply_aqueous_activities(candidate_entries, conditions)
        except Exception as error:
            safe_message = str(error).replace(self._api_key, "[redacted]")
            raise MaterialsProjectUnavailableError(
                f"Materials Project could not create the {normalized_symbol} diagram: {safe_message}"
            ) from error
        return evaluate_official_materials_project_entries(
            normalized_symbol, conditions, candidate_entries,
            database_version=database_version, mp_api_version=mp_api_version,
            pymatgen_version=pymatgen_version, filter_solids=filter_solids,
            use_gibbs_300K=use_gibbs_300K,
        )


class OfficialMaterialsProjectComparator:
    """Fetch MP and compare it with the publication's experimental diagram."""

    def __init__(self, engine: PourbaixEngine, client: OfficialMaterialsProjectClient) -> None:
        self.engine = engine
        self.client = client

    def compare(
        self,
        symbol: str,
        conditions: PourbaixConditions,
        *,
        filter_solids: bool = True,
        use_gibbs_300K: bool = False,
        allow_incomplete: bool = True,
        energy_policy: GibbsEnergyPolicy | str = GibbsEnergyPolicy.EXPERIMENTAL_ONLY,
    ) -> OfficialMaterialsProjectComparison:
        experimental = self.engine.calculate(
            symbol, conditions, allow_incomplete=allow_incomplete,
            energy_policy=energy_policy,
        )
        materials_project = self.client.calculate(
            symbol, conditions, filter_solids=filter_solids,
            use_gibbs_300K=use_gibbs_300K,
        )
        equivalence = np.asarray([
            [
                thermodynamic_species_equivalence_key(experimental_species)
                == mp_phase.equivalence_key
                for mp_phase in materials_project.phases
            ]
            for experimental_species in experimental.system.species
        ], dtype=np.bool_)
        same = equivalence[
            experimental.stable_species_index, materials_project.stable_phase_index
        ]
        same.setflags(write=False)
        return OfficialMaterialsProjectComparison(experimental, materials_project, same)
