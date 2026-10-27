# Policies and own data

## A different selection policy

Copy the default policy, edit it and calculate with it:

```python
import pourbase as pb

policy = pb.SelectionPolicy.load("my-policy.toml")
database = pb.with_policy(pb.open_database(), policy)
calculation = pb.calculate(pb.Scenario("Fe"), database)

for change in pb.compare_policies(pb.open_database(), pb.SelectionPolicy.default(), policy):
    print(change.record_id, change.property_name, change.first.value, change.second.value)
```

The default policy is `src/pourbase/data/selection-policy.toml`; [How values are selected](../data/selection.md)
explains its keys.

## Your own values

```python
database = pb.with_user_species(pb.open_database(), "own.csv")   # add to or replace bundled species
dataset = pb.open_dataset("own.csv")                              # your species alone
calculation = pb.calculate(pb.Scenario("Cu"), database)
```

The CSV format is described in [Your own data](../app/own-data.md). User values are marked `user_supplied` in
every result.
