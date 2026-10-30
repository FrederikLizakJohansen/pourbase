# Contributing features and applications

You can contribute a scientific idea, a worked example, data, Python code or a desktop
feature. This guide explains where to start and how to turn a contribution into something
the rest of the team can use.

The Python API and the desktop GUI share the same calculation code. A useful starting
point is a script that answers one research question. Once its inputs and results are
clear, we can expose it in the app.

## Choose a contribution

| What you want to do | A useful first contribution |
| --- | --- |
| Suggest a feature | Describe the user, the task and an example of the desired result. A sketch or spreadsheet helps. |
| Add an analysis | Write a Python function using a `Calculation`, with a small worked example and a check of the result. |
| Improve the GUI | Show the current interaction and the proposed interaction; connect the new view to the shared calculation code. |
| Build a technoeconomic application | Make a script or separate package that combines pourbase results with explicit process and cost assumptions. |
| Improve the thermochemical data | Supply the value, exact source location, chemical identity and reuse evidence. See the [data contribution instructions](https://github.com/FrederikLizakJohansen/pourbase/blob/main/CONTRIBUTING.md#reporting-a-data-problem-or-a-new-source). |
| Check the science | Supply a hand calculation, experimental comparison or independently calculated example that another person can reproduce. |

You can contribute requirements, source checks and examples through a GitHub issue even
if you do not plan to write the code.

## Describe the first working version

For a substantial feature, open an [issue](https://github.com/FrederikLizakJohansen/pourbase/issues)
before implementing it. This lets collaborators agree on the scientific scope and divide
the work. Use this outline:

```text
User and task:
Example input:
Expected output, including units:
Scientific or process assumptions:
Where it belongs: Python API / GUI / separate application
How we will check it:
First working version:
Possible later additions:
```

For example: “Given a set of pH–potential points for a zinc process, export the predicted
species, excluded species and sources beside separately supplied electricity and reagent
costs.” This gives the team a concrete result to review.

## Set up a development copy

Use Python 3.11 or newer. Create your own branch so collaborators can work independently.
An editable installation makes Python use the code in your checkout as you change it.

```bash
git clone https://github.com/FrederikLizakJohansen/pourbase.git
cd pourbase
git switch -c feature/process-screen
python -m venv .venv
```

Activate the environment on macOS or Linux:

```bash
source .venv/bin/activate
```

On Windows, use this command in Command Prompt:

```bat
.venv\Scripts\activate.bat
```

Install the API, GUI and documentation tools, then open the app:

```bash
python -m pip install -e ".[gui,docs]"
pourbase gui Fe
```

For API work alone, `python -m pip install -e .` supplies the calculation package.
Install `".[materials-project]"` when working on that integration, or `".[mcp]"` for
the agent server. The [installation guide](install.md) describes these extras.

Collaborators with repository write access can push their feature branch. Otherwise,
fork the repository on GitHub and clone your fork; a fork is your own copy on GitHub.
In both cases, submit a pull request to the main pourbase repository. A pull request
shows the proposed changes and gives reviewers a place to discuss them.

## Understand the calculation path

`Scenario` holds the inputs to a calculation. `calculate()` runs it with a chosen
database and selection policy. The returned `Calculation` provides the diagram, a
point probe, boundaries and the species left out of the calculation.

```python
import pourbase as pb

database = pb.open_database()
scenario = pb.Scenario(
    "Zn", mode="mass_balance", concentration=1e-6,
    concentration_unit="molar", pH_points=41, U_points=51,
)
calculation = pb.calculate(scenario, database)
point = calculation.probe(pH=9, U_V=0)
print(point.species.species)
print(point.dissolved_metal_mol_L)
print([item.record_id for item in calculation.excluded])
```

In the GUI, **File → Copy Python code** gives you a script for the displayed diagram,
including its data and policy settings. It is a good starting example for a feature.
The [Python quick start](python/index.md) and [analyses](python/analyses.md) describe
the public functions you can build on.

These files are the main places to look in the
[repository](https://github.com/FrederikLizakJohansen/pourbase):

| Area | Files and their roles |
| --- | --- |
| Public Python interface | `src/pourbase/__init__.py` exports supported names; `scenario.py` defines `Scenario`, `Calculation` and `calculate()`. |
| Scientific models | `engine.py` calculates fixed-activity diagrams; `mass_balance.py` solves closed metal balances; `temperature.py` handles temperature changes. |
| Additional analyses | `equilibria.py`, `inverse.py`, `sections.py`, `sensitivity.py` and `paths.py` contain boundaries, operating windows, sections, sensitivity and paths. |
| Data and evidence | `database.py`, `records.py` and `selection.py` read observations, expose their sources and choose preferred values. |
| GUI inputs and saved state | `gui/state.py` holds `Settings` and the cached calculations in `Session`; `gui/session.py` reads and writes session files; `gui/history.py` handles undo/redo. |
| GUI controls and views | `gui/settings_panel.py` contains the inputs; `gui/pages.py` and dedicated page modules present results; `gui/plots.py` draws the interactive diagrams. |
| GUI coordination | `gui/window.py` connects controls, calculations and pages; `gui/tasks.py` runs background work through `TaskRunner`. |
| Other interfaces | `cli.py` provides the command line; `mcp_server.py` provides the optional agent server. |

## Add a Python feature

1. Write down the input, output and units. Decide whether the feature consumes an
   existing `Calculation` or needs a new calculation setting.
2. Put the scientific work in a regular Python module. Functions should accept their
   inputs explicitly and return results that a script, test or GUI can read. Keep Qt
   widgets and file dialogs in the GUI code.
3. Reuse the database and policy passed by the caller. This preserves the user's own
   dataset, species and preferred-value choices.
4. Check one small case against a hand calculation or independent result. Cover a
   meaningful failure case, such as a missing property or unsupported condition.
5. Export a new public function or result class from `src/pourbase/__init__.py` when
   it is intended for users. Add an example and update the relevant reference page.
6. Connect it to the GUI, command line or agent server where that interface is useful.

Use the existing analyses as patterns. `sections.py`, for example, calculates
solubility and ligand predominance from a calculation, while
`gui/fixed_potential.py` presents those results in the app.

For a change to the underlying thermodynamics, also explain its reference states,
formula basis and effect on existing results. The engines use J/mol of metal for
transformed energies; stored thermochemical observations use J/mol of the full formula
unit, with entropies in J/(mol K). Preserve that distinction in new calculations.

## Connect a feature to the GUI

First decide whether you are adding an input, an analysis view or a display option.
Follow the existing state and task patterns:

1. **Inputs:** add calculation inputs to `Scenario` and the corresponding GUI
   `Settings` fields where appropriate. Keep view-only choices with `DisplayOptions`
   in `gui/plots.py`. A process extension may need its own assumptions object.
2. **Controls:** add a clearly labelled control with its units in `settings_panel.py`
   or the relevant page. Check how it behaves when an element, unit or model changes.
3. **Calculation:** call the shared Python function. For expensive work, use
   `TaskRunner` and update Qt widgets when the result returns to the UI thread.
4. **Current results:** include every relevant input in the cache/task key. Follow
   `MainWindow._wanted` and `_task_finished` so an older job cannot overwrite the
   result for the user's latest settings. Long loops should check cancellation where
   the calculation supports it.
5. **Save and reproduce:** check undo/redo, saved sessions and copied Python code.
   New saved settings need a sensible default when reading an older session. Existing
   `Settings` fields participate in generic save/code generation; test the complete
   round trip, including any separate process assumptions.
6. **Presentation:** provide useful empty, loading and error states. Include units,
   source information and export of the underlying numbers. Check light/dark themes
   and resize the window.

Use `tests/test_gui.py` for controls, state conversion, background results and copied
code, and `tests/test_gui_history.py` for history behaviour. A new analysis should also
have a numerical test that runs through its Python function.

GUI features currently connect through these application modules. There is no public
plugin registration interface; a separately developed application can use the public
Python API directly.

## Build a technoeconomic application

A technoeconomic analysis combines a process model with costs. Pourbase can supply
equilibrium species, phase boundaries, speciation and sensitivity to thermochemical
data. A process model supplies feed composition, throughput, actual recovery, energy
use, reagent consumption and equipment assumptions. A cost model attaches prices and
a stated currency and price year to those quantities.

Start with a separate script or package that imports `pourbase`. This makes it possible
to develop the process model with its own inputs and dependencies. General analyses
that other pourbase users need can later move into the shared API, with an optional GUI
view. The interface you develop in that companion project can also call pourbase directly.

Keep the distinction between equilibrium and process performance explicit. An equilibrium
precipitated fraction describes a closed-metal calculation. Actual recovery, selectivity,
corrosion rate, reaction time and cell efficiency need their own evidence or models.
Likewise, a stable solid phase alone does not establish a protective film's performance.
The current elemental calculations and buffered ligands provide parts of a process
model; a coupled flowsheet needs additional material balances and process equations.

For a first increment, pair the zinc calculation above with an explicitly supplied cost
case. These numbers are fictional currency units (CU), used to demonstrate the arithmetic:

```python
# Continue from the calculation example above.
assumptions = {
    "feed_kg_per_year": 1000.0,
    "metal_mass_fraction": 0.02,
    "assumed_recovery_fraction": 0.8,
    "electricity_kWh_per_year": 2500.0,
    "electricity_CU_per_kWh": 0.10,
    "reagents_CU_per_year": 100.0,
}
recovered_kg_per_year = (
    assumptions["feed_kg_per_year"]
    * assumptions["metal_mass_fraction"]
    * assumptions["assumed_recovery_fraction"]
)
variable_CU_per_year = (
    assumptions["electricity_kWh_per_year"]
    * assumptions["electricity_CU_per_kWh"]
    + assumptions["reagents_CU_per_year"]
)
print(recovered_kg_per_year)                       # 16.0
print(variable_CU_per_year / recovered_kg_per_year)  # 21.875 CU/kg
print(point.species.species)  # A separate equilibrium result at the chosen point.
```

Here, recovery is an assumption; its value comes from the supplied process case. The
solution concentration in `Scenario` and the annual feed describe different quantities.
A working process model must connect them through flow, composition and material balances.
The cost example covers electricity and reagents. A fuller model adds feed cost, labour,
water, waste treatment, maintenance and capital costs with a stated time basis. Validate
fraction bounds, finite inputs and positive product output before calculating unit costs.

Build the application in increments:

| Increment | Deliverable |
| --- | --- |
| One process case | A reproducible chemical calculation beside a cost calculation with stated assumptions. |
| Several alternatives | A table comparing candidate conditions or process routes on the same basis. |
| Uncertainty and sensitivity | Separate variations in thermochemical data from variations in prices, recovery and energy use. |
| User interface | Editable assumptions, clear units, saved cases, plots and a report that includes the input data. |
| A complete process model | Linked unit operations, material/energy balances and comparison with experimental or plant observations. |

Record the source, date, currency, price year and system boundary for real cost inputs.
Document mixture, temperature, pressure and activity-model assumptions alongside them.
The [temperature guide](TEMPERATURE_TRENDS.md) and the calculation's excluded-species
list help show where a proposed operating condition has limited thermochemical coverage.

For each saved case, keep the `Scenario`, process assumptions, `Calculation.as_dict()`
summary, actual selected values and their sources. The evidence records are available
through `database.species_records(record_ids)` and `SpeciesRecord.as_dict()`. Record the
pourbase version, database version/file hash and selection policy as well. The case should
contain enough information for another collaborator to reproduce both calculations.

## Check and submit your work

Run a focused test while developing, for example:

```bash
python -m unittest discover -s tests -p "test_calculations.py"
```

Before submitting code or data changes, run the full suite with the extras your work
needs installed:

```bash
python -m unittest discover -s tests
```

On Linux machines without a display, run GUI tests with:

```bash
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests
```

For documentation changes, preview with `zensical serve` and check with
`zensical build --strict`. CI tests the project on Linux, macOS and Windows with Python
3.11 and 3.13. The full GUI tests need the `gui` extra; tests for optional integrations
may be skipped when their dependencies are absent.

Include the following in your pull request:

- The task the change enables and a short script or sequence of GUI actions to try it.
- The assumptions, units and any effect on existing scientific results.
- The checks you ran and their outcomes; screenshots help for visible GUI changes.
- Any new dependencies, data sources and associated licence/attribution requirements.

Keep a pull request focused on one usable change. A short plan in the issue can track
the following increments. Work on separate branches and coordinate before changing a
shared area such as `gui/window.py` or the bundled database.

For shared database additions, follow the [data dictionary](DATA_DICTIONARY.md) and
[selection policy guide](data/selection.md). Keep every justified observation, its exact
source and reuse evidence; the policy chooses one preferred value per property. Use your
own [CSV dataset](app/own-data.md) while trying a process case. Dataset snapshot tests and
generated statistics are updated when an accepted contribution changes the bundled data.

Contributions to pourbase follow its
[GPL-3.0 licence](https://github.com/FrederikLizakJohansen/pourbase/blob/main/LICENSE).
Reuse and redistribution of data also carry the requirements in
[THIRD_PARTY_NOTICES.md](https://github.com/FrederikLizakJohansen/pourbase/blob/main/THIRD_PARTY_NOTICES.md).
Keep private process data, credentials and correspondence in your own local files.
