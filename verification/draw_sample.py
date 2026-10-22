"""Draw a reproducible random sample of reported values for the transcription audit.

    python draw_sample.py -n 50 --seed 20261022            # simple random sample
    python draw_sample.py -n 30 --seed 7 --stratify        # proportional to each source family

Every call appends a new round to samples.csv and never draws a value already sampled, so later
rounds extend the audit. The seed and database version are stored with each row.
"""

from __future__ import annotations

import argparse
import datetime
import random
from collections import defaultdict

from audit import SAMPLE_FIELDS, SAMPLES, append_csv, connect, database_version, population, read_csv, source_family


def draw(count: int, seed: int, stratify: bool = False) -> list[dict]:
    connection = connect()
    version = database_version(connection)
    existing = read_csv(SAMPLES)
    taken = {row["value_id"] for row in existing}
    pool = [row for row in population(connection) if row["value_id"] not in taken]
    rng = random.Random(seed)
    if stratify:
        groups: dict[str, list] = defaultdict(list)
        for row in pool:
            groups[source_family(row["url"])].append(row)
        chosen = []
        for name in sorted(groups):
            share = round(count * len(groups[name]) / len(pool))
            chosen += rng.sample(groups[name], min(share, len(groups[name])))
        rng.shuffle(chosen)
        chosen = chosen[:count]
    else:
        chosen = rng.sample(pool, min(count, len(pool)))
    round_number = 1 + max((int(row["round"]) for row in existing), default=0)
    start = 1 + max((int(row["sample_id"][1:]) for row in existing), default=0)
    today = datetime.date.today().isoformat()
    rows = []
    for offset, row in enumerate(chosen):
        rows.append({"sample_id": f"S{start + offset:04d}", "round": round_number, "seed": seed, "drawn_on": today,
                     "database_version": version, **{key: row[key] for key in SAMPLE_FIELDS[5:]}})
    append_csv(SAMPLES, SAMPLE_FIELDS, rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-n", "--count", type=int, default=50)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--stratify", action="store_true", help="draw proportionally from each source family")
    args = parser.parse_args()
    rows = draw(args.count, args.seed, args.stratify)
    print(f"Drew {len(rows)} values ({rows[0]['sample_id']}–{rows[-1]['sample_id']}) into {SAMPLES.name}"
          if rows else "Nothing left to draw")


if __name__ == "__main__":
    main()
