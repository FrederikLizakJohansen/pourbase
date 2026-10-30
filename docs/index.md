# pourbase

pourbase is a database of experimental standard thermochemistry, with a Python package and a desktop app for
calculating Pourbaix diagrams. For each value we store the citation, the table or page it came from, how it was
checked, its uncertainty when one was reported, and any other published values for the same species. A
selection policy picks the value used in calculations. You can read the policy, change it or replace it.

![The periodic table at pH 7 and 0 V](assets/screens/periodic-table.png#only-light)![The periodic table at pH 7 and 0 V](assets/screens/dark/periodic-table.png#only-dark)

<div class="grid cards" markdown>

- [Install](install.md): the package, the app and the optional extras.
- [Tour](tour.md): iron, from the periodic table to the sources behind one boundary.
- [The app](app/index.md): what each part of the app does.
- [Python](python/index.md): the same calculations in a script.
- [The data](data/selection.md): how values are selected, and which compilations we could not include.
- [Contribute](contributing.md): API features, GUI changes and new applications, including technoeconomic analysis.
- [Reference](reference/calculation.md): the classes and functions, generated from the docstrings.

</div>

The database is part of the package, so calculations run offline without downloads or API keys. The values were
collected with agent-guided literature searches. Each one points to the place in the source it was taken from,
so it can be checked. Please check the values your conclusions depend on, and
[report](https://github.com/FrederikLizakJohansen/pourbase/issues/new/choose) any that are wrong.
