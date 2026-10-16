# Changelog

## 1.0.0rc2 (unreleased)

Release candidate for collaborator review. Package version `1.0.0rc2`; dataset version `1.0.0`.

- Review the held NEA calcium-silicate formula and original-source targets.
  Show that the published Gibbs calculation uses the printed inconsistent
  stoichiometry; preserve the identity/molar-basis hold. Database counts and
  preferred values are unchanged.
- Retain 24 NEA observations and 11 mixed-metal zirconium species, adding
  20 usable 298.15 K properties. Schema 9 and independent buffered components
  support conditional secondary-metal activities. Preserve three 323.15 K
  observations outside 298.15 K selection and both NASICON Gibbs alternatives.
  Keep the calcium formula and ZrH admission holds separate from temperature
  and gas-source follow-ups. All earlier preferred selections are preserved.
- Review four disputed zirconium rows and retain nine observations across
  three species. Keep two oxide-gas triplets as explicitly selected historical
  estimates with the later NEA critique. Reconcile the selected-table ZrS1.5
  estimate and structural notation; preserve the bulk ZrH model hold.
  All earlier preferred values and default phase maps remain unchanged.
- Resolve six zirconium reference/model holds with 16 observations and six
  species. Add explicitly buffered crystalline Te, N2 gas and graphite
  references. Preserve full formulas, signed reaction coefficients, the
  ZrC thermal estimate and the tellurite Gibbs gap. All earlier preferred
  values and 74 default phase maps are preserved; 16 zirconium holds remain.
- Resolve five zirconium source/model holds with nine NEA observations and
  three species. Select two hydrolysis Gibbs values in the existing water
  component basis, preserving source formulas, uncertainty intervals and all
  alternatives. Add open NBS selenite and neutral silica references, zircon
  G/H/S, zirconium selenite H and explicitly selected Zr(g). Keep the remaining
  22 zirconium holds tracked separately.
- Review all nine selected G/H/S cells for Ni(g), Ni(l) and SnH4(g).
  Add nine observations and three phase identities, preserving all earlier
  preferred values. Add explicit selection for the two new gas phases while
  preserving default nickel/tin closed balances and strict completeness.
- Complete the targeted NEA-derived PSI/Nagra, SUPCRT and MINES crosswalk.
  Add the selected nickel trihydroxo Gibbs value in the existing HNiO2⁻
  water-component basis, preserving the source interval and all alternatives.
  One preferred value changes; wider source/version reviews stay tracked.
- Inventory all 97 selected rows of NEA zirconium volume 8 and add 148
  observations and 63 species. Fill 137 properties and change 11 selections
  under the existing policy. Add an open NBS free-sulfite reference; retain
  27 specific scientific/model holds and two heat-capacity routes separately.
  Zirconium stability regions change; the other 73 default diagrams are preserved.

- Add 86 NEA iron/nickel/tin ligand observations and 45 species, filling
  82 properties and changing four selections under the unchanged policy.
  Add open NBS free-ion references for thiocyanate, pyrophosphate and arsenate.
  Preserve aqueous, gas and liquid identities and document differences between
  the runtime ligand references and NEA's internally consistent reaction set.

- Add a distinct fixed-composition Fe0.932O phase with three NEA source-reviewed
  G/H/S estimates. Preserve fractional molar normalization, source metastability,
  third-law enthalpy assumptions and the omitted residual-entropy contribution.
  All earlier selections and the stoichiometric FeO request status are preserved.

- Review all 103 solid rows of the retained iron/nickel/tin NEA selected tables.
  Add 158 observations and 48 species, filling 115 properties and changing
  42 selections under the unchanged policy. Preserve all earlier evidence;
  keep distinct polymorphs, amorphous phases and complete hydrated formulas.
  Unsupported chemistry and unresolved compositions remain explicitly held.

- Apply written NEA-TDB permission under OECD data terms, preserve the evidence,
  and distribute OECD attribution with the required downstream acknowledgment.
  All 28 historical NEA requests already match stored observations; their reuse
  status is updated. NIST and other source permission holds remain separate.
- Add 25 NEA iron/nickel/tin observations and six aqueous species, filling 15
  properties. The unchanged policy changes ten earlier selections and preserves
  all alternatives. Exact locators retain units and source uncertainty intervals.
- Expose each reported observation's property-specific source locator through the
  database API, with the general source locator as fallback.

- Trace Nordstrom (1990) magnesium carbonate/bicarbonate models to the original
  Siebert/Hostetler (1977) studies and review 21 native association blocks.
  Document commercial activity-calibration ancestry, differing thermal models
  and an independently recovered federal dielectric source. Numerical imports
  remain held pending complete eligible reconstructions; release counts are unchanged.

- Review the original Christ/Hostetler (1970) magnesite study: distinguish the
  measured 90°C activity product from calculated values, document inherited
  CRC/JANAF supporting inputs and retain explicit reconstruction holds. This
  source-review checkpoint adds zero observations and preserves the database
  and paper numbers.

- Species without a recommended Gibbs energy are left out and reported by default;
  `allow_incomplete=False` and `--require-complete` stop instead.
- Ligand reservoirs are global, with a master switch and per-ligand toggles on the periodic table.
- Application: policy comparison dialog, copied code that reproduces the shown diagram
  (`pb.plot_uncertainty`), flagged source disagreements, grouped ligand complexes, background
  calculations behind a loading overlay, faster tables and tabs, no wheel changes on inputs.
- Application: a Sensitivity tab mapping where the stable species depends on the choice between
  eligible published Gibbs energies (`pb.selection_sensitivity`), the publications behind a diagram
  with BibTeX export, and search over elements, species, sources and commands (Ctrl+K).
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

- 855 species and 2840 retained observations across 74 supported elemental systems, with
  recommended Gibbs energies for 754.
- One conditional magnesite Gibbs alternative uses the original 1965 solubility
  evaluation and openly licensed ion/gas/water anchors. The ideal CO2 reference
  correction is explicit; source complexing and pressure assumptions remain attached.
  Existing preferred values are preserved. The JANAF-dependent decomposition fit
  remains a separate source hold.
- Four formation estimates reconstruct nesquehonite and five-Mg hydromagnesite from
  original calorimetric reaction heats and openly licensed constituent anchors.
  Earlier recommendations remain selected. The historical four-Mg hydromagnesite
  formula is disputed by the original authors; its reported value remains stored
  and is excluded from calculations pending independent phase evidence.
- Seven magnesium mineral observations: original artinite entropy with its residual-disorder
  model, and six openly licensed NBS properties. Lansfordite and a distinct four-Mg basic
  carbonate retain complete hydration. The unchanged NBS-first policy selects four older
  mineral properties; both older and later evaluations remain accessible. Corrected the
  artinite formation values' parent-publication locators.
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
