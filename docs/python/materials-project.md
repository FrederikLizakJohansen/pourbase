# Materials Project

To compare pourbase with the official Materials Project diagrams, install the `materials-project` extra and get
a free [API key](https://materialsproject.org/api).

## The official diagram

[`OfficialMaterialsProjectComparator`](../reference/materials-project.md#pourbase.OfficialMaterialsProjectComparator)
downloads the Materials Project Pourbaix entries of an element and evaluates them on the same grid and at the same
activity as an experimental diagram:

```python
import os
import pourbase as pb

database = pb.open_database()
calculation = pb.calculate(pb.Scenario("Fe"), database)
comparator = pb.OfficialMaterialsProjectComparator(
    pb.PourbaixEngine(database), pb.OfficialMaterialsProjectClient(os.environ["MP_API_KEY"]))
comparison = comparator.compare("Fe", calculation.diagram.conditions)

print(f"{comparison.equivalent_domain_fraction:.0%} of the grid agrees")
print(f"{comparison.water_window_equivalent_domain_fraction:.0%} within the water window")
pb.plot_official_materials_project_comparison(comparison)
```

By default (`filter_solids=True`), only the solids that are stable on the compositional phase diagram are kept,
as in pymatgen. `use_gibbs_300K=True` applies the Materials Project's machine-learned 300 K correction to the
solids. Species are matched by what they are thermodynamically: solids by their oxygen and hydrogen per metal atom,
and dissolved species by their protons, electrons and metal atoms.

## Stored estimates

The database contains Materials Project estimates of the Gibbs energy at 300 K for the solids that are terminal
evidence gaps. They are only used when you ask for them:

```python
pb.calculate(pb.Scenario("Pt", energy_policy="experimental_then_mp"))
```

These species are labelled in the results (`calculation.fallback_species`).

## Formation energies

The database also contains Materials Project formation energies (GGA, GGA+U and r²SCAN) for the experimental
solids that could be matched to a Materials Project structure. `pourbase mp-thermo-figures --output-dir mp-thermochemistry`, or
[`write_mp_thermochemistry_bundle`](../reference/materials-project.md#pourbase.write_mp_thermochemistry_bundle), writes the
comparison figures, the data behind them, the metrics for each method and notes on the methods.
