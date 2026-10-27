# Plotting and export

The plotting functions use Matplotlib and return its figures and axes, so they can be changed and saved in the
usual way.

```python
import pourbase as pb

calculation = pb.calculate(pb.Scenario("Fe"))
ax = pb.plot_diagram(calculation.diagram, title="Iron, a = 10⁻⁶")
pb.plot_uncertainty(calculation.diagram, ax=ax, confidence_sigma=1)
ax.figure.savefig("fe.png", dpi=300)
```

| Function | Draws |
|---|---|
| [`plot_diagram`](../reference/plotting.md#pourbase.plot_diagram) | One diagram, fixed activity or mass balance. Domain labels, legend, boundaries and water lines can be turned off, and `colors` sets your own colors by record ID |
| [`plot_uncertainty`](../reference/plotting.md#pourbase.plot_uncertainty) | Hatching on existing axes where another species lies within `confidence_sigma` combined uncertainties |
| [`plot_boltzmann_diagram`](../reference/plotting.md#pourbase.plot_boltzmann_diagram) | A blend of the soft-minimum weights from [`boltzmann_smooth`](../reference/plotting.md#pourbase.boltzmann_smooth) |
| [`plot_mass_balance_summary`](../reference/plotting.md#pourbase.plot_mass_balance_summary) | Phase domains, precipitated fraction and dissolved metal of a mass-balance diagram |
| [`plot_speciation_profile`](../reference/plotting.md#pourbase.plot_speciation_profile) | Species fractions along pH from `speciation_profile` |
| [`plot_concentration_sweep`](../reference/plotting.md#pourbase.plot_concentration_sweep) | A concentration sweep as stacked 3D boundaries with two projections |
| [`diagram_figure`](../reference/plotting.md#pourbase.diagram_figure) | A whole figure of a diagram with the display options of the app: labels, legend, boundaries, water lines, plating potential and blending |
| [`species_colors`](../reference/plotting.md#pourbase.species_colors) | The colors the app and the plots use, keyed by record ID |
| [`save_figure`](../reference/plotting.md#pourbase.save_figure) | Saves a figure, at 300 dpi by default |

## Blended diagrams

[`boltzmann_smooth`](../reference/plotting.md#pourbase.boltzmann_smooth) calculates the weights
exp(−(G − Gmin)/width) for the dissolved species of a fixed-activity diagram. At a width of RT (2.48 kJ/mol at
25 °C, the default) the weights equal the species fractions of the mass-balance model.

```python
smoothed = pb.boltzmann_smooth(calculation.diagram, 2480)
pb.plot_boltzmann_diagram(smoothed)
```

## Grids

[`grid_csv`](../reference/plotting.md#pourbase.grid_csv) returns the grid as CSV text, with the pH, potential
(V vs SHE), record ID, species and phase of each point, and for a mass balance also the metal in each species.

```python
open("fe-grid.csv", "w").write(pb.grid_csv(calculation.diagram))
```

[`boundary_equations`](../reference/calculation.md#pourbase.boundary_equations) and `calculation.boundaries`
give the boundaries as balanced reactions and equations.
[`phase_boundary_segments`](../reference/calculation.md#pourbase.phase_boundary_segments) gives the boundary lines
along the edges of the grid cells.
