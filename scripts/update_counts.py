#!/usr/bin/env python3
"""Fill the database counts and the NEA acknowledgement in README.md and CONTRIBUTING.md.

Run from the repository root after the database changes::

    python scripts/update_counts.py          # rewrite the files
    python scripts/update_counts.py --check  # exit 1 if a file is out of date

A count is written between ``<!-- count:NAME -->`` and ``<!-- /count -->``; the NEA volumes cited by
the database are listed between ``<!-- nea-volumes -->`` and ``<!-- /nea-volumes -->``.
"""

from __future__ import annotations

import re
import sys
from contextlib import closing
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "src"))
import pourbase as pb  # noqa: E402

DATABASE = REPOSITORY / "src" / "pourbase" / "data" / "pourbase.sqlite"
FILES = (REPOSITORY / "README.md", REPOSITORY / "CONTRIBUTING.md")
WORDS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")

# Chemical Thermodynamics Series volumes, in the form the acknowledgement lists them.
NEA_VOLUMES = {
    "1": ("Grenthe, I., Fuger, J., Konings, R. J. M., Lemire, R. J., Muller, A. B., Nguyen-Trung, C. "
          "and Wanner, H.", "Chemical Thermodynamics of Uranium", 1992),
    "3": ("Rard, J. A., Rand, M. H., Anderegg, G. and Wanner, H.",
          "Chemical Thermodynamics of Technetium", 1999),
    "5": ("Guillaumont, R., Fanghänel, T., Fuger, J., Grenthe, I., Neck, V., Palmer, D. A. and Rand, M. H.",
          "Update on the Chemical Thermodynamics of Uranium, Neptunium, Plutonium, Americium and "
          "Technetium", 2003),
    "6": ("Gamsjäger, H., Bugajski, J., Gajda, T., Lemire, R. J. and Preis, W.",
          "Chemical Thermodynamics of Nickel", 2005),
    "7": ("Olin, Å., Noläng, B., Osadchii, E. G., Öhman, L.-O. and Rosén, E.",
          "Chemical Thermodynamics of Selenium", 2005),
    "8": ("Brown, P. L., Curti, E. and Grambow, B., with Ekberg, C.",
          "Chemical Thermodynamics of Zirconium", 2005),
    "11": ("Rand, M., Fuger, J., Grenthe, I., Neck, V. and Rai, D.",
           "Chemical Thermodynamics of Thorium", 2008),
    "12": ("Gamsjäger, H., Gajda, T., Sangster, J., Saxena, S. K. and Voigt, W.",
           "Chemical Thermodynamics of Tin", 2012),
    "13a": ("Lemire, R. J., Berner, U., Musikas, C., Palmer, D. A., Taylor, P. and Tochiyama, O.",
            "Chemical Thermodynamics of Iron, Part 1", 2013),
    "13b": ("Lemire, R. J., Palmer, D. A., Taylor, P. and Schlenz, H.",
            "Chemical Thermodynamics of Iron, Part 2", 2020),
    "14": ("Grenthe, I., Gaona, X., Plyasunov, A. V., Rao, L., Runde, W. H., Grambow, B., Konings, R. J. M., "
           "Smith, A. L. and Moore, E. E.",
           "Second Update on the Chemical Thermodynamics of Uranium, Neptunium, Plutonium, Americium and "
           "Technetium", 2020),
    "15": ("Rand, M., Palmer, D. A., Fuger, J. and Gajda, T.",
           "Chemical Thermodynamics of Selected Ancillary Compounds of Interest to Radioactive Waste "
           "Management", 2024),
}
NEA_NUMBERS = {"6355": "13a", "7499": "13b", "7500": "14", "7626": "15"}
VOLUME = re.compile(r"Chemical Thermodynamics(?: Series)?,? ?(?:[Vv]olume)? ?(\d+[ab]?)\b")
NEA_NUMBER = re.compile(r"NEA No\. ?(\d{4})")
COUNT = re.compile(r"(<!-- count:(\w+) -->).*?(<!-- /count -->)", re.S)
VOLUMES = re.compile(r"(<!-- nea-volumes -->\n).*?(<!-- /nea-volumes -->)", re.S)


def counts() -> dict[str, int]:
    with closing(pb.ThermodynamicDatabase(DATABASE).connect()) as connection:
        def scalar(query: str) -> int:
            return connection.execute(query).fetchone()[0]

        return {
            "species": scalar("SELECT COUNT(*) FROM species"),
            "systems": scalar("SELECT COUNT(*) FROM element_coverage WHERE coverage_status='supported'"),
            "reported": scalar("SELECT COUNT(*) FROM reported_thermochemistry"),
            "ligands": scalar("SELECT COUNT(*) FROM ligands"),
            "terminal_gaps": scalar(
                "SELECT COUNT(*) FROM selected_thermochemistry WHERE gibbs_status='terminal_evidence_gap'"
            ),
            "fallbacks": scalar("SELECT COUNT(*) FROM computational_fallbacks"),
        }


def nea_volumes() -> list[str]:
    """The Chemical Thermodynamics Series volumes cited by the database, in series order."""
    with closing(pb.ThermodynamicDatabase(DATABASE).connect()) as connection:
        citations = [row[0] for row in connection.execute(
            "SELECT DISTINCT citation FROM sources WHERE citation LIKE '%Nuclear Energy Agency%'"
        )]
    volumes = set()
    for citation in citations:
        volumes.update(VOLUME.findall(citation))
        volumes.update(NEA_NUMBERS[number] for number in NEA_NUMBER.findall(citation))
    unknown = volumes - NEA_VOLUMES.keys()
    if unknown:
        raise SystemExit(f"Add NEA volume(s) {', '.join(sorted(unknown))} to NEA_VOLUMES")
    return sorted(volumes, key=lambda volume: (int(volume.rstrip("ab")), volume))


def formatted(value: int) -> str:
    return WORDS[value] if value < len(WORDS) else f"{value:,}"


def acknowledgement(volumes: list[str]) -> str:
    return "".join(
        f"- {authors} *{title}*. OECD Nuclear Energy Agency, Chemical Thermodynamics Series Volume "
        f"{volume} ({year}).\n"
        for volume in volumes
        for authors, title, year in [NEA_VOLUMES[volume]]
    )


def update(text: str, values: dict[str, int], volumes: str) -> str:
    def count(match: re.Match[str]) -> str:
        name = match.group(2)
        if name not in values:
            raise SystemExit(f"Unknown count {name!r}; known: {', '.join(values)}")
        return f"{match.group(1)}{formatted(values[name])}{match.group(3)}"

    text = COUNT.sub(count, text)
    return VOLUMES.sub(lambda match: f"{match.group(1)}{volumes}{match.group(2)}", text)


def main() -> None:
    check = "--check" in sys.argv[1:]
    values = counts()
    volumes = acknowledgement(nea_volumes())
    stale = []
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        new = update(text, values, volumes)
        if new != text:
            stale.append(path.name)
            if not check:
                path.write_text(new, encoding="utf-8")
    if check and stale:
        raise SystemExit(f"Out of date: {', '.join(stale)}. Run python scripts/update_counts.py")
    print(f"Updated {', '.join(stale)}" if stale else "Up to date")


if __name__ == "__main__":
    main()
