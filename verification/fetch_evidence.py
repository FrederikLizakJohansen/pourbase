"""Download the sources of sampled values and grab the place where each value should be.

    QT_QPA_PLATFORM=offscreen python fetch_evidence.py            # every sample without evidence
    QT_QPA_PLATFORM=offscreen python fetch_evidence.py S0007      # one sample again

For each sample, evidence/<sample_id>.png shows the source around the value and evidence/<sample_id>.json
says how it was found:

* NBS Tables (NIST digitization): the CSV row named in the locator, with the property column marked.
* NIST-JANAF: the 298.15 K row of the table, with the property column marked.
* PDF sources: the page named in the locator (or found by search), with every place the database value
  appears highlighted. No highlight on the right page is itself a finding to check.
* Anything else (paywalled articles, web pages): no picture; the app opens the link.

Rows are located from the locator text and values from the database number, never from the reviewer's entry.
"""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRectF, QSize, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QGuiApplication, QImage, QPainter, QPen  # noqa: E402
from PySide6.QtPdf import QPdfDocument  # noqa: E402

from audit import CACHE, EVIDENCE, NBS_CSV_URL, SAMPLES, derivation, guess_source_unit, read_csv, source_family, to_source_unit  # noqa: E402

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) pourbase-audit"
NBS_COLUMNS = {"enthalpy_of_formation": 7, "gibbs_energy_of_formation": 8, "absolute_entropy": 10}
JANAF_COLUMNS = {"absolute_entropy": 2, "enthalpy_of_formation": 5, "gibbs_energy_of_formation": 6}


def download(url: str) -> Path | None:
    """The cached file for ``url``, downloaded on first use; None when the server refuses."""
    CACHE.mkdir(exist_ok=True)
    stem = hashlib.sha1(url.encode()).hexdigest()[:16]
    for existing in CACHE.glob(stem + ".*"):
        return existing
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=90) as response:
            data = response.read()
    except Exception as error:  # reported in the evidence note
        print(f"  download failed: {url}: {error}", file=sys.stderr)
        return None
    if data[:5] != b"%PDF-" and (match := re.search(rb'citation_pdf_url"\s+content="([^"]+)"', data)):
        try:  # a landing page that names its PDF, as USGS and many journals do
            pdf_url = html.unescape(match.group(1).decode())
            with urllib.request.urlopen(urllib.request.Request(pdf_url, headers={"User-Agent": USER_AGENT}),
                                        timeout=120) as response:
                pdf = response.read()
            if pdf[:5] == b"%PDF-":
                data = pdf
        except Exception as error:
            print(f"  linked PDF failed: {error}", file=sys.stderr)
    suffix = ".pdf" if data[:5] == b"%PDF-" else ".csv" if url.endswith(".csv") else ".txt" if url.endswith(".txt") \
        else ".html"
    path = CACHE / (stem + suffix)
    path.write_bytes(data)
    return path


def local_override(url: str) -> Path | None:
    """A PDF the reviewer attached in the app for a source the script cannot download."""
    path = CACHE / ("attached-" + hashlib.sha1(url.encode()).hexdigest()[:16] + ".pdf")
    return path if path.exists() else None


# text tables (NBS CSV, JANAF) drawn as images
def table_image(title: str, header: list[str], rows: list[list[str]], mark_row: int, mark_column: int,
                path: Path) -> None:
    font = QFont("DejaVu Sans Mono")
    font.setPixelSize(15)
    metrics = QFontMetricsF(font)
    widths = [max(metrics.horizontalAdvance(str(row[i])) if i < len(row) else 0 for row in [header] + rows) + 18
              for i in range(len(header))]
    line = metrics.height() + 8
    image = QImage(QSize(int(sum(widths) + 20), int(line * (len(rows) + 3) + 20)), QImage.Format_RGB32)
    image.fill(QColor("white"))
    painter = QPainter(image)
    painter.setFont(font)
    painter.setPen(QColor("#555"))
    painter.drawText(QRectF(10, 6, image.width() - 20, line), Qt.AlignLeft | Qt.AlignVCenter, title)
    for r, row in enumerate([header] + rows):
        y = 10 + line * (r + 1)
        x = 10.0
        if r - 1 == mark_row:
            painter.fillRect(QRectF(10, y, sum(widths), line), QColor("#fff3b0"))
        for c, width in enumerate(widths):
            cell = row[c] if c < len(row) else ""
            if r - 1 == mark_row and c == mark_column:
                painter.setPen(QPen(QColor("#d62728"), 2))
                painter.drawRect(QRectF(x + 2, y + 1, width - 4, line - 2))
            painter.setPen(QColor("#111") if r else QColor("#1f4e78"))
            painter.drawText(QRectF(x + 6, y, width - 8, line), Qt.AlignLeft | Qt.AlignVCenter, str(cell))
            x += width
    painter.end()
    image.save(str(path))


def strip_tags(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


_nbs_rows: list[list[str]] | None = None


def nbs_rows() -> list[list[str]]:
    global _nbs_rows
    if _nbs_rows is None:
        path = download(NBS_CSV_URL)
        text = path.read_text(encoding="utf-8-sig")
        _nbs_rows = list(csv.reader(io.StringIO(text)))
    return _nbs_rows


def nbs_evidence(sample: dict, image: Path) -> dict:
    rows = nbs_rows()
    locator = sample["locator"]
    index = None
    if match := re.search(r"zero-based row (\d+)", locator):
        index = int(match.group(1))
    elif match := re.search(r"logical record (\d+)", locator):
        index = int(match.group(1)) - 1
    elif match := re.search(r"(Table \d+:[A-Za-z]+);\s*([^;]+)\((\w+)\)\s*(?:[;,]|$)", locator):
        table, formula, state = match.group(1), match.group(2).strip(), match.group(3)
        start = next((i for i, row in enumerate(rows) if row and row[0].strip() == table), None)
        if start is not None:
            for i in range(start + 1, len(rows)):
                if rows[i] and rows[i][0].startswith("Table "):
                    break
                states = ("ai", "ao", "aq") if state == "aq" else (state,)  # NBS splits aqueous into ai and ao
                if len(rows[i]) > 4 and strip_tags(rows[i][0]) == formula and rows[i][4].strip() in states:
                    index = i
                    break
    if index is None or index >= len(rows):
        return {"method": "nbs-csv", "located": False, "note": "Row not identified from the locator"}
    column = NBS_COLUMNS[sample["property"]]
    header = ["Formula", "Solvent", "Name", "State descr.", "State", "M g/mol", "ΔfH(0 K) kJ/mol", "ΔfH° kJ/mol",
              "ΔfG° kJ/mol", "H°−H0° kJ/mol", "S° J/(mol K)", "Cp J/(mol K)"]
    low, high = max(index - 4, 0), min(index + 5, len(rows))
    shown = [[strip_tags(cell) for cell in row[:12]] for row in rows[low:high]]
    table_image(f"NBS_Tables_with_ErratumValues.csv, row {index} (zero-based)", header, shown, index - low, column,
                image)
    return {"method": "nbs-csv", "located": True, "row": index, "file": NBS_CSV_URL,
            "note": f"CSV row {index}, column {header[column]}"}


def janaf_evidence(sample: dict, image: Path) -> dict:
    url = re.sub(r"\.html$", ".txt", sample["url"])
    path = download(url)
    if path is None:
        return {"method": "janaf", "located": False, "note": "Table not downloaded"}
    lines = [line.split("\t") for line in path.read_text(errors="replace").splitlines()]
    index = next((i for i, line in enumerate(lines) if line and line[0].strip() == "298.15"), None)
    if index is None:
        return {"method": "janaf", "located": False, "note": "No 298.15 K row"}
    low, high = max(index - 3, 2), min(index + 4, len(lines))
    table_image(f"{lines[0][0].strip()}  {' '.join(lines[0][1:]).strip()}  ({url})", lines[1], lines[low:high],
                index - low, JANAF_COLUMNS[sample["property"]], image)
    return {"method": "janaf", "located": True, "file": url, "note": "298.15 K row; JANAF prints kJ/mol and J/(K mol)"}


# PDF sources
def value_strings(sample: dict) -> list[str]:
    """Ways the database value may be printed in the source, most specific first."""
    unit = guess_source_unit(sample["unit"], sample["locator"])
    value = to_source_unit(float(sample["value"]), sample["unit"], unit)
    found = []
    for decimals in (4, 3, 2, 1, 0):
        text = f"{value:.{decimals}f}"
        if decimals and abs(float(text) - value) > 0.5 * 10 ** -decimals + 1e-9:
            continue
        for variant in (text, text.replace("-", "−"), text.lstrip("-")):
            if len(re.sub(r"\D", "", variant)) >= 3 and variant not in found:
                found.append(variant)
    return found


def candidate_pages(document: QPdfDocument, locator: str) -> list[int]:
    pages = []
    for match in re.finditer(r"PDF\s*(?:page|pp?)\.?\s*(\d+)", locator, re.I):
        pages.append(int(match.group(1)) - 1)
    for match in re.finditer(r"printed\s*(?:page|pp?)\.?\s*(\d+)", locator, re.I):
        label = document.pageIndexForLabel(match.group(1))
        if label >= 0:
            pages.append(label)
    ordered = []
    for page in pages + [p + d for p in pages for d in (1, -1, 2, -2)]:
        if 0 <= page < document.pageCount() and page not in ordered:
            ordered.append(page)
    return ordered


SUBSCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻·", "01234567890123456789+-.")
MARGIN = 0.07  # share of the page height at top and bottom where running heads and page numbers sit


def row_labels(sample: dict) -> list[str]:
    """Texts that name the source row: the row given in the locator and the species formula."""
    labels = []
    for match in re.finditer(r"\brow\s+([^,;]+)|([A-Za-z][\w().+-]*)\s+row\b", sample["locator"]):
        label = (match.group(1) or match.group(2)).strip()
        labels += [label, re.sub(r"\((cr|s|l|g|aq|am)\)$", "", label)]
    formula = re.sub(r"\s*\(.*$", "", sample["species"]).translate(SUBSCRIPTS)
    labels += [formula, formula.replace("(H2O)", ".H2O")]
    return [label for i, label in enumerate(labels) if len(label) >= 2 and label not in labels[:i]]


def _occurrences(document: QPdfDocument, page: int, text: str, string: str, numeric: bool) -> list[QRectF]:
    rects, start = [], 0
    haystack, needle = (text, string) if numeric else (text.lower(), string.lower())
    while (index := haystack.find(needle, start)) >= 0:
        before = text[index - 1] if index else " "
        after = text[index + len(string)] if index + len(string) < len(text) else " "
        follow = text[index + len(string) + 1] if index + len(string) + 1 < len(text) else " "
        decimal_follows = after in ".," and follow.isdigit()  # "163" at the start of "163.100"
        clean = (not (before.isdigit() or before == "." or after.isdigit() or decimal_follows) if numeric
                 else not before.isalnum())
        if clean:
            rects.append(document.getSelectionAtIndex(page, index, len(string)).boundingRectangle())
        start = index + len(string)
    return rects


def find_on_page(document: QPdfDocument, page: int, strings: list[str], labels: list[str]) -> list[tuple[float, QRectF]]:
    """Places on ``page`` where the value is printed, best first.

    Numbers in the top and bottom margins (page numbers, running heads) are skipped. A number on the same
    line as a row label ranks first; then longer printed forms; then position on the page.
    """
    text = document.getAllText(page).text()
    height = document.pagePointSize(page).height()
    label_lines = [rect.center().y() for label in labels for rect in _occurrences(document, page, text, label, False)]
    found: list[tuple[tuple, QRectF]] = []
    for rank, string in enumerate(strings):
        for rect in _occurrences(document, page, text, string, True):
            if not MARGIN * height < rect.center().y() < (1 - MARGIN) * height:
                continue
            if any(rect.intersects(other) for _key, other in found):
                continue
            tolerance = max(rect.height(), 6.0)
            on_row = any(abs(rect.center().y() - y) <= tolerance for y in label_lines)
            found.append(((0 if on_row else 1, rank, rect.y()), rect))
    found.sort(key=lambda item: item[0])
    return [(key[0], rect) for key, rect in found]


def pdf_evidence(sample: dict, path: Path, image: Path) -> dict:
    document = QPdfDocument()
    document.load(str(path))
    if document.status() != QPdfDocument.Status.Ready:
        return {"method": "pdf", "located": False, "note": "PDF could not be opened"}
    strings = value_strings(sample)
    labels = row_labels(sample)
    pages = candidate_pages(document, sample["locator"])
    if derivation(sample) is not None:
        # the stored number is computed, so searching for it finds only coincidences; show the input pages
        named = re.search(r'"source_pdf_pages":\s*\[([\d,\s]+)\]', sample["locator"])
        pages = [int(p) - 1 for p in named.group(1).split(",")] if named else pages
        strings = []
    hits, page = [], None
    # the first located page whose best match sits on a labelled row; else the first page with any match
    for candidate in pages:
        found = find_on_page(document, candidate, strings, labels)
        if found and (not hits or (found[0][0] == 0 and hits[0][0] != 0)):
            hits, page = found, candidate
        if hits and hits[0][0] == 0:
            break
    searched_all = False
    if not hits and strings and document.pageCount() <= 1500:
        searched_all = True
        for candidate in range(document.pageCount()):
            found = find_on_page(document, candidate, strings, labels)
            if found and (not hits or (found[0][0] == 0 and hits[0][0] != 0)):
                hits, page = found, candidate
            if hits and hits[0][0] == 0:
                break
    if page is None:
        page = pages[0] if pages else None
    if page is None:
        return {"method": "pdf", "located": False, "file": str(path), "page": None,
                "note": "No page in the locator and the value was not found by search"}
    size = document.pagePointSize(page)
    scale = 2.2
    render = document.render(page, QSize(int(size.width() * scale), int(size.height() * scale)))
    canvas = QImage(render.size(), QImage.Format_RGB32)
    canvas.fill(QColor("white"))
    painter = QPainter(canvas)
    painter.drawImage(0, 0, render)
    for index, (_on_row, rect) in reversed(list(enumerate(hits))):
        painter.setPen(QPen(QColor("#d62728"), 3.5) if index == 0 else QPen(QColor(240, 150, 40, 170), 1.5))
        painter.drawRect(QRectF(rect.x() * scale - 4, rect.y() * scale - 3, rect.width() * scale + 8,
                                rect.height() * scale + 6))
    painter.end()
    full = image.with_name(image.stem + "-page.png")
    canvas.save(str(full))
    if hits:
        centre = hits[0][1].center().y() * scale
        top = max(int(centre - 330), 0)
        canvas.copy(0, top, canvas.width(), min(660, canvas.height() - top)).save(str(image))
    else:
        canvas.save(str(image))
    no_text = not document.getAllText(page).text().strip()
    if not strings:
        note = (f"Derived value: the stored number is not printed. PDF page {page + 1} holds the reaction data; "
                "the other inputs are named in the panel")
    elif hits:
        note = (f"Database value found {len(hits)}× on PDF page {page + 1}; the red box "
                + ("is on the row named in the locator" if hits[0][0] == 0 else "is the best guess (no row label matched)")
                + ("; orange boxes are other occurrences" if len(hits) > 1 else ""))
    else:
        note = ("PDF has no text layer (scan); read the page" if no_text else
                f"Database value not found on PDF page {page + 1}" + (" or anywhere in the PDF" if searched_all else ""))
    # every occurrence in the PDF, the chosen page's (best first) leading, for stepping through in the app
    occurrences = [(page, on_row, rect) for on_row, rect in hits]
    if strings and document.pageCount() <= 1500:
        for other in range(document.pageCount()):
            if other != page and len(occurrences) < 300:
                occurrences += [(other, on_row, rect) for on_row, rect in find_on_page(document, other, strings, labels)]
    occurrences_json = [{"page": p, "on_row": not r, "x": q.x(), "y": q.y(), "w": q.width(), "h": q.height()}
                        for p, r, q in occurrences]
    return {"method": "pdf", "located": bool(hits), "on_labelled_row": bool(hits) and hits[0][0] == 0,
            "occurrences": occurrences_json,
            "file": str(path), "page": page, "page_image": str(full), "searched": strings[:6], "labels": labels,
            "note": note}


def evidence(sample: dict) -> dict:
    EVIDENCE.mkdir(exist_ok=True)
    image = EVIDENCE / f"{sample['sample_id']}.png"
    family = source_family(sample["url"])
    try:
        if family.startswith("NBS"):
            result = nbs_evidence(sample, image)
        elif family == "NIST-JANAF":
            result = janaf_evidence(sample, image)
        else:
            path = local_override(sample["url"]) or download(sample["url"])
            if path is not None and path.suffix == ".pdf":
                result = pdf_evidence(sample, path, image)
            else:
                result = {"method": "link", "located": False, "file": str(path) if path else None,
                          "note": "Not a downloadable PDF; open the link (institutional access may be needed)"}
    except Exception as error:  # one bad source must not stop the batch
        result = {"method": "error", "located": False, "note": f"{type(error).__name__}: {error}"}
    result["image"] = str(image) if image.exists() else None
    (EVIDENCE / f"{sample['sample_id']}.json").write_text(json.dumps(result, indent=1))
    return result


def main() -> None:
    QGuiApplication.instance() or QGuiApplication([])
    wanted = set(sys.argv[1:])
    for sample in read_csv(SAMPLES):
        done = (EVIDENCE / f"{sample['sample_id']}.json").exists()
        if (wanted and sample["sample_id"] not in wanted) or (not wanted and done):
            continue
        result = evidence(sample)
        print(f"{sample['sample_id']}  {source_family(sample['url']):32s} {result['note']}")


if __name__ == "__main__":
    main()
