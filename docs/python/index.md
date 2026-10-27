# Quick start

```python
import pourbase as pb

calculation = pb.calculate(pb.Scenario("Fe", concentration=10, concentration_unit="ppm"))
pb.plot_diagram(calculation.diagram)

probe = calculation.probe(pH=7, U_V=0)
print(probe.species.species)            # the stable species at pH 7, 0 V
for boundary in calculation.boundaries:
    print(boundary.reaction, boundary.equation, boundary.source_ids)
```

[`Scenario`](../reference/calculation.md#pourbase.Scenario) takes the settings in everyday units:

```python
pb.Scenario("Zn", mode="mass_balance", concentration=1e-6, concentration_unit="molar",
            davies_ionic_strength_mol_L=0.01)
pb.Scenario("Ag", ligands=(pb.LigandActivity("chloride-cl", log10_free_activity=-2),))
pb.Scenario("Cu", temperature_K=353.15)
pb.Scenario("Pt", energy_policy="experimental_then_mp")   # fill terminal gaps with Materials Project estimates
```

Species without a recommended Gibbs energy are left out and listed with every result.
`allow_incomplete=False` raises `IncompleteSystemError` instead.

## Records and sources

```python
database = pb.open_database()
for record in database.species_records(["gfe-fe-fe2o3-q+0-solid-hematite"]):
    print(record.thermochemistry.gibbs_energy_J_mol)   # value, status, uncertainty and source
    for value in record.reported:                      # every published value
        print(value.value, value.status, value.source.citation)
```

File → Copy Python code in the app gives the script for the diagram on screen.
