"""Add the table ``element_production`` to the database from its source file.

    python scripts/add_element_production.py [--apply]

The table holds one row per element: global annual production in metric tons, or an explicit gap.
It is separate from the thermochemical evidence and no calculation reads it. Every value comes
from U.S. Geological Survey publications and carries no third-party attribution on production.

Without ``--apply`` the new file is written next to the database and checked, and the database is
left unchanged.
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "src" / "pourbase" / "data" / "pourbase.sqlite"
SOURCE = ROOT / "data" / "production" / "element_production.csv"

SCHEMA = """CREATE TABLE element_production (
    atomic_number INTEGER PRIMARY KEY REFERENCES element_coverage(atomic_number),
    symbol TEXT NOT NULL UNIQUE,
    production_t_per_year REAL CHECK(production_t_per_year IS NULL OR production_t_per_year > 0),
    range_low_t_per_year REAL,
    range_high_t_per_year REAL,
    reference_year INTEGER,
    measured_as TEXT,
    value_basis TEXT NOT NULL CHECK(value_basis IN ('reported', 'converted', 'modelled', 'proxy', 'gap')),
    source_value REAL,
    source_unit TEXT,
    conversion_factor REAL,
    source_citation TEXT,
    source_url TEXT,
    source_locator TEXT,
    reuse_basis TEXT,
    notes TEXT,
    CHECK((production_t_per_year IS NULL) = (value_basis = 'gap')),
    CHECK(production_t_per_year IS NULL OR (source_citation IS NOT NULL AND source_url IS NOT NULL
          AND source_locator IS NOT NULL AND reuse_basis IS NOT NULL))
)"""

COLUMNS = ("atomic_number", "symbol", "production_t_per_year", "range_low_t_per_year", "range_high_t_per_year",
           "reference_year", "measured_as", "value_basis", "source_value", "source_unit", "conversion_factor",
           "source_citation", "source_url", "source_locator", "reuse_basis", "notes")
INTEGERS = {"atomic_number", "reference_year"}
REALS = {"production_t_per_year", "range_low_t_per_year", "range_high_t_per_year", "source_value", "conversion_factor"}


def convert(column: str, text: str) -> object:
    if text == "":
        return None
    if column in INTEGERS:
        return int(text)
    return float(text) if column in REALS else text


def read_rows(path: Path) -> list[tuple]:
    with path.open(newline="", encoding="ascii") as handle:
        return [tuple(convert(column, row[column]) for column in COLUMNS) for row in csv.DictReader(handle)]


def migrate(source: Path, target: Path, rows: list[tuple]) -> None:
    shutil.copyfile(source, target)
    with closing(sqlite3.connect(target)) as connection, connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("DROP TABLE IF EXISTS element_production")
        connection.execute(SCHEMA)
        connection.executemany(f"INSERT INTO element_production VALUES ({','.join('?' * len(COLUMNS))})", rows)


def check(path: Path, rows: list[tuple]) -> None:
    with closing(sqlite3.connect(path)) as connection:
        expected = connection.execute("SELECT atomic_number, symbol FROM element_coverage ORDER BY atomic_number").fetchall()
        stored = connection.execute("SELECT atomic_number, symbol FROM element_production ORDER BY atomic_number").fetchall()
        if stored != expected:
            raise SystemExit("element_production does not match element_coverage")
        if problems := connection.execute("PRAGMA foreign_key_check").fetchall():
            raise SystemExit(f"Foreign-key problems: {problems[:5]}")
        values = connection.execute("SELECT count(production_t_per_year) FROM element_production").fetchone()[0]
    print(f"{len(rows)} rows, {values} values, {len(rows) - values} gaps")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    rows = read_rows(SOURCE)
    target = DATABASE.with_suffix(".production.sqlite")
    migrate(DATABASE, target, rows)
    check(target, rows)
    if args.apply:
        target.replace(DATABASE)
        print(f"applied to {DATABASE}")
    else:
        print(f"checked; new file at {target}")


if __name__ == "__main__":
    main()
