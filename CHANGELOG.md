# Changelog

## 1.0.0rc2 (unreleased)

Release candidate for collaborator review. Package version `1.0.0rc2`; dataset version `1.0.0`.

- 460 species across 74 supported elemental systems, with recommended Gibbs energies for 454.
- Six solid gaps with separately stored, opt-in Materials Project 300 K SISSO estimates.
- 105 accepted Materials Project phase matches and 299 method-specific energy rows from MP
  database version 2026.04.13.
- Fixed-activity and closed-inventory diagrams, Davies activity corrections, ligand and gas
  reservoirs, concentration sweeps, Boltzmann-like smoothing, and an official Materials Project
  comparison.
- Desktop application (`pourbase-gui`, PySide6 and pyqtgraph) and LaTeX data paper.

Fixed: the official Materials Project diagram used an ion activity of 10⁻⁶ whatever activity was
requested, because pymatgen's `PourbaixDiagram` resets ion concentrations when it is built. The
requested activities are now applied to the filtered entries after construction, and every
filtered entry is evaluated on the grid.

Remaining release gates: collaborator review, confirmed credits and licensing, archival deposit of
the full curation record, and assignment of the final release date and DOI.
