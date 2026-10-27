# Files and export

## Sessions

File → Save session… writes the settings of the element view, the display options and the concentration sweep
settings to a `.pourbase.json` file. It also stores the paths of your own species file and selection policy, if you
use them. File → Open session… restores everything, as long as those files are still in the same place. Sessions
are plain JSON, so they can be read and compared as text.

## Figures and data

| Command | Writes |
|---|---|
| File → Export figure… (Ctrl+S) | The current diagram as PNG, PDF or SVG |
| File → Export grid as CSV… | Each grid point with its pH, potential (V vs SHE), stable species and phase, and in the mass-balance model also the amount of metal in each species |
| File → Copy Python code | A script that reproduces the diagram, copied to the clipboard |

Right-clicking a figure (the diagram, the periodic table, the speciation plots or the 3D views) gives these options:

| Item | Does |
|---|---|
| Export figure as PNG / PDF / SVG… | Saves the figure as it is shown |
| Export data as CSV… / TXT (tab separated)… | Saves the numbers behind the figure, for figures that have them |
| Pop out | Opens the diagram in a separate window |
| Copy Python code, Export Python code… | The script that draws the figure |

The DFT comparison and the policy comparison have their own export buttons. Tools → Sources behind this diagram…
exports the sources as BibTeX or text (see [Database](database.md#sources-behind-a-diagram)).

## Python code

The copied script uses the public API. For iron with the default settings it is:

```python
import pourbase as pb

database = pb.open_database()
calculation = pb.calculate(pb.Scenario('Fe'), database)
ax = pb.plot_diagram(calculation.diagram)
```

The script only lists the settings that differ from the defaults. When they are in use, it also loads your own
dataset, species or policy, draws the mass-balance or blended plot, and adds the uncertainty hatching.
[Python](../python/index.md) describes the rest of the API.
