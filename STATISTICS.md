# Dataset statistics

pourbase dataset 1.0.0, generated from the bundled database by `scripts/dataset_statistics.py`. Machine-readable versions are in [`docs/statistics`](docs/statistics).

## Summary

| | |
|---|---|
| Species | 1455 |
| Supported elemental systems | 75 of 118 elements |
| Recommended Gibbs energies | 1168 (80 %) |
| Recommended entropies | 1141 (78 %) |
| Recommended formation enthalpies | 1026 (71 %) |
| Reported values retained | 4448 |
| Source records | 1795 (236 distinct citations) |
| Phase records | 841 (479 resolved) |
| Warnings | 2186 |
| Materials Project matches | 105 phases, 299 energy rows |
| Materials Project fallback estimates | 6 |
| Ligands | 30 |

Gibbs energies by evidence status:

| Status | Species |
|---|---|
| `verified` | 765 |
| `source_verified_estimate` | 328 |
| `not_available` | 281 |
| `defined_reference_state` | 75 |
| `terminal_evidence_gap` | 6 |

Species by phase:

| Phase | Species | Gibbs | Entropy | Enthalpy |
|---|---|---|---|---|
| solid | 697 | 559 | 530 | 610 |
| aqueous | 586 | 518 | 441 | 323 |
| gas | 167 | 88 | 167 | 88 |
| liquid | 5 | 3 | 3 | 5 |

## Database tables

| Table | Rows | Contents |
|---|---|---|
| `species` | 1455 | Formula, charge, phase, composition, oxidation state and reaction coefficients |
| `selected_thermochemistry` | 1455 | Derived by the selection policy: one recommended Gibbs energy, entropy and enthalpy per species |
| `reported_thermochemistry` | 4448 | Every retained reported value, recommended or not, with supersession links |
| `sources` | 1795 | Full citations, links, locators and access dates |
| `phases` | 841 | Phase identity, candidate polymorphs, space group and evidence |
| `warnings` | 2186 | Scientific cautions attached to records |
| `computational_fallbacks` | 6 | Opt-in Materials Project 300 K estimates for missing solid Gibbs energies |
| `materials_project_matches` | 105 | Reviewed experimental-phase to Materials Project structure matches |
| `materials_project_energies` | 299 | Method-specific Materials Project energies with provenance |
| `element_coverage` | 118 | Status of every chemical element |
| `ligands` | 30 | Free-ligand reference states for ligand-aware calculations |
| `additional_components` | 59 | Additional independent buffered references per species, beyond the first ligand |
| `metadata` | 113 | Dataset version, reference conditions, schema version and value policy |

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
| Ag | Silver (Ag) | 26 | 14 | 9 | 3 | 0 | 23 | 25 | 20 | 47 |
| Al | Aluminum (Al) | 66 | 8 | 56 | 2 | 0 | 63 | 62 | 62 | 94 |
| As | Arsenic (As) | 11 | 7 | 4 | 0 | 0 | 11 | 10 | 10 | 5 |
| Au | Gold (Au) | 20 | 15 | 5 | 0 | 0 | 13 | 10 | 8 | 34 |
| B | Boron (B) | 11 | 3 | 5 | 3 | 0 | 8 | 10 | 9 | 12 |
| Ba | Barium (Ba) | 19 | 6 | 11 | 2 | 0 | 17 | 18 | 16 | 34 |
| Be | Beryllium (Be) | 20 | 11 | 6 | 3 | 0 | 8 | 19 | 7 | 36 |
| Bi | Bismuth (Bi) | 12 | 5 | 6 | 1 | 0 | 9 | 9 | 5 | 18 |
| Br | Bromine (Br) | 10 | 6 | 0 | 3 | 1 | 8 | 10 | 8 | 6 |
| C | Carbon (C) | 12 | 6 | 1 | 5 | 0 | 10 | 12 | 10 | 17 |
| Ca | Calcium (Ca) | 37 | 11 | 24 | 2 | 0 | 31 | 30 | 32 | 84 |
| Cd | Cadmium (Cd) | 21 | 12 | 7 | 2 | 0 | 14 | 17 | 9 | 29 |
| Ce | Cerium (Ce) | 15 | 7 | 8 | 0 | 0 | 13 | 10 | 12 | 17 |
| Cl | Chlorine (Cl) | 12 | 8 | 0 | 4 | 0 | 10 | 12 | 10 | 7 |
| Co | Cobalt (Co) | 24 | 7 | 14 | 3 | 0 | 17 | 22 | 14 | 38 |
| Cr | Chromium (Cr) | 17 | 8 | 7 | 2 | 0 | 9 | 13 | 6 | 24 |
| Cs | Caesium (Cs) | 10 | 5 | 2 | 3 | 0 | 7 | 10 | 5 | 16 |
| Cu | Copper (Cu) | 39 | 18 | 18 | 3 | 0 | 30 | 37 | 24 | 66 |
| Dy | Dysprosium (Dy) | 10 | 5 | 5 | 0 | 0 | 9 | 7 | 8 | 12 |
| Er | Erbium (Er) | 10 | 5 | 5 | 0 | 0 | 9 | 7 | 9 | 13 |
| Eu | Europium (Eu) | 18 | 7 | 11 | 0 | 0 | 15 | 11 | 14 | 22 |
| F | Fluorine (F) | 7 | 3 | 0 | 4 | 0 | 5 | 7 | 5 | 7 |
| Fe | Iron (Fe) | 88 | 29 | 56 | 3 | 0 | 72 | 65 | 60 | 122 |
| Ga | Gallium (Ga) | 13 | 6 | 5 | 2 | 0 | 9 | 12 | 5 | 23 |
| Gd | Gadolinium (Gd) | 13 | 6 | 7 | 0 | 0 | 11 | 7 | 9 | 15 |
| Ge | Germanium (Ge) | 10 | 1 | 5 | 4 | 0 | 8 | 9 | 7 | 12 |
| Hf | Hafnium (Hf) | 9 | 6 | 3 | 0 | 0 | 9 | 9 | 9 | 18 |
| Hg | Mercury (Hg) | 17 | 11 | 3 | 2 | 1 | 11 | 17 | 10 | 26 |
| Ho | Holmium (Ho) | 12 | 6 | 6 | 0 | 0 | 11 | 8 | 10 | 15 |
| I | Iodine (I) | 13 | 8 | 2 | 3 | 0 | 11 | 12 | 10 | 9 |
| In | Indium (In) | 15 | 7 | 6 | 2 | 0 | 7 | 11 | 6 | 26 |
| Ir | Iridium (Ir) | 5 | 1 | 4 | 0 | 0 | 3 | 2 | 4 | 6 |
| K | Potassium (K) | 20 | 10 | 7 | 3 | 0 | 17 | 18 | 15 | 44 |
| La | Lanthanum (La) | 14 | 5 | 9 | 0 | 0 | 11 | 9 | 10 | 17 |
| Li | Lithium (Li) | 11 | 3 | 5 | 3 | 0 | 7 | 9 | 7 | 15 |
| Lu | Lutetium (Lu) | 12 | 6 | 6 | 0 | 0 | 11 | 8 | 9 | 14 |
| Mg | Magnesium (Mg) | 45 | 11 | 32 | 2 | 0 | 40 | 38 | 38 | 85 |
| Mn | Manganese (Mn) | 32 | 11 | 19 | 2 | 0 | 28 | 30 | 25 | 49 |
| Mo | Molybdenum (Mo) | 12 | 1 | 8 | 3 | 0 | 6 | 8 | 8 | 17 |
| N | Nitrogen (N) | 10 | 5 | 0 | 5 | 0 | 9 | 10 | 9 | 24 |
| Na | Sodium (Na) | 22 | 10 | 9 | 3 | 0 | 20 | 20 | 17 | 46 |
| Nb | Niobium (Nb) | 20 | 11 | 6 | 3 | 0 | 14 | 12 | 11 | 39 |
| Nd | Neodymium (Nd) | 14 | 5 | 9 | 0 | 0 | 11 | 8 | 12 | 20 |
| Ni | Nickel (Ni) | 65 | 28 | 33 | 3 | 1 | 58 | 48 | 47 | 89 |
| Os | Osmium (Os) | 9 | 2 | 6 | 1 | 0 | 7 | 5 | 7 | 12 |
| P | Phosphorus (P) | 15 | 9 | 3 | 3 | 0 | 12 | 12 | 11 | 14 |
| Pb | Lead (Pb) | 24 | 10 | 10 | 4 | 0 | 20 | 23 | 17 | 52 |
| Pd | Palladium (Pd) | 12 | 7 | 5 | 0 | 0 | 9 | 4 | 2 | 13 |
| Pr | Praseodymium (Pr) | 15 | 7 | 8 | 0 | 0 | 10 | 5 | 10 | 21 |
| Pt | Platinum (Pt) | 9 | 1 | 8 | 0 | 0 | 2 | 2 | 5 | 19 |
| Ra | Radium (Ra) | 7 | 2 | 5 | 0 | 0 | 6 | 7 | 6 | 20 |
| Rb | Rubidium (Rb) | 11 | 6 | 2 | 3 | 0 | 8 | 11 | 6 | 18 |
| Re | Rhenium (Re) | 6 | 1 | 5 | 0 | 0 | 5 | 5 | 4 | 4 |
| Rh | Rhodium (Rh) | 10 | 6 | 4 | 0 | 0 | 9 | 8 | 9 | 15 |
| Ru | Ruthenium (Ru) | 8 | 2 | 6 | 0 | 0 | 6 | 7 | 4 | 9 |
| S | Sulfur (S) | 13 | 9 | 1 | 3 | 0 | 11 | 12 | 10 | 10 |
| Sb | Antimony (Sb) | 9 | 3 | 6 | 0 | 0 | 9 | 7 | 7 | 5 |
| Sc | Scandium (Sc) | 13 | 5 | 5 | 3 | 0 | 9 | 11 | 11 | 23 |
| Se | Selenium (Se) | 30 | 11 | 8 | 11 | 0 | 26 | 22 | 26 | 42 |
| Si | Silicon (Si) | 20 | 10 | 8 | 2 | 0 | 19 | 12 | 11 | 45 |
| Sm | Samarium (Sm) | 16 | 7 | 9 | 0 | 0 | 13 | 7 | 11 | 21 |
| Sn | Tin (Sn) | 55 | 23 | 19 | 12 | 1 | 50 | 32 | 29 | 62 |
| Sr | Strontium (Sr) | 18 | 6 | 10 | 2 | 0 | 17 | 18 | 15 | 30 |
| Ta | Tantalum (Ta) | 10 | 2 | 5 | 3 | 0 | 5 | 5 | 5 | 18 |
| Tb | Terbium (Tb) | 13 | 6 | 7 | 0 | 0 | 11 | 8 | 10 | 16 |
| Te | Tellurium (Te) | 5 | 2 | 3 | 0 | 0 | 4 | 3 | 4 | 4 |
| Ti | Titanium (Ti) | 12 | 2 | 7 | 3 | 0 | 10 | 12 | 7 | 23 |
| Tl | Thallium (Tl) | 17 | 10 | 7 | 0 | 0 | 10 | 14 | 9 | 25 |
| Tm | Thulium (Tm) | 12 | 6 | 6 | 0 | 0 | 10 | 8 | 8 | 15 |
| V | Vanadium (V) | 23 | 13 | 7 | 3 | 0 | 17 | 21 | 11 | 28 |
| W | Tungsten (W) | 12 | 1 | 8 | 3 | 0 | 6 | 8 | 8 | 21 |
| Y | Yttrium (Y) | 13 | 8 | 5 | 0 | 0 | 12 | 10 | 11 | 27 |
| Yb | Ytterbium (Yb) | 12 | 6 | 6 | 0 | 0 | 10 | 7 | 9 | 15 |
| Zn | Zinc (Zn) | 30 | 13 | 15 | 2 | 0 | 28 | 29 | 26 | 59 |
| Zr | Zirconium (Zr) | 97 | 26 | 49 | 21 | 1 | 74 | 68 | 76 | 131 |
