# Changelog

## 1.0.0rc2 (unreleased)

Release candidate for collaborator review. Package version `1.0.0rc2`; dataset version `1.0.0`.

- 760 species and 2481 retained observations across 74 supported elemental systems, with
  recommended Gibbs energies for 696.
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
