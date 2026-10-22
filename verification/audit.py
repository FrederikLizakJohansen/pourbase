"""Shared pieces of the transcription audit: database entries, units, discrepancy classes and statistics."""

from __future__ import annotations

import csv
import json
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATABASE = REPO / "src" / "pourbase" / "data" / "pourbase.sqlite"
SAMPLES = HERE / "samples.csv"
RESULTS = HERE / "results.csv"
CACHE = HERE / "cache"
EVIDENCE = HERE / "evidence"

NBS_CSV_URL = "https://data.nist.gov/od/ds/mds2-2124/NBS_Tables_with_ErratumValues.csv"

SAMPLE_FIELDS = ["sample_id", "round", "seed", "drawn_on", "database_version", "value_id", "record_id", "species",
                 "phase", "property", "value", "unit", "status", "source_id", "citation", "url", "locator"]
RESULT_FIELDS = ["sample_id", "reviewer", "reviewed_on", "seconds", "outcome", "source_text", "source_unit",
                 "source_value_SI", "database_value_SI", "database_in_source_unit", "difference_SI",
                 "relative_difference", "classes", "digit_edits", "decimals", "flags", "notes", "inputs"]

# statuses without a transcribed number: reference states are zero by definition
EXCLUDED_STATUSES = ("defined_reference_state",)

# source units the reviewer can pick, as factor to the database unit
UNITS = {
    "J/mol": {"kJ/mol": 1000.0, "J/mol": 1.0, "kcal/mol": 4184.0, "cal/mol": 4.184},
    "J/(mol K)": {"J/(mol K)": 1.0, "cal/(mol K)": 4.184},
}

FLAGS = {
    "not_found": "Value not found in the source",
    "wrong_row": "Number belongs to another species or phase",
    "wrong_property": "Number belongs to another property (G, H or S)",
    "wrong_conditions": "Different temperature, pressure or standard state",
    "derived": "Database value is derived (converted or combined), not printed",
    "source_unreadable": "Source not available or unreadable",
}
# recorded by the app, not ticked: the reading was changed after the database value was shown
REVISED_FLAG = "revised_after_reveal"


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def database_version(connection: sqlite3.Connection) -> str:
    rows = dict(connection.execute("SELECT key, value FROM metadata").fetchall())
    return rows.get("data_version") or rows.get("version") or ""


def population(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    """Every reported value with a number and a cited source."""
    marks = ",".join("?" * len(EXCLUDED_STATUSES))
    return connection.execute(
        f"""SELECT r.value_id, r.record_id, sp.species, sp.phase, r.property, r.value, r.unit, r.status,
                   r.source_id, s.citation, s.url, COALESCE(r.source_locator, s.locator) AS locator
            FROM reported_thermochemistry r
            JOIN species sp USING (record_id)
            JOIN sources s USING (source_id)
            WHERE r.value IS NOT NULL AND r.status NOT IN ({marks})
            ORDER BY r.value_id""",
        EXCLUDED_STATUSES,
    ).fetchall()


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def append_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if new:
            writer.writeheader()
        writer.writerows(rows)


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def source_family(url: str) -> str:
    """A short name for the kind of source, for stratified statistics."""
    url = url or ""
    if "M32124" in url or "mds2-2124" in url:
        return "NBS Tables (NIST digitization)"
    if "janaf" in url:
        return "NIST-JANAF"
    if "oecd" in url:
        return "OECD NEA TDB"
    if "S0016-7037(96)00339" in url or "S0016-7037(97)00" in url:  # the Shock et al. (1997) papers only
        return "Shock et al. (1997)"
    if "usgs" in url or "10.3133" in url:
        return "USGS"
    if "doi.org" in url:
        return "Other journal articles"
    return "Technical reports and books"


def guess_source_unit(unit: str, locator: str) -> str:
    """The unit the source most likely prints, read from the locator text."""
    text = locator or ""
    if unit == "J/mol":
        if re.search(r"kcal", text, re.I):
            return "kcal/mol"
        if re.search(r"\bcal\b", text, re.I):
            return "cal/mol"
        return "kJ/mol"
    if re.search(r"cal\s*/?\s*\(?\s*mol", text, re.I) and not re.search(r"J\s*/?\s*\(?\s*mol\s*K", text, re.I):
        return "cal/(mol K)"
    return "J/(mol K)"


def to_source_unit(value: float, unit: str, source_unit: str) -> float:
    return value / UNITS[unit][source_unit]


# discrepancy classification
@dataclass
class Comparison:
    outcome: str  # match, rounding, mismatch
    classes: list[str]
    source_SI: float
    database_in_source_unit: float
    difference_SI: float
    relative: float
    digit_edits: int
    decimals: int


def _digits(text: str) -> str:
    return re.sub(r"\D", "", text)


def _levenshtein(a: str, b: str) -> int:
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def _is_transposition(a: str, b: str) -> bool:
    if len(a) != len(b) or a == b:
        return False
    diff = [i for i in range(len(a)) if a[i] != b[i]]
    return len(diff) == 2 and diff[1] == diff[0] + 1 and a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]]


def parse_number(text: str) -> float:
    cleaned = text.strip().replace("−", "-").replace("–", "-").replace(",", ".").replace(" ", "")
    return float(cleaned)


def compare(source_text: str, source_unit: str, database_value: float, database_unit: str) -> Comparison:
    """Classify the difference between the number printed in the source and the database value."""
    source = parse_number(source_text)
    factor = UNITS[database_unit][source_unit]
    shown = database_value / factor
    cleaned = source_text.strip().replace("−", "-").replace(",", ".")
    decimals = len(cleaned.split(".")[1]) if "." in cleaned else 0
    half_step = 0.5 * 10 ** -decimals
    database_text = f"{shown:.{decimals}f}"
    edits = _levenshtein(_digits(cleaned), _digits(database_text))
    difference = database_value - source * factor
    relative = abs(difference) / abs(source * factor) if source else (0.0 if difference == 0 else math.inf)
    classes: list[str] = []
    if abs(shown - source) <= half_step * 1.0001:
        outcome = "match"
    elif abs(shown - source) <= 2 * half_step * 1.0001 + 1e-12:
        outcome, classes = "rounding", ["last digit"]
    else:
        outcome = "mismatch"
        if source and math.isclose(shown, -source, rel_tol=1e-9, abs_tol=half_step):
            classes.append("sign")
        ratio = abs(shown / source) if source else 0
        if ratio > 0:
            power = math.log10(ratio)
            if abs(power - round(power)) < 1e-6 and round(power) != 0:
                classes.append(f"decimal shift ({round(power):+d})")
            for name, scale in (("kcal↔kJ", 4.184), ("cal↔J", 4.184)):
                if math.isclose(ratio, scale, rel_tol=2e-3) or math.isclose(ratio, 1 / scale, rel_tol=2e-3):
                    classes.append(name)
                    break
        if _is_transposition(_digits(cleaned), _digits(database_text)):
            classes.append("transposed digits")
        elif not classes:
            classes.append(f"{edits} digit(s) differ" if edits else "other")
    return Comparison(outcome, classes, source * factor, shown, difference, relative, edits, decimals)


def wilson(successes: int, total: int, z: float = 1.959964) -> tuple[float, float]:
    """95 % Wilson score interval for a proportion."""
    if total == 0:
        return (0.0, 1.0)
    p = successes / total
    centre = (p + z * z / (2 * total)) / (1 + z * z / total)
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return max(0.0, centre - half), min(1.0, centre + half)


# derived values: the source prints the inputs, not the stored number
PROPERTY_SYMBOLS = {"gibbs_energy_of_formation": "ΔfG°", "enthalpy_of_formation": "ΔfH°", "absolute_entropy": "S°"}
T_REF = 298.15
R_GAS = 8.31446261815324
LN10 = math.log(10)
DIATOMIC = {"H": "H2(g)", "O": "O2(g)", "N": "N2(g)", "F": "F2(g)", "Cl": "Cl2(g)", "Br": "Br2(l)", "I": "I2(cr)"}
SUBSCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "01234567890123456789+-")


@dataclass
class Term:
    """One printed input: the reviewer types it in ``unit``; it adds ``coefficient`` × value × ``factor``."""

    label: str
    coefficient: float
    unit: str
    factor: float  # input unit to database unit
    hint: str = ""
    default: float | None = None  # filled in for standard values the reviewed source does not print
    default_source: str = ""


@dataclass
class Recipe:
    """How the database computes a stored value from printed inputs."""

    equation: str
    terms: list
    note: str = ""

    def __post_init__(self) -> None:
        merged: dict[tuple, Term] = {}
        for term in self.terms:  # one field per input, e.g. H2(g) from the composition and from the charge
            key = (term.label, term.unit)
            if key in merged:
                merged[key].coefficient += term.coefficient
            else:
                merged[key] = Term(term.label, term.coefficient, term.unit, term.factor, term.hint, term.default,
                                   term.default_source)
        self.terms = [term for term in merged.values() if abs(term.coefficient) > 1e-12]

    def total(self, values: list[float]) -> float:
        return sum(term.coefficient * term.factor * value for term, value in zip(self.terms, values))


def _energy_unit(prop: str) -> tuple[str, float]:
    return ("J/(mol K)", 1.0) if prop == "absolute_entropy" else ("kJ/mol", 1000.0)


def _core(token: str) -> str:
    """The formula of a species without phase, charge or coefficient: ``2H2O(l)`` → ``H2O``, ``Ra2+`` → ``Ra``."""
    token = re.sub(r"\s*\([^()]*[a-z]{3,}[^()]*\)$", "", token.strip())  # "(s, witherite)", "(aqueous)"
    token = re.sub("[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+$", "", token)  # a superscript charge, before its digits merge with subscripts
    token = token.translate(SUBSCRIPTS)
    token = re.sub(r"^\d+(?=[A-Z(])", "", token)
    token = re.sub(r"\((cr|s|l|g|aq|am|c)\)$", "", token)
    token = re.sub(r"\(\d*[+-]+\d*\)$", "", token)
    token = re.sub(r"[+-]+$", "", token)
    # digits before a bare sign are the charge on a single element ("Ra2+") and a subscript otherwise ("IO3-")
    return re.sub(r"^([A-Z][a-z]?)\d+$", r"\1", token)


def _species_tokens(side: str) -> list[tuple[float, str]]:
    side = re.sub(r"([)+-])\+(?=\d*[A-Z(])", r"\1 ", side)  # "(cr)+2H+" and "IO3-+H+"
    side = re.sub(r"\s\+\s*(?=\d*[A-Z(])", " ", side)  # " +H2O" and " + H2O" separate species
    tokens = [t for t in side.split() if t and t != "+"]
    out = []
    for token in tokens:
        match = re.match(r"^(\d+(?:\.\d+)?)(?=[A-Z(])", token)
        out.append((float(match.group(1)) if match else 1.0, token[match.end():] if match else token))
    return out


def _reaction_recipe(sample: dict, data: dict) -> Recipe | None:
    reaction = data.get("reaction") or data.get("reaction_kind")
    if not reaction or "=" not in reaction:
        return None
    prop = sample["property"]
    symbol = PROPERTY_SYMBOLS[prop]
    unit, factor = _energy_unit(prop)
    left, right = (_species_tokens(part) for part in reaction.split("=", 1))
    target_core = _core(sample["species"])
    record_tail = sample["record_id"]

    def is_target(token: str) -> bool:
        return _core(token) == target_core or token.startswith(record_tail[:12]) or "-q" in token

    side = "right" if any(is_target(t) for _c, t in right) else "left" if any(is_target(t) for _c, t in left) else None
    if side is None:
        return None
    own, other = (right, left) if side == "right" else (left, right)
    target_coefficient = next(c for c, t in own if is_target(t))
    # ΔrX = Σ products − Σ reactants; solve for the target
    sign = 1.0 if side == "right" else -1.0  # target on the product side gets +ΔrX
    terms = []
    # ν_t X_t = ±ΔrX + Σ ν X (other side) − Σ ν X (own side, target excluded); H+ and e- are zero by convention
    for coefficient, token in other:
        if re.search(r"^(H\+|e-)$", token):
            continue
        terms.append(Term(f"{symbol} of {token}", coefficient / target_coefficient, unit, factor))
    for coefficient, token in own:
        if is_target(token) or re.search(r"^(H\+|e-)$", token):
            continue
        terms.append(Term(f"{symbol} of {token}", -coefficient / target_coefficient, unit, factor))
    log_key = next((k for k in ("log10K", "log10_beta", "cumulative_log_beta", "combined_log10K", "source_log10K")
                    if k in data), None)
    if prop == "gibbs_energy_of_formation":
        if "reaction_G_J_mol" in data:
            terms.append(Term("ΔrG° of the reaction", sign / target_coefficient, "kJ/mol", 1000.0))
        elif log_key:
            terms.append(Term("log10 K of the reaction", -sign * R_GAS * T_REF * LN10 / target_coefficient, "", 1.0))
        else:
            return None
    elif prop == "enthalpy_of_formation":
        if "reaction_H_kcal_mol" in data:
            terms.append(Term("ΔrH° of the reaction", sign / target_coefficient, "kcal/mol", 4184.0))
        elif "reaction_H_J_mol" in data:
            terms.append(Term("ΔrH° of the reaction", sign / target_coefficient, "kJ/mol", 1000.0))
        else:
            return None
    else:  # ΔrS = (ΔrH − ΔrG)/T with ΔrG = −RT ln10 log K
        if "reaction_H_J_mol" in data and log_key:
            terms.append(Term("ΔrH° of the reaction", sign / target_coefficient / T_REF, "kJ/mol", 1000.0))
            terms.append(Term("log10 K of the reaction", sign * R_GAS * LN10 / target_coefficient, "", 1.0))
        else:
            return None
    pages = data.get("source_pdf_pages") or ([data["source_pdf_page"]] if data.get("source_pdf_page") else [])
    note = f"Reaction data on PDF page {', '.join(str(p) for p in pages)}" if pages else ""
    return Recipe(f"Reaction: {reaction}", terms, note)


def _water_recipe(sample: dict) -> Recipe | None:
    words = {"one": "1", "two": "2", "three": "3", "four": "4"}
    match = (re.search(r"source formula \+ (\d+) H2O\(l\)", sample["locator"])
             or re.search(r"Formula normalization: \S+ \+ (\d*)\s*H2O\(l\)", sample["locator"])
             or re.search(r"add (one|two|three|four|\d+) H2O\(l\)", sample["locator"])
             or re.search(r"normali[sz]ation: source \S+ \+ (\d*)\s*H2O\(l\) = stored", sample["locator"]))
    if not match:
        return None
    prop = sample["property"]
    symbol = PROPERTY_SYMBOLS[prop]
    unit, factor = _energy_unit(prop)
    locator = sample["locator"]
    calories = bool(re.search(r"cal\b|factor 4\.184", locator))  # Shock et al. and similar print calories
    stated_unit = re.search(r"column[^;]*?:\s*[-−]?[\d.]+\s*(kJ/mol|J/mol|kcal/mol|cal/mol|J/\(mol K\)|cal/\(mol K\))",
                            locator)
    if stated_unit and stated_unit.group(1) in UNITS[sample["unit"]]:
        printed_unit = stated_unit.group(1)  # "…G column: -1575097 J/mol"
    elif prop == "absolute_entropy":
        printed_unit = "cal/(mol K)" if calories else "J/(mol K)"
    else:
        printed_unit = ("kcal/mol" if re.search(r"kcal", locator) else "cal/mol") if calories else "kJ/mol"
    printed_factor = UNITS[sample["unit"]][printed_unit]
    row = (re.search(r"row ([^,;]+)", sample["locator"]) or re.search(r"; (\S+) (?:aqueous )?row", sample["locator"])
           or re.search(r"source (\S+) \+", sample["locator"]))
    count = int(words.get(match.group(1), match.group(1)) or 1)
    return Recipe(f"Stored formula = source formula + {count} H2O(l)", [
        Term(f"{symbol} printed for {row.group(1).strip() if row else 'the source formula'}", 1.0, printed_unit,
             printed_factor),
        Term(f"{symbol} of H2O(l)", float(count), unit, factor),
    ])


def _composition(record_id: str) -> tuple[dict, float] | None:
    with connect() as connection:
        row = connection.execute("SELECT formula_ascii, charge FROM species WHERE record_id = ?", (record_id,)).fetchone()
    if row is None:
        return None
    from pymatgen.core import Composition
    try:
        composition = Composition(re.sub(r"[\[(][+-]?\d*[+-]?[\])]$|[+-]\d*$", "", row["formula_ascii"]))
    except Exception:
        return None
    return {str(element): amount for element, amount in composition.get_el_amt_dict().items()}, float(row["charge"])


def _gibbs_helmholtz_recipe(sample: dict) -> Recipe | None:
    match = re.search(r"\b([GH])\s*=\s*([GH])\s*([-−+])\s*(?:298\.15|T)\s*\*", sample["locator"])
    if match:
        result, given = match.group(1), match.group(2)
    elif (sample["property"] == "gibbs_energy_of_formation"
          and re.search(r"(Delta_f H|ΔfH)[^;]*?=[^;]*?\bS\b[^;]*?=", sample["locator"])):
        result, given = "G", "H"  # "Derived properties: Delta_f H = … and S = …"
    else:
        return None
    stored = re.search(r"stored composition=(\{[^}]*\})", sample["locator"])
    found = _composition(sample["record_id"])
    if found is None:
        return None
    composition, charge = found
    if stored:
        composition = json.loads(stored.group(1))
    q = re.search(r"\bq=([-\d.]+)", sample["locator"])
    charge = float(q.group(1)) if q else charge
    sign = -1.0 if result == "G" else 1.0  # G = H − T·ΔfS ; H = G + T·ΔfS
    given_symbol = "ΔfH°" if given == "H" else "ΔfG°"
    terms = [Term(f"{given_symbol} of the compound", 1.0, "kJ/mol", 1000.0),
             Term("S° of the compound", sign * T_REF, "J/(mol K)", 1.0)]
    for element, amount in sorted(composition.items()):
        state = DIATOMIC.get(element)
        per_atom = 0.5 if state else 1.0
        state = state or ("Hg(l)" if element == "Hg" else f"{element}(cr)")
        terms.append(Term(f"S° of {state}", -sign * T_REF * amount * per_atom, "J/(mol K)", 1.0))
    if charge:
        terms.append(Term("S° of H2(g)", sign * T_REF * charge / 2, "J/(mol K)", 1.0))
    equation = (f"{result} = {given} {'−' if sign < 0 else '+'} T·(S − Σ nᵢ S°ᵢ"
                + (" + q·S°(H2)/2" if charge else "") + ")")
    return Recipe(equation, terms)


NBS_COLUMNS = {"ΔfH°": 7, "ΔfG°": 8, "S°": 10}
_nbs_table: list[list[str]] | None = None


def nbs_value(formula: str, state: str, symbol: str) -> float | None:
    """A value from the NBS Tables (NIST digitization), in kJ/mol or J/(mol K)."""
    global _nbs_table
    if _nbs_table is None:
        import hashlib
        import io
        import urllib.request
        path = CACHE / (hashlib.sha1(NBS_CSV_URL.encode()).hexdigest()[:16] + ".csv")
        if not path.exists():
            CACHE.mkdir(exist_ok=True)
            with urllib.request.urlopen(NBS_CSV_URL, timeout=90) as response:
                path.write_bytes(response.read())
        _nbs_table = list(csv.reader(io.StringIO(path.read_text(encoding="utf-8-sig"))))
    for row in _nbs_table:
        if len(row) > 10 and re.sub(r"<[^>]+>", "", row[0]).strip() == formula and row[4].strip() == state:
            try:
                return float(row[NBS_COLUMNS[symbol]])
            except ValueError:
                return None
    return None


def _json_reference(data: dict, token: str, prop: str, sample_source: str) -> tuple[float, str] | None:
    """The value a reaction locator records for ``token`` from another source, in J/mol or J/(mol K)."""
    charge = re.search(r"\((\d*)[+-]+\)$", token) or re.match(r"^[A-Z][a-z]?(\d+)[+-]+$", token)
    wanted = re.sub(r"[^a-z0-9]", "", _core(token).lower() + (charge.group(1) if charge else ""))
    def matches(name: str) -> bool:
        key = re.sub(r"[^a-z0-9]", "", name.lower())
        return bool(key) and wanted.startswith(key) and len(wanted) - len(key) <= 2
    inputs = data.get("inputs") if isinstance(data.get("inputs"), dict) else {}
    for key, value in [*data.items(), *inputs.items()]:
        if key.endswith(("_reference", "_input")) and isinstance(value, dict) and matches(key.rsplit("_", 1)[0]):
            entry = value.get(prop, value)
            if isinstance(entry, (int, float)):  # {"enthalpy_of_formation": -527600.0, ...}
                return float(entry), "locator"
            if isinstance(entry, dict) and entry.get("source_id") != sample_source:
                number = entry.get("value", entry.get("value_J_mol"))
                if isinstance(number, (int, float)):
                    return float(number), entry.get("source_id", "")
        if key.endswith("_G_J_mol") and prop == "gibbs_energy_of_formation" and isinstance(value, (int, float)):
            name = key[: -len("_G_J_mol")]
            if matches(name) or (name == "water" and _core(token) == "H2O"):
                return float(value), "locator"
    if prop == "gibbs_energy_of_formation" and inputs:
        if inputs.get("ligand_formula") and _core(inputs["ligand_formula"]) == _core(token):
            return float(inputs["ligand_G_J_mol"]), "locator"
        if "metal_G_J_mol" in inputs and re.search(r"\d*\+$", token):
            return float(inputs["metal_G_J_mol"]), inputs.get("metal_value_id", "locator")
    for item in data.get("other_inputs", []) if isinstance(data.get("other_inputs"), list) else []:
        if isinstance(item, dict) and _core(item.get("formula", "")) == _core(token) and "value_J_mol" in item:
            return float(item["value_J_mol"]), "locator"
    anchor = data.get("anchor")
    if isinstance(anchor, dict) and anchor.get("property") == prop and anchor.get("source_id") != sample_source:
        anchor_species = anchor.get("record_id", "").split("-")[2:3]
        if anchor_species and anchor_species[0] == _core(token).lower():
            return float(anchor["value"]), anchor.get("source_id", "")
    return None


def _complete_inputs(locator: str) -> dict | None:
    """The "Complete inputs: {…}" block of a G = H − TΔS locator, naming the source of H (or G) and S."""
    match = re.search(r"Complete inputs:\s*(\{)", locator)
    if not match:
        return None
    try:
        return json.JSONDecoder().raw_decode(locator[match.start(1):])[0]
    except ValueError:
        return None


def _fill_compound(found: Recipe, sample: dict) -> None:
    """For G = H − TΔS: fill the compound's H, G or S when another source supplied it; ask for printed S in its unit."""
    inputs = _complete_inputs(sample.get("locator") or "")
    if not inputs:
        return
    for term in found.terms:
        if not term.label.endswith("of the compound"):
            continue
        key = {"ΔfH°": "H", "ΔfG°": "G", "S°": "S"}[term.label.split()[0]]
        value = inputs.get(f"{key}_J_mol" if key != "S" else "S_J_mol_K")
        source = str(inputs.get(f"{key}_source_id", ""))
        where = str(inputs.get(f"{key}_locator", ""))
        if value is None:
            continue
        if source and source != sample.get("source_id") and re.search(r"NBS|NIST", source + where):
            term.default = float(value) / term.factor
            term.default_source = "NBS Tables"
        elif re.search(r"cal/\(mol K\)" if key == "S" else r"k?cal/mol", where):
            unit = "cal/(mol K)" if key == "S" else ("kcal/mol" if "kcal" in where else "cal/mol")
            term.unit, term.factor = unit, UNITS["J/(mol K)" if key == "S" else "J/mol"][unit]


def _fill_standards(found: Recipe, sample: dict, data: dict | None) -> Recipe:
    """Fill in inputs the reviewed source does not print: water, element standard states, other references."""
    prop_of = {"ΔfH°": "enthalpy_of_formation", "ΔfG°": "gibbs_energy_of_formation", "S°": "absolute_entropy"}
    _fill_compound(found, sample)
    for term in found.terms:
        match = re.match(r"(ΔfH°|ΔfG°|S°) of (\S+)$", term.label)
        if not match:
            continue
        symbol, token = match.groups()
        to_unit = 1000.0 if term.unit == "kJ/mol" else 1.0
        if _core(token) == "H2O":
            value = nbs_value("H2O", "l", symbol)
            if value is not None:
                term.default, term.default_source = value, "NBS Tables"
            continue
        element = re.match(r"^([A-Z][a-z]?)2?\((cr|g|l)\)$", token)
        if element and symbol == "S°":
            formula = token.split("(")[0]
            value = nbs_value(formula, element.group(2), "S°")
            if value is not None:
                term.default, term.default_source = value, "NBS Tables"
            continue
        if data:
            reference = _json_reference(data, token, prop_of[symbol], sample.get("source_id", ""))
            if reference:
                term.default = reference[0] / to_unit
                term.default_source = ("NBS Tables" if re.match(r"(NIST|NBS)", reference[1])
                                       else "database reference")
    return found


def recipe(sample: dict) -> Recipe | None:
    """The printed inputs and arithmetic behind a derived value; None when the source prints the value."""
    found, data = _recipe(sample)
    return None if found is None else _fill_standards(found, sample, data)


def database_inputs(sample: dict, found: Recipe) -> list[float | None]:
    """The input values the database used, each in its term's unit; None where they cannot be recovered."""
    values: list[float | None] = [term.default for term in found.terms]
    locator = (sample.get("locator") or "").lstrip()
    data = None
    if locator.startswith("{"):
        try:
            data = json.JSONDecoder().raw_decode(locator)[0]
        except ValueError:
            data = None
    for index, term in enumerate(found.terms):
        if values[index] is not None:
            continue
        if isinstance(data, dict):
            if term.label.startswith("ΔrH°"):
                if term.unit == "kcal/mol" and "reaction_H_kcal_mol" in data:
                    values[index] = float(data["reaction_H_kcal_mol"])
                elif "reaction_H_J_mol" in data:
                    values[index] = float(data["reaction_H_J_mol"]) / 1000
            elif term.label.startswith("ΔrG°") and "reaction_G_J_mol" in data:
                values[index] = float(data["reaction_G_J_mol"]) / 1000
            elif term.label.startswith("log10 K"):
                key = next((k for k in ("log10K", "log10_beta", "cumulative_log_beta", "combined_log10K",
                                        "source_log10K") if isinstance(data.get(k), (int, float))), None)
                if key:
                    values[index] = float(data[key])
    # a printed value plus water: the locator gives the printed number as "original=…"
    original = re.search(r"original=(-?[\d.]+)", locator)
    for index, term in enumerate(found.terms):
        if values[index] is None and " printed for " in term.label and original and len(
                [t for t in found.terms if " printed for " in t.label]) == 1:
            values[index] = float(original.group(1))
    # text locators state the G, H and S they combined, in J (the water reference statement left out)
    locator = re.sub(r"H2O\(l\),\s*G=[^;]*?J/\(mol K\)", "", locator)
    stated = {name: float(m.group(1)) for name, pattern in
              (("G", r"\bG=(-?[\d.]+)\s*J/mol"), ("H", r"\bH=(-?[\d.]+)\s*J/mol"),
               ("S", r"\bS=(-?[\d.]+)\s*J/\(mol K\)")) if (m := re.search(pattern, locator))}
    water = {term.label.split()[0]: (term, values[i]) for i, term in enumerate(found.terms)
             if term.label.endswith("of H2O(l)") and values[i] is not None}
    if (m := re.search(r"(?:Delta_f H|ΔfH)\s*(?:degree|°)?\s*=\s*(-?[\d.]+)\s*(?:\+/-\s*[\d.]+\s*)?kJ/mol", locator)):
        stated.setdefault("H", float(m.group(1)) * 1000)
    if (m := re.search(r"\bS\s*(?:degree|°)\s*=\s*(-?[\d.]+)\s*(?:\+/-\s*[\d.]+\s*)?J/\(mol K\)", locator)):
        stated.setdefault("S", float(m.group(1)))
    for index, term in enumerate(found.terms):
        if values[index] is not None:
            continue
        symbol = term.label.split()[0]
        key = {"ΔfG°": "G", "ΔfH°": "H", "S°": "S"}.get(symbol)
        if key not in stated:
            continue
        if term.label.endswith("of the compound"):
            values[index] = stated[key] / term.factor
        elif " printed for " in term.label and symbol in water:
            # stated = printed + n·water, and the two terms carry coefficients in the same ratio
            water_term, water_value = water[symbol]
            ratio = water_term.coefficient / term.coefficient
            values[index] = (stated[key] - ratio * water_value * water_term.factor) / term.factor
    # one input still unknown: the stored value fixes it
    missing = [i for i, value in enumerate(values) if value is None]
    if len(missing) == 1:
        i = missing[0]
        known = sum(t.coefficient * t.factor * v for t, v in zip(found.terms, values) if v is not None)
        term = found.terms[i]
        if term.coefficient:
            values[i] = (float(sample["value"]) - known) / (term.coefficient * term.factor)
    return values


def _potential_recipe(sample: dict) -> Recipe | None:
    """ΔfG° of a metal ion from the standard potential of M^z+ + z e- = M: ΔfG° = z·F·E°."""
    match = re.search(r"E\s*(?:degree|°)\s*=\s*\(?(-?[\d.]+)\)?\s*V", sample["locator"])
    if not match or sample["property"] != "gibbs_energy_of_formation":
        return None
    found = _composition(sample["record_id"])
    if found is None or not found[1]:
        return None
    charge = found[1]
    couple = re.search(r"(\S+/\S+),\s*E", sample["locator"])
    label = f"E° of {couple.group(1)}" if couple else "E° of the couple"
    return Recipe(f"ΔfG° = z·F·E° with z = {charge:g}", [Term(label, charge * 96485.33212, "V", 1.0)])


def _text_reaction_recipe(sample: dict) -> Recipe | None:
    """A reaction written in the locator text, with its log K: "…: Ta(OH)5 + H+ = Ta(OH)4+ + H2O, log10 K=0.7007"."""
    if sample["property"] != "gibbs_energy_of_formation":
        return None
    match = (re.search(r"(?:Reaction:|table:)\s*([^,;]*?=[^,;]*?)(?:[,;]|\.\s|$)", sample["locator"])
             or re.search(r"\breaction\s+([^,;]*?=[^,;]*?)(?:[,;]|\.\s|$)", sample["locator"]))
    if not match:
        return None
    reaction = re.sub(r"\((aq|cr|l|g)\)", "", match.group(1)).strip()  # phase marks get in the way of matching
    found = _reaction_recipe(sample, {"reaction": reaction, "log10K": 0.0})
    fit = re.search(r"log10 K\(T\)=([^;,]+?), coefficients \[a,b,c,d\]=\[([^\]]+)\]", sample["locator"])
    if found is not None and fit:
        found.note = (f"The source prints log K(T) = {fit.group(1)} with [a, b, c, d] = [{fit.group(2)}]; "
                      "evaluate it at T = 298.15 K (the Calculator helps)")
    return found


def _text_anchors(locator: str) -> dict | None:
    """Reference values embedded in a text locator: "…anchors: {"Sr": {"formula": …, "values": {…}}, …}"."""
    match = re.search(r"anchors[^{]*(\{)", locator)
    if not match:
        return None
    try:
        anchors = json.JSONDecoder().raw_decode(locator[match.start(1):])[0]
    except ValueError:
        return None
    data = {}
    for name, entry in anchors.items():
        if isinstance(entry, dict) and isinstance(entry.get("values"), dict):
            formula = re.sub(r"<[^>]+>", "", entry.get("formula", name))
            data[f"{formula}_reference"] = {prop: {"value": value, "source_id": "NBS anchor"}
                                            for prop, value in entry["values"].items()}
    return data or None


def _recipe(sample: dict) -> tuple[Recipe | None, dict | None]:
    locator = (sample.get("locator") or "").lstrip()
    if locator.startswith("{"):
        try:
            data = json.JSONDecoder().raw_decode(locator)[0]
        except ValueError:
            return None, None
        return (_reaction_recipe(sample, data), data) if isinstance(data, dict) else (None, None)
    gibbs_helmholtz, water = _gibbs_helmholtz_recipe(sample), _water_recipe(sample)
    if gibbs_helmholtz and water:
        # both steps: the G (or H) and S of the stored formula are each a printed value plus water
        if len(water.terms) < 2:  # "+ 0 H2O(l)": nothing to add
            return gibbs_helmholtz, None
        count = water.terms[1].coefficient
        calories = (water.terms[0].unit.startswith(("cal", "kcal"))
                    or bool(re.search(r"S0016-7037\(96\)00339|slop\d*\.dat", sample["locator"])))  # Shock et al.
        given, entropy = gibbs_helmholtz.terms[0], gibbs_helmholtz.terms[1]
        given_symbol = given.label.split()[0]
        energy_unit, energy_factor = (("cal/mol", 4.184) if calories else ("kJ/mol", 1000.0))
        entropy_unit, entropy_factor = (("cal/(mol K)", 4.184) if calories else ("J/(mol K)", 1.0))
        row = re.search(r"row ([^,;]+)", sample["locator"])
        name = row.group(1).strip() if row else "the source formula"
        expanded = [Term(f"{given_symbol} printed for {name}", 1.0, energy_unit, energy_factor),
                    Term(f"{given_symbol} of H2O(l)", count, "kJ/mol", 1000.0),
                    Term(f"S° printed for {name}", entropy.coefficient, entropy_unit, entropy_factor),
                    Term("S° of H2O(l)", entropy.coefficient * count, "J/(mol K)", 1.0)]
        return Recipe(gibbs_helmholtz.equation + f", with {water.equation[0].lower()}{water.equation[1:]}",
                      expanded + gibbs_helmholtz.terms[2:]), None
    text_reaction = None if (gibbs_helmholtz or water) else _text_reaction_recipe(sample)
    if text_reaction is not None:
        return text_reaction, _text_anchors(locator)
    return gibbs_helmholtz or water or _potential_recipe(sample), None


def derivation(sample: dict) -> str | None:
    """A one-line description of a derived value, or None for a printed one."""
    found = recipe(sample)
    return None if found is None else found.equation
