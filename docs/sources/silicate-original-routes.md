# R11j: seven silicate source routes

Reviewed 20 October 2026. Six routes support eligible additions: **27 observations,
five species and one free silicate reference**. Seven previously missing properties
become available. All earlier observations and preferred IDs remain. The seventh
route has a specific temperature and ionic-strength hold.

| Native route | Full formula and decision |
| --- | --- |
| 48, Si4O10(4−), log K −36.3 | H4Si4O12(4−): retain NEA1992 and NEA2003 selected G, plus local G alternatives from the original PSI2014 and Nagra2023 SIT evaluations. |
| 154, AlSiO5(3−), 0.53 | AlH4SiO7(3−): hold the 20 °C, 1.2 M measurement and unverified temperature conversion. |
| 230, CaSiO3(aq), 4.6 | CaH2SiO4(aq): retain original 2002/2014/2023 association evaluations. |
| 238, MgSiO3(aq), 5.7 | MgH2SiO4(aq): retain the corresponding three association evaluations. |
| 280, FeHSiO3(2+), 9.7 | FeH3SiO4(2+): retain the original 2002 mean and 2023 SIT evaluation. |
| 408, AlHSiO3(2+), 7.4 | Existing AlH3SiO4(2+): retain original 2002/2014/2023 alternatives. |
| 427, SiO3(2−), −23.14 | H2SiO4(2−): retain NEA1992 and NEA2003 selected G/H/S and add the matching free ligand reference. |

The same Ca/Mg source reviews also provide alternatives for the existing
MH3SiO4(+) complexes. Their protonation and charge distinguish them from the new
neutral MH2SiO4 complexes. The 2014 Ca/Mg reevaluation retains the 2002 rounded
constants with revised interaction coefficients. These observations share experimental
ancestry; their separate references identify the evaluations without treating them
as independent measurements.

## Exact sources and reuse

- [Grenthe et al. (1992), *Chemical Thermodynamics of Uranium*, OECD2004 reprint](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/uranium.pdf): Table IV.1, printed p. 72 / PDF p. 90; silicon discussion pp. 394–399 / PDF pp. 412–417.
- [Guillaumont et al. (2003), *Update on the Chemical Thermodynamics of Uranium, Neptunium, Plutonium, Americium and Technetium*](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/update_on_the_chemical_thermodynamics_of_uranium_neptunium_plutonium_americium_and_technetium_volume_5.pdf): Table 8-1, pp. 141–142 / PDF pp. 181–182.
- [Hummel et al. (2002), Nagra NTB02-16](https://media.nagra.ch/uploads/2022/08/e_ntb02-016.pdf): own evaluations pp. 315–317 / PDF pp. 339–341.
- [Hummel (2014), *Data Selection for Silicon*, PSI TM-44-12-05](https://www.psi.ch/sites/default/files/import/les/DatabaseEN/TM-44-12-05.pdf): own tetramer SIT p. 9, Ca/Mg p. 10, aluminium regression p. 13; printed and PDF page numbers coincide.
- [Hummel and Thoenen (2023), Nagra NTB21-03](https://media.nagra.ch/uploads/2023/05/NTB-21-03.pdf): own tetramer p. 966, Ca/Mg p. 969, Al p. 972, alkaline-Al conditions pp. 973–974 and Fe pp. 994–996. Add 58 for PDF page numbers.

The NEA observations are NEA-authored selected or calculated auxiliary evaluations.
Their reaction analyses and derivations are checked separately from inherited
commercial compilation constants. Reuse follows **NEA-TDB-OECD-2026-10-14** and
the [OECD data terms](https://www.oecd.org/en/about/terms-conditions.html).
OECD and NEA are acknowledged through the volume citations. Every sublicense
of work using the data must carry the same acknowledgment requirement and require
further sublicensees to do the same. No separate third-party restriction was
identified for these NEA-authored evaluations. Full books and private permission
correspondence remain external.

The reprint warns that its selected tables were superseded in part. The four
admitted cells were checked against the original 2003 update and its observations
are retained explicitly. G/H and tetramer G agree; H2SiO4 entropy changes from
−1.487 to −1.488 J/(mol K). The [official November2005 volume-5 errata](https://www.oecd-nea.org/dbtdb/pubs/Errata_Update.pdf)
were retrieved through the direct publication link and checked in full. They contain
no correction to these four silicon cells. Reconciliation with the 2020 auxiliary
tables remains a separate source follow-up. These entries identify the historical
editions examined.
Nagra2023 continues to use the original NEA monomer reaction constants.

Nagra/PSI additions follow the completed isolated-original-numerical-facts review.
Each is an original author evaluation with a local, reproducible formation-G
adaptation. Publication copyright and reproduction/storage rights remain applicable.
Full reports, table expression and bulk database files stay external. This is distinct
from a blanket open licence for those publications. Open non-SRD NBS inputs retain
NIST credit and warranty terms; the Miron2017 H3SiO4 input carries its completed R04
original-result/open-water review. Distributed notices describe these routes separately.

## Values, arithmetic and reference scope

NEA2003 supplies H2SiO4(2−) G = −1175651 ± 1265 J/mol,
H = −1381960 ± 15330 J/mol and S = −1.488 ± 51.592 J/(mol K).
Its tetramer G is −4075179 ± 5437 J/mol. The original assigned intervals remain;
no uniform standard-deviation convention is imposed. The H2 thermal interval is
large because the original association experiment required extrapolation from
60–200 °C and 1 m NaCl. No tetramer H/S/Cp is inferred.

Local association estimates use

`G(complex) = G(metal ion) + G(free silicate) − RT ln(10) log K`.

The new H2SiO4 ligand is pinned to its preferred NEA G. Existing H3SiO4 retains
its preferred Miron2017 G = −1252304 J/mol. The Ca/Mg neutral constants are
4.6/5.7 in 2002 and 2014 and 4.50/5.52 in 2023. Existing Ca/Mg H3 complexes
receive 1.2/1.5 and 1.17/1.36 variants. Aluminium receives 7.4, 7.42 and 7.49;
iron receives 9.7 and 9.69. All reaction intervals and exact input IDs are stored.
Local total-G uncertainty remains NULL because input covariance is unavailable.

Tetramer alternatives use

`4 H4SiO4 = H4Si4O12(4−) + 4 H+ + 4 H2O`,

`G(tetramer) = 4 G(H4SiO4) − 4 G(H2O) − RT ln(10) log K`.

PSI2014 gives −36.3 ± 0.2; Nagra2023 gives −36.28 ± 0.16. These local
alternatives explicitly use the retained NBS H4SiO4 G = −1316600 J/mol and
water G = −237129 J/mol. NEA's source tetramer discussion uses an H4SiO4
reference of −1309 ± 3 kJ/mol, differing from its table's −1307.735 kJ/mol.
That internal source discrepancy is retained. The mixed preferred NBS, Miron
and NEA references do not reproduce every source's acid-base and polymerization
constant jointly. Each local estimate records its own reference basis.

The unchanged policy prefers NEA2003 G/H/S and tetramer G. It prefers the
2002 Ca/Mg/Fe local evaluations under its earlier-publication tie break; the
later alternatives remain selectable. Existing Miron Ca/Mg/Al preferred values
and the explicit aluminium override remain. The policy fingerprint stays
`b2ad235bba62` with 46 overrides and 10 exclusions.

## Conditions hold and calculation checks

The alkaline aluminium route corresponds to **AlH4SiO7(3−)**. Its native 0.53
is log10(3.4), an apparent constant measured at **20 °C and I = 1.2 M** by
Gout et al. (2000). Nagra2023 extrapolates to zero ionic strength, obtaining
−0.4 ± 0.2, while a justified conversion to 298.15 K remains unverified.
Neither number enters the 298.15 K observation table. The withdrawn
AlH6SiO7(−) proposal is a different species. Its original methods and temperature
conversion remain an explicit follow-up, as does the inherited aluminium thermal
reaction from Pokrovski1996.

Staging preserves every prior SQL row and preferred ID and is idempotent.
Full-formula atom/charge, electron/proton coefficients and reaction arithmetic pass.
All 74 default maps and uncertainty masks remain unchanged. Twelve buffered
scenarios cover Ca/Mg/Fe/Al; 25 supported metal balances conserve the primary
inventory. Fe silicate changes optional buffered diagrams. Calcium and magnesium
neutral complexes become available with the new fixed free-H2SiO4 activity.
No total-silicon inventory is inferred. Tetramer energies normalize over four Si;
the existing closed-balance filter excludes polynuclear aqueous species.

The dataset now contains **1043 species / 3313 observations**, with selected
G/S/H **920/817/701**, 29 ligand references and 74 supported systems.
Historical request coverage remains **116/131 (NEA28/28, NIST88/103)**;
six original crystalline G gaps remain. **Fifteen further R11 routes** and the
separate source/chemistry holds stay open. The next finite batch is the two
pyrophosphate routes. Completed source reviews and concurrent GUI work are retained.
