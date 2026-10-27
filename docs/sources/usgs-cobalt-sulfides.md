# USGS cobalt sulfide selections

R16d5a adds six original author-selected values from
[Robie and Hemingway (1995), USGS Bulletin2131](https://doi.org/10.3133/b2131),
printed p.11 (PDF p.17), at298.15 K and1 bar. Every earlier observation and
preferred choice remains. Each source interval retains its published meaning;
no uniform conversion to one standard deviation or covariance is assumed.

| Phase | Formula | G, kJ/mol | H, kJ/mol | S, J/(mol K) |
| --- | --- | ---: | ---: | ---: |
| Cattierite | CoS2 | −145.1 ±4.9 | −150.9 ±4.9 | 74.8 ±0.2 |
| Linnaeite | Co3S4 | −334.9 ±7.3 | −347.5 ±7.3 | 176.0 ±0.4 |

The complete source formula unit is retained. For Co3S4, energy per primary
atom divides by three once. Against externally buffered S2−, net electrons
per Co are4 for CoS2 and8/3 for Co3S4. Formal Co in the disulfide is+2;
Co3S4 uses a conventional formula-average state8/3. The divalent pyrite
definition is documented in
[Shirako et al. (2014), Table4](https://doi.org/10.1021/ic501770g).
The named minerals resolve phase identity; exact specimen space groups stay
unassigned. Solid solutions and composition-dependent activities remain separate.

## Property-specific ancestry and the entropy-column check

The source H/G column cites original reaction calorimetry by
[Cemič and Kleppa (1988)](https://doi.org/10.1007/BF00203201), reference60,
with additional reference376 for CoS2. The S column cites Stuve, Beyer and
Brown (1985), US Bureau of Mines RI8994, reference399. The published USGS G
cells are retained directly; no reconstructed G is added as an observation.
References in the separate C column concern higher-temperature properties
outside this import. Shared ancestry does not establish independent measurements.

The [original RI8994](https://stacks.cdc.gov/view/cdc/10745) is explicitly
marked Public Domain. Its Table6, p.8 (PDF p.13), gives CoS2
S(T)−S(0)=17.876 cal/(mol K) at298.15 K. Conversion by4.184 gives
74.793184 J/(mol K), consistent with the selected74.8 after rounding.
Table5, p.7 (PDF p.12), gives14.018 cal/(mol K) on the nominal CoS1.33
basis; conversion and the published Co3S4 basis factor of three give
175.953936 J/(mol K), consistent with176.0 after rounding.

The report abstract and discussion label numbers matching the heat-capacity
column as entropy. The table entries Cp=16.313 and12.958 cal/(mol K) are
kept distinct from the S column. This apparent property-column error and its
confidence widths are not imported as entropy. The USGS quoted S widths are
retained independently. The original CoS2 specimen was analyzed asCoS1.973;
USGS provides a nominal-endmember selection. That sample qualification stays
explicit, with no hidden composition correction or claim of exact ideal material.

## Selection, validation and reuse

The policy selects all six new class-B USGS observations. Its fingerprint
`544b421b7f1c` remains unchanged, with53 overrides and13 exclusions.
Recommendation fingerprint: `cfe67366d3a4a32d`. Source-cycle residuals are
within100 J/mol against the diagnostic elemental entropy references; source
rounding supplies no additional confidence interval.

Validation covers54 transformed energies, three buffered diagrams, eight primary
balances and two unchanged thermal inventories. All three buffered diagrams
change; new phases occupy4917 scenario points. All75 default maps and
uncertainty masks remain unchanged. Strict coverage stays53 experimental
systems or56 with fallbacks; the historical116/131 request coverage and six
original crystalline G gaps remain.

The completed USGS federal-evaluation reuse route carries forward to these
individually verified author selections, with property-specific original
numerical ancestry. USGS, Robie and Hemingway are credited. Original reports,
article tables and private correspondence stay outside distributions. These
additions import no direct JANAF, Mills or other held compilation cells.
NIST attribution, OECD/NEA downstream acknowledgment and all independent
source/model holds remain applicable to their separately retained evidence.

Metadata: `R16d5a_USGS_cobalt_sulfides`, `R16d5a_USGS_cobalt_observations`
and `R16d5a_entropy_column_proof`.
