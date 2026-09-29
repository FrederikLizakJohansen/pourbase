# Data paper

This folder contains a concise LaTeX data paper for the pourbase database. Its statistics,
source list, tables, and figures are generated from the files distributed in this repository.

Generate every asset and compile the PDF from the repository root with:

```bash
make -C paper
```

The build requires Python with the package dependencies and LuaLaTeX. The output is
`manuscript.pdf`. The manuscript intentionally has no authors yet.

Generated scientific outputs are retained in the repository:

- `generated/dataset-summary.json`: complete machine-readable release statistics;
- `generated/per-system-statistics.csv`: coverage for each supported elemental system;
- `generated/dataset-statistics.tex`: manuscript count macros;
- `generated/references.tex`: every distinct citation in the SQLite `sources` table, plus method
  and software references;
- `figures/dataset-overview.*`: elemental, phase, property, and evidence coverage;
- `data/fe-official-mp-*`: versioned official Materials Project inputs for the Fe comparison;
- `generated/fe-pourbaix-comparison*`: comparison settings, agreement metrics, and changed phase
  pairs;
- `figures/calculation-showcase.*`: experimental, official Materials Project, and difference maps
  for Fe;
- `figures/mp-thermochemistry.*`: phase-matched experimental and Materials Project comparisons.

The plotting style follows the compact figure conventions used in the qECMS paper scripts: small
type, restrained colors, open top and right spines, direct panel labels, and vector PDF output.
