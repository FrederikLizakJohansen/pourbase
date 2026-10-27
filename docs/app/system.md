# An element

![The iron diagram with a probe](../assets/screens/fe-diagram.png#only-light)![The iron diagram with a probe](../assets/screens/dark/fe-diagram.png#only-dark)

Clicking an element on the periodic table, or choosing it under System → Element, opens its tab. The
[settings](settings.md) are on the left. On the right are the context bar and the [views](views.md), starting with
the diagram.

## The diagram

The diagram shows the stable species over pH and potential. The water stability lines are dashed. Each species has
one color, which it keeps in all views. The pH, potential and stable species under the mouse are shown in the
bottom-left corner of the plot.

- Scroll or drag to zoom and pan. Ctrl+0 resets the axes.
- Click to move the probe there, or drag the probe marker.
- Click a boundary to see its balanced reaction, its equation and the sources of the Gibbs energies on both sides.
  The popup also says what kind of boundary it is: redox (Eq. 3 in the paper), acid–base (Eq. 4) or, in the
  mass-balance model, numerical. Clicking elsewhere closes it.
- Right-click to export (see [Files and export](files.md)).

In the mass-balance model, the diagram shows the dominant species: the solid where metal precipitates, and
otherwise the dissolved species with the highest concentration.

![Iron in the mass-balance model](../assets/screens/fe-mass-balance.png#only-light)![Iron in the mass-balance model](../assets/screens/dark/fe-mass-balance.png#only-dark)

## The panels below the diagram

### Probe

For the point it marks, the probe reports:

- the stable species, its phase and the coordinates, also on the diagram's potential scale if that is not the SHE;
- the next species and the energy gap to it in kJ per mole of metal, with its combined uncertainty, and whether
  the two are within the uncertainty of the data, one to two uncertainties apart, or clearly separated;
- the recommended Gibbs energy of the stable species with its uncertainty, status, source and location in the
  source; away from 25 °C, also the extrapolated value and the 25 °C value it comes from;
- the distance to the nearest boundary going up and down in potential and in pH, and the species on the other side;
- in the mass-balance model, the dissolved metal concentration, the precipitated fraction and the largest
  dissolved species;
- the first warning on the record, if there is one, with a link to the full record in the Species view.

The probe can be placed exactly under Axes → Probe point.

### Path

A path is a line through pH and potential. The panel lists the stable species along it and the boundaries it
crosses.

![A path through the iron diagram](../assets/screens/fe-path.png#only-light)![A path through the iron diagram](../assets/screens/dark/fe-path.png#only-dark)

| Control | Does |
|---|---|
| Pick points on the diagram | Click to add points. Double-click, or press the button again, to finish |
| Add point, Remove point | Edit the table of points by hand |
| Potential sweep at the probe pH | A vertical path through the probe |
| pH sweep at the probe U | A horizontal path through the probe |
| Straight segments, Smooth curve | How the points are joined |
| Slider | Moves the probe along the path |
| Clear | Removes the path |

The points of a path can be dragged on the diagram. Clicking a point selects it. The arrow keys then move it
(with Shift for larger steps), Delete removes it and Escape deselects it.

### Measured points

Import measured points… reads a CSV file with the columns `label`, `pH`, `potential_V` and, if needed,
`reference`. The reference can be SHE (the default), RHE, SCE, Ag/AgCl (sat. KCl), Ag/AgCl (3 M KCl) or Hg/HgO
(1 M KOH). The points are drawn on the diagram, and the table gives for each one its pH and potential vs SHE, the
predicted species, the next species and the margin, with a note if the point is outside the diagram or within the
uncertainty. Clicking a row moves the probe to the point.

![Four measured points on the iron diagram](../assets/screens/fe-points.png#only-light)![Four measured points on the iron diagram](../assets/screens/dark/fe-points.png#only-dark)

### Find region

Find region shades where a species, or a kind of species, is stable by at least a given margin.

| Control | Sets |
|---|---|
| Stable | A kind (metal stable, solid compound stable, dissolved, any solid or liquid) or one species |
| Require | *Energy margin above* a value in kJ/mol, or *At least k combined uncertainties* |
| Margin | The value |

The panel gives the fraction of the diagram where this holds, and its pH and potential range.

![Where a solid compound of iron is stable by at least 5 kJ/mol](../assets/screens/fe-region.png#only-light)![Where a solid compound of iron is stable by at least 5 kJ/mol](../assets/screens/dark/fe-region.png#only-dark)
