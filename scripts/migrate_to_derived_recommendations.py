"""Move the database to schema 8, in which recommended values are derived by a selection policy.

    python scripts/migrate_to_derived_recommendations.py [--apply]

Schema 7 stores the recommended value of every species twice: as the table ``thermochemistry``
and as the flag ``selected_as_recommended`` in ``reported_thermochemistry``. Schema 8 keeps only
the evidence. The script

1. adds ``source_locator`` to ``reported_thermochemistry`` and fills it with the locator that
   ``thermochemistry`` holds for each recommended value;
2. adds a reported row for every evidence gap recorded only in ``thermochemistry``;
3. drops the flag and the table, and sets ``schema_version`` to 8;
4. derives the recommendations from the new file with the default policy and checks that every
   value, status, uncertainty, source and locator equals the stored one.

Without ``--apply`` the new file is written next to the database and checked, and the database is
left unchanged.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pourbase.database import PROPERTY_COLUMNS, ThermodynamicDatabase  # noqa: E402

DATABASE = ROOT / "src" / "pourbase" / "data" / "pourbase.sqlite"
COLUMNS = ["record_id", "temperature_K", "pressure_bar"] + [
    column for _property, value, prefix, uncertainty in PROPERTY_COLUMNS
    for column in (value, f"{prefix}_status", uncertainty, f"{prefix}_source_id", f"{prefix}_source_locator")]


def stored(path: Path) -> dict[str, tuple]:
    with closing(sqlite3.connect(path)) as connection:
        locators = dict(connection.execute("SELECT source_id, locator FROM sources"))
        rows = {}
        for row in connection.execute(f"SELECT {', '.join(COLUMNS)} FROM thermochemistry"):
            item = dict(zip(COLUMNS, row))
            for _property, _value, prefix, _uncertainty in PROPERTY_COLUMNS:
                # a locator equal to the source's general locator carries no extra information
                if item[f"{prefix}_source_locator"] is None:
                    item[f"{prefix}_source_locator"] = locators.get(item[f"{prefix}_source_id"])
            rows[item["record_id"]] = tuple(item[column] for column in COLUMNS)
        return rows


def migrate(source: Path, target: Path) -> None:
    shutil.copyfile(source, target)
    with closing(sqlite3.connect(target)) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("ALTER TABLE reported_thermochemistry ADD COLUMN source_locator TEXT")
        for property_name, _value, prefix, _uncertainty in PROPERTY_COLUMNS:
            connection.execute(
                f"""UPDATE reported_thermochemistry AS r SET source_locator = (
                        SELECT t.{prefix}_source_locator FROM thermochemistry AS t WHERE t.record_id = r.record_id)
                    WHERE r.property = ? AND r.selected_as_recommended = 1""", (property_name,))
            gaps = connection.execute(
                f"""SELECT t.record_id, t.{prefix}_source_id FROM thermochemistry AS t
                    WHERE t.{prefix}_status = 'terminal_evidence_gap' AND NOT EXISTS (
                        SELECT 1 FROM reported_thermochemistry AS r WHERE r.record_id = t.record_id
                        AND r.property = ? AND r.status = 'terminal_evidence_gap')""", (property_name,)).fetchall()
            unit = "J/(mol K)" if property_name == "absolute_entropy" else "J/mol"
            for record_id, source_id in gaps:
                connection.execute(
                    """INSERT INTO reported_thermochemistry (value_id, record_id, property, value, unit,
                       temperature_K, pressure_bar, status, selected_as_recommended, uncertainty, source_id,
                       supersedes_value_id, source_locator)
                       VALUES (?, ?, ?, NULL, ?, 298.15, 1.0, 'terminal_evidence_gap', 0, NULL, ?, NULL, NULL)""",
                    (f"{record_id}:{property_name}:evidence-gap", record_id, property_name, unit, source_id))
            print(f"{property_name}: {len(gaps)} evidence gaps moved to reported values")
        connection.execute("DROP INDEX IF EXISTS reported_thermo_record_idx")
        connection.execute("ALTER TABLE reported_thermochemistry DROP COLUMN selected_as_recommended")
        connection.execute("CREATE INDEX reported_thermo_record_idx ON reported_thermochemistry(record_id)")
        connection.execute("DROP TABLE thermochemistry")
        connection.execute("UPDATE metadata SET value = '8' WHERE key = 'schema_version'")
        connection.execute("DELETE FROM metadata WHERE key IN ('selection_policy', 'selection_policy_fingerprint')")
        connection.commit()
        if problems := connection.execute("PRAGMA foreign_key_check").fetchall():
            raise SystemExit(f"Foreign-key problems: {problems[:5]}")
        connection.execute("VACUUM")


def derived(path: Path) -> dict[str, tuple]:
    database = ThermodynamicDatabase(path)
    with closing(database.connect()) as connection:
        return {row[0]: tuple(row) for row in connection.execute(f"SELECT {', '.join(COLUMNS)} FROM thermochemistry")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    before = stored(DATABASE)
    target = DATABASE.with_suffix(".schema8.sqlite")
    migrate(DATABASE, target)
    after = derived(target)
    differences = [(key, before[key], after.get(key)) for key in before if before[key] != after.get(key)]
    for key, old, new in differences[:10]:
        print("DIFFERENT", key, [(c, a, b) for c, a, b in zip(COLUMNS, old, new or ()) if a != b])
    print(f"{len(before)} records, {len(differences)} differ")
    if differences:
        target.unlink()
        raise SystemExit("not applied")
    if args.apply:
        target.replace(DATABASE)
        print(f"applied to {DATABASE}")
    else:
        print(f"checked; new file at {target}")


if __name__ == "__main__":
    main()
