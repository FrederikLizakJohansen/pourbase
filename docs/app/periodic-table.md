# Periodic table

![The periodic table at pH 7 and 0 V](../assets/screens/periodic-table.png#only-light)![The periodic table at pH 7 and 0 V](../assets/screens/dark/periodic-table.png#only-dark)

The periodic table shows, for each element with data, the species with the lowest transformed Gibbs energy at one
point. The point is set by the pH, potential and temperature at the top. The table uses the metal concentration,
model and ligands of the [element view](settings.md), so both describe the same conditions.

## Controls

| Control | Sets |
|---|---|
| pH | From −2 to 16 |
| U, vs SHE or vs RHE | The potential. On the RHE scale it moves with pH |
| T | The temperature of all elements, 0 to 100 °C. This is the same setting as System → Temperature |
| Ligands | Turns the buffered ligands on or off for all elements, here and in the element view |
| Color by | What the tiles show (see below) |
| 3D | Raises the table into columns whose height is the stability margin |
| Sweep | Shows controls that run the table through a range of pH or potential |

## Color modes

With *Stable species category*, the tile color gives the kind of stable species: dissolved or gas, oxide,
hydroxide, the element itself as a solid or liquid, or another solid. Clicking a category in the legend
highlights those elements, and clicking it again removes the highlight.

With *Stability margin*, the color gives how far the stable species lies below the next species, in kJ per mole
of metal.

![The periodic table colored by stability margin](../assets/screens/periodic-table-margin.png#only-light)![The periodic table colored by stability margin](../assets/screens/dark/periodic-table-margin.png#only-dark)

With *Share of a pH–potential window*, you set a window and a criterion, and each tile shows the fraction of the
window where the criterion holds, from 0 to 1.

| Criterion | Holds where |
|---|---|
| Metal stable (immunity) | The element itself is stable |
| Solid compound stable (passivation) | A solid compound is stable |
| Dissolved (corrosion) | A dissolved species is stable |
| Any solid or liquid stable | Any condensed phase is stable |

The window is set by its pH and potential limits. With a minimum margin, the criterion only counts where its
species lie at least that far below all others.

![The share of a window where a solid compound is stable](../assets/screens/periodic-table-window.png#only-light)![The share of a window where a solid compound is stable](../assets/screens/dark/periodic-table-window.png#only-dark)

## Tiles

When you hover over a tile, the card at the top of the table shows the element's category, its stable species and
phase, the margin to the next species in kJ per mole of metal, and the citation for the stable species' Gibbs
energy. In window mode, the card also gives the fraction of the window and the smallest margin in it. Clicking a
tile opens the element.

A dashed outline marks an element with species left out because they have no recommended Gibbs energy. The card
gives the number, and the legend counts these elements under "Some species are left out for missing data". If
Materials Project estimates are filling the gaps (System → Evidence policy), the card says so.

## 3D

![The periodic table in 3D](../assets/screens/periodic-table-3d.png#only-light)![The periodic table in 3D](../assets/screens/dark/periodic-table-3d.png#only-dark)

In 3D, each element is a column whose height is its stability margin, on a logarithmic scale up to 1000 kJ mol⁻¹
of metal. Drag to rotate, scroll to zoom and double-click to reset the view. Pressing 3D again lowers the table
back to 2D.

## Sweep

The Sweep button shows a second row of controls. Choose pH or potential, a start value, an end value and the
number of frames, then press ▶ Play. The table, in 2D or 3D, then steps through the range. With Loop it runs back
and forth until you press ■ Stop. When the sweep stops, the last frame becomes the current pH or potential.
