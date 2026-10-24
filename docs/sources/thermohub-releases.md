# R14: Additional ThermoHub releases

The catalog was checked on **24 October 2026**. The latest listed
[GitHub release](https://github.com/thermohub/thermohub/releases) and
[Zenodo deposit](https://doi.org/10.5281/zenodo.13797639) remained v1.2.0.
The tag points to `ebca97700353c039c86f8759cb4ce75ab1f204f2`;
repository HEAD is `c3e4acf4531204e4c2974c2d4ac5a1b96f37d5ba`.
All 23 compressed graph collections have identical bytes in the archive,
tag and HEAD. The later README change carries no numerical update.
Later releases require a new comparison.

## Licence and source decisions

Repository and archive contain GPL-3.0 licence text; deposit metadata says
CC BY 4.0. This review uses the explicit repository GPL route for verified
identical files and preserves the metadata discrepancy. ThermoHub contributors,
George Dan Miron, ORD Thrace and the ETH Board Open Research Data Program
are acknowledged. Original numerical sources retain separate reuse assessments.

The graph has **9,039 substance records in nine families**, eight dataset
definitions, 2,723 reaction records, 277 bibliography nodes and 5,271 citation
edges. All **27,117 G/H/S slots** have external dispositions: 12,346 scalars
with explicit supported units, 2,508 with missing or ambiguous units, and
12,263 absent or non-scalar properties. Exact symbol, formula, phase, charge
and reference-condition comparisons with older pinned exports identify
5,218 repeated scalar cells, ten changed cells and 7,118 additional cells.
Comparison matches alone establish no original-source lineage.

| Graph family | Records | Disposition |
| --- | ---: | --- |
| NASA-TDB | 2,067 | Carry R08: original tables, polynomial range, phase encoding and units. |
| SLOP16 | 2,035 | Carry R06/R07 and R12; verify differences against original sources. |
| THERMOCHIMIE | 1,456 | Catalog says 10a; datasource/records say 12a. Resolve version, terms and reaction inputs. |
| PSI_NAGRA20 | 1,356 | Distinct 2020 family; original per-property sources and references need review. |
| HERACLES | 949 | Carry the completed 949-record R10 review and holds. |
| MINES23 | 775 | Compare with original MINES23.1; keep versions distinct. |
| CODATA | 151 | Commercial 1989 compilation held; seek independent open evaluations. |
| CEMDATA18 | 127 | Carry R09 phase, inherited-source and component/model decisions. |
| PSI_NAGRA | 123 | Residual family without a dataset definition; establish exact version and lineage. |

No graph scalar enters this batch. All graph reactions retain coupled
source/model decisions. Original-source follow-ups R14a–e and earlier
independent permission and model holds remain separately tracked.

## Fourteen new original NEA observations

The source continuation adds **14 observations on six new solids** from
Rand, Palmer, Fuger and Gajda (2024), *Selected Ancillary Compounds of
Interest to Radioactive Waste Management*, Chemical Thermodynamics 15,
OECD Nuclear Energy Agency, NEA No. 7626, edited by Martinez, Ragoussi
and Costa. The source is
[Table III-1, printed p. 47, PDF p. 89](https://www.oecd-nea.org/upload/docs/application/pdf/2024-06/cts15-selected_ancillary_compounds-r-final-rev.pdf).
PDF SHA-256: `a692194c759255a4d534b30be98080139b0de49c26d35e649313fbb8878b3d99`.
These independently checked 2024 evaluations retain their own source identity.

| Source crystal | G / kJ mol⁻¹ | H / kJ mol⁻¹ | S / J mol⁻¹ K⁻¹ | Discussion |
| --- | ---: | ---: | ---: | --- |
| Na₂CO₃ | −1045.450 ±0.345 | −1129.250 ±0.300 | 135.000 ±0.400 | V.7.1, pp. 381–384 |
| NaHCO₃ | −851.175 ±0.365 | −949.000 ±0.200 | 102.000 ±1.000 | V.7.2, pp. 384–386 |
| K₂CO₃ | −1065.833 ±2.060 | −1151.500 ±2.000 | 155.500 ±1.600 | V.7.3, pp. 387–389 |
| KHCO₃ | Missing | −960.700 ±2.000 | Missing | V.7.4, pp. 389–390 |
| Na₂B₄O₇·10H₂O, borax | Missing | −6289.600 ±3.400 | Missing | V.8.3.1, pp. 410–413 |
| Ca(H₂PO₄)₂·H₂O | −3071.840 ±2.306 | −3423.405 ±2.295 | 259.840 ±0.420 | V.6.2.1.7, pp. 296–297 |

All refer to 298.15 K and 0.1 MPa per full formula unit. G/H are converted
to J/mol; S retains J/(mol K). The four G values are source-internal
calculations identified by footnote (a). Quoted total uncertainty widths
retain their approximately 95% interpretation and the existing mixed-interval
limitation of the uncertainty screen. Informational entropy estimates and
heat capacities supply no missing selected G/S.

Structural discussions establish all six crystal identities. Borax's
traditional formula and structural Na₂B₄O₅(OH)₄·8H₂O have identical atoms.
Calcium phosphate retains both phosphate groups and its water molecule.
Its triclinic identity is recorded without assigning a space group from an
ambiguous overbar in the extracted text.

## Permission and calculation scope

OECD and the OECD Nuclear Energy Agency are acknowledged. The written
clarification supplied on 14 October 2026 and the
[OECD data terms](https://www.oecd.org/en/about/terms-conditions.html)
permit use, adaptation and redistribution, including commercially, with
appropriate citation. Every sublicense of work using these data must include
the same OECD acknowledgment requirement and require further sublicensees
to do the same. Existing permission email and terms evidence are retained.

Publication-use wording was checked with the later explicit TDB data
clarification. These six rows contain NEA-selected evaluations, with no bold
CODATA cells copied without evaluation. No additional restriction or separately
identified third-party ownership was found for the imported cells. Independent
commercial compilation holds remain. See [NEA reuse instructions](nea-tdb-reuse.md).

Calculations require existing free carbonate, phosphate or sodium activities.
Closed balances conserve primary Na, K, Ca or B; secondary references remain
externally prescribed. Na₂CO₃/K₂CO₃ have two primary atoms and one carbonate;
bicarbonates have one primary atom, one carbonate and residual H₁. Calcium
phosphate has one Ca, two phosphate references and residual O₁H₆. Borax has
four B, two sodium references and residual O₁₇H₂₀. Electron coefficients per
primary are Na 1, K 1, Ca 2 and B 3. Mixed source/reference evaluations retain
the existing qualification about NEA's internally consistent reaction set.

All earlier SQL rows and preferred values remain. Policy selects all 14
new observations as class A, filling four G, four S and six H properties.
KHCO₃ and borax remain excluded from Gibbs calculations. All 75 default maps
and uncertainty masks remain unchanged. In tested 19-by-21 phosphate-enabled
Ca grids, the new hydrate occupies 168, 189 and 231 points at free phosphate
log activities −6, −3 and 0. Validation covers 12 buffered diagrams, 36 energies
and 48 primary balances. Historical requests remain 116/131; six original
crystalline G gaps remain open. Totals: **1,302 species, 3,988 observations
and 75 systems**, with selected G/S/H **1084/1061/875**.
