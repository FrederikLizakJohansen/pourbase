# Quick start

```python
import pourbase as pb

calculation = pb.calculate(pb.Scenario("Fe", concentration=10, concentration_unit="ppm"))
pb.plot_diagram(calculation.diagram)

probe = calculation.probe(pH=7, U_V=0)
print(probe.species.species)            # the stable species at pH 7, 0 V vs SHE
for boundary in calculation.boundaries:
    print(boundary.reaction, "|", boundary.equation)
```

```text
Fe₂O₃
Fe(OH)₂ + 2 H+ + 2 e- ⇌ Fe + 2 H2O | U = -0.1047 -0.0592·pH V vs SHE
Fe(OH)₂ + 2 H+ ⇌ Fe²⁺ + 2 H2O | pH = 8.050
...
```

The database comes with the package, so this runs offline. In the app, File → Copy Python code gives the script
for the diagram on the screen.

## Scenario

A [`Scenario`](../reference/calculation.md#pourbase.Scenario) holds everything that defines one diagram, in the
units you would normally use:

| Field | Default | Meaning |
|---|---|---|
| `symbol` | | The element, e.g. `"Fe"` |
| `mode` | `"fixed_activity"` | `"fixed_activity"` or `"mass_balance"` (closed total metal) |
| `concentration` | `-6.0` | The metal concentration in `concentration_unit` |
| `concentration_unit` | `"log10_molar"` | `"log10_molar"`, `"molar"`, `"ppm"` (mg of metal per litre) or `"wt_percent"` |
| `solution_density_kg_L` | `1.0` | Converts weight percent |
| `davies_ionic_strength_mol_L` | `None` | Davies activity coefficients at this ionic strength (mass balance) |
| `log10_gas_fugacity` | `0.0` | The fugacity of every gas relative to 1 bar |
| `ligands` | `()` | Buffered ligands, as [`LigandActivity`](../reference/calculation.md#pourbase.LigandActivity) |
| `pH_min`, `pH_max` | `0`, `14` | The pH range |
| `U_min_V`, `U_max_V` | `-1.5`, `1.5` | The potential range in V vs SHE |
| `pH_points`, `U_points` | `281`, `301` | The grid resolution |
| `allow_incomplete` | `True` | Leave out species without a recommended Gibbs energy; `False` raises `IncompleteSystemError` |
| `energy_policy` | `"experimental_only"` | `"experimental_then_mp"` fills terminal gaps with the stored Materials Project 300 K estimates |
| `activity_overrides` | `()` | `(record_id, log10_activity)` pairs that set one species' activity |
| `temperature_K` | `298.15` | 273.15 to 373.15 K, extrapolated from the stored enthalpies and entropies |

```python
pb.Scenario("Zn", mode="mass_balance", concentration=1e-6, concentration_unit="molar",
            davies_ionic_strength_mol_L=0.01)
pb.Scenario("Ag", ligands=(pb.LigandActivity("chloride-cl", log10_free_activity=-2),))
pb.Scenario("Ni", ligands=(pb.LigandActivity("ammonia-nh3", total_unbound_mol_L=0.1, acid_pKa=9.25),))
pb.Scenario("Cu", temperature_K=353.15)
pb.Scenario("Pt", energy_policy="experimental_then_mp")
```

A ligand is given either by its free activity (`log10_free_activity`) or by its total unbound concentration
(`total_unbound_mol_L`). With `acid_pKa`, protonation lowers the free activity at low pH.
`pb.open_database().available_ligands()` lists the ligand IDs.

## Calculation

[`calculate`](../reference/calculation.md#pourbase.calculate) returns a
[`Calculation`](../reference/calculation.md#pourbase.Calculation) with these attributes:

| Attribute | Holds |
|---|---|
| `diagram` | The [`PourbaixDiagram`](../reference/calculation.md#pourbase.PourbaixDiagram) or [`MassBalancedPourbaixDiagram`](../reference/calculation.md#pourbase.MassBalancedPourbaixDiagram): the grid, the stable species at each point and the species |
| `stable_species` | The species stable somewhere on the grid |
| `boundaries` | The boundaries, each as a reaction, an equation and its sources |
| `excluded` | The species left out, each with its reason |
| `fallback_species` | The species whose Gibbs energy is a Materials Project estimate |
| `concentration` | The concentration converted to molarity, with the assumptions used |
| `probe(pH, U_V)` | The stable species at one point; in the mass-balance model also the dissolved metal, the precipitated fraction and the speciation |
| `is_mass_balance` | Whether the mass-balance model was used |

```python
zinc = pb.calculate(pb.Scenario("Zn", mode="mass_balance", concentration=1e-6, concentration_unit="molar"))
probe = zinc.probe(pH=9, U_V=0)
print(probe.dissolved_metal_mol_L, probe.precipitated_fraction)
```

## Records and sources

```python
database = pb.open_database()
for record in database.species_records(["gfe-fe-fe2o3-q+0-solid-hematite"]):
    print(record.thermochemistry.gibbs_energy_J_mol)   # value, status, uncertainty and source
    for value in record.reported:                      # every published value
        print(value.value, value.status, value.source.citation)
```

`pb.open_database().available_systems()` lists the elemental systems, and
[`select`](../reference/selection.md#pourbase.select) returns the recommended value of every species and property
with the policy's reason (`basis`), the candidates it chose from and whether the species is flagged for review.
