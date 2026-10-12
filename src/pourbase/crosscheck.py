"""Cross-check fixed-activity diagrams against pymatgen's Pourbaix implementation.

The species, energies and activities of a pourbase diagram are converted to pymatgen
``PourbaixEntry`` objects and evaluated on the same grid. pymatgen differs from pourbase in two
constants: it takes ΔfG°(H₂O) = -2.4583 eV (-237.190 kJ/mol) and a Nernst slope of
0.0591 V. With ``aligned=True`` both are replaced by the values pourbase uses, so any remaining
difference comes from the calculation itself. Ligand complexes are skipped: pymatgen normalizes
energies per non-H/O atom, which counts the ligand atoms in a single-metal diagram.

Requires the optional ``pymatgen`` dependency.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

import numpy as np

from .constants import FARADAY_C_MOL, GAS_CONSTANT_J_MOL_K, LN_10
from .engine import PourbaixDiagram

TIE_TOLERANCE_EV = 1e-6


@dataclass(frozen=True)
class CrossCheck:
    """Agreement between a pourbase diagram and the pymatgen evaluation of its data."""

    symbol: str
    aligned: bool
    species_compared: int
    species_skipped: tuple[str, ...]
    agreement: float
    disagreement_beyond_ties: float
    max_energy_difference_eV: float
    differing_pairs: tuple[tuple[str, str, int], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol, "aligned": self.aligned, "species_compared": self.species_compared,
            "species_skipped": list(self.species_skipped), "agreement": self.agreement,
            "disagreement_beyond_ties": self.disagreement_beyond_ties,
            "max_energy_difference_eV": self.max_energy_difference_eV,
            "differing_pairs": [list(item) for item in self.differing_pairs],
        }


@contextmanager
def _pymatgen_constants(water_eV: float | None, slope_V: float | None) -> Iterator[None]:
    import pymatgen.analysis.pourbaix_diagram as module

    saved = module.MU_H2O, module.PREFAC
    try:
        if water_eV is not None:
            module.MU_H2O = water_eV
        if slope_V is not None:
            module.PREFAC = slope_V
        yield
    finally:
        module.MU_H2O, module.PREFAC = saved


def _ion_formula(species: Any) -> str:
    charge = int(round(species.charge))
    if abs(species.charge - charge) > 1e-9:
        raise ValueError(f"fractional charge of {species.record_id}")
    return species.formula_ascii + (f"[{charge:+d}]" if charge else "(aq)")


def pymatgen_entries(diagram: PourbaixDiagram) -> tuple[list[Any], tuple[str, ...]]:
    """``(PourbaixEntry per species, record IDs skipped)`` at the activities of ``diagram``."""
    from pymatgen.analysis.phase_diagram import PDEntry
    from pymatgen.analysis.pourbaix_diagram import IonEntry, PourbaixEntry
    from pymatgen.core import Composition
    from pymatgen.core.ion import Ion

    conditions = diagram.conditions
    entries, skipped = [], []
    for species in diagram.system.species:
        if not species.is_ligand_free:
            skipped.append(species.record_id)
            continue
        energy_eV = species.gibbs_energy_J_mol / FARADAY_C_MOL
        identifiers = (species.record_id, species.species, species.formula_ascii)
        if species.is_aqueous:
            entry = PourbaixEntry(IonEntry(Ion.from_formula(_ion_formula(species)), energy_eV),
                                  entry_id=species.record_id)
            entry.concentration = 10.0 ** conditions.aqueous_activities.log10_activity_for(*identifiers)
        else:
            if species.is_gas:
                # pymatgen has no gas phase; the fugacity enters as RT ln f of a condensed entry
                log10_fugacity = conditions.gas_fugacities.log10_fugacity_for(*identifiers)
                energy_eV += GAS_CONSTANT_J_MOL_K * conditions.temperature_K * LN_10 * log10_fugacity / FARADAY_C_MOL
            entry = PourbaixEntry(PDEntry(Composition(species.formula_ascii), energy_eV),
                                  entry_id=species.record_id)
        entries.append(entry)
    return entries, tuple(skipped)


def crosscheck(diagram: Any, water_gibbs_energy_J_mol: float, aligned: bool = True) -> CrossCheck:
    """Compare the stable species and energies of ``diagram`` with pymatgen on the same grid.

    ``water_gibbs_energy_J_mol`` is the database value used by pourbase; with ``aligned`` it
    and the exact Nernst slope also go into pymatgen.
    """
    energies = getattr(diagram, "transformed_gibbs_J_mol_metal", None)
    if energies is None:
        raise ValueError("The cross-check needs a fixed-activity diagram with stored energies")
    temperature = diagram.conditions.temperature_K
    slope = GAS_CONSTANT_J_MOL_K * temperature * LN_10 / FARADAY_C_MOL
    entries, skipped = pymatgen_entries(diagram)
    included = [index for index, item in enumerate(diagram.system.species) if item.record_id not in skipped]
    pH, eh = np.meshgrid(diagram.pH, diagram.eh_V)
    with _pymatgen_constants(water_gibbs_energy_J_mol / FARADAY_C_MOL if aligned else None,
                             slope if aligned else None):
        theirs = np.stack([entry.normalized_energy_at_conditions(pH, eh) for entry in entries])
    ours = energies[included] / FARADAY_C_MOL
    our_stable = np.argmin(ours, axis=0)
    their_stable = np.argmin(theirs, axis=0)
    same = our_stable == their_stable
    # A different choice between two species within the tolerance of each other is a tie
    rows, columns = np.indices(our_stable.shape)
    gap = np.abs(ours[their_stable, rows, columns] - ours[our_stable, rows, columns])
    beyond = ~same & (gap > TIE_TOLERANCE_EV)
    ids = np.asarray([diagram.system.species[index].record_id for index in included])
    pairs: dict[tuple[str, str], int] = {}
    for a, b in zip(ids[our_stable[beyond]], ids[their_stable[beyond]], strict=True):
        pairs[(a, b)] = pairs.get((a, b), 0) + 1
    return CrossCheck(
        symbol=diagram.system.symbol,
        aligned=aligned,
        species_compared=len(entries),
        species_skipped=skipped,
        agreement=float(same.mean()),
        disagreement_beyond_ties=float(beyond.mean()),
        max_energy_difference_eV=float(np.abs(ours - theirs).max()),
        differing_pairs=tuple(sorted(((a, b, n) for (a, b), n in pairs.items()), key=lambda item: -item[2])),
    )
