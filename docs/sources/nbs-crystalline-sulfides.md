# Original open NBS crystalline sulfides

R16d4a retains 99 original G/H/S observations from 34 eligible Gibbs-bearing
source rows: 27 records, 83 previously missing properties and three links to
original PbS cells already retained. Pyrite gains its missing G and H. Seven
earlier preferred values change under the source-family ranking: CuS G/H/S,
sphalerite G/H/S and pyrite S. All previous observations remain.

Wagman et al. (1982), *The NBS Tables of Chemical Thermodynamic Properties*,
digitized with errata in explicitly open non-SRD
[NIST M32124](https://doi.org/10.18434/M32124), supplies the values. The
completed release-specific source and reuse review carries forward. Exact CSV
records, columns, raw numbers, phase/name fields, units, temperature, pressure,
missing confidence intervals and evaluation/derivation identities remain in
observation provenance. G/H are in J/mol, S in J/(mol K), at 298.15 K and
1 bar per complete source formula unit. Class B identifies the critical
compilation; the digitized cells leave underlying measurement versus estimate
classification unspecified.

## Full formula units and electron balances

Fe7S8, Pd4S, Nd2S3, Ni3S2 and alkali sulfides retain their full primary and
sulfur counts. Energy per primary atom divides by that primary count once.
Against externally buffered S2−, the net electron coefficient is 2nS/nPrimary.
Formal oxidation state is stored separately. In Na2S2, Na is formally +1 and
the net coefficient is 2 per Na. For normal-pressure PdS2, Pd is formally +2
and the net coefficient is 4. [Selb et al. (2017), Crystal Chemistry](https://doi.org/10.1002/zaac.201700140)
supports the Pd(II)/disulfide definition. No thermochemical values from that
article enter this release. High-pressure, Pd-deficient phases stay separate.

Explicit source names map ZnS to sphalerite and FeS2 to pyrite. New HgS red
and black records retain their separate source forms. New exact structures
remain unassigned. The original silver-sulfide alpha/orthorhombic and beta
state holds carry forward from the completed acanthite review. Generic NiS
needs correspondence to the retained polymorphs; the NBS Cu2S alpha modifier
needs a documented link to chalcocite. These four rows and their 12 numeric
cells remain outside this batch.

## Molybdenite revisions and preferred values

NBS Table 52:Mo, p.2-201 (PDF p.209), was prepared in 1966. Its MoS2 cells
are G −225900 J/mol, H −235100 J/mol and S 62.59 J/(mol K); the printed
original confirms the digitized numbers. USGS Bulletin 2131 (1995), p.13
(PDF p.19), retains the later revised molybdenite triplet already reviewed
and stored: G −262800 ±4900 J/mol, H −271800 ±4900 J/mol and
S 62.6 ±0.2 J/(mol K). Its H/G reference explicitly identifies the revised
O'Hare, Lewis and Parkinson (1988) fluorine-combustion evaluation; S cites
McBride and Westrum (1976) calorimetry. The source intervals retain their
published interpretation.

Three documented property overrides keep that later source-consistent triplet
preferred. All older NBS values remain eligible alternatives. All prior 46
overrides and 13 exclusions remain; the R16d4a policy has 49 overrides and
fingerprint `586e3da17300`. The recommendation fingerprint is `8b7deec3f6d62880`.
The selector implementation and source-family order are unchanged.

## Source precision, validation and reuse

Printed Table 42:Pd, p.2-183 (PDF p.191), confirms PdS G −67 kJ/mol,
H −75 kJ/mol and S 46 J/(mol K). The source-cycle residual of
−1032.2345 J/mol is compatible with those coarsely rounded numbers.
Original values stay unchanged; printed precision supplies no confidence interval.

Validation covers 34 source cycles, 891 energies, 81 buffered diagrams,
216 primary balances and 54 unchanged thermal inventories. Forty-six buffered
diagrams change; new phases occupy 52875 scenario points. All 75 default maps
and uncertainty masks remain unchanged. Strict periodic coverage stays
53 experimental systems or 56 with fallbacks; available-data calculations cover
75. Historical request coverage and the six original crystalline G gaps remain.

NIST is acknowledged and its recorded open terms and warranty statement apply.
OECD/NEA attribution and downstream acknowledgment requirements remain applicable
to the separately retained NEA observations. Independent original-source,
calibration and permission holds carry forward. Closed sulfur, coupled
H2S/HS−/S2− protonation, brines, water activity and new thermal component
models remain separate. The remaining 53 source rows and named phase holds
continue in the external plan.

Metadata keys are `R16d4a_NBS_sulfide_source_review`,
`R16d4a_NBS_sulfide_observations` and `R16d4a_source_and_model_holds`.


## Remaining H/S observations: R16d4b

The remaining 53 source rows contain one numeric H or S cell each. This batch
adds 48 observations from 48 rows: 46 H and two S, with 42 new records and
six alternatives for existing phases. Forty-two previously missing properties
become available. All earlier preferred values stay unchanged. The new records
have no G; they appear in the evidence API and are reported as unavailable for
calculations when sulfide is enabled. No Gibbs energy is inferred.

Printed NBS Table 20:As, prepared in 1964, p.2-77 (PDF p.85), confirms
As2S2 H −142.7 kJ/mol. The stored realgar formula is As4S4, so the retained
alternative is −285400 J/mol. USGS Bulletin 2131 p.11 (PDF p.17) reports
H −30.9 ±5 kJ/mol per empirical AsS, correctly stored as −123600 ±20000
J/mol per As4S4. Its reference419 is Wagman et al. (1982); the shared nominal
ancestry leaves an unresolved published-source discrepancy. Both published
numbers and their formula conversions are preserved. No independence is assumed.

Four explicit H-only policy rules preserve the current coherent USGS G/H/S
triplets for realgar, wurtzite, marcasite and tungstenite, including their stated
intervals. The NBS H alternatives stay eligible. The new rules preserve all prior
49 overrides and 13 exclusions; the policy now has 53 overrides, fingerprint
`544b421b7f1c`. Recommendation fingerprint: `f304af9ea86db5bf`.
NEA SnS2 S and ZrS2 H stay preferred under the existing class ranking.

Full Ni6S5, Ni7S6, In3S4 and In4S5 formula units retain each primary atom.
Fractional hydrate waters remain explicit, including Na2S·4.5H2O and
K2S4·0.5H2O. Alkali polysulfides have formal alkali state +1; their net
S2−-referenced electron coefficient is 2nS/nPrimary. Conventional formal
states in ordinary sulfides are formula averages, without assigning atomic
charges to individual sites. In N4S4, the N–S ionic-bond approximation gives
N(−III), while the balanced sulfide-reference coefficient is +2 per N.
[Mason (1969)](https://doi.org/10.1039/J19690001567) provides the electronic
structure context. RuS2 and OsS2 use formal +2 and net coefficient4;
[Shirako et al. (2014), Table4](https://doi.org/10.1021/ic501770g)
documents the divalent bulk disulfide definitions. Exact NBS specimen structures
remain unassigned. These references supply chemical definitions; their numerical
thermochemistry is outside this import.

Five H/S observations remain external: precipitated NiS needs correspondence
to the retained polymorphs; IrS2, Re2S7, CeS2 and Ce3S4 need source-specific
formal-state and bonding/phase evidence. These holds are scientific and remain
separate from permissions. Together with the four earlier Gibbs-bearing holds,
the full 91-row source accounts for 147 new observations, three retained
original-cell links, 17 held numeric cells and 106 source blanks: 273 slots.
This covers every original source row; the named holds continue as R16d4c.

Validation preserves all earlier SQL rows and choices, all 75 default maps and
uncertainty masks, 90 buffered sulfide maps, 240 primary balances and 60 thermal
inventories. Strict coverage stays 53 experimental or 56 with fallbacks.
Historical request coverage remains 116/131; the six original crystalline G gaps
remain. The same open non-SRD M32124 reuse evidence, NIST credit and warranty
statement apply. Independent source/model holds and the OECD/NEA downstream
acknowledgment requirements carry forward.

Metadata keys are `R16d4b_NBS_sulfide_HS_review`,
`R16d4b_NBS_sulfide_HS_observations` and `R16d4b_source_and_model_holds`.
