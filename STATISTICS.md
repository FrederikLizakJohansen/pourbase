# Dataset statistics

pourbase dataset 1.0.0, generated from the bundled database by `scripts/dataset_statistics.py`. Machine-readable versions are in [`docs/statistics`](docs/statistics).

## Summary

| | |
|---|---|
| Species | 1610 |
| Supported elemental systems | 75 of 118 elements |
| Recommended Gibbs energies | 1241 (77 %) |
| Recommended entropies | 1213 (75 %) |
| Recommended formation enthalpies | 1180 (73 %) |
| Reported values retained | 4889 |
| Source records | 1822 (262 distinct citations) |
| Phase records | 990 (479 resolved) |
| Warnings | 2490 |
| Materials Project matches | 105 phases, 299 energy rows |
| Materials Project fallback estimates | 6 |
| Ligands | 31 |

Gibbs energies by evidence status:

| Status | Species |
|---|---|
| `verified` | 838 |
| `not_available` | 363 |
| `source_verified_estimate` | 328 |
| `defined_reference_state` | 75 |
| `terminal_evidence_gap` | 6 |

Species by phase:

| Phase | Species | Gibbs | Entropy | Enthalpy |
|---|---|---|---|---|
| solid | 846 | 626 | 596 | 758 |
| aqueous | 590 | 522 | 445 | 327 |
| gas | 169 | 90 | 169 | 90 |
| liquid | 5 | 3 | 3 | 5 |

## Database tables

| Table | Rows | Contents |
|---|---|---|
| `species` | 1610 | Formula, charge, phase, composition, oxidation state and reaction coefficients |
| `selected_thermochemistry` | 1610 | Derived by the selection policy: one recommended Gibbs energy, entropy and enthalpy per species |
| `reported_thermochemistry` | 4889 | Every retained reported value, recommended or not, with supersession links |
| `sources` | 1822 | Full citations, links, locators and access dates |
| `phases` | 990 | Phase identity, candidate polymorphs, space group and evidence |
| `warnings` | 2490 | Scientific cautions attached to records |
| `computational_fallbacks` | 6 | Opt-in Materials Project 300 K estimates for missing solid Gibbs energies |
| `materials_project_matches` | 105 | Reviewed experimental-phase to Materials Project structure matches |
| `materials_project_energies` | 299 | Method-specific Materials Project energies with provenance |
| `element_coverage` | 118 | Status of every chemical element |
| `ligands` | 31 | Free-ligand reference states for ligand-aware calculations |
| `additional_components` | 59 | Additional independent buffered references per species, beyond the first ligand |
| `metadata` | 150 | Dataset version, reference conditions, schema version and value policy |

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
| Ag | Silver (Ag) | 27 | 14 | 10 | 3 | 0 | 24 | 26 | 21 | 48 |
| Al | Aluminum (Al) | 68 | 8 | 58 | 2 | 0 | 64 | 63 | 64 | 97 |
| As | Arsenic (As) | 16 | 7 | 8 | 1 | 0 | 14 | 13 | 15 | 23 |
| Au | Gold (Au) | 23 | 15 | 8 | 0 | 0 | 13 | 10 | 11 | 40 |
| B | Boron (B) | 13 | 3 | 7 | 3 | 0 | 10 | 12 | 11 | 16 |
| Ba | Barium (Ba) | 27 | 6 | 19 | 2 | 0 | 19 | 20 | 24 | 52 |
| Be | Beryllium (Be) | 22 | 11 | 8 | 3 | 0 | 8 | 19 | 9 | 40 |
| Bi | Bismuth (Bi) | 13 | 5 | 7 | 1 | 0 | 10 | 9 | 5 | 19 |
| Br | Bromine (Br) | 10 | 6 | 0 | 3 | 1 | 8 | 10 | 8 | 7 |
| C | Carbon (C) | 14 | 6 | 2 | 6 | 0 | 12 | 14 | 12 | 21 |
| Ca | Calcium (Ca) | 41 | 11 | 28 | 2 | 0 | 34 | 33 | 36 | 89 |
| Cd | Cadmium (Cd) | 24 | 12 | 10 | 2 | 0 | 17 | 20 | 12 | 32 |
| Ce | Cerium (Ce) | 16 | 7 | 9 | 0 | 0 | 13 | 10 | 13 | 19 |
| Cl | Chlorine (Cl) | 12 | 8 | 0 | 4 | 0 | 10 | 12 | 10 | 8 |
| Co | Cobalt (Co) | 27 | 7 | 17 | 3 | 0 | 17 | 22 | 17 | 44 |
| Cr | Chromium (Cr) | 20 | 8 | 10 | 2 | 0 | 9 | 13 | 9 | 30 |
| Cs | Caesium (Cs) | 15 | 5 | 7 | 3 | 0 | 12 | 15 | 10 | 21 |
| Cu | Copper (Cu) | 42 | 18 | 21 | 3 | 0 | 31 | 38 | 27 | 71 |
| Dy | Dysprosium (Dy) | 11 | 5 | 6 | 0 | 0 | 9 | 7 | 9 | 14 |
| Er | Erbium (Er) | 11 | 5 | 6 | 0 | 0 | 9 | 7 | 10 | 15 |
| Eu | Europium (Eu) | 18 | 7 | 11 | 0 | 0 | 15 | 11 | 14 | 22 |
| F | Fluorine (F) | 7 | 3 | 0 | 4 | 0 | 5 | 7 | 5 | 9 |
| Fe | Iron (Fe) | 88 | 29 | 56 | 3 | 0 | 72 | 65 | 60 | 127 |
| Ga | Gallium (Ga) | 15 | 6 | 7 | 2 | 0 | 10 | 13 | 7 | 26 |
| Gd | Gadolinium (Gd) | 14 | 6 | 8 | 0 | 0 | 11 | 7 | 10 | 17 |
| Ge | Germanium (Ge) | 12 | 1 | 7 | 4 | 0 | 10 | 11 | 9 | 14 |
| Hf | Hafnium (Hf) | 9 | 6 | 3 | 0 | 0 | 9 | 9 | 9 | 18 |
| Hg | Mercury (Hg) | 19 | 11 | 5 | 2 | 1 | 13 | 19 | 12 | 28 |
| Ho | Holmium (Ho) | 13 | 6 | 7 | 0 | 0 | 11 | 8 | 11 | 17 |
| I | Iodine (I) | 14 | 8 | 3 | 3 | 0 | 11 | 12 | 11 | 12 |
| In | Indium (In) | 18 | 7 | 9 | 2 | 0 | 9 | 13 | 9 | 30 |
| Ir | Iridium (Ir) | 5 | 1 | 4 | 0 | 0 | 3 | 2 | 4 | 6 |
| K | Potassium (K) | 23 | 10 | 10 | 3 | 0 | 19 | 20 | 18 | 50 |
| La | Lanthanum (La) | 15 | 5 | 10 | 0 | 0 | 11 | 9 | 11 | 19 |
| Li | Lithium (Li) | 18 | 3 | 12 | 3 | 0 | 14 | 16 | 14 | 22 |
| Lu | Lutetium (Lu) | 13 | 6 | 7 | 0 | 0 | 11 | 8 | 10 | 16 |
| Mg | Magnesium (Mg) | 48 | 11 | 35 | 2 | 0 | 43 | 41 | 41 | 88 |
| Mn | Manganese (Mn) | 37 | 11 | 24 | 2 | 0 | 28 | 30 | 30 | 59 |
| Mo | Molybdenum (Mo) | 14 | 1 | 10 | 3 | 0 | 6 | 8 | 10 | 21 |
| N | Nitrogen (N) | 10 | 5 | 0 | 5 | 0 | 9 | 10 | 9 | 25 |
| Na | Sodium (Na) | 28 | 10 | 15 | 3 | 0 | 25 | 25 | 23 | 56 |
| Nb | Niobium (Nb) | 22 | 11 | 8 | 3 | 0 | 14 | 12 | 13 | 43 |
| Nd | Neodymium (Nd) | 15 | 5 | 10 | 0 | 0 | 11 | 8 | 13 | 22 |
| Ni | Nickel (Ni) | 66 | 28 | 34 | 3 | 1 | 58 | 48 | 48 | 95 |
| Os | Osmium (Os) | 9 | 2 | 6 | 1 | 0 | 7 | 5 | 7 | 12 |
| P | Phosphorus (P) | 21 | 12 | 6 | 3 | 0 | 15 | 15 | 17 | 25 |
| Pb | Lead (Pb) | 25 | 10 | 11 | 4 | 0 | 21 | 24 | 18 | 53 |
| Pd | Palladium (Pd) | 14 | 7 | 7 | 0 | 0 | 10 | 5 | 4 | 16 |
| Pr | Praseodymium (Pr) | 16 | 7 | 9 | 0 | 0 | 10 | 5 | 11 | 23 |
| Pt | Platinum (Pt) | 14 | 1 | 13 | 0 | 0 | 2 | 2 | 10 | 29 |
| Ra | Radium (Ra) | 7 | 2 | 5 | 0 | 0 | 6 | 7 | 6 | 20 |
| Rb | Rubidium (Rb) | 15 | 6 | 6 | 3 | 0 | 11 | 14 | 10 | 23 |
| Re | Rhenium (Re) | 7 | 1 | 6 | 0 | 0 | 5 | 5 | 5 | 6 |
| Rh | Rhodium (Rh) | 10 | 6 | 4 | 0 | 0 | 9 | 8 | 9 | 15 |
| Ru | Ruthenium (Ru) | 10 | 2 | 8 | 0 | 0 | 6 | 7 | 6 | 13 |
| S | Sulfur (S) | 14 | 10 | 1 | 3 | 0 | 12 | 13 | 11 | 15 |
| Sb | Antimony (Sb) | 11 | 3 | 8 | 0 | 0 | 10 | 8 | 9 | 8 |
| Sc | Scandium (Sc) | 14 | 5 | 6 | 3 | 0 | 9 | 11 | 12 | 25 |
| Se | Selenium (Se) | 30 | 11 | 8 | 11 | 0 | 26 | 22 | 26 | 42 |
| Si | Silicon (Si) | 21 | 10 | 9 | 2 | 0 | 19 | 12 | 12 | 47 |
| Sm | Samarium (Sm) | 17 | 7 | 10 | 0 | 0 | 13 | 7 | 12 | 23 |
| Sn | Tin (Sn) | 56 | 23 | 20 | 12 | 1 | 50 | 32 | 30 | 69 |
| Sr | Strontium (Sr) | 26 | 6 | 18 | 2 | 0 | 21 | 22 | 23 | 47 |
| Ta | Tantalum (Ta) | 11 | 2 | 6 | 3 | 0 | 5 | 5 | 6 | 20 |
| Tb | Terbium (Tb) | 13 | 6 | 7 | 0 | 0 | 11 | 8 | 10 | 16 |
| Te | Tellurium (Te) | 6 | 2 | 4 | 0 | 0 | 4 | 3 | 5 | 8 |
| Ti | Titanium (Ti) | 17 | 2 | 12 | 3 | 0 | 13 | 15 | 12 | 30 |
| Tl | Thallium (Tl) | 20 | 10 | 10 | 0 | 0 | 12 | 16 | 12 | 31 |
| Tm | Thulium (Tm) | 13 | 6 | 7 | 0 | 0 | 10 | 8 | 9 | 17 |
| V | Vanadium (V) | 30 | 13 | 14 | 3 | 0 | 20 | 24 | 18 | 43 |
| W | Tungsten (W) | 14 | 1 | 10 | 3 | 0 | 6 | 8 | 10 | 25 |
| Y | Yttrium (Y) | 14 | 8 | 6 | 0 | 0 | 12 | 10 | 12 | 29 |
| Yb | Ytterbium (Yb) | 12 | 6 | 6 | 0 | 0 | 10 | 7 | 9 | 15 |
| Zn | Zinc (Zn) | 33 | 13 | 18 | 2 | 0 | 31 | 32 | 29 | 62 |
| Zr | Zirconium (Zr) | 97 | 26 | 49 | 21 | 1 | 74 | 68 | 76 | 135 |
