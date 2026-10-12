# Changelog

## 1.0.0rc2 (unreleased)

Release candidate for collaborator review. Package version `1.0.0rc2`; dataset version `1.0.0`.

- Species without a recommended Gibbs energy are left out and reported by default;
  `allow_incomplete=False` and `--require-complete` stop instead.
- Ligand reservoirs are global, with a master switch and per-ligand toggles on the periodic table.
- Application: policy comparison dialog, copied code that reproduces the shown diagram
  (`pb.plot_uncertainty`), flagged source disagreements, grouped ligand complexes, background
  calculations behind a loading overlay, faster tables and tabs, no wheel changes on inputs.
- Schema 8: the database file stores evidence only. The recommended values are derived from the
  reported values by the active selection policy when the database is opened and appear to every
  connection as the temporary table `selected_thermochemistry`. Reported values gain `source_locator`; six
  entropy evidence gaps move from the stored `thermochemistry` table to reported rows; `selected_as_recommended`
  and the stored `thermochemistry` table are removed. Every derived value, status, uncertainty,
  source and locator equals the schema 7 recommendation, and the `species` table is unchanged.
  Schema 7 files remain readable.
- Seven aqueous species listed in the NBS Tables under two water-equivalent formulas are single
  records, each with a warning naming the second formula.
- `pourbase.crosscheck` and `scripts/pymatgen_crosscheck.py` compare every system with pymatgen;
  with the same water energy and Nernst slope all diagrams agree at every grid point.
- `with_user_species` adds or substitutes user species from a CSV file, with the evidence status
  `user_supplied`; the desktop application loads them from the File menu and stores them in sessions.
- The calculation modules state the equations they implement, numbered as in the paper.
- Recommended values follow a selection policy, `data/selection-policy.toml`: evidence classes A–F
  (NBS Tables first in class B; fitted estimates before correlations in class E), tie-breaks and
  43 overrides and 2 exclusions with reasons. Applying it changed 94 recommendations (23 Gibbs
  energies, mostly NIST-JANAF to NBS). `SelectionPolicy`, `select`, `with_policy` and
  `compare_policies` calculate with any policy, and `scripts/selection_report.py` reports one. The application loads policies from the File
  menu and shows each value's class and selection basis in the Species tab.
- The soft-minimum view takes a blend width in kJ/mol (`boltzmann_smooth(diagram, width_J_mol)`,
  `--blend-width`, a width slider in the application). At a width of RT the weights equal the
  fractions of dissolved species where no solid precipitates; `thermal_scale` and
  `--boltzmann-scale` remain as deprecated aliases.

- 798 species and 2642 retained observations across 74 supported elemental systems, with
  recommended Gibbs energies for 706.
- Four magnesium carbonate minerals and 17 observations: 12 USGS mineral properties,
  three original entropy alternatives, Mg²⁺ enthalpy and MgHCO3+ Gibbs energy.
  Complete hydrated/basic-carbonate formula units fill 13 missing properties. The default
  policy selects the open NBS MgHCO3+ Gibbs evaluation; all earlier evidence remains stored.
  Original hydromagnesite entropy retains its zero-residual-entropy assumption as an estimate.
- Seven open calcium observations: the missing Ca²⁺ formation enthalpy and six
  original-fit CaCO3(aq)/CaHCO3+ formation alternatives. Earlier recommendations
  and calculations are preserved. Original fit derivatives and inconsistent
  WATEQ4F reaction-enthalpy points have separate source decisions.
- Original Fe/Mn carbonate calorimetry and open NBS ion enthalpies: four observations,
  two newly available preferred enthalpies, and explicit links between the original
  entropy measurements and later critical evaluations. Existing recommendations and
  default/carbonate-enabled Fe/Mn calculations are preserved; original entropy pressure
  remains unspecified in the evidence record.
- Original strontium/barium carbonate fits and open NBS aqueous anchors: 20 observations,
  two bicarbonate complexes and eight newly available preferred fields. Original-fit
  estimates replace six preferred correlation values for aqueous SrCO3/BaCO3; all earlier
  evidence remains stored. Locators state the local pressure-flat approximation and
  unavailable total uncertainty. The 74 default ligand-free diagrams are preserved.
- Seven pure carbonate minerals from the public-domain USGS Bulletin 2131 evaluation:
  19 source-linked properties, distinct calcium carbonate polymorphs, published uncertainty
  intervals and buffered carbonate support. Earlier evidence and recommendations are preserved.
- Six original solubility-fit G/H/S alternatives for aragonite and vaterite, derived using
  relative phase differences and documented calcite anchors. Vaterite gains estimated entropy
  and enthalpy; selected Gibbs energies and existing calculations are preserved. The source
  locators state pressure assumptions and unavailable total uncertainty.
- Remaining Shock1997 hydrolysis fits and entropy correlations: 67 observations,
  26 species and eight NBS-reference enthalpy calculations. Original-paper identities
  resolve two native charge errors; unresolved entropy ancestry remains held.
- Original Fe/Ni/Sn/Pb hydrolysis fits and entropy correlations, including both iron fits
  and ten separately calculated NBS-reference enthalpies. Intra-paper NiO/PbOH entropy
  conflicts remain held. Entropy-only Fe/Ni records require `allow_incomplete=True` for
  calculations; examples and dataset snapshots record this choice.
- Original SLOP aqueous-complex evaluations from the CC BY 4.0 GEOPIG release, with
  explicit hydration conversions, open NBS enthalpy derivations and buffered bromide support.
- Original rare-earth chloride and fluoride fits, retained alternative entropy fits, explicitly
  NBS-derived enthalpy estimates, and distinct boehmite and diaspore phases.
- Six solid gaps with separately stored, opt-in Materials Project 300 K SISSO estimates.
- 105 accepted Materials Project phase matches and 299 method-specific energy rows from MP
  database version 2026.04.13.
- Fixed-activity and closed-inventory diagrams, Davies activity corrections, ligand and gas
  reservoirs, concentration sweeps, Boltzmann-like smoothing, and an official Materials Project
  comparison.
- Desktop application (`pourbase-gui`, PySide6 and pyqtgraph) and dataset statistics in `STATISTICS.md`.

API:

- `Scenario` and `calculate` describe and run a diagram in user-facing units; `Calculation`
  carries boundaries, plating potentials and point probes.
- `screen_periodic_table` returns typed `ElementResult`s with an `ElementStatus`.
- `ThermodynamicDatabase.species_records` returns typed `SpeciesRecord`s.
- `EvidenceStatus` and `ExclusionReason` enumerate Gibbs statuses and exclusion reasons.
- `ConcentrationSweepEngine` stores levels compactly, accepts up to 201 levels and reports
  progress with cancellation; `PourbaixEngine.calculate(store_energies=False)` gives compact
  diagrams.
- `grid_csv`, `diagram_figure` and `save_figure` export results; `pourbase.__data_version__`
  reports the dataset version.
- `PourbaseError` is the base exception.

Fixed: the official Materials Project diagram used an ion activity of 10⁻⁶ whatever activity was
requested, because pymatgen's `PourbaixDiagram` resets ion concentrations when it is built. The
requested activities are now applied to the filtered entries after construction, and every
filtered entry is evaluated on the grid.

Remaining release gates: collaborator review, confirmed credits and licensing, archival deposit of
the full curation record, and assignment of the final release date and DOI.
