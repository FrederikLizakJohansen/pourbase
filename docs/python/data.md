# Policies and own data

## Another selection policy

To use your own rule, copy the default policy, edit it and calculate with it:

```python
import pourbase as pb

policy = pb.SelectionPolicy.load("my-policy.toml")
database = pb.with_policy(pb.open_database(), policy)
calculation = pb.calculate(pb.Scenario("Fe"), database)

for change in pb.compare_policies(pb.open_database(), pb.SelectionPolicy.default(), policy):
    print(change.record_id, change.property_name, change.first.value, change.second.value)
```

The default policy is the file `src/pourbase/data/selection-policy.toml`.
[How values are selected](../data/selection.md) explains its keys.
[`select`](../reference/selection.md#pourbase.select) gives the recommended value of each species and property
under a policy, with the reason for the choice.

## Your own values

```python
database = pb.with_user_species(pb.open_database(), "own.csv")   # add to or replace bundled species
dataset = pb.open_dataset("own.csv")                              # only your species
calculation = pb.calculate(pb.Scenario("Cu"), database)
```

[Your own data](../app/own-data.md) describes the CSV format. Your values are marked `user_supplied` in the
results. `open_dataset` also opens another pourbase SQLite file, and
[`dataset_from_csv`](../reference/user-data.md#pourbase.dataset_from_csv) writes a CSV file as a SQLite dataset.
