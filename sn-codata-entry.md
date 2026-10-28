# Sn(cr) entropy cited to the CODATA Key Values

The findings below describe the original correction request. Implementation on
28 October 2026 is recorded in the checklist at the end and in
[the source review](docs/sources/reference-state-corrections.md).

pourbase does not redistribute the CODATA Key Values (Cox, Wagman and Medvedev 1989): it is a
commercially published compilation, and its values are excluded where they reappear, such as the bold
entries of NEA tables (see `docs/excluded-compilations.md` and `THIRD_PARTY_NOTICES.md`). One record
breaks that rule.

## The record

| value_id | value | status | source_id | locator |
|---|---|---|---|---|
| `gfe-sn-sn-q+0-solid-metal:entropy:preferred` | 51.18 J/(mol K) | `defined_reference_state` | `NIST_CODATA_1984_Sn` | "CODATA Key Values table; Sn(cr, white); S° at 298.15 K" |

The same record already has an open value that is identical:

| value_id | value | status | source_id |
|---|---|---|---|
| `gfe-sn-sn-q+0-solid-metal:absolute_entropy:nea02a-selected` | 51.18 ± 0.08 J/(mol K) | `verified` | `NEA_OECD_20261014_Sn` (Table III-1, printed p. 44) |

The digitized NBS Tables (CSV row 3098, Sn "I, white", cr) give 51.55 J/(mol K).

## Requested change

Remove the CODATA-cited value (and the `NIST_CODATA_1984_Sn` source if nothing else uses it), so that
the NEA value becomes the recommended S° of Sn(cr). The recommended number stays 51.18 J/(mol K), so no
diagram changes. Then:

- check that the default selection policy picks the NEA value and that nothing else depended on the
  removed value ID;
- regenerate the statistics and update the snapshot tests as usual;
- confirm that no other value cites the CODATA Key Values directly
  (`citation LIKE '%CODATA Key Values%'`).

## Related, optional

`NIST_CODATA_1984_Ag` (S° of Ag(cr), 42.55 J/(mol K)) cites the NBS Tables, not CODATA. Only the
source ID is misleading; renaming it is cosmetic and can wait.

## Also: three CODATA constants in the temperature code

`src/pourbase/temperature.py` hard-codes `ENTROPY_H2, ENTROPY_O2, ENTROPY_WATER = 130.680, 205.152, 69.95`
J/(mol K) from the CODATA Key Values. The database uses the NBS Tables values for the same quantities
(H2(g) 130.684, O2(g) 205.138, H2O(l) 69.91 J/(mol K); these are also what the transcription audit fills
in). Please switch the constants (and their comment and `CODATA` citation string) to the NBS values,
then rerun the temperature tests and the paper's temperature statistics, which will move slightly.

## Also: drop CODATA from the default policy

pourbase does not redistribute CODATA Key Values, so the default policy should not rank a CODATA family.
In `src/pourbase/data/selection-policy.toml`, remove `"CODATA"` from class A (`families = ["NEA-TDB"]`)
and remove the `"CODATA" = ["CODATA"]` line under `[families]`. With the Sn record gone, no
recommended value changes; check that with `compare_policies` against the current default.

## Also: two recommended values in the wrong family

- `gfe-ge-hgeo3-q-1-aqueous-aq` ΔfG° (source `Barner_Scheuerman_1978_HGeO3_via_MP`) is classed as
  "Materials Project" (class F, "computed values, included only on explicit request") because its
  citation contains "Materials Project", yet the default policy selects it. The value is from Barner and
  Scheuerman (1978), an experimental compilation reached through the MP ion reference data. Fix the
  citation or family so it is not class F; check that the paper's statement about class F then holds
  (no recommended value from the Materials Project family under the default policy).
- `gfe-n-n2-q+0-aqueous-aq` (G, H and S; source `NIST_WebBook_N2_Henry_298K`) cites the NIST Chemistry
  WebBook, SRD 69, a restricted NIST database (listed in docs/excluded-compilations.md). The Henry's-law
  data are Rolf Sander's compilation; cite Sander's openly licensed publication (Atmos. Chem. Phys. 2023,
  CC BY 4.0, verify) as the source instead, or replace the values.
  After re-citing, remove the "NIST WebBook" family from the default policy as well (class B families and
  the `"NIST WebBook" = ["WebBook"]` pattern), as for CODATA; the paper's policy table no longer lists it.

## Links from source notes to repository-root files

The documentation site is built from `docs/` only and its CI build runs with `--strict`, so a link
such as `../../THIRD_PARTY_NOTICES.md` breaks the build. In new or edited notes under `docs/`, link
files outside `docs/` by their GitHub URL, for example
`https://github.com/FrederikLizakJohansen/pourbase/blob/main/THIRD_PARTY_NOTICES.md`. Check with
`zensical build --strict` before committing.

## Statuses of elemental reference states

The paper defines *defined reference state* as a value fixed by thermodynamic convention (for example
ΔfG° = 0 for an element in its standard state). The selected values label elemental reference states
inconsistently across properties:

- Entropy: the 46 `defined_reference_state` entropies are the nonzero absolute entropies of elements
  (Ag 42.55, Au 47.4 J/(mol K), ...). These are measured values; give them the status of the source
  they come from (`verified` where checked against it).
- Formation enthalpy: the ΔfH° = 0 of the 75 reference elements is `accepted` for 40, `defined_reference_state`
  for 2 (Se, Ra(cr)) and absent (`not_available`) for 33. Record ΔfH° = 0 as `defined_reference_state`
  for all 75, consistent with ΔfG°.

The paper's status table (`paper/generated/status-table.tex`, written by
`paper/scripts/generate_paper_assets.py`) regenerates from the database, so no paper edit is needed
after the data change.

## Resolution checklist

- [x] Remove the directly cited Sn CODATA observation and unused source. Select
  the existing NEA entropy, 51.18 ± 0.08 J/(mol K), and redirect the old rounded
  observation's supersession link to it.
- [x] Confirm that no source citation contains `CODATA Key Values` and that no
  observation link depends on the removed value ID.
- [x] Replace the temperature module's entropy constants and citation with the
  open NBS values; regenerate temperature statistics.
- [x] Remove CODATA and NIST WebBook from the default policy. Comparison against
  the previous policy on the corrected database changes zero selections.
- [x] Keep the Barner/Scheuerman experimental citation separate from its Materials
  Project transcription locator. No default recommendation is classified as MP.
- [x] Remove the three restricted WebBook-derived N2 observations and unused source.
  Select the already retained CC BY 4.0 Sander/NBS triplet, whose absolute entropy
  includes the gas reference. Preserve the other open alternatives and estimate warnings.
- [x] Relabel the 73 remaining nonzero reference-state entropies as source values:
  71 accepted and two verified by matching retained verified observations.
- [x] Record zero formation enthalpy by convention for all 75 elemental standard
  states: relabel 40 existing zeros, retain two defined zeros and add 33 missing ones.
- [x] Regenerate database statistics and update intentional count, selection and
  temperature expectations. The database has 1,771 species and 5,297 observations;
  the additional enthalpy zeros are defined conventions, separate from measurements.
- [x] Complete the final full tests, paper sensitivity outputs, proof and release checks:
  580 tests pass, strict Zensical build reports no issues, the full sensitivity run
  uses 200 samples per mode across 75 systems, and the private 56-page paper proof
  compiles in three LuaLaTeX passes. Wheel/source packaging and installed-wheel checks pass.

The optional Ag source-ID rename remains cosmetic and deferred; its actual citation
already identifies the NBS Tables. This correction keeps the completed expansion
round closed and carries forward other source reviews and permission holds.
