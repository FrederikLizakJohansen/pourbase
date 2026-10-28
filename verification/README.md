# Transcription audit

A manual check of randomly drawn database values against their cited sources, with the tools to
repeat or extend it. `samples.csv` and `results.csv` retain 96 completed reviews
from the original 100-value sample reported in the paper (section "Manual
verification of thermodynamic records"). Four direct JANAF observations and
their completed reviews were archived privately on 28 October 2026 when those
observations were excluded from the distributed database. The remaining sample
and result rows are unchanged; no new sample or source review was performed.
`sampling-provenance.json` records the excluded IDs, original file hashes and
the original sampling population. Exported statistics describe the retained
subset and preserve that historical population instead of relabelling the
sample as a fresh draw from today's database.

    python draw_sample.py -n 50 --seed <any integer>         # or use "Draw sample…" in the app
    QT_QPA_PLATFORM=offscreen python fetch_evidence.py        # or "Fetch missing evidence" in the app
    python verify_app.py

## Files

| File | Content |
|---|---|
| `samples.csv` | Every drawn value, with round, seed, draw date and database version. Later rounds never repeat a value. |
| `evidence/` | Not in the repository; `fetch_evidence.py` rebuilds it. Per sample: a grab of the source around the value (`.png`), the full page for PDFs (`-page.png`) and how it was found (`.json`). |
| `cache/` | Downloaded sources. PDFs you attach in the app are stored as `attached-*.pdf`. Not in the repository. |
| `results.csv` | One row per reviewed sample (the latest review counts). |
| `sampling-provenance.json` | Original sampling scope, private-archive hashes and the IDs excluded from the public review corpus. Contains no archived thermochemical values. |
| `summary-by-family.csv`, `audit-statistics.tex`, `audit-table.tex` | Written by Statistics → export (also copied to `paper/generated/` when that folder exists). |

## Population

All reported values with a number and a cited source, except defined reference states (zero by
convention): every status, including superseded source values, since each was transcribed.

## How evidence is found

* NBS Tables: the row of the NIST CSV named in the locator; the property column is boxed.
* NIST-JANAF: the 298.15 K row of the table text; the property column is boxed.
* PDFs (NEA, USGS, others; landing pages that name their PDF are followed): the page named in the
  locator. Every place the database value appears on it is boxed; if it is not on that page the whole PDF
  is searched. A box marks where the database number is printed, so check that it sits in the right row
  and column. No box is itself a finding to check.
* Paywalled articles and web pages: no picture. Open the link, or attach a PDF you have.

## Reviewing

With **Blind review** on, the database value stays hidden until you save. Type the number exactly as
printed (sign and all decimals), pick the printed unit, tick what applies, Ctrl+Enter.

Outcomes:
* match: equal at the printed precision;
* rounding: differs by one in the last printed digit;
* mismatch, with the kind: sign, decimal shift, kcal↔kJ, transposed digits, n digit(s) differ, or a
  ticked wrong row, property or conditions;
* not found: the value is not in the source;
* not verifiable: the source could not be read (left out of the error rate).

The error rate counts mismatches and values not found among all checked values, with a 95 % Wilson
interval. Values the database derives (unit conversion, combination of G = H − TS) should be ticked as
derived; compare against the printed inputs and note them.

With blind review, Ctrl+Enter first checks the reading (and reveals the database value), then saves on
the second press. A reading changed after the reveal is saved with the flag `revised_after_reveal` and
the blind reading in the notes; Statistics counts them.

**⏸ Defer** (Ctrl+D), below the check boxes, marks a sample you could not locate yet and moves to the next one: the row turns grey,
the database value stays hidden and Ctrl+Enter skips it until every other sample is done. Clicking it
again (▶ Undo defer) returns the sample to pending at once. Saving a reading replaces the deferral.
Deferred samples stay out of the statistics.

In PDF grabs the red box is the chosen occurrence: numbers in the top and bottom 7 % of the page (page
numbers, running heads) are ignored, and an occurrence on the same line as the row named in the locator
(or the species formula) wins. Orange boxes mark other occurrences.

For PDFs the Evidence tab can step through every place the database number is printed in the PDF
(**◀ Previous** / **Next number in PDF ▶**, chosen page first); the Source tab follows to that page.
**Redo grab** fetches the sample's evidence again, for instance after attaching a PDF.

Derived values get a form in the panel with one field per printed input (name, unit and coefficient,
never the value). Four recipes are recognised: a reaction with reference values and ΔrH° or log K; a
metal–ligand complex from log K; a printed value plus n H2O(l) (Shock et al. print the anhydrous
formula, often in calories); and G = H − T(S − Σ nᵢ S°ᵢ) or its inverse, also combined with the water
step. The result is worked out as the fields fill and goes into your reading in kJ/mol or J/(mol K).
The free Calculator stays available for anything else.

Inputs the reviewed source does not print are filled in and shown in grey: H2O(l) and element
standard-state values from the NBS Tables, and reference ions or ligands the database took from another
source (as recorded in the locator). Hover for the source; overwrite if needed. Only the printed inputs
are left to type.
