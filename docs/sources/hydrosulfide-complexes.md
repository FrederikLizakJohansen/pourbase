# R15: Hydrosulfide complexes

R15 adds **38 observations and nine aqueous species**, filling **28 missing
properties**: nine G, nine S and ten H. All earlier SQL rows and preferred
values remain. The default policy and existing sulfur references are preserved.
The dataset becomes **1,311 species /4,026 observations /75 systems**, with
selected G/S/H **1093/1070/885**.

## Original sources and reuse

The batch follows the established **individual original numerical facts** route
for isolated authors' fitted results, with attribution. This route applies to
numerical facts and carries no open licence for whole publications or databases.
Complete papers, prose, tables, figures and native exports stay outside the
distribution. Source copyright notices, publisher metadata, PSI report and
imprint were checked; no separate restriction on these isolated results was
identified. This is separate from NEA permission and from an open wrapper's
licence. See the project's [NEA/source instructions](nea-tdb-reuse.md) and
[Copyright Office factual-material guidance](https://www.copyright.gov/help/faq/faq-protect.html).

**Akinfiev and Zotov (2001)**, *Thermodynamic Description of Chloride,
Hydrosulfide, and Hydroxo Complexes of Ag(I), Cu(I), and Au(I) at Temperatures
of 25–500°C and Pressures of 1–2000 bar*, Geochemistry International 39,
990–1006, Table 2 p.993, supplies **17 observations**. The original authors'
UT-HEL, isocoulomb and ion-association estimates retain their methods.
Their H column is calculated by the authors from their evaluation's G/S.
The [public author-uploaded body](https://www.researchgate.net/publication/225543604)
identifies the 2001 volume and printed page, although its host-page title
says 2010. The primary table text and its exact hash are retained externally.

**Akinfiev and Zotov (2010)**, *Thermodynamic Description of Aqueous Species
in the System Cu–Ag–Au–S–O–H at Temperatures of 0–600°C and Pressures of
1–3000 bar*, Geochemistry International 48, 714–720,
[doi:10.1134/S0016702910070074](https://doi.org/10.1134/S0016702910070074),
Table 3 p.717, supplies **11 revised observations**. The retrieved PDF has
an incorrect 2001 cover; the article body identifies the correct 2010 title,
DOI, volume and page. The numerical table was inspected visually. Original
2001 and 2010 evidence identities are recorded separately.

Both papers report G/H in cal/mol and S in cal/(mol K) at 298.15 K and 1 bar.
All are converted with **1 cal = 4.184 J**, with no invented uncertainty.
Their fitted/correlated status is `source_verified_estimate`, class E.

| Species | Charge | Original 2001 G/H/S | Revised 2010 G/H/S admitted |
| --- | ---: | --- | --- |
| AgHS(aq) | 0 | 2791 /H held /36.221 | 2314 /2722 /34.77 |
| Ag(HS)₂⁻ | −1 | 287 /−6636 /49.00 | Unchanged repeat |
| CuHS(aq) | 0 | −3401 /883 /45.557 | Unchanged, rounded repeat |
| Cu(HS)₂⁻ | −1 | −5942 /−9825 /56.997 | −5902 /−12725 /47.09 |
| AuHS(aq) | 0 | 6434 /9122 /43.592 | 8344 /H held /50.86 |
| Au(HS)₂⁻ | −1 | 1829 /−2569 /58.630 | 3487 /4703 /77.46 |

The six species retain complete source formula units. Unchanged or rounded
repetitions contribute one original observation. Genuine revisions remain
eligible alternatives. The unchanged policy's same-author earliest-publication
tie-break selects **2001** where eligible; AgHS H uses 2010 because its 2001 H is held. The later revision is explicitly
flagged for scientific review. No supersession or preference override is inferred.

The printed 2010 AuHS H is **11032 cal/mol**. MINES stores about
55,263.08 J/mol, while the printed value converts to 46,157.888 J/mol.
Across the two published evaluations, `ΔH − ΔG − TΔS` has a residual of
−9,066.536 J/mol for this neutral species. This is a source-consistency hold,
with both numbers preserved externally. The disputed 2010 H is excluded
from the released observations. The original 2001 H remains with its own
consistent evaluation. No silent correction is made.

The 2001 AgHS derived H column reports **4769 cal/mol**. Its G/H/S
triplet has a **4740.888 J/mol** residual using the independently open NBS
elemental entropies (Ag logical5041, Cu4765, Au5223, rhombic S507 and H2(g)27).
The G and S entries are independently fitted inputs; the H column says it is
calculated from them. This derived H is held pending original-PDF/correction
evidence. The verified 2010 H is selected. The other admitted complete source
triplets have residuals below 100 J/mol against those NBS references, consistent
with source-vintage reference differences and printed precision; this screen
supplies no new uncertainty interval. Both multi-kJ derived-H discrepancies
remain explicit scientific holds.

## Independent zinc reaction adaptations

**Hummel and Thoenen (2023)**, *The PSI Chemical Thermodynamic Database
2020*, Nagra NTB 21-03, section32.3 pp.1243–1247 and Table32-2 p.1249,
provides its own regressions of Tagirov et al.(2007) and Tagirov and Seward(2010).
[Original report](https://nagra.ch/wp-content/uploads/2023/05/NTB-21-03.pdf),
SHA256 `f972212d592f0c02d95eb4dd7a3f5dcb1087d792e46041279c564530d588f9cc`.
These regressions use the same individual-facts route and yield **nine local
G/H/S estimates** on three new species:

| Reaction | log₁₀β° | ΔrH° /kJ mol⁻¹ | Original fit range |
| --- | ---: | ---: | --- |
| Zn²⁺ + 2HS⁻ = Zn(HS)₂(aq) | 9.30 ±0.17 | −13.7 ±3.2 | 50–100°C |
| Zn²⁺ + 3HS⁻ = Zn(HS)₃⁻ | 13.30 ±0.05 | −50.7 ±1.7 | 25–100°C |
| Zn²⁺ + 2HS⁻ = ZnS(HS)⁻ + H⁺ | 3.36 ±0.20 | 25.9 ±3.0 | 75–100°C |

These are the final regression values at 298.15 K. The Zn(HS)₂ and ZnS(HS)
values extrapolate beyond the experimental fit range. The Zn(HS)₃ width 0.05
comes from the final regression and selected table; the earlier tabulated
pointwise value has a different width. Original widths retain their interpretation.

The independent open non-SRD NBS PDR release
[M32124](https://doi.org/10.18434/M32124) supplies reference G/H/S:
Zn²⁺ −147060 /−153890 /−112.1 and HS⁻ 12080 /−17600 /62.8, in J/mol,
J/mol and J/(mol K). Exact CSV logical records are **4023** and **584**,
zero-based columns 8/7/10, aqueous-ion state `ao`. The CSV SHA256 is
`cb8a8b8b94a287e6e8c82eed8bad2cf9b611d574d1cfd95c8528d318dfef4b44`.
Only the missing Zn²⁺ H adds a direct NBS observation; existing G/S and HS
anchors are verified without duplication. Its per-value locator overrides the
historical general source locator. NIST is acknowledged under its
[open licence](https://www.nist.gov/open/license); data are supplied without warranty.

Local equations are `G = G(Zn²⁺) + nG(HS⁻) − RT ln(10) logβ`,
`H = H(Zn²⁺) + nH(HS⁻) + ΔrH`, and
`S = S(Zn²⁺) + nS(HS⁻) + (ΔrH + RT ln(10) logβ)/T`.
H⁺ has conventional G/H/S zero. Exact inputs and observation IDs accompany
each estimate. Anchor uncertainty and covariance are unavailable; total
uncertainties remain NULL. Source Cp functions supply no new thermal model.

## Sulfur reference and supported calculations

The existing `sulfide-s` reference is free **S²⁻**, G = **120695 J/mol**,
from the retained NEA evaluation. It has been updated since the dated R11d
checkpoint; its old NBS value remains stored. Existing physical HS⁻ has
G = 12080 J/mol. Consequently, at 298.15 K,

`pKa(HS⁻) = [G(S²⁻) − G(HS⁻)] / [RT ln(10)] = 19.028524733842467`

and `log a(S²⁻) = log a(HS⁻) + pH − pKa`. Source G values are independent
of this calculation reference. Nickel species and all previous reference rows
remain unchanged. OECD/NEA acknowledgment and downstream sublicense
requirements continue for the existing NEA reference; they do not grant
permission for the new papers.

Each new species has one primary metal atom. All sulfur atoms use the
external S²⁻ component; residual H is the full formula's H count. Electron
coefficients per primary are Ag/Cu/Au 1 and Zn 2. For ZnS(HS)⁻ the source
formula has S₂H₁, charge −1 and no oxygen. Native Zn(HS)₂(OH)⁻ has an extra
water equivalent and remains outside production pending original convention
verification. Native Zn charge errors **16/23/30** map chemically to **0/−1/−2**;
these raw charges and unverified 2014 values are excluded from import.

Fixed S²⁻ activity, pointwise fixed-HS equivalence and the existing one-acid
unbound HS⁻/S²⁻ pool are supported. The latter uses
`LigandActivity('sulfide-s', total_unbound_mol_L=1e-3, acid_pKa=pKa)`.
It conserves that unbound pool. A full H₂S/HS⁻/S²⁻ reservoir, closed total
sulfur and solution electroneutrality require separate models. Closed balances
here conserve the primary metal with externally prescribed sulfur activity.
Ligand species keep the existing exclusion from non-298.15 K calculations.

Validation covers **81 energies, nine atom/charge balances, 24 buffered
diagrams and 96 ideal/Davies primary balances**. Six tested sulfur-enabled
gold maps change; all 75 default maps and uncertainty masks remain unchanged.
All 135 original routed slots have dispositions: 84 metal-hydrosulfide slots,
nine free-HS reference slots and 42 tin, silicate or oxyanion false positives.
Inherited Pb/SLOP routes, original 2014 numerical cells, disputed Zn(HS)₄²⁻,
the two derived-enthalpy issues and broader sulfur models retain explicit follow-ups.
Historical requests remain **116/131** and six original crystalline G gaps
remain open.
