#!/usr/bin/env python3
"""Check every species and its evidence fields without changing the database.

Run ``python scripts/audit_database_representation.py --json report.json --csv species.csv``.
The CSV distinguishes representation checks from the recorded phase-identity limitations.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PHASES = {"solid", "aqueous", "gas", "liquid"}
IDENTITY_STATUSES = {"resolved", "unresolved", "ambiguous", "aqueous_species_identified",
                     "phase_identity_incomplete", "reported_composition_disputed"}
STATUSES = {"verified", "accepted", "source_verified_estimate", "defined_reference_state",
            "superseded_source_value", "terminal_evidence_gap", "not_available"}
UNITS = {"gibbs_energy_of_formation": "J/mol", "enthalpy_of_formation": "J/mol",
         "absolute_entropy": "J/(mol K)"}
TOKENS = re.compile(r"[A-Z][a-z]?|\d+(?:\.\d+)?|[()\[\]]")
PROVENANCE_IN_LABEL = re.compile(
    r"\b(?:NBS|NEA\d*|USGS\d*|Cemdata\d*|HKF|Peiffert\d*|Akinfiev|source|"
    r"fit|fitted|evaluation|estimated|estimate|valid|ageing|aging)\b", re.I)


def formula_counts(formula: str) -> Counter:
    """Read a complete formula, including nested groups and fractional occupancies.

    Charge and oxidation annotations belong in separate fields. Hydrates use explicit
    groups such as ``CaSO4(H2O)0.5``, avoiding ambiguous decimal/dot separators.
    """
    tokens = TOKENS.findall(formula)
    if not tokens or "".join(tokens) != formula:
        raise ValueError("formula contains unsupported text or annotations")
    position = 0

    def group(ending: str | None = None) -> Counter:
        nonlocal position
        counts: Counter = Counter()
        while position < len(tokens):
            token = tokens[position]
            position += 1
            if token in (")", "]"):
                if token != ending or not counts:
                    raise ValueError("unexpected or empty formula group")
                return counts
            if token in ("(", "["):
                inner = group(")" if token == "(" else "]")
            elif re.fullmatch(r"[A-Z][a-z]?", token):
                inner = {token: 1.0}
            else:
                raise ValueError("number has no preceding element or group")
            factor = 1.0
            if position < len(tokens) and tokens[position][0].isdigit():
                factor = float(tokens[position])
                position += 1
            if not math.isfinite(factor) or factor <= 0:
                raise ValueError("formula counts must be positive and finite")
            for element, count in inner.items():
                counts[element] += factor * count
        if ending:
            raise ValueError("unclosed formula group")
        return counts

    return group()


def audit_database(path: str | Path) -> dict:
    path = Path(path).resolve()
    findings = []

    def issue(table, key, field, message):
        findings.append({"table": table, "id": str(key), "field": field, "message": message})

    with sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        tables = {row[0]: [dict(r) for r in connection.execute(f'SELECT * FROM "{row[0]}"')]
                  for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' "
                                                "AND name NOT LIKE 'sqlite_%'").fetchall()}
        profile = {}
        for table, rows in tables.items():
            columns = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
            profile[table] = {}
            for column in columns:
                name, declared = column[1], column[2]
                profile[table][name] = dict(connection.execute(
                    f'SELECT typeof("{name}"),count(*) FROM "{table}" GROUP BY typeof("{name}")'))
                if declared in ("REAL", "INTEGER"):
                    for row in rows:
                        value = row[name]
                        if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value)):
                            issue(table, row.get("value_id", row.get("record_id", row.get("ligand_id", ""))),
                                  name, "numeric field requires a finite number or NULL")
            for row in rows:
                for name in ("url", "source_url"):
                    url = row.get(name)
                    if url is not None:
                        try:
                            parsed = urlsplit(url)
                            valid = parsed.scheme in ("http", "https") and parsed.netloc and not re.search(r"\s", url)
                        except (ValueError, TypeError):
                            valid = False
                        if not valid:
                            issue(table, row.get("source_id", row.get("record_id", "")), name,
                                  "URL field requires a single HTTP(S) URL or NULL")
                if table == "sources" and row["locator"] and row["locator"].lstrip().startswith(("{", "[")):
                    try:
                        if not isinstance(json.loads(row["locator"]), dict):
                            raise ValueError("structured locator must be an object")
                    except ValueError as error:
                        issue(table, row["source_id"], "locator", str(error))
        integrity = [r[0] for r in connection.execute("PRAGMA integrity_check")]
        foreign_keys = [tuple(r) for r in connection.execute("PRAGMA foreign_key_check")]
        if integrity != ["ok"]:
            issue("database", "", "integrity", str(integrity))
        if foreign_keys:
            issue("database", "", "foreign_keys", str(foreign_keys))

    elements = {row["symbol"] for row in tables["element_coverage"]}
    ligands = {row["ligand_id"]: row for row in tables["ligands"]}
    phases = {row["record_id"]: row for row in tables["phases"]}
    sources = {row["source_id"] for row in tables["sources"]}
    additional = defaultdict(list)
    for row in tables["additional_components"]:
        additional[row["record_id"]].append((row["ligand_id"], row["component_count"]))
    compositions = {}
    for lid, row in ligands.items():
        if row["name"].lower().startswith("free "):
            issue("ligands", lid, "name", "use the component name and formula; explain free activity in the controls")
        try:
            compositions[lid] = formula_counts(row["formula_ascii"])
            if set(compositions[lid]) - elements:
                raise ValueError("unrecognized element symbol")
        except ValueError as error:
            issue("ligands", lid, "formula_ascii", str(error))
        if row["gibbs_status"] not in {"verified", "accepted", "source_verified_estimate", "defined_reference_state"}:
            issue("ligands", lid, "gibbs_status", "buffered reference requires an admitted evidence status")

    systems = defaultdict(set)
    identities = defaultdict(list)
    ledger = []
    for row in tables["species"]:
        rid = row["record_id"]
        systems[row["symbol"]].add(row["system"])
        for name in ("record_id", "system", "symbol", "species", "formula_ascii", "phase", "phase_detail"):
            value = row[name]
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                issue("species", rid, name, "requires nonempty text without surrounding whitespace")
        if row["symbol"] not in elements or not row["system"].endswith(f"({row['symbol']})"):
            issue("species", rid, "symbol", "element symbol and system label disagree")
        if row["phase"] not in PHASES:
            issue("species", rid, "phase", "unknown controlled phase")
        if row["phase_detail"] and PROVENANCE_IN_LABEL.search(row["phase_detail"]):
            issue("species", rid, "phase_detail", "source/provenance text belongs in evidence or review notes")
        if row["phase_detail"] in ("(aq)", "aqueous standard state", "(g)"):
            issue("species", rid, "phase_detail", "use the canonical generic aqueous or gas label")
        lid, count = row["ligand_id"], row["ligand_count"]
        components = list(additional[rid])
        if lid is None:
            if count is not None or row["ligand_charge"] is not None:
                issue("species", rid, "ligand_id", "unused ligand count and charge must both be NULL")
        elif lid not in ligands or not isinstance(count, (int, float)) or count <= 0:
            issue("species", rid, "ligand_id", "requires a valid reference and positive component count")
        else:
            components.insert(0, (lid, count))
            if row["ligand_charge"] != ligands[lid]["charge"]:
                issue("species", rid, "ligand_charge", "disagrees with the buffered reference")
        if len({item[0] for item in components}) != len(components):
            issue("species", rid, "components", "buffered reference is counted more than once")
        try:
            counts = formula_counts(row["formula_ascii"])
            if set(counts) - elements:
                raise ValueError("unrecognized element symbol")
            if not math.isclose(sum(counts.values()), row["atom_count"], abs_tol=1e-7):
                issue("species", rid, "atom_count", "does not equal the complete formula-unit atom count")
            if row["metal_count"] <= 0 or min(row["core_oxygen_count"], row["core_hydrogen_count"]) < 0:
                raise ValueError("primary count must be positive; residual O/H counts must be nonnegative")
            represented = Counter({row["symbol"]: row["metal_count"]})
            represented["O"] += row["core_oxygen_count"]
            represented["H"] += row["core_hydrogen_count"]
            component_charge = 0.0
            for component, amount in components:
                if component not in compositions or not isinstance(amount, (int, float)) or amount <= 0:
                    raise ValueError("invalid buffered component")
                for element, number in compositions[component].items():
                    represented[element] += amount * number
                component_charge += amount * ligands[component]["charge"]
            if any(not math.isclose(counts.get(el, 0), represented.get(el, 0), abs_tol=1e-7)
                   for el in counts.keys() | represented.keys()):
                issue("species", rid, "components", "primary atom, O/H and buffered components do not reproduce the formula")
            electron = (row["charge"] - component_charge + 2 * row["core_oxygen_count"]
                        - row["core_hydrogen_count"]) / row["metal_count"]
            if not math.isclose(electron, row["electron_coefficient_per_metal"], abs_tol=1e-7):
                issue("species", rid, "electron_coefficient_per_metal", "does not balance the stored metal/water reaction")
            composition_key = tuple(sorted(counts.items()))
        except (ValueError, TypeError, KeyError, ZeroDivisionError) as error:
            issue("species", rid, "formula_ascii", str(error))
            composition_key = row["formula_ascii"]
        identities[(row["symbol"], composition_key, row["phase"], row["charge"], row["phase_detail"])].append(rid)
        identity = phases.get(rid)
        ledger.append({"record_id": rid, "symbol": row["symbol"], "formula_ascii": row["formula_ascii"],
                       "phase": row["phase"], "phase_detail": row["phase_detail"],
                       "charge": row["charge"], "atom_count": row["atom_count"],
                       "identity_status": identity["identity_status"] if identity else "not_recorded"})
    for symbol, names in systems.items():
        if len(names) > 1:
            issue("species", symbol, "system", "element has inconsistent system labels")
    for ids in identities.values():
        if len(ids) > 1:
            issue("species", ";".join(ids), "identity", "duplicate formula/charge/phase/detail identity requires review")

    for rid, row in phases.items():
        if row["identity_status"] not in IDENTITY_STATUSES:
            issue("phases", rid, "identity_status", "unknown or conflated phase/evidence status")
        for name in ("identified_phase", "spacegroup_symbol", "spacegroup_number", "possible_phases", "notes"):
            if row[name] is not None and not row[name].strip():
                issue("phases", rid, name, "unknown optional text must be NULL")
        number = row["spacegroup_number"]
        if number is not None and (not re.fullmatch(r"\d+", number) or not 1 <= int(number) <= 230):
            issue("phases", rid, "spacegroup_number", "requires an International Tables number, stored as digits")
        if bool(row["spacegroup_symbol"]) != bool(number):
            issue("phases", rid, "spacegroup_symbol", "space group symbol and number must be supplied together")

    values = {row["value_id"]: row for row in tables["reported_thermochemistry"]}
    locator_formats = Counter()
    for vid, row in values.items():
        if row["property"] not in UNITS or row["unit"] != UNITS.get(row["property"]):
            issue("reported_thermochemistry", vid, "unit", "property and canonical unit disagree")
        if row["status"] not in STATUSES:
            issue("reported_thermochemistry", vid, "status", "unknown evidence status")
        if row["property"] == "gibbs_energy_of_formation" and row["status"] == "accepted":
            issue("reported_thermochemistry", vid, "status", "accepted applies to compilation enthalpies and entropies")
        if row["status"] == "not_available" and row["value"] is not None:
            issue("reported_thermochemistry", vid, "value", "missing-evidence status requires a NULL value")
        for field, lower_bound in (("temperature_K", 0), ("pressure_bar", 0)):
            condition = row[field]
            if isinstance(condition, (int, float)) and (condition < lower_bound or
                                                      (field == "pressure_bar" and condition == 0)):
                issue("reported_thermochemistry", vid, field, "invalid absolute observation condition")
        if row["uncertainty"] is not None and (row["value"] is None or row["uncertainty"] < 0):
            issue("reported_thermochemistry", vid, "uncertainty", "requires a value and a nonnegative uncertainty")
        if row["status"] in {"verified", "accepted", "source_verified_estimate", "defined_reference_state"}:
            if row["value"] is None or row["source_id"] not in sources:
                issue("reported_thermochemistry", vid, "source_id", "admitted observation requires a value and source")
        if row["status"] == "defined_reference_state" and (row["value"] != 0 or row["property"] == "absolute_entropy"):
            issue("reported_thermochemistry", vid, "status", "reference conventions apply to zero formation G/H")
        parent = values.get(row["supersedes_value_id"])
        if row["supersedes_value_id"] and (not parent or any(parent[k] != row[k] for k in ("record_id", "property"))):
            issue("reported_thermochemistry", vid, "supersedes_value_id", "link must identify the same species and property")
        locator = row.get("source_locator")
        if locator and locator.lstrip().startswith(("{", "[")):
            try:
                if not isinstance(json.loads(locator), dict):
                    raise ValueError("structured locator must be an object")
                locator_formats["json_object"] += 1
            except ValueError as error:
                issue("reported_thermochemistry", vid, "source_locator", str(error))
        else:
            locator_formats["text" if locator else "source_fallback"] += 1

    affected_by_source = defaultdict(set)
    affected_by_ligand = defaultdict(set)
    for row in tables["species"]:
        for lid in [row["ligand_id"], *(item[0] for item in additional[row["record_id"]])]:
            if lid in ligands:
                affected_by_ligand[lid].add(row["record_id"])
                affected_by_source[ligands[lid]["source_id"]].add(row["record_id"])
    for row in values.values():
        affected_by_source[row["source_id"]].add(row["record_id"])
    species_errors = Counter()
    for row in findings:
        if row["table"] in ("species", "phases"):
            affected = row["id"].split(";")
        elif row["table"] == "reported_thermochemistry":
            affected = [values[row["id"]]["record_id"]]
        elif row["table"] == "sources":
            affected = affected_by_source[row["id"]]
        elif row["table"] == "ligands":
            affected = affected_by_ligand[row["id"]]
        else:
            affected = []
        species_errors.update(affected)
    for row in ledger:
        row["representation_errors"] = species_errors[row["record_id"]]
    return {"database": str(path), "counts": {t: len(rows) for t, rows in tables.items()},
            "species_checked": len(ledger), "errors": len(findings), "findings": findings,
            "phase_identity_counts": dict(Counter(row["identity_status"] for row in ledger)),
            "locator_formats": dict(locator_formats), "storage_types": profile,
            "species": sorted(ledger, key=lambda row: row["record_id"])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=ROOT / "src/pourbase/data/pourbase.sqlite")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()
    result = audit_database(args.database)
    if args.json:
        args.json.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    if args.csv:
        with args.csv.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(result["species"][0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(result["species"])
    print(f"Checked {result['species_checked']} species and {result['counts']['reported_thermochemistry']} "
          f"observations: {result['errors']} representation errors.")
    raise SystemExit(bool(result["errors"]))


if __name__ == "__main__":
    main()
