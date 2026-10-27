# Periodic table

![The periodic table at pH 7 and 0 V](../assets/screens/periodic-table.png)

The controls at the top set the pH, the potential (vs SHE or RHE) and the temperature. The metal concentration,
the ligands and the other System settings are shared with the element view.

**Color by** chooses what the tiles show:

| Mode | Color |
|---|---|
| Stable species category | Dissolved, oxide, hydroxide, element, other solid |
| Stability margin | The energy margin to the next species |
| Share of a pH–potential window | How much of a chosen window a criterion holds in (immune, passive, corroding) |

Hovering over a tile shows the stable species, its margin and its source; clicking opens the element.
Elements with a dashed outline have species left out for missing data.

## 3D and sweep

**3D** raises the table into columns as tall as each element's stability margin, on a logarithmic scale up to
1000 kJ mol⁻¹ metal. Drag to rotate, scroll to zoom, double-click to reset; pressing 3D again lowers it.

**Sweep** shows controls that play the table through a range of pH or potential, in 2D or 3D, once or back and
forth. When it stops, the last frame becomes the current setting.
