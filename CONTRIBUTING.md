# Contributing to pourbase

pourbase is a living database. It grows as sources are checked, gaps are filled and mistakes are
corrected, and contributions of both data and code are welcome.

For API features, GUI changes and applications such as technoeconomic analysis, start with
the [collaborator guide](docs/contributing.md). It covers development setup, the code
layout, how to connect an analysis to the GUI, worked examples and pull requests.
Contributors can also propose workflows, check sources or supply validation examples
through an issue.

## How the data were gathered

The literature search behind the database was agentic: GPT 5.6 Sol located candidate sources and
the tables and values in them. We acknowledge that this search can miss a better source, pick up a
secondary copy of a value, confuse phases or conventions, or misread a table.

Every value is therefore stored with what you need to check it:

- the full citation, a link where one exists, and the exact location of the value in the source
  (table, row, column or page);
- an evidence status: `verified`, `source_verified_estimate`, `defined_reference_state` or
  `terminal_evidence_gap`;
- every retained alternative and superseded value in `reported_thermochemistry`, next to the
  recommended value in `selected_thermochemistry`;
- scientific cautions in `warnings` and the phase and polymorph assignment in `phases`;
- explicit gaps where no defensible value was found, and <!-- count:fallbacks -->six<!-- /count --> Materials Project estimates kept
  separately in `computational_fallbacks` and used only on request.

Check the cited source for any value your conclusions depend on. The Species tab of the desktop
application and `ThermodynamicDatabase.species_records` show the citation and locator of every
value. If you find a mistake, please tell us.

## Reporting a data problem or a new source

Open an issue with the
[Data correction or addition](https://github.com/FrederikLizakJohansen/pourbase/issues/new/choose)
form and give:

- the record ID from the Species tab, or the formula and phase of a missing species;
- the property, value, units, temperature, pressure and standard state you propose, with its
  uncertainty if reported;
- the full citation and the exact table, row, column or page of the value;
- anything that affects comparability, such as the ion convention, the phase or whether the value
  is derived;
- the licence, public-domain basis or written permission that allows redistribution, including
  any attribution requirements. See [the distributed notices](THIRD_PARTY_NOTICES.md) for existing
  source conditions.

Each accepted change is recorded with its source and a plain-language reason. Earlier values stay
in `reported_thermochemistry`, and the change appears in the next dataset release.

Which value is recommended follows the selection policy in `src/pourbase/data/selection-policy.toml`.
A new value enters as a candidate; the policy decides whether it becomes the recommendation. To
propose a change to the rule itself, such as the order of two source families or an exception with
its reason, edit the policy file, run `python scripts/selection_report.py` on it and include the
report with your pull request. The package derives the recommended values from the policy when it
opens the database. Include any resulting changes to scientific examples, tests and statistics.

## Contributing code

```bash
git clone https://github.com/FrederikLizakJohansen/pourbase.git
cd pourbase
git switch -c feature/my-analysis
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[gui,docs]"
python -m unittest discover -s tests
```

Open an issue before a large change, keep pull requests focused, and add tests with new behaviour.
The [collaborator guide](docs/contributing.md) includes Windows setup, headless GUI checks and
instructions for contributors using a fork. Install the `materials-project` or `mcp` extra when
working on those integrations.
`tests/test_dataset_snapshot.py` pins the released dataset; update it only in pull requests that
change the data.
