# Dataset statistics

pourbase dataset 1.0.0, generated from the bundled database by `scripts/dataset_statistics.py`. Machine-readable versions are in [`docs/statistics`](docs/statistics).

## Summary

| | |
|---|---|
| Species | 490 |
| Supported elemental systems | 74 of 118 elements |
| Recommended Gibbs energies | 484 (99 %) |
| Recommended entropies | 413 (84 %) |
| Recommended formation enthalpies | 312 (64 %) |
| Reported values retained | 1622 |
| Source records | 633 (86 distinct citations) |
| Phase records | 156 (118 resolved) |
| Warnings | 356 |
| Materials Project matches | 105 phases, 299 energy rows |
| Materials Project fallback estimates | 6 |
| Ligands | 6 |

Gibbs energies by evidence status:

| Status | Species |
|---|---|
| `verified` | 328 |
| `source_verified_estimate` | 82 |
| `defined_reference_state` | 74 |
| `terminal_evidence_gap` | 6 |

Species by phase:

| Phase | Species | Gibbs | Entropy | Enthalpy |
|---|---|---|---|---|
| aqueous | 285 | 285 | 221 | 152 |
| solid | 194 | 188 | 181 | 149 |
| gas | 9 | 9 | 9 | 9 |
| liquid | 2 | 2 | 2 | 2 |

## Database tables

| Table | Rows | Contents |
|---|---|---|
| `species` | 490 | Formula, charge, phase, composition, oxidation state and reaction coefficients |
| `thermochemistry` | 490 | One recommended Gibbs energy, entropy and enthalpy per species |
| `reported_thermochemistry` | 1622 | Every retained reported value, recommended or not, with supersession links |
| `sources` | 633 | Full citations, links, locators and access dates |
| `phases` | 156 | Phase identity, candidate polymorphs, space group and evidence |
| `warnings` | 356 | Scientific cautions attached to records |
| `computational_fallbacks` | 6 | Opt-in Materials Project 300 K estimates for missing solid Gibbs energies |
| `materials_project_matches` | 105 | Reviewed experimental-phase to Materials Project structure matches |
| `materials_project_energies` | 299 | Method-specific Materials Project energies with provenance |
| `element_coverage` | 118 | Status of every chemical element |
| `ligands` | 6 | Free-ligand reference states for ligand-aware calculations |
| `metadata` | 9 | Dataset version, reference conditions, schema version and value policy |

[`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) defines every column, unit and join.

## Coverage

![Dataset overview](docs/statistics/dataset-overview.png)

Elemental coverage, species by phase, property availability and evidence status.

## Comparison with Materials Project

![Experimental and Materials Project formation energies](docs/statistics/mp-thermochemistry.png)

Phase-matched experimental formation energies against Materials Project DFT formation energies (database 2026.04.13). Mean absolute differences, in eV per atom:

| Method | Enthalpy (n) | Enthalpy MAE | Gibbs (n) | Gibbs MAE |
|---|---|---|---|---|
| GGA_GGA+U | 99 | 0.155 | 103 | 0.307 |
| GGA_GGA+U_R2SCAN | 99 | 0.151 | 103 | 0.307 |
| r2SCAN | 90 | 0.085 | 93 | 0.171 |

The enthalpy is the closest comparison with a 0 K DFT formation energy; the Gibbs difference also includes finite-temperature entropy. These differences are diagnostics, not experimental error estimates.

## Example: the iron system

![Iron Pourbaix diagram compared with Materials Project](docs/statistics/calculation-showcase.png)

The experimental Fe diagram at log₁₀ a = -6 and the official Materials Project diagram (database 2026.04.13) have the same thermodynamic species over 90 % of the grid and 86 % of the water-stability window.

## Systems

| Element | System | Species | Aqueous | Solid | Gas | Liquid | Gibbs | Entropy | Enthalpy | Warnings |
|---|---|---|---|---|---|---|---|---|---|---|
| Ag | Silver (Ag) | 14 | 6 | 8 | 0 | 0 | 14 | 13 | 11 | 13 |
| Al | Aluminum (Al) | 8 | 5 | 3 | 0 | 0 | 8 | 5 | 2 | 7 |
| As | Arsenic (As) | 12 | 9 | 3 | 0 | 0 | 12 | 11 | 11 | 1 |
| Au | Gold (Au) | 12 | 10 | 2 | 0 | 0 | 11 | 5 | 3 | 17 |
| B | Boron (B) | 6 | 4 | 2 | 0 | 0 | 6 | 6 | 6 | 0 |
| Ba | Barium (Ba) | 4 | 2 | 2 | 0 | 0 | 4 | 3 | 1 | 2 |
| Be | Beryllium (Be) | 5 | 2 | 3 | 0 | 0 | 5 | 5 | 3 | 4 |
| Bi | Bismuth (Bi) | 6 | 3 | 3 | 0 | 0 | 6 | 2 | 2 | 5 |
| Br | Bromine (Br) | 7 | 6 | 0 | 0 | 1 | 7 | 7 | 7 | 0 |
| C | Carbon (C) | 7 | 4 | 1 | 2 | 0 | 7 | 7 | 7 | 7 |
| Ca | Calcium (Ca) | 8 | 6 | 2 | 0 | 0 | 8 | 7 | 1 | 10 |
| Cd | Cadmium (Cd) | 10 | 7 | 3 | 0 | 0 | 10 | 4 | 4 | 6 |
| Ce | Cerium (Ce) | 5 | 2 | 3 | 0 | 0 | 5 | 5 | 5 | 0 |
| Cl | Chlorine (Cl) | 9 | 8 | 0 | 1 | 0 | 9 | 9 | 9 | 1 |
| Co | Cobalt (Co) | 7 | 2 | 5 | 0 | 0 | 7 | 6 | 3 | 6 |
| Cr | Chromium (Cr) | 7 | 5 | 2 | 0 | 0 | 7 | 6 | 1 | 3 |
| Cs | Caesium (Cs) | 2 | 1 | 1 | 0 | 0 | 2 | 2 | 0 | 1 |
| Cu | Copper (Cu) | 13 | 9 | 4 | 0 | 0 | 13 | 13 | 9 | 21 |
| Dy | Dysprosium (Dy) | 3 | 1 | 2 | 0 | 0 | 3 | 3 | 3 | 0 |
| Er | Erbium (Er) | 3 | 1 | 2 | 0 | 0 | 3 | 3 | 3 | 0 |
| Eu | Europium (Eu) | 7 | 2 | 5 | 0 | 0 | 7 | 7 | 7 | 0 |
| F | Fluorine (F) | 4 | 3 | 0 | 1 | 0 | 4 | 4 | 4 | 1 |
| Fe | Iron (Fe) | 14 | 9 | 5 | 0 | 0 | 14 | 11 | 4 | 10 |
| Ga | Gallium (Ga) | 7 | 4 | 3 | 0 | 0 | 7 | 6 | 2 | 5 |
| Gd | Gadolinium (Gd) | 3 | 1 | 2 | 0 | 0 | 3 | 3 | 3 | 0 |
| Ge | Germanium (Ge) | 4 | 1 | 3 | 0 | 0 | 4 | 3 | 3 | 2 |
| Hf | Hafnium (Hf) | 8 | 6 | 2 | 0 | 0 | 8 | 8 | 8 | 12 |
| Hg | Mercury (Hg) | 9 | 6 | 1 | 1 | 1 | 9 | 8 | 8 | 6 |
| Ho | Holmium (Ho) | 3 | 1 | 2 | 0 | 0 | 3 | 3 | 3 | 0 |
| I | Iodine (I) | 9 | 8 | 1 | 0 | 0 | 9 | 8 | 8 | 1 |
| In | Indium (In) | 7 | 4 | 3 | 0 | 0 | 6 | 5 | 2 | 7 |
| Ir | Iridium (Ir) | 3 | 1 | 2 | 0 | 0 | 3 | 2 | 2 | 2 |
| K | Potassium (K) | 7 | 5 | 2 | 0 | 0 | 7 | 5 | 1 | 7 |
| La | Lanthanum (La) | 4 | 1 | 3 | 0 | 0 | 4 | 4 | 4 | 0 |
| Li | Lithium (Li) | 3 | 2 | 1 | 0 | 0 | 3 | 3 | 1 | 1 |
| Lu | Lutetium (Lu) | 3 | 1 | 2 | 0 | 0 | 3 | 3 | 3 | 0 |
| Mg | Magnesium (Mg) | 8 | 6 | 2 | 0 | 0 | 8 | 7 | 1 | 9 |
| Mn | Manganese (Mn) | 10 | 5 | 5 | 0 | 0 | 10 | 9 | 6 | 7 |
| Mo | Molybdenum (Mo) | 4 | 1 | 3 | 0 | 0 | 4 | 4 | 2 | 1 |
| N | Nitrogen (N) | 8 | 5 | 0 | 3 | 0 | 8 | 8 | 8 | 16 |
| Na | Sodium (Na) | 6 | 5 | 1 | 0 | 0 | 6 | 4 | 0 | 6 |
| Nb | Niobium (Nb) | 7 | 4 | 3 | 0 | 0 | 7 | 4 | 4 | 5 |
| Nd | Neodymium (Nd) | 4 | 1 | 3 | 0 | 0 | 4 | 4 | 4 | 0 |
| Ni | Nickel (Ni) | 7 | 2 | 5 | 0 | 0 | 6 | 5 | 2 | 8 |
| Os | Osmium (Os) | 8 | 3 | 4 | 1 | 0 | 8 | 5 | 5 | 8 |
| P | Phosphorus (P) | 9 | 7 | 2 | 0 | 0 | 9 | 7 | 7 | 2 |
| Pb | Lead (Pb) | 10 | 3 | 7 | 0 | 0 | 10 | 9 | 6 | 7 |
| Pd | Palladium (Pd) | 4 | 1 | 3 | 0 | 0 | 3 | 3 | 1 | 4 |
| Pr | Praseodymium (Pr) | 5 | 3 | 2 | 0 | 0 | 5 | 2 | 2 | 3 |
| Pt | Platinum (Pt) | 4 | 1 | 3 | 0 | 0 | 2 | 2 | 0 | 9 |
| Rb | Rubidium (Rb) | 2 | 1 | 1 | 0 | 0 | 2 | 2 | 0 | 1 |
| Re | Rhenium (Re) | 4 | 1 | 3 | 0 | 0 | 4 | 4 | 2 | 0 |
| Rh | Rhodium (Rh) | 9 | 6 | 3 | 0 | 0 | 9 | 8 | 8 | 13 |
| Ru | Ruthenium (Ru) | 5 | 2 | 3 | 0 | 0 | 5 | 5 | 2 | 5 |
| S | Sulfur (S) | 10 | 9 | 1 | 0 | 0 | 10 | 9 | 9 | 2 |
| Sb | Antimony (Sb) | 8 | 4 | 4 | 0 | 0 | 8 | 6 | 6 | 2 |
| Sc | Scandium (Sc) | 8 | 5 | 3 | 0 | 0 | 8 | 8 | 8 | 10 |
| Se | Selenium (Se) | 7 | 6 | 1 | 0 | 0 | 7 | 7 | 7 | 0 |
| Si | Silicon (Si) | 5 | 3 | 2 | 0 | 0 | 5 | 4 | 4 | 1 |
| Sm | Samarium (Sm) | 4 | 2 | 2 | 0 | 0 | 4 | 3 | 3 | 1 |
| Sn | Tin (Sn) | 7 | 4 | 3 | 0 | 0 | 7 | 5 | 3 | 5 |
| Sr | Strontium (Sr) | 4 | 2 | 2 | 0 | 0 | 4 | 3 | 1 | 2 |
| Ta | Tantalum (Ta) | 4 | 2 | 2 | 0 | 0 | 4 | 2 | 1 | 6 |
| Tb | Terbium (Tb) | 3 | 1 | 2 | 0 | 0 | 3 | 3 | 3 | 0 |
| Te | Tellurium (Te) | 4 | 2 | 2 | 0 | 0 | 4 | 3 | 3 | 2 |
| Ti | Titanium (Ti) | 7 | 2 | 5 | 0 | 0 | 7 | 7 | 4 | 9 |
| Tl | Thallium (Tl) | 9 | 5 | 4 | 0 | 0 | 9 | 6 | 6 | 3 |
| Tm | Thulium (Tm) | 3 | 1 | 2 | 0 | 0 | 3 | 3 | 3 | 0 |
| V | Vanadium (V) | 14 | 9 | 5 | 0 | 0 | 14 | 12 | 7 | 5 |
| W | Tungsten (W) | 4 | 1 | 3 | 0 | 0 | 4 | 4 | 2 | 5 |
| Y | Yttrium (Y) | 7 | 5 | 2 | 0 | 0 | 7 | 7 | 7 | 10 |
| Yb | Ytterbium (Yb) | 4 | 2 | 2 | 0 | 0 | 4 | 3 | 3 | 1 |
| Zn | Zinc (Zn) | 12 | 9 | 3 | 0 | 0 | 12 | 12 | 9 | 18 |
| Zr | Zirconium (Zr) | 9 | 6 | 3 | 0 | 0 | 9 | 9 | 9 | 12 |
