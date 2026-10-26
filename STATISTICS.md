# Dataset statistics

pourbase dataset 1.0.0, generated from the bundled database by `scripts/dataset_statistics.py`. Machine-readable versions are in [`docs/statistics`](docs/statistics).

## Summary

| | |
|---|---|
| Species | 1658 |
| Supported elemental systems | 75 of 118 elements |
| Recommended Gibbs energies | 1266 (76 %) |
| Recommended entropies | 1240 (75 %) |
| Recommended formation enthalpies | 1222 (74 %) |
| Reported values retained | 4992 |
| Source records | 1824 (264 distinct citations) |
| Phase records | 1038 (479 resolved) |
| Warnings | 2567 |
| Materials Project matches | 105 phases, 299 energy rows |
| Materials Project fallback estimates | 6 |
| Ligands | 31 |

Gibbs energies by evidence status:

| Status | Species |
|---|---|
| `verified` | 863 |
| `not_available` | 386 |
| `source_verified_estimate` | 328 |
| `defined_reference_state` | 75 |
| `terminal_evidence_gap` | 6 |

Species by phase:

| Phase | Species | Gibbs | Entropy | Enthalpy |
|---|---|---|---|---|
| solid | 894 | 651 | 623 | 800 |
| aqueous | 590 | 522 | 445 | 327 |
| gas | 169 | 90 | 169 | 90 |
| liquid | 5 | 3 | 3 | 5 |

## Database tables

| Table | Rows | Contents |
|---|---|---|
| `species` | 1658 | Formula, charge, phase, composition, oxidation state and reaction coefficients |
| `selected_thermochemistry` | 1658 | Derived by the selection policy: one recommended Gibbs energy, entropy and enthalpy per species |
| `reported_thermochemistry` | 4992 | Every retained reported value, recommended or not, with supersession links |
| `sources` | 1824 | Full citations, links, locators and access dates |
| `phases` | 1038 | Phase identity, candidate polymorphs, space group and evidence |
| `warnings` | 2567 | Scientific cautions attached to records |
| `computational_fallbacks` | 6 | Opt-in Materials Project 300 K estimates for missing solid Gibbs energies |
| `materials_project_matches` | 105 | Reviewed experimental-phase to Materials Project structure matches |
| `materials_project_energies` | 299 | Method-specific Materials Project energies with provenance |
| `element_coverage` | 118 | Status of every chemical element |
| `ligands` | 31 | Free-ligand reference states for ligand-aware calculations |
| `additional_components` | 59 | Additional independent buffered references per species, beyond the first ligand |
| `metadata` | 157 | Dataset version, reference conditions, schema version and value policy |

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
| Ag | Silver (Ag) | 31 | 14 | 14 | 3 | 0 | 26 | 28 | 25 | 54 |
| Al | Aluminum (Al) | 69 | 8 | 59 | 2 | 0 | 65 | 64 | 65 | 98 |
| As | Arsenic (As) | 16 | 7 | 8 | 1 | 0 | 14 | 13 | 15 | 23 |
| Au | Gold (Au) | 24 | 15 | 9 | 0 | 0 | 13 | 10 | 12 | 42 |
| B | Boron (B) | 13 | 3 | 7 | 3 | 0 | 10 | 12 | 11 | 16 |
| Ba | Barium (Ba) | 28 | 6 | 20 | 2 | 0 | 20 | 21 | 25 | 53 |
| Be | Beryllium (Be) | 24 | 11 | 10 | 3 | 0 | 9 | 20 | 11 | 43 |
| Bi | Bismuth (Bi) | 13 | 5 | 7 | 1 | 0 | 10 | 9 | 5 | 19 |
| Br | Bromine (Br) | 10 | 6 | 0 | 3 | 1 | 8 | 10 | 8 | 7 |
| C | Carbon (C) | 14 | 6 | 2 | 6 | 0 | 12 | 14 | 12 | 21 |
| Ca | Calcium (Ca) | 42 | 11 | 29 | 2 | 0 | 35 | 34 | 37 | 90 |
| Cd | Cadmium (Cd) | 25 | 12 | 11 | 2 | 0 | 18 | 21 | 13 | 33 |
| Ce | Cerium (Ce) | 16 | 7 | 9 | 0 | 0 | 13 | 10 | 13 | 19 |
| Cl | Chlorine (Cl) | 12 | 8 | 0 | 4 | 0 | 10 | 12 | 10 | 8 |
| Co | Cobalt (Co) | 29 | 7 | 19 | 3 | 0 | 18 | 23 | 19 | 47 |
| Cr | Chromium (Cr) | 23 | 8 | 13 | 2 | 0 | 10 | 14 | 12 | 36 |
| Cs | Caesium (Cs) | 17 | 5 | 9 | 3 | 0 | 13 | 16 | 12 | 24 |
| Cu | Copper (Cu) | 44 | 18 | 23 | 3 | 0 | 32 | 38 | 28 | 75 |
| Dy | Dysprosium (Dy) | 11 | 5 | 6 | 0 | 0 | 9 | 7 | 9 | 14 |
| Er | Erbium (Er) | 11 | 5 | 6 | 0 | 0 | 9 | 7 | 10 | 15 |
| Eu | Europium (Eu) | 18 | 7 | 11 | 0 | 0 | 15 | 11 | 14 | 22 |
| F | Fluorine (F) | 7 | 3 | 0 | 4 | 0 | 5 | 7 | 5 | 9 |
| Fe | Iron (Fe) | 88 | 29 | 56 | 3 | 0 | 72 | 65 | 60 | 128 |
| Ga | Gallium (Ga) | 16 | 6 | 8 | 2 | 0 | 11 | 14 | 8 | 27 |
| Gd | Gadolinium (Gd) | 14 | 6 | 8 | 0 | 0 | 11 | 7 | 10 | 17 |
| Ge | Germanium (Ge) | 12 | 1 | 7 | 4 | 0 | 10 | 11 | 9 | 14 |
| Hf | Hafnium (Hf) | 10 | 6 | 4 | 0 | 0 | 10 | 10 | 10 | 19 |
| Hg | Mercury (Hg) | 19 | 11 | 5 | 2 | 1 | 13 | 19 | 12 | 28 |
| Ho | Holmium (Ho) | 13 | 6 | 7 | 0 | 0 | 11 | 8 | 11 | 17 |
| I | Iodine (I) | 14 | 8 | 3 | 3 | 0 | 11 | 12 | 11 | 12 |
| In | Indium (In) | 18 | 7 | 9 | 2 | 0 | 9 | 13 | 9 | 30 |
| Ir | Iridium (Ir) | 6 | 1 | 5 | 0 | 0 | 4 | 3 | 5 | 7 |
| K | Potassium (K) | 25 | 10 | 12 | 3 | 0 | 21 | 22 | 20 | 52 |
| La | Lanthanum (La) | 15 | 5 | 10 | 0 | 0 | 11 | 9 | 11 | 19 |
| Li | Lithium (Li) | 19 | 3 | 13 | 3 | 0 | 15 | 17 | 15 | 23 |
| Lu | Lutetium (Lu) | 13 | 6 | 7 | 0 | 0 | 11 | 8 | 10 | 16 |
| Mg | Magnesium (Mg) | 49 | 11 | 36 | 2 | 0 | 44 | 42 | 42 | 89 |
| Mn | Manganese (Mn) | 38 | 11 | 25 | 2 | 0 | 28 | 31 | 30 | 61 |
| Mo | Molybdenum (Mo) | 14 | 1 | 10 | 3 | 0 | 6 | 8 | 10 | 21 |
| N | Nitrogen (N) | 10 | 5 | 0 | 5 | 0 | 9 | 10 | 9 | 25 |
| Na | Sodium (Na) | 28 | 10 | 15 | 3 | 0 | 25 | 25 | 23 | 56 |
| Nb | Niobium (Nb) | 23 | 11 | 9 | 3 | 0 | 15 | 13 | 14 | 44 |
| Nd | Neodymium (Nd) | 15 | 5 | 10 | 0 | 0 | 11 | 8 | 13 | 22 |
| Ni | Nickel (Ni) | 67 | 28 | 35 | 3 | 1 | 59 | 48 | 48 | 98 |
| Os | Osmium (Os) | 10 | 2 | 7 | 1 | 0 | 7 | 6 | 7 | 14 |
| P | Phosphorus (P) | 21 | 12 | 6 | 3 | 0 | 15 | 15 | 17 | 25 |
| Pb | Lead (Pb) | 27 | 10 | 13 | 4 | 0 | 22 | 25 | 20 | 56 |
| Pd | Palladium (Pd) | 14 | 7 | 7 | 0 | 0 | 10 | 5 | 4 | 16 |
| Pr | Praseodymium (Pr) | 16 | 7 | 9 | 0 | 0 | 10 | 5 | 11 | 23 |
| Pt | Platinum (Pt) | 15 | 1 | 14 | 0 | 0 | 2 | 3 | 10 | 31 |
| Ra | Radium (Ra) | 7 | 2 | 5 | 0 | 0 | 6 | 7 | 6 | 20 |
| Rb | Rubidium (Rb) | 17 | 6 | 8 | 3 | 0 | 11 | 14 | 12 | 27 |
| Re | Rhenium (Re) | 7 | 1 | 6 | 0 | 0 | 5 | 5 | 5 | 6 |
| Rh | Rhodium (Rh) | 10 | 6 | 4 | 0 | 0 | 9 | 8 | 9 | 15 |
| Ru | Ruthenium (Ru) | 11 | 2 | 9 | 0 | 0 | 6 | 7 | 7 | 15 |
| S | Sulfur (S) | 14 | 10 | 1 | 3 | 0 | 12 | 13 | 11 | 15 |
| Sb | Antimony (Sb) | 12 | 3 | 9 | 0 | 0 | 10 | 8 | 10 | 10 |
| Sc | Scandium (Sc) | 15 | 5 | 7 | 3 | 0 | 10 | 12 | 13 | 26 |
| Se | Selenium (Se) | 30 | 11 | 8 | 11 | 0 | 26 | 22 | 26 | 42 |
| Si | Silicon (Si) | 21 | 10 | 9 | 2 | 0 | 19 | 12 | 12 | 47 |
| Sm | Samarium (Sm) | 17 | 7 | 10 | 0 | 0 | 13 | 7 | 12 | 23 |
| Sn | Tin (Sn) | 56 | 23 | 20 | 12 | 1 | 50 | 32 | 30 | 69 |
| Sr | Strontium (Sr) | 27 | 6 | 19 | 2 | 0 | 22 | 23 | 24 | 48 |
| Ta | Tantalum (Ta) | 12 | 2 | 7 | 3 | 0 | 5 | 5 | 7 | 22 |
| Tb | Terbium (Tb) | 13 | 6 | 7 | 0 | 0 | 11 | 8 | 10 | 16 |
| Te | Tellurium (Te) | 6 | 2 | 4 | 0 | 0 | 4 | 3 | 5 | 8 |
| Ti | Titanium (Ti) | 17 | 2 | 12 | 3 | 0 | 13 | 15 | 12 | 30 |
| Tl | Thallium (Tl) | 21 | 10 | 11 | 0 | 0 | 12 | 16 | 13 | 33 |
| Tm | Thulium (Tm) | 13 | 6 | 7 | 0 | 0 | 10 | 8 | 9 | 17 |
| V | Vanadium (V) | 32 | 13 | 16 | 3 | 0 | 20 | 25 | 19 | 47 |
| W | Tungsten (W) | 14 | 1 | 10 | 3 | 0 | 6 | 8 | 10 | 25 |
| Y | Yttrium (Y) | 15 | 8 | 7 | 0 | 0 | 13 | 11 | 13 | 30 |
| Yb | Ytterbium (Yb) | 12 | 6 | 6 | 0 | 0 | 10 | 7 | 9 | 15 |
| Zn | Zinc (Zn) | 34 | 13 | 19 | 2 | 0 | 32 | 33 | 30 | 63 |
| Zr | Zirconium (Zr) | 99 | 26 | 51 | 21 | 1 | 74 | 68 | 78 | 140 |
