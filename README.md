# pourbase

pourbase is a source-linked database of experimental standard thermochemistry and a Python package
for calculating Pourbaix diagrams at 298.15 K and 1 bar. The bundled SQLite database holds 460
aqueous, solid, liquid and gas species across 74 elemental systems. Every value keeps its citation,
exact source location, evidence status, uncertainty when available, phase identity and scientific
warnings. Reviewed crystalline phases are matched to Materials Project structures and DFT formation
energies.

## Install

```bash
pip install pourbase                           # database, calculations and command line
pip install "pourbase[gui]"                    # plus the desktop application
pip install "pourbase[gui,materials-project]"  # plus live Materials Project comparisons
```

The database ships inside the package. Experimental calculations run offline and need no download,
API key or data path.

## Desktop application

```bash
pourbase-gui          # or: pourbase gui Fe
```

The application opens on a periodic table showing the stable species of every supported element at
a chosen pH and potential (SHE or RHE). Hover over an element for its stable species and Gibbs
source; click it to open the system. For one system you get:

- fixed-activity and closed total-metal (mass-balance) diagrams that update as you change settings;
- concentration as log10 molarity, molarity, ppm or weight percent; ideal or Davies activity
  coefficients; gas fugacity; ligand reservoirs for the ligands that complex the element;
- a probe with the stable species, its Gibbs energy, uncertainty and source, and in mass-balance
  mode the dissolved and precipitated metal;
- tables of every species with recommended and reported values and citations, and of the balanced
  boundary reactions and Nernst equations;
- species fractions along pH;
- a concentration sweep over log10 activity, pH and Eh, drawn as a rotatable 3D stack that can be
  sliced along any axis;
- a DFT comparison with the official Materials Project diagram: both diagrams and an agreement map
  side by side, also available in the sweep and speciation views;
- export of figures (PNG, PDF, SVG), calculated grids (CSV) and the equivalent Python code.

The DFT comparison needs the `materials-project` extra and a free API key from the
[Materials Project](https://materialsproject.org/api). Enter it under Tools → Materials Project API
key; the application can remember it in the system keyring.

## Python

A `Scenario` describes one diagram in everyday units; `calculate` returns the diagram with its
evidence:

```python
import pourbase as pb

calculation = pb.calculate(pb.Scenario("Fe", concentration=10, concentration_unit="ppm"))
pb.plot_diagram(calculation.diagram)

for boundary in calculation.boundaries:
    print(boundary.reaction, boundary.equation, boundary.source_ids)

probe = calculation.probe(pH=7, eh_V=0)
record = pb.open_database().species_records([probe.species.record_id])[0]
print(probe.species.species, record.thermochemistry.gibbs_energy_J_mol.source.citation)
```

Conserve a closed total-metal inventory, with Davies activity coefficients, and follow the species
fractions along pH:

```python
calculation = pb.calculate(pb.Scenario(
    "Zn", mode="mass_balance", concentration=1e-6, concentration_unit="molar",
    davies_ionic_strength_mol_L=0.01,
))
pb.plot_speciation_profile(pb.speciation_profile(calculation.diagram, eh_V=0.0))
```

Add buffered ligands, here chloride at a free activity of 10⁻²:

```python
chloride = pb.LigandActivity("chloride-cl", log10_free_activity=-2)
pb.plot_diagram(pb.calculate(pb.Scenario("Ag", ligands=(chloride,))).diagram)
```

Six solids lack a recommended experimental Gibbs energy. Such systems raise
`IncompleteSystemError` unless you leave those species out or use the separately stored Materials
Project 300 K estimates:

```python
exploratory = pb.calculate(pb.Scenario("Pt", allow_incomplete=True))
estimated = pb.calculate(pb.Scenario("Pt", energy_policy="experimental_then_mp"))
```

The stable species of every element at one pH and potential:

```python
screen = pb.screen_periodic_table(pH=7, potential_V=0.4, reference="RHE")
print(screen.element("Fe").stable.species, screen.calculated_count)
```

Sweep the metal activity; levels are stored compactly and the progress callback can cancel:

```python
conditions = pb.Scenario("Fe").conditions()
sweep = pb.ConcentrationSweepEngine(pb.open_database()).calculate("Fe", conditions, -10, 0, points=41)
pb.plot_concentration_sweep(sweep, probe_pH=7, probe_eh_V=0)
```

Compare with the official Materials Project diagram (needs the `materials-project` extra):

```python
from pourbase import OfficialMaterialsProjectClient, OfficialMaterialsProjectComparator, PourbaixEngine

client = OfficialMaterialsProjectClient(api_key="your Materials Project API key")
comparison = OfficialMaterialsProjectComparator(PourbaixEngine(pb.open_database()), client).compare(
    "Fe", pb.Scenario("Fe").conditions()
)
pb.plot_official_materials_project_comparison(comparison)
print(comparison.equivalent_domain_fraction, comparison.materials_project.database_version)
```

The lower-level `PourbaixEngine`, `MassBalanceEngine` and `PourbaixConditions` take the same
settings as explicit models, for custom calculations.

## Command line

```bash
pourbase systems
pourbase plot Fe --output fe.png
pourbase plot Zn --mode mass_balance --total-metal 1e-6 --output zn.png
pourbase plot Fe --concentration 10 --unit ppm --grid-csv fe-grid.csv
pourbase plot Pt --use-mp-fallbacks --output pt.png
pourbase sweep Fe --minimum -10 --maximum 0 --points 7 --output fe-sweep.png
pourbase mp-thermo-figures --output-dir mp-thermochemistry
```

## How values are selected

`reported_thermochemistry` holds every retained value from every source. `thermochemistry` holds
one recommended value per property, which the calculations use. The recommendation is chosen for
the exact species, phase, polymorph, temperature, pressure and standard state, and for the
traceability and quality of the evaluation. Values are not averaged: many apparent alternatives are
copies of the same measurement or use different conventions. Missing values stay visible as
explicit evidence gaps.

Solids are compared with Materials Project on their O and H content per metal, and aqueous species
on their proton and electron coefficients and metal count. Differences between experimental Gibbs
energies and DFT formation energies are diagnostics, not experimental error estimates.

## Concentration conventions

- `log10_molar`: base-10 logarithm of the concentration relative to 1 mol L⁻¹.
- `molar`: mol of elemental metal per litre.
- `ppm`: mg of elemental metal per litre of solution.
- `wt_percent`: mass percentage of elemental metal in the solution; the solution density (default
  1 kg L⁻¹) converts mass to volume.

In fixed-activity mode the concentration sets the activity of every aqueous metal species. In
mass-balance mode it sets the conserved total metal concentration. Atomic weights follow
[CIAAW](https://ciaaw.org/atomic-weights.htm).

## Scientific limits

- 298.15 K and 1 bar, in water.
- One independently conserved metal per calculation.
- Fixed-activity mode treats aqueous activities as externally buffered.
- The Davies model applies up to an ionic strength of 0.1 mol L⁻¹, as a fixed background.
- Ligands are buffered reservoirs; there is no closed ligand balance.
- `allow_incomplete=True` omits species without a recommended Gibbs energy and gives an
  exploratory diagram.
- Materials Project comparisons use one activity for all aqueous species and ligand-free systems.

## Repository

| Path | Contents |
|---|---|
| `src/pourbase/` | Python package, with the database in `data/` and the application in `gui/` |
| `docs/` | Data dictionary and exploratory temperature-trend model |
| `paper/` | LaTeX data paper, generated statistics and figures |
| `tests/` | Database, calculation and application tests |

Run the tests with `python -m unittest discover -s tests`. Build the paper with `make -C paper`.

## Citation and licence

pourbase is released under GPL-3.0. Cite this release (`CITATION.cff`) and the sources attached to
the values you use. `THIRD_PARTY_NOTICES.md` lists the terms of the data sources, and
`docs/DATA_DICTIONARY.md` describes every table.
