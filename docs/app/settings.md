# Settings

The panel to the left of an element's diagram has three tabs: System, Axes and Display. Each section can be folded
away, and the app remembers which ones are open. Every change can be undone and is saved with the session.

## System

![The System tab](../assets/screens/settings-system.png#only-light)![The System tab](../assets/screens/dark/settings-system.png#only-dark)

### Element

| Setting | Does |
|---|---|
| System | The element to calculate |
| Model | *Fixed activity* gives every dissolved species the same activity, as in Pourbaix's atlas. *Mass balance (closed total metal)* shares a fixed total amount of metal between the dissolved species and at most one solid |
| Overlay | Draws the boundaries of a second element under the same conditions, as dashed lines with names in italics |

![Iron with nickel as an overlay](../assets/screens/fe-overlay.png#only-light)![Iron with nickel as an overlay](../assets/screens/dark/fe-overlay.png#only-dark)

### Metal concentration

| Setting | Does |
|---|---|
| Unit | log₁₀ (mol/L), mol/L, ppm (mg of metal per litre) or wt % |
| Value | The concentration in that unit. In the fixed-activity model it sets the activity of each dissolved species. In the mass-balance model it is the total metal |
| Solution density | Used to convert weight percent to molarity (kg/L) |

The line under the value gives the molarity and the log₁₀ activity.

### Water

A water composition sets the ligands, the ionic strength and the probe pH in one step.

| Composition | Ligands | Ionic strength | Probe pH |
|---|---|---|---|
| Pure water | None | 0 | Unchanged |
| Seawater (S = 35) | Chloride, sulfate, bromide, carbonate, fluoride | 0.723 mol/L | 8.1 |
| River water (world average) | Carbonate, sulfate, chloride, nitrate | 0.0021 mol/L | Unchanged |
| Simulated body fluid | Chloride, carbonate, phosphate, sulfate | 0.161 mol/L | 7.40 |
| Saline, 0.9 % NaCl | Chloride | 0.154 mol/L | Unchanged |

The note under the list gives the source of each composition. If you change a ligand afterwards, the list shows
*Custom*. The ionic strength of seawater is above the limit of the Davies equation (0.1 mol/L), so the app does
not apply it there.

![Silver in seawater](../assets/screens/ag-seawater.png#only-light)![Silver in seawater](../assets/screens/dark/ag-seawater.png#only-dark)

### Temperature

The temperature can be set from 0 to 100 °C. The data are for 25 °C. At other temperatures, each Gibbs energy is
extrapolated with its entropy of formation, assuming the formation enthalpy and entropy stay constant. Species
without entropy data, and all ligand species, are left out away from 25 °C, and the context bar counts them.
[Temperature trends](../TEMPERATURE_TRENDS.md) describes the method and its error estimate.

### Activities

| Setting | Does |
|---|---|
| Davies activity coefficients (mass balance) | Corrects the activities of dissolved ions for their charge, using the Davies equation at the ionic strength below. It is valid up to about 0.1 mol/L |
| Ionic strength | 0 to 0.1 mol/L |
| log₁₀ gas fugacity | The fugacity of all gases relative to 1 bar |

### Evidence policy

| Setting | Does |
|---|---|
| Require a Gibbs energy for every species | Normally, species without a recommended Gibbs energy are left out and listed in the Species view. With this ticked, the calculation stops instead |
| Fill missing solid Gibbs values with labelled MP 300 K estimates | Uses the stored Materials Project estimates for the solids that are terminal evidence gaps. These species are labelled in the results |

### Ligands

*Use ligand reservoirs* turns all ligands on or off at once and keeps their individual settings. The periodic
table has the same switch. Below it, each ligand that forms complexes with the element has its own row:

| Control | Does |
|---|---|
| Checkbox | Includes the ligand and its complexes |
| Free activity (log₁₀ a) | Holds the free ligand at this activity |
| Unbound pool (mol/L) | Holds the total unbound ligand at this concentration. With a pKa, protonation lowers the free activity at low pH |

Ligands are treated as buffered reservoirs, so binding to the metal does not change their activity.

## Axes

![The Axes tab](../assets/screens/settings-axes.png#only-light)![The Axes tab](../assets/screens/dark/settings-axes.png#only-dark)

| Setting | Does |
|---|---|
| pH minimum, pH maximum | The pH range, −4 to 18 (default 0 to 14) |
| U minimum, U maximum | The potential range in V vs SHE, −4 to 4 (default −1.5 to 1.5) |
| pH points, U points | The grid resolution, 11 to 801 points (default 281 × 301) |
| Default axes | Goes back to the default range and resolution |
| Diagram axis | The potential scale of the plot: SHE, RHE (depends on pH), Ag/AgCl (sat. KCl, +0.197 V), Ag/AgCl (3 M KCl, +0.210 V), SCE (sat. KCl, +0.241 V) or Hg/HgO (1 M KOH, +0.098 V) |
| Probe point | The pH and potential (V vs SHE) of the probe. Clicking or dragging in the diagram also moves it |

The calculation and the probe always use the SHE. On the RHE scale, the corners outside the calculated potential
range are left empty.

## Display

![The Display tab](../assets/screens/settings-display.png#only-light)![The Display tab](../assets/screens/dark/settings-display.png#only-dark)

### Diagram

| Option | Shows |
|---|---|
| Domain labels | The species name in each region |
| Legend | The species and their colors |
| Phase boundaries | The lines between regions |
| Water stability lines | The hydrogen and oxygen evolution lines |
| Direct plating potential (fixed activity) | The potential at which the simple cation deposits as the metal, at the set activity |

### Uncertainty hatching (fixed activity)

With hatching on, the diagram is hatched wherever a competing species lies within *k* combined standard
uncertainties of the stable species, with *k* = 1, 2 or 3. Reported ΔfG° uncertainties are used where they exist,
and reference states are exact. Other species get the assumed σ, which is 2 kJ/mol by default and can be set from
0.1 to 20 kJ/mol.

![Iron with uncertainty hatching at 1 σ](../assets/screens/fe-hatching.png#only-light)![Iron with uncertainty hatching at 1 σ](../assets/screens/dark/fe-hatching.png#only-dark)

### Blend dissolved species

With blending on, each point is colored by a mix of the species present. In the mass-balance model, the colors mix
by the fractions of the dissolved species. In the fixed-activity model, the weights are proportional to
exp(−(G − Gmin)/width) over the dissolved species. At a width of RT (2.48 kJ/mol) these weights equal the
fractions of the mass-balance model; other widths only blend the colors. Solids keep sharp edges in both models.

![Iron with the colors of dissolved species blended](../assets/screens/fe-blend.png#only-light)![Iron with the colors of dissolved species blended](../assets/screens/dark/fe-blend.png#only-dark)
