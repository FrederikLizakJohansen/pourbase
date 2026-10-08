# Dataset statistics

pourbase dataset 1.0.0, generated from the bundled database by `scripts/dataset_statistics.py`. Machine-readable versions are in [`docs/statistics`](docs/statistics).

## Summary

| | |
|---|---|
| Species | 792 |
| Supported elemental systems | 74 of 118 elements |
| Recommended Gibbs energies | 700 (88 %) |
| Recommended entropies | 670 (85 %) |
| Recommended formation enthalpies | 519 (66 %) |
| Reported values retained | 2583 |
| Source records | 1608 (197 distinct citations) |
| Phase records | 451 (235 resolved) |
| Warnings | 1124 |
| Materials Project matches | 105 phases, 299 energy rows |
| Materials Project fallback estimates | 6 |
| Ligands | 12 |

Gibbs energies by evidence status:

| Status | Species |
|---|---|
| `verified` | 394 |
| `source_verified_estimate` | 232 |
| `not_available` | 86 |
| `defined_reference_state` | 74 |
| `terminal_evidence_gap` | 6 |

Species by phase:

| Phase | Species | Gibbs | Entropy | Enthalpy |
|---|---|---|---|---|
| aqueous | 471 | 402 | 401 | 267 |
| solid | 310 | 287 | 258 | 241 |
| gas | 9 | 9 | 9 | 9 |
| liquid | 2 | 2 | 2 | 2 |

## Database tables

| Table | Rows | Contents |
|---|---|---|
| `species` | 792 | Formula, charge, phase, composition, oxidation state and reaction coefficients |
| `thermochemistry` | 792 | One recommended Gibbs energy, entropy and enthalpy per species |
| `reported_thermochemistry` | 2583 | Every retained reported value, recommended or not, with supersession links |
| `sources` | 1608 | Full citations, links, locators and access dates |
| `phases` | 451 | Phase identity, candidate polymorphs, space group and evidence |
| `warnings` | 1124 | Scientific cautions attached to records |
| `computational_fallbacks` | 6 | Opt-in Materials Project 300 K estimates for missing solid Gibbs energies |
| `materials_project_matches` | 105 | Reviewed experimental-phase to Materials Project structure matches |
| `materials_project_energies` | 299 | Method-specific Materials Project energies with provenance |
| `element_coverage` | 118 | Status of every chemical element |
| `ligands` | 12 | Free-ligand reference states for ligand-aware calculations |
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
| Ag | Silver (Ag) | 21 | 12 | 9 | 0 | 0 | 20 | 20 | 17 | 37 |
| Al | Aluminum (Al) | 15 | 6 | 9 | 0 | 0 | 14 | 13 | 12 | 28 |
| As | Arsenic (As) | 13 | 9 | 4 | 0 | 0 | 13 | 12 | 12 | 2 |
| Au | Gold (Au) | 15 | 13 | 2 | 0 | 0 | 11 | 8 | 3 | 23 |
| B | Boron (B) | 6 | 4 | 2 | 0 | 0 | 6 | 6 | 6 | 0 |
| Ba | Barium (Ba) | 8 | 5 | 3 | 0 | 0 | 8 | 8 | 5 | 16 |
| Be | Beryllium (Be) | 14 | 11 | 3 | 0 | 0 | 5 | 14 | 3 | 26 |
| Bi | Bismuth (Bi) | 8 | 5 | 3 | 0 | 0 | 6 | 5 | 2 | 13 |
| Br | Bromine (Br) | 7 | 6 | 0 | 0 | 1 | 7 | 7 | 7 | 0 |
| C | Carbon (C) | 7 | 4 | 1 | 2 | 0 | 7 | 7 | 7 | 9 |
| Ca | Calcium (Ca) | 19 | 9 | 10 | 0 | 0 | 19 | 19 | 16 | 43 |
| Cd | Cadmium (Cd) | 16 | 13 | 3 | 0 | 0 | 10 | 12 | 4 | 23 |
| Ce | Cerium (Ce) | 13 | 7 | 6 | 0 | 0 | 12 | 9 | 10 | 14 |
| Cl | Chlorine (Cl) | 9 | 8 | 0 | 1 | 0 | 9 | 9 | 9 | 1 |
| Co | Cobalt (Co) | 16 | 7 | 9 | 0 | 0 | 12 | 15 | 8 | 25 |
| Cr | Chromium (Cr) | 10 | 8 | 2 | 0 | 0 | 7 | 9 | 1 | 12 |
| Cs | Caesium (Cs) | 6 | 5 | 1 | 0 | 0 | 5 | 6 | 3 | 9 |
| Cu | Copper (Cu) | 29 | 16 | 13 | 0 | 0 | 22 | 27 | 16 | 50 |
| Dy | Dysprosium (Dy) | 8 | 5 | 3 | 0 | 0 | 8 | 6 | 6 | 9 |
| Er | Erbium (Er) | 8 | 5 | 3 | 0 | 0 | 8 | 6 | 7 | 10 |
| Eu | Europium (Eu) | 13 | 6 | 7 | 0 | 0 | 12 | 10 | 11 | 13 |
| F | Fluorine (F) | 4 | 3 | 0 | 1 | 0 | 4 | 4 | 4 | 1 |
| Fe | Iron (Fe) | 34 | 17 | 17 | 0 | 0 | 28 | 31 | 18 | 60 |
| Ga | Gallium (Ga) | 9 | 6 | 3 | 0 | 0 | 7 | 8 | 2 | 17 |
| Gd | Gadolinium (Gd) | 11 | 6 | 5 | 0 | 0 | 10 | 6 | 7 | 12 |
| Ge | Germanium (Ge) | 4 | 1 | 3 | 0 | 0 | 4 | 3 | 3 | 2 |
| Hf | Hafnium (Hf) | 8 | 6 | 2 | 0 | 0 | 8 | 8 | 8 | 17 |
| Hg | Mercury (Hg) | 14 | 11 | 1 | 1 | 1 | 9 | 14 | 8 | 21 |
| Ho | Holmium (Ho) | 10 | 6 | 4 | 0 | 0 | 10 | 7 | 8 | 12 |
| I | Iodine (I) | 9 | 8 | 1 | 0 | 0 | 9 | 8 | 8 | 1 |
| In | Indium (In) | 10 | 7 | 3 | 0 | 0 | 6 | 8 | 2 | 17 |
| Ir | Iridium (Ir) | 3 | 1 | 2 | 0 | 0 | 3 | 2 | 2 | 2 |
| K | Potassium (K) | 13 | 10 | 3 | 0 | 0 | 13 | 12 | 10 | 33 |
| La | Lanthanum (La) | 11 | 5 | 6 | 0 | 0 | 10 | 7 | 8 | 13 |
| Li | Lithium (Li) | 4 | 3 | 1 | 0 | 0 | 4 | 4 | 2 | 3 |
| Lu | Lutetium (Lu) | 10 | 6 | 4 | 0 | 0 | 10 | 7 | 7 | 11 |
| Mg | Magnesium (Mg) | 16 | 8 | 8 | 0 | 0 | 14 | 14 | 13 | 32 |
| Mn | Manganese (Mn) | 20 | 10 | 10 | 0 | 0 | 17 | 19 | 13 | 28 |
| Mo | Molybdenum (Mo) | 5 | 1 | 4 | 0 | 0 | 5 | 5 | 3 | 2 |
| N | Nitrogen (N) | 8 | 5 | 0 | 3 | 0 | 8 | 8 | 8 | 20 |
| Na | Sodium (Na) | 17 | 10 | 7 | 0 | 0 | 16 | 15 | 13 | 37 |
| Nb | Niobium (Nb) | 7 | 4 | 3 | 0 | 0 | 7 | 4 | 4 | 5 |
| Nd | Neodymium (Nd) | 11 | 5 | 6 | 0 | 0 | 10 | 7 | 9 | 15 |
| Ni | Nickel (Ni) | 18 | 7 | 11 | 0 | 0 | 14 | 14 | 11 | 32 |
| Os | Osmium (Os) | 8 | 3 | 4 | 1 | 0 | 8 | 5 | 5 | 8 |
| P | Phosphorus (P) | 9 | 7 | 2 | 0 | 0 | 9 | 7 | 7 | 2 |
| Pb | Lead (Pb) | 19 | 10 | 9 | 0 | 0 | 17 | 18 | 14 | 42 |
| Pd | Palladium (Pd) | 4 | 1 | 3 | 0 | 0 | 3 | 3 | 1 | 4 |
| Pr | Praseodymium (Pr) | 12 | 7 | 5 | 0 | 0 | 10 | 5 | 7 | 15 |
| Pt | Platinum (Pt) | 4 | 1 | 3 | 0 | 0 | 2 | 2 | 0 | 9 |
| Rb | Rubidium (Rb) | 7 | 6 | 1 | 0 | 0 | 6 | 7 | 4 | 11 |
| Re | Rhenium (Re) | 4 | 1 | 3 | 0 | 0 | 4 | 4 | 2 | 0 |
| Rh | Rhodium (Rh) | 9 | 6 | 3 | 0 | 0 | 9 | 8 | 8 | 13 |
| Ru | Ruthenium (Ru) | 5 | 2 | 3 | 0 | 0 | 5 | 5 | 2 | 5 |
| S | Sulfur (S) | 10 | 9 | 1 | 0 | 0 | 10 | 9 | 9 | 3 |
| Sb | Antimony (Sb) | 8 | 4 | 4 | 0 | 0 | 8 | 6 | 6 | 2 |
| Sc | Scandium (Sc) | 8 | 5 | 3 | 0 | 0 | 8 | 8 | 8 | 13 |
| Se | Selenium (Se) | 7 | 6 | 1 | 0 | 0 | 7 | 7 | 7 | 0 |
| Si | Silicon (Si) | 6 | 4 | 2 | 0 | 0 | 6 | 5 | 5 | 8 |
| Sm | Samarium (Sm) | 13 | 7 | 6 | 0 | 0 | 12 | 6 | 8 | 16 |
| Sn | Tin (Sn) | 10 | 5 | 5 | 0 | 0 | 8 | 9 | 4 | 14 |
| Sr | Strontium (Sr) | 8 | 5 | 3 | 0 | 0 | 8 | 8 | 5 | 15 |
| Ta | Tantalum (Ta) | 4 | 2 | 2 | 0 | 0 | 4 | 2 | 1 | 6 |
| Tb | Terbium (Tb) | 11 | 6 | 5 | 0 | 0 | 10 | 7 | 8 | 13 |
| Te | Tellurium (Te) | 4 | 2 | 2 | 0 | 0 | 4 | 3 | 3 | 2 |
| Ti | Titanium (Ti) | 7 | 2 | 5 | 0 | 0 | 7 | 7 | 4 | 15 |
| Tl | Thallium (Tl) | 14 | 10 | 4 | 0 | 0 | 9 | 13 | 6 | 20 |
| Tm | Thulium (Tm) | 10 | 6 | 4 | 0 | 0 | 10 | 7 | 7 | 11 |
| V | Vanadium (V) | 18 | 13 | 5 | 0 | 0 | 14 | 16 | 7 | 17 |
| W | Tungsten (W) | 5 | 1 | 4 | 0 | 0 | 5 | 5 | 3 | 6 |
| Y | Yttrium (Y) | 11 | 8 | 3 | 0 | 0 | 11 | 9 | 9 | 24 |
| Yb | Ytterbium (Yb) | 9 | 6 | 3 | 0 | 0 | 9 | 6 | 6 | 10 |
| Zn | Zinc (Zn) | 22 | 10 | 12 | 0 | 0 | 21 | 21 | 18 | 47 |
| Zr | Zirconium (Zr) | 9 | 6 | 3 | 0 | 0 | 9 | 9 | 9 | 17 |
