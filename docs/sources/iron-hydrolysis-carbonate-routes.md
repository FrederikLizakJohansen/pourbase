# R11i: iron hydrolysis and carbonate routes

Reviewed 19 October 2026. Five PSI/Nagra routes are reconciled. The ferric dimer
already has a complete NEA G/H/S triplet. Four native routes retain specific
source or phase holds. Four eligible NEA model alternatives are added for the
two existing nominal ferrihydrite records; all earlier observations remain.

| Native route | Decision |
| --- | --- |
| Fe(OH)3(am), log K −5 | Hold the generic proxy: its line count and specimen composition are unspecified. Retain the separate line-specific NEA models below. |
| Fe(OH)3(mic), log K −3 | Hold the generic proxy: microcrystalline does not establish six-line ferrihydrite identity. |
| FeCO3(pr), association log K 0.12115 | Hold the precipitate's original-source and phase mapping. Qualify its historical link to crystalline siderite as a phase mismatch. |
| Fe2(OH)2(4+), log K −2.95 | Link existing NEA2013 selected G/H/S. The inherited native constant adds no independent NEA observation. |
| Fe3(OH)4(5+), log K −6.3 | Hold original numerical methods and standard-state correction; NEA2013 selected no trimer. |

## Eligible NEA alternatives and reuse

[Lemire et al. (2013), Chemical Thermodynamics of Iron, Part 1, NEA No. 6355](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/6355-vol13a-iron.pdf)
provides the following model evaluations at 298.15 K and 1 bar. The nominal
composition is fixed Fe(OH)3; actual ferrihydrite composition varies.

| Observation | Value | Exact source |
| --- | --- | --- |
| Nominal two-line formation H | −826.7 ± 2.1 kJ/mol | Section VII.2.15.1, printed p. 227 / PDF p. 269 |
| Nominal six-line formation H | −829.9 ± 2.0 kJ/mol | Same section and page |
| Nominal six-line standard S | 130 ± 10 J/(mol K) | Table VII-13 footnote 3, p. 228 / PDF p. 270 |
| Local nominal six-line formation G | From calculated log Ksp = −38.97 ± 0.64 | Table VII-13 ferrihydrite row and footnote 3, p. 228 / PDF p. 270 |

NEA adjusts the original Majzlan et al. (2004) calorimetric results to its
lepidocrocite reference. The original −827.1/−830.3 kJ/mol model observations
remain available, with their completed R05 source review. NEA explicitly
qualifies the nominal enthalpies as suggestions outside its normal selected
set. The entropy is estimated and the solubility is calculated from the model.
All four additions therefore retain `source_verified_estimate`; their shared
ancestry is explicit. They are alternatives within existing property coverage.

Reuse follows the written **NEA-TDB-OECD-2026-10-14** clarification and
[OECD data terms](https://www.oecd.org/en/about/terms-conditions.html).
OECD and NEA are acknowledged through the volume citation. The same OECD
acknowledgment requirement must accompany every sublicense of work using the
data, and further sublicensees must pass it on. The carried source review
identifies no separate restriction on these NEA-authored adjustments and model
evaluations. Upstream calorimetry is retained as scientific provenance.
The permission evidence, email hash and exact source-file hash remain in the
external checkpoint; complete publications and private correspondence remain
external. This permission is separate from other sources' holds.

## Arithmetic, policy and temperature

The local G estimate uses the source-consistent equation

`Gf(Fe(OH)3) = Gf(Fe3+) + 3 Gf(OH−) + RT ln(10) log Ksp`.

The retained NEA selected Fe3+ anchor is −16226 J/mol (Table III-1, p. 44 /
PDF p. 86). NEA's auxiliary OH− anchor is −157220 ± 72 J/mol (Table IV-1,
p. 55 / PDF p. 97). This uses NEA's own evaluated auxiliary data. Switching
to the separately retained NBS OH− anchor −157244 would shift the result by
−72 J/mol. No free-ion reference or ligand table is changed. The source's
log Ksp interval is labelled ±2σ. Shared thermochemical inputs and covariance
prevent an independently supported total formation-G interval, which stays NULL.
The calculated solubility is linked model evidence, not an independent experiment.

The unchanged policy classifies the NEA citation as international-review family
A while preserving its model estimate status. It selects both adjusted H
observations and the six-line S. The existing explicit G overrides retain the
original preferred Gibbs endpoints. These preferred properties constitute a
mixed-source set; they are not a jointly consistent NEA triplet. Every original
observation remains, and the policy has 46 overrides and 10 exclusions.

All 74 default phase maps and uncertainty masks remain unchanged. With the
existing constant formation-entropy approximation, each ferrihydrite's G shifts
by −33.54 J/mol at 323.15 K and −100.62 J/mol at 373.15 K because H increases
by 400 J/mol. The checked iron phase maps and masks remain unchanged at both
temperatures. Three fixed-free-carbonate scenarios and six supported ideal/Davies
primary-iron balances pass. Existing polynuclear-aqueous exclusions in closed
mass balance remain applicable; this batch adds no trimer or new solver model.

## Native-source findings and separate holds

[Hummel et al. (2002), Nagra NTB02-16](https://media.nagra.ch/uploads/2022/08/e_ntb02-016.pdf),
section 5.6, p. 173, adopts the Pearson/Nordstrom iron data unchanged. The native
amorphous and microcrystalline solubility proxies span variable crystallinity.
The labels do not specify the two-line/six-line materials used for the NEA
alternatives. Their source/identity holds remain independent of those additions.

[Hummel and Thoenen (2023), Nagra NTB21-03](https://media.nagra.ch/uploads/2023/05/NTB-21-03.pdf),
pp. 400–401 and 416–419, traces the native dimer and trimer to Baes and Mesmer
(1976), with an unexplained Nordstrom correction of Kester et al. (1975) for the
trimer. Its newer dimer calculation fixes Brown and Ekberg's (2016) log K to
fit interaction coefficients. This does not establish a new Nagra-authored
standard log K. New commercial-compilation imports stay excluded from this task.
The [original Kester chapter record](https://digitalcommons.usf.edu/msc_facpub/1597/)
identifies DOI 10.1021/bk-1975-0018.ch003; numerical methods remain a retrieval target.

Nagra2023 pp. 487–488 distinguishes room-temperature precipitated FeCO3 from
heat-treated siderite. The old precipitate link to `r07-fe-feco3-siderite`
remains in the reconciliation history with its mismatch documented; it is
removed from current compatible links. Existing crystalline-siderite observations
are preserved. The [original Jensen et al. (2002) author abstract](https://orbit.dtu.dk/en/publications/the-solubility-of-rhodochrosite-mncosub3sub-and-siderite-fecosub3/)
confirms wet/dried log Ksp values −10.43/−11.03 and original intervals. NEA2013
p. 368 gives −11.43 for wet crystals; Nagra2023 p. 487 footnote 46 identifies
that typo. The incorrect value is not imported. Full original phase/method
verification and a suitable precipitated-phase representation remain follow-up.

## Progress

- [x] Review five routes and stage four eligible ferrihydrite alternatives.
- [x] Preserve all earlier rows, qualify the carbonate phase mismatch, and link the existing dimer.
- [x] Verify selection changes, default diagrams, thermal shifts and supported iron balances.

There are **22 further original-source routes** in the R11 queue. The four
iron holds remain separate. Historical request coverage stays **116/131
(NEA 28/28; NIST 88/103)**, with six original crystalline G gaps. Earlier
solid, nickel, tin, palladium, europium, ammonia and zirconium holds are carried
forward. See the external running tracker for release completion and next work.
