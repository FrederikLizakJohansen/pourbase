"""Report every recommendation a selection policy would change, and its effect on the diagrams.

    python scripts/selection_report.py [policy.toml] [--output DIR]

Without a policy file the bundled default policy is compared with the recommendations stored in the
database. The report lists each changed value with both candidates and their difference, the share
of each affected element's diagram whose stable species changes, and every species whose eligible
Gibbs energies differ by more than the policy's review threshold.
"""

from __future__ import annotations

import argparse
import csv
import sys
import warnings
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

import pourbase as pb  # noqa: E402
from pourbase.selection import select, stored_selection, with_policy  # noqa: E402

UNITS = {"gibbs_energy_of_formation": ("kJ/mol", 1000.0), "enthalpy_of_formation": ("kJ/mol", 1000.0),
         "absolute_entropy": ("J/(mol K)", 1.0)}


def main() -> None:
    warnings.filterwarnings("ignore")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("policy", nargs="?", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT.parent / "pourbase-work" / "selection-report")
    args = parser.parse_args()
    database = pb.open_database()
    policy = pb.SelectionPolicy.load(args.policy) if args.policy else pb.SelectionPolicy.default()
    selection = select(database, policy)
    stored = stored_selection(database)
    symbols = {row["record_id"]: (row["symbol"], row["species"], row["phase"])
               for row in database._rows("SELECT record_id, symbol, species, phase FROM species")}
    values = {row["value_id"]: row for row in database._rows(
        "SELECT r.value_id, r.value, r.source_id, s.citation FROM reported_thermochemistry AS r "
        "JOIN sources AS s USING(source_id)")}

    changes = []
    for key, item in sorted(selection.items()):
        current_id = stored.get(key)
        if current_id is None or current_id == item.chosen.value_id:
            continue
        current = values[current_id]
        candidate = next((c for c in item.candidates if c.value_id == current_id), None)
        family = (f"{candidate.family} ({candidate.evidence_class})" if candidate is not None
                  else "ineligible: " + policy.family_of(current["citation"], ""))
        unit, scale = UNITS[key[1]]
        symbol, species, phase = symbols[key[0]]
        changes.append({
            "symbol": symbol, "species": species, "phase": phase, "record_id": key[0], "property": key[1],
            "current": current["value"] / scale, "current_family": family, "current_source": current["source_id"],
            "rule": item.chosen.value / scale, "rule_family": f"{item.chosen.family} ({item.chosen.evidence_class})",
            "rule_source": item.chosen.source_id, "difference": (item.chosen.value - current["value"]) / scale,
            "unit": unit, "basis": item.basis,
        })

    # effect on each element's default diagram (fixed activity, a = 1e-6)
    affected = sorted({row["symbol"] for row in changes if row["property"] == "gibbs_energy_of_formation"})
    policy_database = with_policy(database, policy)
    impact = {}
    for symbol in affected:
        scenario = pb.Scenario(symbol, allow_incomplete=True)
        before = pb.calculate(scenario, database).diagram
        after = pb.calculate(scenario, policy_database).diagram
        ids_before = np.asarray([item.record_id for item in before.system.species])[before.stable_species_index]
        ids_after = np.asarray([item.record_id for item in after.system.species])[after.stable_species_index]
        impact[symbol] = float((ids_before != ids_after).mean())

    review = [item for key, item in sorted(selection.items())
              if key[1] == "gibbs_energy_of_formation" and item.needs_review]

    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    with (output / "changes.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(changes[0].keys()) if changes else ["record_id"])
        writer.writeheader()
        writer.writerows(changes)
    with (output / "review.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["symbol", "species", "phase", "record_id", "spread_kJ_mol", "chosen_kJ_mol",
                         "chosen_family", "basis", "candidates"])
        for item in review:
            symbol, species, phase = symbols[item.record_id]
            writer.writerow([symbol, species, phase, item.record_id, f"{item.spread_J_mol / 1000:.2f}",
                             f"{item.chosen.value / 1000:.3f}", item.chosen.family, item.basis,
                             "; ".join(f"{c.value / 1000:.3f} ({c.family})" for c in item.candidates)])

    by_property = defaultdict(list)
    for row in changes:
        by_property[row["property"]].append(row)
    lines = [f"# Selection report: {policy.name} ({policy.fingerprint})", "",
             f"Compared with the recommendations stored in dataset {database.data_version}.", ""]
    for property_name, rows in by_property.items():
        unit = rows[0]["unit"]
        lines += [f"## {property_name}: {len(rows)} changes", "",
                  f"| Element | Species | Phase | Current ({unit}) | From | Rule ({unit}) | From | Difference |",
                  "|---|---|---|---|---|---|---|---|"]
        for row in sorted(rows, key=lambda item: -abs(item["difference"])):
            lines.append(f"| {row['symbol']} | {row['species']} | {row['phase']} | {row['current']:.3f} | "
                         f"{row['current_family']} | {row['rule']:.3f} | {row['rule_family']} | "
                         f"{row['difference']:+.3f} |")
        lines.append("")
    lines += ["## Effect on the diagrams (fixed activity, a = 10⁻⁶)", "",
              "| Element | Grid points with a different stable species |", "|---|---|"]
    lines += [f"| {symbol} | {fraction:.1%} |" for symbol, fraction in sorted(impact.items(), key=lambda x: -x[1])]
    lines += ["", f"## Species with Gibbs energies more than {policy.review_threshold_J_mol / 1000:g} kJ/mol "
              f"apart: {len(review)}", "", "Listed in review.csv with every candidate.", ""]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
    counts = {key: len(rows) for key, rows in by_property.items()}
    print(f"{counts}; {len(affected)} elements' diagrams affected; {len(review)} species to review; wrote {output}")


if __name__ == "__main__":
    main()
