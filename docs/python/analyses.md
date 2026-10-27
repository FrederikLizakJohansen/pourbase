# Analyses

| Function | Answers |
|---|---|
| [`stability_margin`](../reference/analyses.md#pourbase.stability_margin), [`stability_uncertainty`](../reference/analyses.md#pourbase.stability_uncertainty) | How firmly a species is stable, given the uncertainties |
| [`selection_sensitivity`](../reference/analyses.md#pourbase.selection_sensitivity) | How the diagram moves with each alternative published value |
| [`stability_region`](../reference/analyses.md#pourbase.stability_region), [`screen_window`](../reference/analyses.md#pourbase.screen_window) | Where a species or kind is stable; which elements are passive in a window |
| [`phase_path`](../reference/analyses.md#pourbase.phase_path) | The stable species and boundary crossings along a path |
| [`screen_periodic_table`](../reference/analyses.md#pourbase.screen_periodic_table) | The stable species of every element at one point |
| [`speciation_profile`](../reference/analyses.md#pourbase.speciation_profile), [`solubility`](../reference/analyses.md#pourbase.solubility), [`ligand_predominance`](../reference/analyses.md#pourbase.ligand_predominance) | Fractions along pH, and fixed-potential diagrams |
| [`ConcentrationSweepEngine`](../reference/analyses.md#pourbase.ConcentrationSweepEngine) | Diagrams over a range of metal activities |

```python
import pourbase as pb

calculation = pb.calculate(pb.Scenario("Fe"))
region = pb.stability_region(calculation, "passivation", min_margin_J_mol=5000)
print(f"{region.fraction:.0%} passive, pH {region.pH_range}")

screen = pb.screen_periodic_table(pH=0, potential_V=1.6)
print([item.symbol for item in screen.elements if item.category.name == "SOLID_OXIDE"])
```
