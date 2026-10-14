"""Water compositions as buffered ligand reservoirs, for diagrams in realistic solutions.

Each preset lists the dissolved anions that the database treats as ligands, as total unbound
concentrations. Weak acids are given one acid dissociation constant (25 °C, I = 0; Stumm and
Morgan 1996), so the free ligand follows Eq. 11; the more protonated forms of carbonate and
phosphate are not separated. Ligand activity coefficients are not applied. The ionic strength is
the one of the full composition; the Davies model (Eq. 9) applies it only up to 0.1 mol/L.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import LigandActivity

STUMM_MORGAN = "Stumm, W. and Morgan, J. J. (1996). Aquatic Chemistry, 3rd ed. Wiley, New York."

# pKa of the last proton of each weak-acid ligand at 25 °C and zero ionic strength (Stumm and Morgan 1996)
PKA = {"carbonate-co3": 10.33, "sulfate-so4": 1.99, "phosphate-po4": 12.35, "fluoride-f": 3.17}


@dataclass(frozen=True)
class WaterPreset:
    key: str
    name: str
    concentrations_mol_L: tuple[tuple[str, float], ...]  # (ligand ID, total unbound concentration)
    ionic_strength_mol_L: float
    pH: float | None
    citation: str

    @property
    def ligands(self) -> tuple[LigandActivity, ...]:
        return tuple(LigandActivity(ligand_id, total_unbound_mol_L=value, acid_pKa=PKA.get(ligand_id))
                     for ligand_id, value in self.concentrations_mol_L)


WATER_PRESETS: dict[str, WaterPreset] = {item.key: item for item in (
    WaterPreset("pure", "Pure water", (), 0.0, None, "No dissolved ligands."),
    WaterPreset(
        "seawater", "Seawater (S = 35)",
        (("chloride-cl", 0.5459), ("sulfate-so4", 0.02824), ("bromide-br", 8.42e-4),
         ("carbonate-co3", 1.97e-3), ("fluoride-f", 6.8e-5)),
        0.7227, 8.1,
        "Millero, F. J., Feistel, R., Wright, D. G. and McDougall, T. J. (2008). The composition of Standard "
        "Seawater and the definition of the Reference-Composition Salinity Scale. Deep-Sea Research I 55, 50-72. "
        "Reference composition in mol/kg, read as mol/L; carbonate is the total dissolved inorganic carbon."),
    WaterPreset(
        "river", "River water (world average)",
        (("carbonate-co3", 9.57e-4), ("sulfate-so4", 1.17e-4), ("chloride-cl", 2.20e-4), ("nitrate-no3", 1.6e-5)),
        0.0021, None,
        "Livingstone, D. A. (1963). Chemical composition of rivers and lakes. U.S. Geological Survey Professional "
        "Paper 440-G. Mean river water: HCO3- 58.4, SO4 2- 11.2, Cl- 7.8 and NO3- 1 mg/L; the ionic strength "
        "includes Ca, Mg, Na and K."),
    WaterPreset(
        "sbf", "Simulated body fluid",
        (("chloride-cl", 0.1478), ("carbonate-co3", 4.2e-3), ("phosphate-po4", 1.0e-3), ("sulfate-so4", 5.0e-4)),
        0.1605, 7.40,
        "Kokubo, T. and Takadama, H. (2006). How useful is SBF in predicting in vivo bone bioactivity? "
        "Biomaterials 27, 2907-2915. Ion concentrations in mmol/L: Cl- 147.8, HCO3- 4.2, HPO4 2- 1.0, SO4 2- 0.5."),
    WaterPreset("saline", "Saline, 0.9 % NaCl", (("chloride-cl", 0.154),), 0.154, None,
                "9 g/L NaCl (58.44 g/mol): 0.154 mol/L chloride."),
)}
