# Analyses

The analyses take a [`Calculation`](../reference/calculation.md#pourbase.Calculation) or its diagram. The examples
on this page use iron at the default activity of 10⁻⁶:

```python
import pourbase as pb

calculation = pb.calculate(pb.Scenario("Fe"))
database = pb.open_database()
```

## How stable is the stable species?

[`stability_margin`](../reference/analyses.md#pourbase.stability_margin) gives the next species at a point, the
energy gap to it per mole of metal with its combined uncertainty, and the nearest boundary in each direction of
potential and pH.

```python
margin = pb.stability_margin(calculation.diagram, pH=7, U_V=0)
print(margin.species.species, margin.runner_up.species, margin.margin_J_mol_metal / 1000)
# Fe₂O₃ FeOOH 1.25
print(margin.higher_potential.species.species, margin.higher_potential.distance)   # FeO₄²⁻, 1.41 V higher
```

[`stability_uncertainty`](../reference/analyses.md#pourbase.stability_uncertainty) marks the grid points where a
competing species lies within `confidence_sigma` combined uncertainties. Species without a reported uncertainty get
`assumed_uncertainty_J_mol` (2 kJ/mol by default), and `assumed_record_ids` lists them.

```python
uncertain = pb.stability_uncertainty(calculation.diagram, confidence_sigma=1)
print(uncertain.uncertain.mean())        # fraction of the grid within one combined uncertainty
```

## Where is a species stable?

[`stability_region`](../reference/analyses.md#pourbase.stability_region) finds where a target is stable by at
least a given margin. The target is a record ID or one of the kinds in `pb.KINDS`: `"immunity"`, `"passivation"`,
`"corrosion"` or `"solid"`. The margin is either an energy or `k_sigma` combined uncertainties.

```python
region = pb.stability_region(calculation, "passivation", min_margin_J_mol=5000)
print(f"{region.fraction:.0%} passive, pH {region.pH_range}")     # 40% passive, pH (2.35, 14.0)
```

[`screen_window`](../reference/analyses.md#pourbase.screen_window) does the same for all elements over a pH and
potential window. For each element it gives the fraction of the window and the smallest margin in it.

```python
window = pb.screen_window(database, "passivation", pH=(6, 9), U_V=(-0.2, 0.4))
print(window["Al"].fraction)      # 1.0
```

## Along a path

[`phase_path`](../reference/analyses.md#pourbase.phase_path) follows straight lines through points of `(pH, U)`,
or a smooth curve with `smooth=True`. It returns the stable species along the path and the boundaries it crosses.

```python
path = pb.phase_path(calculation, (2, 0.8), (12, -0.6))
for crossing in path.crossings:
    print(f"{crossing.fraction:.0%}", crossing.before.species, "→", crossing.after.species, crossing.boundary.equation)
```

[`assess_points`](../reference/analyses.md#pourbase.assess_points) places measured points on the diagram and gives
the predicted species, the next species and the margin for each.

```python
points = [pb.MeasuredPoint("A", pH=7, U_V=0), pb.MeasuredPoint("B", pH=2, U_V=1.0)]
for item in pb.assess_points(calculation, points):
    print(item.point.label, item.species.species, item.within_uncertainty)
```

## All elements at one point

[`screen_periodic_table`](../reference/analyses.md#pourbase.screen_periodic_table) does what the periodic table in
the app does. It returns the lowest-energy species of each element at one pH and potential, with its category, its
margin and the source of its Gibbs energy.

```python
screen = pb.screen_periodic_table(pH=0, potential_V=1.6)
print([item.symbol for item in screen.elements if item.category is pb.Category.SOLID_OXIDE])
# ['Ti', 'Zr', 'Nb', 'Mo', 'Ru', ...]
```

With `reference="RHE"` the potential is taken against the RHE. The concentration, temperature, ligands and evidence
policy are given as for `Scenario`.

## Sensitivity to the published values

[`selection_sensitivity`](../reference/analyses.md#pourbase.selection_sensitivity) draws random selections, taking
one eligible Gibbs energy per species each time, and reports where the stable species changes. It also gives, for
each species, how much of the diagram changes when only its value is replaced. With `classes={"A", "B", "C"}` it
only draws from critical evaluations.

```python
sensitivity = pb.selection_sensitivity(calculation.diagram, database.selections, samples=300)
print(f"{sensitivity.unfixed_fraction:.1%} of the diagram depends on the choice of value")
for species in sensitivity.species:
    print(species.species, species.spread_J_mol / 1000, species.changed_fraction_alone)
```

## Speciation and diagrams at fixed potential

In the mass-balance model, [`speciation_profile`](../reference/analyses.md#pourbase.speciation_profile) gives the
fraction of the metal in each species along pH at one potential, and
[`speciation_at`](../reference/analyses.md#pourbase.speciation_at) gives the fractions at one point.

```python
zinc = pb.calculate(pb.Scenario("Zn", mode="mass_balance", concentration=1e-6, concentration_unit="molar"))
profile = pb.speciation_profile(zinc.diagram, U_V=0)
print(pb.speciation_at(zinc.diagram, pH=10, U_V=0)[0])
```

[`solubility`](../reference/analyses.md#pourbase.solubility) gives the dissolved metal in equilibrium with the most
stable condensed phase along pH at one potential.
[`ligand_predominance`](../reference/analyses.md#pourbase.ligand_predominance) gives the stable species over pH and
the free activity of a ligand.

```python
curve = pb.solubility(calculation, U_V=0)                 # curve.log10_metal_mol_L along curve.pH
silver = pb.calculate(pb.Scenario("Ag", ligands=(pb.LigandActivity("chloride-cl", log10_free_activity=-2),)))
predominance = pb.ligand_predominance(silver, "chloride-cl", U_V=0.5)
```

[`plating_potentials`](../reference/analyses.md#pourbase.plating_potentials) gives the potential at which each
simple cation deposits as the metal, at the set activity.

```python
print(pb.plating_potentials(calculation.diagram, database)[0].potential_V_vs_SHE)   # Fe²⁺ + 2 e- ⇌ Fe: -0.648
```

## Over a range of concentrations

[`ConcentrationSweepEngine`](../reference/analyses.md#pourbase.ConcentrationSweepEngine) calculates fixed-activity
diagrams at evenly spaced activities. [`plot_concentration_sweep`](plotting.md) draws them as a 3D stack.

```python
sweep = pb.ConcentrationSweepEngine(database).calculate("Fe", calculation.diagram.conditions, -10, -2, points=5)
```

## Concentrations

```python
pb.convert_concentration("Fe", 10, "ppm").molar_concentration      # 1.79e-4 mol/L
pb.express_concentration("Fe", 1e-4, "ppm")                         # 5.58 ppm
pb.metal_molarity_from_mass("Fe", mass_g=0.1, solution_volume_L=1)  # 1.79e-3 mol/L
```

`convert_concentration` also records its assumptions, for example that ppm means milligrams of metal per litre.
