"""Diagrams at one fixed potential: solubility against pH and ligand predominance against pH.

:func:`solubility` gives, at each pH, the dissolved metal in equilibrium with the most stable
condensed phase (Eqs. 6 and 7 with ideal activities): an aqueous species ``i`` with ``m_i`` metal
atoms has the activity ``log10 a_i = m_i (G_s - G_i°) / (RT ln 10)``, where ``G_s`` is the
transformed Gibbs energy of the solid and ``G_i°`` that of the species at unit activity, both per
mole of metal. It carries ``m_i a_i`` mol/L of metal.

:func:`ligand_predominance` gives the stable species of a fixed-activity diagram over pH and the
free activity of one ligand.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from .constants import GAS_CONSTANT_J_MOL_K, LN_10
from .engine import PourbaixEngine, standard_transformed_gibbs_J_mol_metal
from .models import LigandActivity, LigandActivityModel, ThermodynamicSpecies


@dataclass(frozen=True)
class Solubility:
    pH: np.ndarray
    U_V: float
    species: tuple[ThermodynamicSpecies, ...]  # the aqueous species, in the order of the rows below
    log10_metal_mol_L: np.ndarray  # (species, pH): metal carried by each aqueous species
    log10_total_mol_L: np.ndarray  # (pH,): total dissolved metal at saturation
    solids: tuple[ThermodynamicSpecies, ...]
    solid_index: np.ndarray  # (pH,): index into ``solids`` of the phase controlling the solubility


def solubility(calculation, U_V: float, pH: np.ndarray | None = None) -> Solubility:
    """Dissolved metal in equilibrium with the most stable condensed phase at potential ``U_V`` (V vs SHE)."""
    diagram = calculation.diagram
    database = calculation.database
    reference = database.reference_state
    conditions = diagram.conditions
    pH = np.asarray(diagram.pH if pH is None else pH, dtype=np.float64)
    U = np.full_like(pH, float(U_V))
    species = diagram.system.species
    solids = tuple(item for item in species if item.is_condensed)
    aqueous = tuple(item for item in species if item.is_aqueous)
    if not solids:
        raise ValueError(f"{calculation.scenario.symbol} has no solid or liquid phase to control a solubility")
    if not aqueous:
        raise ValueError(f"{calculation.scenario.symbol} has no aqueous species")
    rt_ln_10 = GAS_CONSTANT_J_MOL_K * conditions.temperature_K * LN_10
    solid_energy = np.stack([standard_transformed_gibbs_J_mol_metal(item, reference, conditions, pH, U)
                             for item in solids])
    solid_index = np.argmin(solid_energy, axis=0)
    controlling = solid_energy.min(axis=0)
    rows = []
    for item in aqueous:
        energy = standard_transformed_gibbs_J_mol_metal(item, reference, conditions, pH, U)
        rows.append(np.log10(item.metal_count) + item.metal_count * (controlling - energy) / rt_ln_10)
    log_metal = np.vstack(rows)
    peak = log_metal.max(axis=0)
    total = peak + np.log10(np.sum(10.0 ** (log_metal - peak), axis=0))
    return Solubility(pH, float(U_V), aqueous, log_metal, total, solids, solid_index)


@dataclass(frozen=True)
class LigandPredominance:
    pH: np.ndarray
    log10_activity: np.ndarray
    U_V: float
    ligand_id: str
    species: tuple[ThermodynamicSpecies, ...]
    stable_species_index: np.ndarray  # (activity, pH)


def ligand_predominance(
    calculation,
    ligand_id: str,
    U_V: float,
    log10_activity: np.ndarray | None = None,
) -> LigandPredominance:
    """Stable species over pH and the free activity of ``ligand_id`` at potential ``U_V`` (V vs SHE).

    The metal activity and any other ligands are those of the calculation's scenario, read as a
    fixed-activity diagram.
    """
    scenario = calculation.scenario
    levels = np.linspace(-8.0, 0.0, 161) if log10_activity is None else np.asarray(log10_activity, float)
    others = tuple(item for item in scenario.ligands if item.ligand_id != ligand_id)
    base = scenario.conditions()
    base = replace(base, U_min_V=float(U_V) - 1e-4, U_max_V=float(U_V) + 1e-4, U_points=2)
    if not levels.size:
        raise ValueError("log10_activity must contain at least one value")
    engine = PourbaixEngine(calculation.database)
    rows, species, pH = [], (), np.zeros(0)
    for level in levels:
        ligands = LigandActivityModel(others + (LigandActivity(ligand_id, log10_free_activity=float(level)),))
        diagram = engine.calculate(scenario.symbol, replace(base, ligand_activities=ligands),
                                   allow_incomplete=scenario.allow_incomplete,
                                   energy_policy=scenario.energy_policy, store_energies=False)
        species, pH = diagram.system.species, np.asarray(diagram.pH)
        rows.append(np.asarray(diagram.stable_species_index[0]))
    return LigandPredominance(pH, levels, float(U_V), ligand_id, species, np.vstack(rows))
