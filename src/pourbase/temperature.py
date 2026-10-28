"""Gibbs energies away from 298.15 K, between 0 and 100 °C.

Each species keeps its enthalpy and entropy of formation at their 298.15 K values, so

    ΔfG°(T) = ΔfG°(T₀) − (T − T₀) ΔfS°,                                                  (14)

with T₀ = 298.15 K. ΔfS° comes from the stored values, in this order of preference: the formation
enthalpy from the source of the Gibbs energy, ΔfS° = (ΔfH° − ΔfG°)/T₀; the standard entropy from
that source; then either value from another source. From a standard entropy,

    ΔfS° = S°ᵢ − m S°(M) − n_O S°(O₂)/2 − n_H S°(H₂)/2 + z S°(H₂)/2,                      (15)

which follows the convention S°(H⁺) = 0 and ΔfG°(H⁺) = 0 at every temperature. Species without
either value, and ligand species (the database holds no ligand entropies), are left out.

Neglecting the heat capacity of formation ΔfCp° misplaces ΔfG° by about ΔfCp° (T − T₀)² / 2T. This
term, with ΔfCp° taken as 300 J/(mol K) for aqueous species and 50 J/(mol K) otherwise, is added in
quadrature to each uncertainty (Eq. 12). Liquid water, whose heat capacity is known, is extrapolated
with it, so the water lines (Eq. 5) follow the steam tables.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

from .exceptions import UnsupportedConditionError
from .models import EvidenceStatus, ExclusionReason, MetalSystem, ReferenceState, SpeciesExclusion

T0 = 298.15
MINIMUM_K, MAXIMUM_K = 273.15, 373.15
NBS_TABLES = ("Wagman, D. D. et al. (1982). The NBS Tables of Chemical Thermodynamic Properties. "
              "Journal of Physical and Chemical Reference Data 11, Supplement 2. "
              "Open digitization with errata: https://doi.org/10.18434/M32124.")
# NBS Tables with errata: H2(g), O2(g), H2O(l), J/(mol K).
ENTROPY_H2, ENTROPY_O2, ENTROPY_WATER = 130.684, 205.138, 69.91
WATER_FORMATION_ENTROPY = ENTROPY_WATER - ENTROPY_H2 - ENTROPY_O2 / 2
# heat capacities at 298.15 K, J/(mol K) (Chase 1998, NIST-JANAF Tables): H2O(l), H2(g), O2(g)
WATER_FORMATION_HEAT_CAPACITY = 75.351 - 28.836 - 29.376 / 2
ASSUMED_HEAT_CAPACITY = {"aqueous": 300.0, "other": 50.0}


def extrapolation_uncertainty_J_mol(phase_is_aqueous: bool, temperature_K: float) -> float:
    """The ΔfG° error from neglecting the heat capacity of formation, as an uncertainty."""
    heat_capacity = ASSUMED_HEAT_CAPACITY["aqueous" if phase_is_aqueous else "other"]
    return heat_capacity * (temperature_K - T0) ** 2 / (2 * temperature_K)


def water_gibbs_energy_J_mol(reference_J_mol: float, temperature_K: float) -> float:
    """ΔfG° of liquid water at T from its 298.15 K value, its formation entropy and heat capacity."""
    dT = temperature_K - T0
    return (reference_J_mol - dT * WATER_FORMATION_ENTROPY
            + WATER_FORMATION_HEAT_CAPACITY * (dT - temperature_K * math.log(temperature_K / T0)))


class DatabaseAtTemperature:
    """A view of a ``ThermodynamicDatabase`` whose species and water describe temperature T."""

    def __init__(self, database, temperature_K: float) -> None:
        if not MINIMUM_K <= temperature_K <= MAXIMUM_K:
            raise UnsupportedConditionError(
                f"Temperatures from {MINIMUM_K - 273.15:g} to {MAXIMUM_K - 273.15:g} °C are supported; the "
                "constant-entropy extrapolation is not reliable beyond 100 °C")
        self.base = database
        self.temperature_K = float(temperature_K)
        self._systems: dict[Any, MetalSystem] = {}
        self._entropy = None

    def __getattr__(self, name: str):
        return getattr(self.base, name)

    @property
    def reference_state(self) -> ReferenceState:
        base = self.base.reference_state
        return ReferenceState(self.temperature_K, base.pressure_bar,
                              water_gibbs_energy_J_mol(base.water_gibbs_energy_J_mol, self.temperature_K))

    def formation_entropies(self) -> dict[str, tuple[float, str]]:
        """``record_id → (ΔfS° in J/(mol K), route)`` for every species with the data."""
        if self._entropy is None:
            rows = self.base._rows(
                "SELECT t.record_id, s.symbol, s.charge, s.metal_count, s.core_oxygen_count, s.core_hydrogen_count, "
                "t.gibbs_energy_J_mol g, t.gibbs_status, t.gibbs_source_id gs, t.entropy_J_mol_K S, "
                "t.entropy_source_id ss, t.formation_enthalpy_J_mol H, t.formation_enthalpy_source_id hs "
                "FROM selected_thermochemistry t JOIN species s USING(record_id) WHERE t.gibbs_energy_J_mol IS NOT NULL")
            # entropy per atom of each element in its reference state (N₂, Cl₂ and others hold two atoms)
            elements = {row["symbol"]: row["S"] / row["metal_count"] for row in rows
                        if row["gibbs_status"] == EvidenceStatus.DEFINED_REFERENCE_STATE.value and row["S"] is not None}
            result: dict[str, tuple[float, str]] = {}
            for row in rows:
                if row["gibbs_status"] == EvidenceStatus.DEFINED_REFERENCE_STATE.value:
                    result[row["record_id"]] = (0.0, "reference state")
                    continue
                from_enthalpy = None if row["H"] is None else (row["H"] - row["g"]) / T0
                from_entropy = None
                if row["S"] is not None and row["symbol"] in elements:
                    from_entropy = (row["S"] - row["metal_count"] * elements[row["symbol"]]
                                    - row["core_oxygen_count"] * ENTROPY_O2 / 2
                                    - row["core_hydrogen_count"] * ENTROPY_H2 / 2 + row["charge"] * ENTROPY_H2 / 2)
                for value, same_source, route in (
                    (from_enthalpy, row["hs"] == row["gs"], "ΔfH° and ΔfG°, one source"),
                    (from_entropy, row["ss"] == row["gs"], "S°, source of ΔfG°"),
                    (from_enthalpy, True, "ΔfH° and ΔfG°, two sources"),
                    (from_entropy, True, "S°, another source"),
                ):
                    if value is not None and same_source:
                        result[row["record_id"]] = (value, route)
                        break
            self._entropy = result
        return self._entropy

    def load_system(self, symbol: str, *, ligand_ids=(), energy_policy=None,
                    include_optional_gases: bool = False, **options) -> MetalSystem:
        if not isinstance(include_optional_gases, bool):
            raise TypeError("include_optional_gases must be a bool")
        key = (symbol, tuple(sorted(ligand_ids)), energy_policy, include_optional_gases)
        if key in self._systems:
            return self._systems[key]
        arguments = {"ligand_ids": ligand_ids, **options}
        if include_optional_gases:
            arguments["include_optional_gases"] = True
        if energy_policy is not None:
            arguments["energy_policy"] = energy_policy
        system = self.base.load_system(symbol, **arguments)
        entropies = self.formation_entropies()
        dT = self.temperature_K - T0
        kept, excluded = [], list(system.excluded)
        for item in system.species:
            entry = entropies.get(item.record_id)
            if not item.is_ligand_free or entry is None:
                excluded.append(SpeciesExclusion(item.record_id, item.species,
                                                 ExclusionReason.TEMPERATURE_DATA_UNAVAILABLE,
                                                 item.gibbs_status.value))
                continue
            if item.gibbs_status is EvidenceStatus.DEFINED_REFERENCE_STATE:
                kept.append(item)
                continue
            kept.append(replace(item, gibbs_energy_J_mol=item.gibbs_energy_J_mol - dT * entry[0],
                                temperature_uncertainty_J_mol=extrapolation_uncertainty_J_mol(
                                    item.is_aqueous, self.temperature_K)))
        if not kept:
            raise UnsupportedConditionError(f"No {symbol} species has the entropy data for {self.temperature_K:g} K")
        shifted = replace(system, species=tuple(kept), excluded=tuple(excluded))
        self._systems[key] = shifted
        return shifted


def at_temperature(database, temperature_K: float):
    """``database`` itself at 298.15 K, otherwise a view of it at ``temperature_K``."""
    if math.isclose(temperature_K, T0, abs_tol=1e-9):
        return database
    base = database.base if isinstance(database, DatabaseAtTemperature) else database
    return DatabaseAtTemperature(base, temperature_K)
