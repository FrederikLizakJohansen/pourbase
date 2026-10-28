# Dataset statistics

pourbase dataset 1.0.0, generated from the bundled database by `scripts/dataset_statistics.py`. Machine-readable versions are in [`docs/statistics`](docs/statistics).

## Summary

| | |
|---|---|
| Species | 1771 |
| Supported elemental systems | 75 of 118 elements |
| Recommended Gibbs energies | 1327 (75 %) |
| Recommended entropies | 1296 (73 %) |
| Recommended formation enthalpies | 1352 (76 %) |
| Reported values retained | 5297 |
| Source records | 1839 (266 distinct citations) |
| Phase records | 1141 (491 resolved) |
| Warnings | 2755 |
| Materials Project matches | 105 phases, 299 energy rows |
| Materials Project fallback estimates | 6 |
| Ligands | 33 |

Gibbs energies by evidence status:

| Status | Species |
|---|---|
| `verified` | 925 |
| `not_available` | 438 |
| `source_verified_estimate` | 327 |
| `defined_reference_state` | 75 |
| `terminal_evidence_gap` | 6 |

Species by phase:

| Phase | Species | Gibbs | Entropy | Enthalpy |
|---|---|---|---|---|
| solid | 997 | 702 | 675 | 925 |
| aqueous | 600 | 532 | 449 | 332 |
| gas | 169 | 90 | 169 | 90 |
| liquid | 5 | 3 | 3 | 5 |

## Database tables

| Table | Rows | Contents |
|---|---|---|
| `species` | 1771 | Formula, charge, phase, composition, oxidation state and reaction coefficients |
| `selected_thermochemistry` | 1771 | Derived by the selection policy: one recommended Gibbs energy, entropy and enthalpy per species |
| `reported_thermochemistry` | 5297 | Every retained reported value, recommended or not, with supersession links |
| `sources` | 1839 | Full citations, links, locators and access dates |
| `phases` | 1141 | Phase identity, candidate polymorphs, space group and evidence |
| `warnings` | 2755 | Scientific cautions attached to records |
| `computational_fallbacks` | 6 | Opt-in Materials Project 300 K estimates for missing solid Gibbs energies |
| `materials_project_matches` | 105 | Reviewed experimental-phase to Materials Project structure matches |
| `materials_project_energies` | 299 | Method-specific Materials Project energies with provenance |
| `element_coverage` | 118 | Status of every chemical element |
| `ligands` | 33 | Free-ligand reference states for ligand-aware calculations |
| `additional_components` | 64 | Additional independent buffered references per species, beyond the first ligand |
| `metadata` | 198 | Dataset version, reference conditions, schema version and value policy |

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

The experimental Fe diagram at log₁₀ a = -6 and the official Materials Project diagram (database 2026.04.13) have the same thermodynamic species over 91 % of the grid and 89 % of the water-stability window.

## Systems

| Element | System | Species | Aqueous | Solid | Gas | Liquid | Gibbs | Entropy | Enthalpy | Warnings |
|---|---|---|---|---|---|---|---|---|---|---|
| Ag | Silver (Ag) | 31 | 14 | 14 | 3 | 0 | 26 | 28 | 26 | 54 |
| Al | Aluminum (Al) | 70 | 8 | 60 | 2 | 0 | 65 | 64 | 67 | 100 |
| As | Arsenic (As) | 17 | 7 | 9 | 1 | 0 | 15 | 14 | 16 | 26 |
| Au | Gold (Au) | 24 | 15 | 9 | 0 | 0 | 13 | 10 | 13 | 42 |
| B | Boron (B) | 14 | 3 | 8 | 3 | 0 | 10 | 12 | 12 | 18 |
| Ba | Barium (Ba) | 29 | 6 | 21 | 2 | 0 | 21 | 22 | 27 | 54 |
| Be | Beryllium (Be) | 25 | 11 | 11 | 3 | 0 | 9 | 20 | 13 | 45 |
| Bi | Bismuth (Bi) | 14 | 5 | 8 | 1 | 0 | 11 | 10 | 6 | 20 |
| Br | Bromine (Br) | 10 | 6 | 0 | 3 | 1 | 8 | 10 | 8 | 7 |
| C | Carbon (C) | 14 | 6 | 2 | 6 | 0 | 12 | 14 | 12 | 21 |
| Ca | Calcium (Ca) | 43 | 11 | 30 | 2 | 0 | 36 | 35 | 39 | 91 |
| Cd | Cadmium (Cd) | 26 | 12 | 12 | 2 | 0 | 19 | 22 | 14 | 34 |
| Ce | Cerium (Ce) | 19 | 7 | 12 | 0 | 0 | 14 | 11 | 16 | 24 |
| Cl | Chlorine (Cl) | 12 | 8 | 0 | 4 | 0 | 10 | 12 | 10 | 8 |
| Co | Cobalt (Co) | 33 | 7 | 23 | 3 | 0 | 20 | 25 | 24 | 55 |
| Cr | Chromium (Cr) | 23 | 8 | 13 | 2 | 0 | 10 | 14 | 13 | 36 |
| Cs | Caesium (Cs) | 18 | 5 | 10 | 3 | 0 | 13 | 16 | 14 | 26 |
| Cu | Copper (Cu) | 47 | 18 | 26 | 3 | 0 | 35 | 41 | 32 | 82 |
| Dy | Dysprosium (Dy) | 11 | 5 | 6 | 0 | 0 | 9 | 7 | 9 | 14 |
| Er | Erbium (Er) | 11 | 5 | 6 | 0 | 0 | 9 | 7 | 10 | 15 |
| Eu | Europium (Eu) | 18 | 7 | 11 | 0 | 0 | 15 | 11 | 14 | 22 |
| F | Fluorine (F) | 7 | 3 | 0 | 4 | 0 | 5 | 7 | 5 | 9 |
| Fe | Iron (Fe) | 127 | 39 | 85 | 3 | 0 | 102 | 89 | 85 | 182 |
| Ga | Gallium (Ga) | 16 | 6 | 8 | 2 | 0 | 11 | 14 | 9 | 27 |
| Gd | Gadolinium (Gd) | 14 | 6 | 8 | 0 | 0 | 11 | 7 | 10 | 17 |
| Ge | Germanium (Ge) | 14 | 1 | 9 | 4 | 0 | 11 | 12 | 11 | 17 |
| Hf | Hafnium (Hf) | 10 | 6 | 4 | 0 | 0 | 10 | 10 | 10 | 19 |
| Hg | Mercury (Hg) | 21 | 11 | 7 | 2 | 1 | 15 | 21 | 14 | 30 |
| Ho | Holmium (Ho) | 13 | 6 | 7 | 0 | 0 | 11 | 8 | 11 | 17 |
| I | Iodine (I) | 14 | 8 | 3 | 3 | 0 | 11 | 12 | 11 | 12 |
| In | Indium (In) | 22 | 7 | 13 | 2 | 0 | 11 | 15 | 14 | 36 |
| Ir | Iridium (Ir) | 7 | 1 | 6 | 0 | 0 | 4 | 3 | 6 | 9 |
| K | Potassium (K) | 35 | 10 | 22 | 3 | 0 | 22 | 23 | 31 | 71 |
| La | Lanthanum (La) | 17 | 5 | 12 | 0 | 0 | 12 | 10 | 13 | 22 |
| Li | Lithium (Li) | 21 | 3 | 15 | 3 | 0 | 15 | 17 | 18 | 27 |
| Lu | Lutetium (Lu) | 13 | 6 | 7 | 0 | 0 | 11 | 8 | 10 | 16 |
| Mg | Magnesium (Mg) | 50 | 11 | 37 | 2 | 0 | 45 | 43 | 44 | 90 |
| Mn | Manganese (Mn) | 39 | 11 | 26 | 2 | 0 | 29 | 32 | 32 | 62 |
| Mo | Molybdenum (Mo) | 15 | 1 | 11 | 3 | 0 | 6 | 8 | 12 | 24 |
| N | Nitrogen (N) | 11 | 5 | 1 | 5 | 0 | 9 | 10 | 10 | 24 |
| Na | Sodium (Na) | 36 | 10 | 23 | 3 | 0 | 27 | 27 | 32 | 70 |
| Nb | Niobium (Nb) | 23 | 11 | 9 | 3 | 0 | 15 | 13 | 14 | 44 |
| Nd | Neodymium (Nd) | 16 | 5 | 11 | 0 | 0 | 12 | 9 | 14 | 23 |
| Ni | Nickel (Ni) | 69 | 28 | 37 | 3 | 1 | 59 | 48 | 51 | 103 |
| Os | Osmium (Os) | 11 | 2 | 8 | 1 | 0 | 7 | 6 | 8 | 16 |
| P | Phosphorus (P) | 22 | 12 | 7 | 3 | 0 | 15 | 15 | 18 | 27 |
| Pb | Lead (Pb) | 27 | 10 | 13 | 4 | 0 | 22 | 25 | 21 | 56 |
| Pd | Palladium (Pd) | 17 | 7 | 10 | 0 | 0 | 13 | 8 | 8 | 20 |
| Pr | Praseodymium (Pr) | 16 | 7 | 9 | 0 | 0 | 10 | 5 | 11 | 23 |
| Pt | Platinum (Pt) | 17 | 1 | 16 | 0 | 0 | 4 | 5 | 13 | 33 |
| Ra | Radium (Ra) | 7 | 2 | 5 | 0 | 0 | 6 | 7 | 6 | 20 |
| Rb | Rubidium (Rb) | 18 | 6 | 9 | 3 | 0 | 11 | 14 | 14 | 29 |
| Re | Rhenium (Re) | 8 | 1 | 7 | 0 | 0 | 5 | 5 | 7 | 8 |
| Rh | Rhodium (Rh) | 10 | 6 | 4 | 0 | 0 | 9 | 8 | 9 | 15 |
| Ru | Ruthenium (Ru) | 12 | 2 | 10 | 0 | 0 | 6 | 7 | 9 | 17 |
| S | Sulfur (S) | 14 | 10 | 1 | 3 | 0 | 12 | 13 | 11 | 15 |
| Sb | Antimony (Sb) | 13 | 3 | 10 | 0 | 0 | 11 | 9 | 11 | 11 |
| Sc | Scandium (Sc) | 15 | 5 | 7 | 3 | 0 | 10 | 12 | 13 | 26 |
| Se | Selenium (Se) | 30 | 11 | 8 | 11 | 0 | 26 | 22 | 26 | 42 |
| Si | Silicon (Si) | 22 | 10 | 10 | 2 | 0 | 19 | 12 | 13 | 49 |
| Sm | Samarium (Sm) | 17 | 7 | 10 | 0 | 0 | 13 | 7 | 12 | 23 |
| Sn | Tin (Sn) | 56 | 23 | 20 | 12 | 1 | 50 | 32 | 31 | 71 |
| Sr | Strontium (Sr) | 28 | 6 | 20 | 2 | 0 | 23 | 24 | 26 | 49 |
| Ta | Tantalum (Ta) | 13 | 2 | 8 | 3 | 0 | 5 | 5 | 9 | 24 |
| Tb | Terbium (Tb) | 13 | 6 | 7 | 0 | 0 | 11 | 8 | 10 | 16 |
| Te | Tellurium (Te) | 6 | 2 | 4 | 0 | 0 | 4 | 3 | 5 | 8 |
| Ti | Titanium (Ti) | 19 | 2 | 14 | 3 | 0 | 13 | 16 | 14 | 34 |
| Tl | Thallium (Tl) | 22 | 10 | 12 | 0 | 0 | 13 | 17 | 14 | 34 |
| Tm | Thulium (Tm) | 13 | 6 | 7 | 0 | 0 | 10 | 8 | 9 | 17 |
| V | Vanadium (V) | 32 | 13 | 16 | 3 | 0 | 20 | 25 | 20 | 47 |
| W | Tungsten (W) | 14 | 1 | 10 | 3 | 0 | 6 | 8 | 11 | 27 |
| Y | Yttrium (Y) | 15 | 8 | 7 | 0 | 0 | 13 | 11 | 13 | 30 |
| Yb | Ytterbium (Yb) | 12 | 6 | 6 | 0 | 0 | 10 | 7 | 9 | 15 |
| Zn | Zinc (Zn) | 34 | 13 | 19 | 2 | 0 | 32 | 33 | 31 | 67 |
| Zr | Zirconium (Zr) | 99 | 26 | 51 | 21 | 1 | 74 | 68 | 78 | 141 |
