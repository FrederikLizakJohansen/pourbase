# Dataset statistics

pourbase dataset 1.0.0, generated from the bundled database by `scripts/dataset_statistics.py`. Machine-readable versions are in [`docs/statistics`](docs/statistics).

## Summary

| | |
|---|---|
| Species | 1296 |
| Supported elemental systems | 75 of 118 elements |
| Recommended Gibbs energies | 1080 (83 %) |
| Recommended entropies | 1057 (82 %) |
| Recommended formation enthalpies | 869 (67 %) |
| Reported values retained | 3974 |
| Source records | 1783 (224 distinct citations) |
| Phase records | 697 (463 resolved) |
| Warnings | 1877 |
| Materials Project matches | 105 phases, 299 energy rows |
| Materials Project fallback estimates | 6 |
| Ligands | 30 |

Gibbs energies by evidence status:

| Status | Species |
|---|---|
| `verified` | 679 |
| `source_verified_estimate` | 326 |
| `not_available` | 210 |
| `defined_reference_state` | 75 |
| `terminal_evidence_gap` | 6 |

Species by phase:

| Phase | Species | Gibbs | Entropy | Enthalpy |
|---|---|---|---|---|
| aqueous | 571 | 503 | 431 | 310 |
| solid | 553 | 486 | 456 | 466 |
| gas | 167 | 88 | 167 | 88 |
| liquid | 5 | 3 | 3 | 5 |

## Database tables

| Table | Rows | Contents |
|---|---|---|
| `species` | 1296 | Formula, charge, phase, composition, oxidation state and reaction coefficients |
| `selected_thermochemistry` | 1296 | Derived by the selection policy: one recommended Gibbs energy, entropy and enthalpy per species |
| `reported_thermochemistry` | 3974 | Every retained reported value, recommended or not, with supersession links |
| `sources` | 1783 | Full citations, links, locators and access dates |
| `phases` | 697 | Phase identity, candidate polymorphs, space group and evidence |
| `warnings` | 1877 | Scientific cautions attached to records |
| `computational_fallbacks` | 6 | Opt-in Materials Project 300 K estimates for missing solid Gibbs energies |
| `materials_project_matches` | 105 | Reviewed experimental-phase to Materials Project structure matches |
| `materials_project_energies` | 299 | Method-specific Materials Project energies with provenance |
| `element_coverage` | 118 | Status of every chemical element |
| `ligands` | 30 | Free-ligand reference states for ligand-aware calculations |
| `additional_components` | 58 | Additional independent buffered references per species, beyond the first ligand |
| `metadata` | 84 | Dataset version, reference conditions, schema version and value policy |

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
| Ag | Silver (Ag) | 24 | 12 | 9 | 3 | 0 | 21 | 23 | 18 | 44 |
| Al | Aluminum (Al) | 63 | 8 | 53 | 2 | 0 | 61 | 60 | 58 | 84 |
| As | Arsenic (As) | 11 | 7 | 4 | 0 | 0 | 11 | 10 | 10 | 5 |
| Au | Gold (Au) | 15 | 13 | 2 | 0 | 0 | 11 | 8 | 3 | 24 |
| B | Boron (B) | 8 | 3 | 2 | 3 | 0 | 6 | 8 | 6 | 7 |
| Ba | Barium (Ba) | 14 | 6 | 6 | 2 | 0 | 13 | 14 | 11 | 27 |
| Be | Beryllium (Be) | 18 | 11 | 4 | 3 | 0 | 7 | 18 | 5 | 33 |
| Bi | Bismuth (Bi) | 10 | 5 | 4 | 1 | 0 | 7 | 7 | 3 | 16 |
| Br | Bromine (Br) | 10 | 6 | 0 | 3 | 1 | 8 | 10 | 8 | 6 |
| C | Carbon (C) | 12 | 6 | 1 | 5 | 0 | 10 | 12 | 10 | 17 |
| Ca | Calcium (Ca) | 35 | 11 | 22 | 2 | 0 | 29 | 28 | 30 | 71 |
| Cd | Cadmium (Cd) | 18 | 12 | 4 | 2 | 0 | 11 | 14 | 6 | 26 |
| Ce | Cerium (Ce) | 13 | 7 | 6 | 0 | 0 | 12 | 9 | 10 | 14 |
| Cl | Chlorine (Cl) | 12 | 8 | 0 | 4 | 0 | 10 | 12 | 10 | 7 |
| Co | Cobalt (Co) | 20 | 7 | 10 | 3 | 0 | 14 | 19 | 10 | 33 |
| Cr | Chromium (Cr) | 12 | 8 | 2 | 2 | 0 | 7 | 11 | 1 | 16 |
| Cs | Caesium (Cs) | 9 | 5 | 1 | 3 | 0 | 6 | 9 | 4 | 15 |
| Cu | Copper (Cu) | 34 | 16 | 15 | 3 | 0 | 25 | 32 | 19 | 60 |
| Dy | Dysprosium (Dy) | 8 | 5 | 3 | 0 | 0 | 8 | 6 | 6 | 9 |
| Er | Erbium (Er) | 8 | 5 | 3 | 0 | 0 | 8 | 6 | 7 | 10 |
| Eu | Europium (Eu) | 15 | 7 | 8 | 0 | 0 | 14 | 10 | 11 | 17 |
| F | Fluorine (F) | 7 | 3 | 0 | 4 | 0 | 5 | 7 | 5 | 7 |
| Fe | Iron (Fe) | 88 | 29 | 56 | 3 | 0 | 72 | 65 | 59 | 114 |
| Ga | Gallium (Ga) | 12 | 6 | 4 | 2 | 0 | 8 | 11 | 4 | 22 |
| Gd | Gadolinium (Gd) | 11 | 6 | 5 | 0 | 0 | 10 | 6 | 7 | 12 |
| Ge | Germanium (Ge) | 10 | 1 | 5 | 4 | 0 | 8 | 9 | 7 | 12 |
| Hf | Hafnium (Hf) | 8 | 6 | 2 | 0 | 0 | 8 | 8 | 8 | 17 |
| Hg | Mercury (Hg) | 16 | 11 | 2 | 2 | 1 | 10 | 16 | 9 | 25 |
| Ho | Holmium (Ho) | 10 | 6 | 4 | 0 | 0 | 10 | 7 | 8 | 12 |
| I | Iodine (I) | 12 | 8 | 1 | 3 | 0 | 10 | 11 | 9 | 8 |
| In | Indium (In) | 13 | 7 | 4 | 2 | 0 | 7 | 11 | 4 | 22 |
| Ir | Iridium (Ir) | 3 | 1 | 2 | 0 | 0 | 3 | 2 | 2 | 2 |
| K | Potassium (K) | 18 | 10 | 5 | 3 | 0 | 16 | 17 | 13 | 41 |
| La | Lanthanum (La) | 12 | 5 | 7 | 0 | 0 | 10 | 8 | 8 | 14 |
| Li | Lithium (Li) | 7 | 3 | 1 | 3 | 0 | 5 | 7 | 3 | 9 |
| Lu | Lutetium (Lu) | 10 | 6 | 4 | 0 | 0 | 10 | 7 | 7 | 11 |
| Mg | Magnesium (Mg) | 41 | 10 | 29 | 2 | 0 | 37 | 35 | 34 | 73 |
| Mn | Manganese (Mn) | 28 | 11 | 15 | 2 | 0 | 24 | 26 | 21 | 45 |
| Mo | Molybdenum (Mo) | 8 | 1 | 4 | 3 | 0 | 6 | 8 | 4 | 9 |
| N | Nitrogen (N) | 10 | 5 | 0 | 5 | 0 | 9 | 10 | 9 | 24 |
| Na | Sodium (Na) | 20 | 10 | 7 | 3 | 0 | 17 | 18 | 14 | 43 |
| Nb | Niobium (Nb) | 18 | 11 | 4 | 3 | 0 | 13 | 11 | 9 | 36 |
| Nd | Neodymium (Nd) | 11 | 5 | 6 | 0 | 0 | 10 | 7 | 9 | 15 |
| Ni | Nickel (Ni) | 65 | 28 | 33 | 3 | 1 | 58 | 48 | 47 | 85 |
| Os | Osmium (Os) | 7 | 2 | 4 | 1 | 0 | 7 | 5 | 5 | 8 |
| P | Phosphorus (P) | 14 | 9 | 2 | 3 | 0 | 12 | 12 | 10 | 10 |
| Pb | Lead (Pb) | 24 | 10 | 10 | 4 | 0 | 20 | 23 | 17 | 52 |
| Pd | Palladium (Pd) | 11 | 7 | 4 | 0 | 0 | 9 | 4 | 1 | 11 |
| Pr | Praseodymium (Pr) | 12 | 7 | 5 | 0 | 0 | 10 | 5 | 7 | 15 |
| Pt | Platinum (Pt) | 4 | 1 | 3 | 0 | 0 | 2 | 2 | 0 | 9 |
| Ra | Radium (Ra) | 5 | 2 | 3 | 0 | 0 | 5 | 5 | 5 | 16 |
| Rb | Rubidium (Rb) | 10 | 6 | 1 | 3 | 0 | 7 | 10 | 5 | 17 |
| Re | Rhenium (Re) | 4 | 1 | 3 | 0 | 0 | 4 | 4 | 2 | 0 |
| Rh | Rhodium (Rh) | 9 | 6 | 3 | 0 | 0 | 9 | 8 | 8 | 13 |
| Ru | Ruthenium (Ru) | 7 | 2 | 5 | 0 | 0 | 6 | 7 | 3 | 7 |
| S | Sulfur (S) | 13 | 9 | 1 | 3 | 0 | 11 | 12 | 10 | 10 |
| Sb | Antimony (Sb) | 8 | 3 | 5 | 0 | 0 | 8 | 6 | 6 | 4 |
| Sc | Scandium (Sc) | 11 | 5 | 3 | 3 | 0 | 9 | 11 | 9 | 19 |
| Se | Selenium (Se) | 29 | 11 | 7 | 11 | 0 | 26 | 22 | 25 | 40 |
| Si | Silicon (Si) | 12 | 5 | 5 | 2 | 0 | 11 | 9 | 8 | 20 |
| Sm | Samarium (Sm) | 13 | 7 | 6 | 0 | 0 | 12 | 6 | 8 | 16 |
| Sn | Tin (Sn) | 55 | 23 | 19 | 12 | 1 | 50 | 32 | 29 | 58 |
| Sr | Strontium (Sr) | 13 | 6 | 5 | 2 | 0 | 12 | 13 | 10 | 24 |
| Ta | Tantalum (Ta) | 7 | 2 | 2 | 3 | 0 | 5 | 5 | 2 | 12 |
| Tb | Terbium (Tb) | 11 | 6 | 5 | 0 | 0 | 10 | 7 | 8 | 13 |
| Te | Tellurium (Te) | 4 | 2 | 2 | 0 | 0 | 4 | 3 | 3 | 2 |
| Ti | Titanium (Ti) | 10 | 2 | 5 | 3 | 0 | 8 | 10 | 5 | 21 |
| Tl | Thallium (Tl) | 14 | 10 | 4 | 0 | 0 | 9 | 13 | 6 | 20 |
| Tm | Thulium (Tm) | 10 | 6 | 4 | 0 | 0 | 10 | 7 | 7 | 11 |
| V | Vanadium (V) | 21 | 13 | 5 | 3 | 0 | 15 | 19 | 8 | 24 |
| W | Tungsten (W) | 8 | 1 | 4 | 3 | 0 | 6 | 8 | 4 | 13 |
| Y | Yttrium (Y) | 11 | 8 | 3 | 0 | 0 | 11 | 9 | 9 | 24 |
| Yb | Ytterbium (Yb) | 9 | 6 | 3 | 0 | 0 | 9 | 6 | 6 | 10 |
| Zn | Zinc (Zn) | 26 | 10 | 14 | 2 | 0 | 24 | 25 | 21 | 55 |
| Zr | Zirconium (Zr) | 97 | 26 | 49 | 21 | 1 | 74 | 68 | 76 | 124 |
