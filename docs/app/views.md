# Views of an element

The tabs above an element's diagram show the same calculation in different ways. They follow the current
[settings](settings.md). When a view cannot be made with the current settings, it says why and, where possible,
offers a button that changes the setting.

## Diagram

The diagram with the probe, paths, measured points and region tools, described in [An element](system.md).

## Species

![Species of the iron system](../assets/screens/fe-species.png#only-light)![Species of the iron system](../assets/screens/dark/fe-species.png#only-dark)

The Species view lists the species of the system.

| Column | Shows |
|---|---|
| Species, Phase | The name and phase. The color swatch is the species' color in the diagram |
| Ligand | The ligand of a complex |
| Status | The status of the recommended Gibbs energy, or why the species is left out |
| Class | The evidence class (A–F) of the source of the recommended value |
| Spread (kJ/mol) | The range of the eligible Gibbs energies, marked when it is larger than the policy's review threshold |
| Stable | Whether the species is stable anywhere in the diagram |
| Warnings | The number of notes on the record |
| Record ID | The identifier in the database |

Selecting a row shows the full record next to the table. For the Gibbs energy of formation, the formation enthalpy
and the absolute entropy, it gives the recommended value with its status, evidence class, source family and source,
and the reason the policy chose it. Below that are the other reported values with their status and source, with
the ineligible ones marked. The record ends with the phase identity, any Materials Project estimate and the notes.
Species that were left out are listed with the reason.

## Boundaries

![Boundaries of the iron diagram](../assets/screens/fe-boundaries.png#only-light)![Boundaries of the iron diagram](../assets/screens/dark/fe-boundaries.png#only-dark)

The Boundaries view lists the boundaries between neighbouring regions of the diagram.

| Column | Shows |
|---|---|
| Reaction | The balanced reaction per metal atom, with H⁺, e⁻ and water |
| Equation | The line at the set activities, for example `U = +0.1514 −0.0592·pH V vs SHE`, or `pH = …` for a vertical boundary |
| Kind | Redox, acid–base, or numerical in the mass-balance model |
| Sources of the Gibbs energies | The sources for both species |

In the mass-balance model the boundaries come from a numerical equilibrium that includes the amount of metal, so
there is no single equation for them.

## Speciation

![Speciation of iron at 10⁻⁶ mol/L](../assets/screens/fe-speciation.png#only-light)![Speciation of iron at 10⁻⁶ mol/L](../assets/screens/dark/fe-speciation.png#only-dark)

The Speciation view works in the mass-balance model. In the fixed-activity model it offers a button to switch,
because a fixed activity does not define an amount of metal to share between species.

The upper plot shows the fraction of the metal in each species along pH at the probe potential, including any
solid. The strip below shows the main species along pH, with one row for the experimental data and, once the
Materials Project entries are loaded, one row for the Materials Project diagram at the same total activity.

## Fixed potential

This view draws two classic diagrams at the probe potential. The potential can be set here, and moving the probe
in the diagram also changes it.

The solubility diagram shows the dissolved metal in equilibrium with the most stable condensed phase, against pH.

![Solubility of iron at 0 V](../assets/screens/fe-solubility.png#only-light)![Solubility of iron at 0 V](../assets/screens/dark/fe-solubility.png#only-dark)

The ligand predominance diagram shows the stable species over pH and the free activity of one ligand.

![Silver species over pH and chloride activity at 0.6 V](../assets/screens/ag-ligand-predominance.png#only-light)![Silver species over pH and chloride activity at 0.6 V](../assets/screens/dark/ag-ligand-predominance.png#only-dark)

## Sensitivity

![Sensitivity of the iron diagram](../assets/screens/fe-sensitivity.png#only-light)![Sensitivity of the iron diagram](../assets/screens/dark/fe-sensitivity.png#only-dark)

The Sensitivity view shows where the diagram depends on which published value is used. It draws 300 selections,
each taking one eligible Gibbs energy per species at random, and colors each point by the fraction of selections in
which the stable species differs from the default. You can use all eligible values or only critical evaluations
(classes A–C).

Clicking the diagram lists the species that are stable at that point across the selections, with their fractions.
The table lists each species with more than one eligible value. It gives the fraction of the diagram that changes
when only that value is replaced, the eligible values in kJ/mol and their sources. These fractions describe how
much the diagram depends on the choice of value; they are not probabilities that a phase forms.

## Compare

![Iron and nickel side by side](../assets/screens/fe-compare.png#only-light)![Iron and nickel side by side](../assets/screens/dark/fe-compare.png#only-dark)

Compare shows two diagrams side by side: the current element on the left and any element on the right, with its own
concentration and temperature. The axes are linked, so zooming or panning one also moves the other, and species
that appear in both keep the same color. A shared probe reports the stable species of both at one point, and the
view gives the fraction of the grid where the two differ.

## Concentration sweep

![A concentration sweep of iron](../assets/screens/fe-sweep.png#only-light)![A concentration sweep of iron](../assets/screens/dark/fe-sweep.png#only-dark)

The concentration sweep calculates fixed-activity diagrams over a range of metal activities. They are drawn as a
stack of slices in 3D, next to the selected slice in 2D.

| Control | Sets |
|---|---|
| log₁₀ a from, to | The activity range (−14 to 2) |
| Slices | The number of activity levels and of pH and U grid points |
| Slice along | Whether to step through activity, pH or potential |
| Show | Experimental, DFT (MP) or the agreement between them |
| Other slices | How visible the unselected slices are |
| Reset view | Resets the camera |

Drag to rotate and scroll to zoom. Click a slice, or use the arrow keys, to move through the slices. Each slice is a
fixed-activity diagram, so the mass-balance settings do not apply here.

## DFT comparison

This view puts the official Materials Project diagram next to the experimental one, at the same activity and on the
same grid, with a third panel showing where they differ. It needs the `materials-project` extra and an API key.

| Option | Does |
|---|---|
| Filter solids on the MP phase diagram | pymatgen's default: keep only the solids that are stable on the compositional phase diagram |
| 300 K Gibbs corrections for solids | Applies the Materials Project's machine-learned correction for finite temperature (SISSO) |
| Fetch again | Downloads the entries again |
| Export figure…, API key… | Saves the three panels, or sets the key |

Species are matched by what they are thermodynamically: solids by their oxygen and hydrogen per metal atom, and
dissolved species by their protons, electrons and metal atoms. The table lists each experimental species and
Materials Project phase that coincide, with their share of the grid. The agreement is given for the whole grid and
for the water stability window. Downloaded entries are saved on disk and reused.
