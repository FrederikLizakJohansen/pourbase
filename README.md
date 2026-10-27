<p align="center">
  <img src="docs/logo-wordmark.svg#gh-light-mode-only" alt="pourbase" width="330">
  <img src="docs/logo-wordmark-dark.svg#gh-dark-mode-only" alt="pourbase" width="330">
</p>

pourbase is a source-linked database of experimental standard thermochemistry and a Python package
for calculating Pourbaix diagrams. The bundled SQLite database holds <!-- count:species -->1,771<!-- /count -->
aqueous, solid, liquid and gas species across <!-- count:systems -->75<!-- /count --> elemental systems, with
<!-- count:reported -->5,268<!-- /count --> reported values. Every value keeps its citation, its exact location in
the source, an evidence status, its uncertainty where reported, and every alternative value.

> [!NOTE]
> **A living database.** The data were gathered with agent-guided literature searches (GPT 5.6 Sol,
> GPT 6.1 Sol and Claude Opus 5). Every value links to the table, row or page it came from, so you
> can check it before you rely on it. Found an error or a better source? [Help improve the data](CONTRIBUTING.md).

<p align="center">
  <a href="https://frederiklizakjohansen.github.io/pourbase/">Documentation</a> ·
  <a href="STATISTICS.md">Dataset statistics</a> ·
  <a href="CONTRIBUTING.md">Contributing</a> ·
  <a href="docs/DATA_DICTIONARY.md">Data dictionary</a>
</p>

<p align="center">
  <img src="docs/assets/screens/periodic-table.png#gh-light-mode-only" alt="The pourbase periodic table: the stable species of every element at pH 7 and 0 V vs SHE" width="900">
  <img src="docs/assets/screens/dark/periodic-table.png#gh-dark-mode-only" alt="The pourbase periodic table: the stable species of every element at pH 7 and 0 V vs SHE" width="900">
</p>

## Install

```bash
pip install pourbase                           # database, Python API and command line
pip install "pourbase[gui]"                    # plus the desktop application
pip install "pourbase[gui,materials-project]"  # plus Materials Project comparisons
pip install "pourbase[mcp]"                    # plus the MCP server for language-model agents
```

Python 3.11 or newer. The database ships inside the package; calculations run offline with no
download, API key or data path. For development, clone the repository, run `pip install -e ".[gui]"`
and test with `python -m unittest discover -s tests`.

## Desktop application

`pourbase-gui` (or `pourbase gui`, which prints errors to the terminal on Windows) opens a periodic table coloured by the stable species of every element at a chosen
pH, potential and temperature, or by the share of a pH–potential window where an element is immune,
passive or corroding. Click an element to open its system:

- fixed-activity and closed total-metal (mass-balance) diagrams, in ppm, molarity or weight percent,
  with Davies activity coefficients, <!-- count:ligands -->33<!-- /count --> buffered ligands and water presets (seawater, river water,
  simulated body fluid, saline);
- temperatures from 0 to 100 °C, extrapolated from the stored entropies and enthalpies;
- a probe that reports the stable species, its Gibbs energy, uncertainty and source, and the margin
  to the runner-up; hatching where another species lies within 1–3 combined uncertainties;
- the sources behind the diagram, with BibTeX, and the sensitivity of every boundary to the
  alternative published values;
- regions where a species or kind of species is stable with a chosen margin;
- paths through pH and potential with the boundaries they cross, and measured points imported from
  CSV in any reference electrode;
- solubility and ligand-predominance diagrams at fixed potential, species fractions along pH, and
  concentration sweeps drawn as a rotatable 3D stack;
- comparisons with a second element, concentration or temperature on linked axes, overlays of a
  second element, and linked pop-out windows;
- the official Materials Project diagram beside the experimental one, with an agreement map (needs
  the `materials-project` extra and a free [API key](https://materialsproject.org/api));
- undo and redo, search (Ctrl+K), sessions saved as `.pourbase.json`, and export of figures (PNG,
  PDF, SVG), grids (CSV) and the equivalent Python code.

## Python

```python
import pourbase as pb

calculation = pb.calculate(pb.Scenario("Fe", concentration=10, concentration_unit="ppm"))
pb.plot_diagram(calculation.diagram)

probe = calculation.probe(pH=7, U_V=0)
print(probe.species.species)
for boundary in calculation.boundaries:
    print(boundary.reaction, boundary.equation, boundary.source_ids)
```

`Scenario` takes the other settings in everyday units:

```python
pb.Scenario("Zn", mode="mass_balance", concentration=1e-6, concentration_unit="molar",
            davies_ionic_strength_mol_L=0.01)
pb.Scenario("Ag", ligands=(pb.LigandActivity("chloride-cl", log10_free_activity=-2),))
pb.Scenario("Cu", temperature_K=353.15)
pb.Scenario("Pt", energy_policy="experimental_then_mp")  # fill terminal gaps with Materials Project estimates
```

Analyses of a calculation:

| Function | Answers |
|---|---|
| `stability_margin`, `stability_uncertainty` | how firmly a species is stable, given the uncertainties |
| `selection_sensitivity` | how the diagram moves with each alternative published value |
| `stability_region`, `screen_window` | where a species or kind is stable; which elements are passive in a window |
| `phase_path` | the stable species and boundary crossings along a path |
| `screen_periodic_table` | the stable species of every element at one point |
| `speciation_profile`, `solubility`, `ligand_predominance` | fractions along pH, and fixed-potential diagrams |
| `ConcentrationSweepEngine` | diagrams over a range of metal activities |
| `OfficialMaterialsProjectComparator` | agreement with the official Materials Project diagram |

```python
region = pb.stability_region(calculation, "passivation", min_margin_J_mol=5000)
print(f"{region.fraction:.0%} passive, pH {region.pH_range}")
```

Species without a recommended Gibbs energy are left out and listed with every result.
`allow_incomplete=False` instead raises `IncompleteSystemError` when a system contains such species.

Your own data: `pb.with_user_species(pb.open_database(), "own.csv")` adds or replaces species
(format in `pourbase.user_data`; results mark them `user_supplied`), and `pb.open_dataset("own.csv")`
calculates with your species alone. Both open in the application from the File menu.

With the same water energy and Nernst slope, every bundled system reproduces pymatgen's
`PourbaixEntry` evaluation; `scripts/pymatgen_crosscheck.py` writes the comparison to
[`docs/validation/`](docs/validation/pymatgen-crosscheck.md).

## Command line

```bash
pourbase systems
pourbase plot Fe --concentration 10 --unit ppm --output fe.png --grid-csv fe.csv
pourbase plot Zn --mode mass_balance --total-metal 1e-6 --output zn.png
pourbase sweep Fe --minimum -10 --maximum 0 --points 7 --output fe-sweep.png
```

## Agents (MCP)

`pourbase-mcp` is a [Model Context Protocol](https://modelcontextprotocol.io) server that gives
language-model agents the database and the engine:

```bash
claude mcp add pourbase -- pourbase-mcp
```

Its tools list systems and ligands, search species, return full evidence records, calculate and
render diagrams, probe a point, and compare selection policies. `--dataset`, `--species` and
`--policy` start it on your own data or policy.

## How values are selected

The database retains every published value. A selection policy,
[`selection-policy.toml`](src/pourbase/data/selection-policy.toml), determines the recommended value
for each species and property at runtime. It ranks sources by evidence class (A international critical
reviews, B critical compilations, C single-system evaluations, D single experimental papers,
E estimates, F computed values) and lists every exception with its reason. Values are never averaged,
and missing values stay visible as evidence gaps. Materials Project estimates for the
<!-- count:terminal_gaps -->six<!-- /count --> species without a usable published Gibbs energy are stored separately
and used only on request (`energy_policy="experimental_then_mp"`).

Edit a copy of the policy to calculate with your own rule:

```python
policy = pb.SelectionPolicy.load("my-policy.toml")
calculation = pb.calculate(pb.Scenario("Fe"), pb.with_policy(pb.open_database(), policy))
changes = pb.compare_policies(pb.open_database(), pb.SelectionPolicy.default(), policy)
```

## Scientific limits

- 1 bar, in water; 0–100 °C, with enthalpies and entropies of formation held at their 298.15 K
  values. Away from 25 °C, species without entropy data and all ligand species are left out.
- One conserved metal per calculation; ligands are buffered reservoirs.
- The Davies model applies up to an ionic strength of 0.1 mol L⁻¹.
- Differences between experimental and DFT formation energies are diagnostics, not error estimates.

## Contributing, citation and licence

Report a wrong value, a missing species or a better source with the
[data issue form](https://github.com/FrederikLizakJohansen/pourbase/issues/new/choose);
[CONTRIBUTING.md](CONTRIBUTING.md) describes what to include.

pourbase is released under GPL-3.0. Cite this release ([`CITATION.cff`](CITATION.cff)) and the
sources of the values you use. [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) lists the terms of
the data sources.

## Acknowledgements

We thank the OECD Nuclear Energy Agency Thermochemical Database Project for confirming the terms
under which pourbase redistributes NEA-TDB selected values. Its selected data are used with
acknowledgment of the OECD and the Nuclear Energy Agency:

<!-- nea-volumes -->
- Grenthe, I., Fuger, J., Konings, R. J. M., Lemire, R. J., Muller, A. B., Nguyen-Trung, C. and Wanner, H. *Chemical Thermodynamics of Uranium*. OECD Nuclear Energy Agency, Chemical Thermodynamics Series Volume 1 (1992).
- Rard, J. A., Rand, M. H., Anderegg, G. and Wanner, H. *Chemical Thermodynamics of Technetium*. OECD Nuclear Energy Agency, Chemical Thermodynamics Series Volume 3 (1999).
- Guillaumont, R., Fanghänel, T., Fuger, J., Grenthe, I., Neck, V., Palmer, D. A. and Rand, M. H. *Update on the Chemical Thermodynamics of Uranium, Neptunium, Plutonium, Americium and Technetium*. OECD Nuclear Energy Agency, Chemical Thermodynamics Series Volume 5 (2003).
- Gamsjäger, H., Bugajski, J., Gajda, T., Lemire, R. J. and Preis, W. *Chemical Thermodynamics of Nickel*. OECD Nuclear Energy Agency, Chemical Thermodynamics Series Volume 6 (2005).
- Olin, Å., Noläng, B., Osadchii, E. G., Öhman, L.-O. and Rosén, E. *Chemical Thermodynamics of Selenium*. OECD Nuclear Energy Agency, Chemical Thermodynamics Series Volume 7 (2005).
- Brown, P. L., Curti, E. and Grambow, B., with Ekberg, C. *Chemical Thermodynamics of Zirconium*. OECD Nuclear Energy Agency, Chemical Thermodynamics Series Volume 8 (2005).
- Rand, M., Fuger, J., Grenthe, I., Neck, V. and Rai, D. *Chemical Thermodynamics of Thorium*. OECD Nuclear Energy Agency, Chemical Thermodynamics Series Volume 11 (2008).
- Gamsjäger, H., Gajda, T., Sangster, J., Saxena, S. K. and Voigt, W. *Chemical Thermodynamics of Tin*. OECD Nuclear Energy Agency, Chemical Thermodynamics Series Volume 12 (2012).
- Lemire, R. J., Berner, U., Musikas, C., Palmer, D. A., Taylor, P. and Tochiyama, O. *Chemical Thermodynamics of Iron, Part 1*. OECD Nuclear Energy Agency, Chemical Thermodynamics Series Volume 13a (2013).
- Lemire, R. J., Palmer, D. A., Taylor, P. and Schlenz, H. *Chemical Thermodynamics of Iron, Part 2*. OECD Nuclear Energy Agency, Chemical Thermodynamics Series Volume 13b (2020).
- Grenthe, I., Gaona, X., Plyasunov, A. V., Rao, L., Runde, W. H., Grambow, B., Konings, R. J. M., Smith, A. L. and Moore, E. E. *Second Update on the Chemical Thermodynamics of Uranium, Neptunium, Plutonium, Americium and Technetium*. OECD Nuclear Energy Agency, Chemical Thermodynamics Series Volume 14 (2020).
- Rand, M., Palmer, D. A., Fuger, J. and Gajda, T. *Chemical Thermodynamics of Selected Ancillary Compounds of Interest to Radioactive Waste Management*. OECD Nuclear Energy Agency, Chemical Thermodynamics Series Volume 15 (2024).
<!-- /nea-volumes -->

Materials Project data are used under CC BY 4.0 and keep their IDs, versions and attribution.
