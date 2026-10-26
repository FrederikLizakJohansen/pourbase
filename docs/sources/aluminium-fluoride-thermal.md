# Higher aluminium-fluoride thermal estimates: R11r / R11l6

- [x] Check original numerical inputs, cumulative reactions and finite-medium scope.
- [x] Check the carried numerical-facts route and newly used open NBS cells.
- [x] Add four qualified AlF₅/AlF₆ H/S estimates and the Al³⁺ reference H.

Latimer and Jolly (1953), *Heats and Entropies of Successive Steps in the
Formation of AlF₆³⁻*, JACS 75(7), 1548–1550,
[DOI 10.1021/ja01103a008](https://doi.org/10.1021/ja01103a008), Table VI,
p.1549, reports stepwise association enthalpies. Their numerical inputs,
reaction labels, accuracy statement and ionic-strength footnote were checked
in the search-indexed text of an original journal scan. The publisher confirms
the citation. Full-resolution original PDF retrieval remains unavailable;
no local full-PDF or original-page visual inspection is claimed.

The six unrounded calorimetric inputs and finite-medium convention were
independently crosschecked in the retrieved primary PSI/Nagra evaluation:
Hummel et al. (2002), NTB 02-16, p.98 / PDF p.122, and Hummel and Thoenen
(2023), NTB 21-03, pp.263–264 / PDF pp.321–322
([report](https://media.nagra.ch/uploads/2023/05/NTB-21-03.pdf)).
The review explicitly assumes the enthalpies measured at ionic strengths
0.06–0.2 are approximately valid at infinite dilution because the original
study mentioned no significant variation with ionic strength.

## Accepted local estimates

The cumulative association enthalpies are **+1650 cal/mol** for AlF₅²⁻ and
**+100 cal/mol** for AlF₆³⁻. The latter agrees with the original total row.
The sixth step alone is −1550 cal/mol. Summing the steps preserves the
distinction between stepwise K and cumulative β; using the sixth-step
enthalpy as the overall six-fluoride enthalpy would be an error.

The local H/S estimates adopt the review's stated infinite-dilution
approximation. The existing independently reviewed SIT/trend G values
(log₁₀β = 20.29 for both species) remain preferred and unchanged.
Using 1 cal = 4.184 J and the open non-SRD NBS ionic references gives:

| Species | Formation H (J/mol) | Absolute S (J/mol/K) |
|---|---:|---:|
| AlF₅²⁻(aq) | −2187246.4 | 20.901921 |
| AlF₆³⁻(aq) | −2526361.6 | −14.649546 |

```text
Hcomplex = H(Al3+) + n H(F−) + cumulative association H
Gassociation = Gcomplex − G(Al3+) − n G(F−)
Sassociation = (Hassociation − Gassociation) / 298.15
Scomplex = S(Al3+) + n S(F−) + Sassociation
```

Both properties enter as local class E `source_verified_estimate` observations,
filling four missing fields. Original 1953 entropy values are excluded:
their Gibbs energies use ionic strength 0.50, while the enthalpies use
0.06–0.2. The local entropies above are derived from the retained I=0 G
models and qualified H approximation. No measured infinite-dilution entropy
or additional temperature model is claimed. Ambient aqueous pressure-flat
behaviour is an explicit approximation to the 1 bar target.

The authors' per-step accuracy estimates are retained in observation metadata.
Their statistical meaning, correlations and finite-medium correction interval
are unavailable. Total H/S uncertainties remain NULL; no independent
quadrature or one-sigma conversion is invented.

## Open reference and selection

The NBS digitization's Al³⁺ H cell, logical record 3571, column 8,
is **−531000 J/mol** at 298.15 K and 1 bar. It is added as an independent
class B observation, using the existing NBS source record. Earlier Al³⁺
enthalpies remain; the default policy changes its preferred H from the 2017
model value −538350 J/mol. The 7.350 kJ/mol spread is explicitly reviewed
and retained as a difference between evaluations. The earlier interval
remains attached to its own observation. NBS supplies no interval for this cell.

Recipes retain all relevant reference cells: Al³⁺ G/H/S at logical record
3571 and F⁻ G/H/S at record 119. No ligand reference or preferred G/S changes.
The source-consistent temperature backend changes Al³⁺ G by approximately
6.87 J/mol at 323.15 K and 20.61 J/mol at 373.15 K. Sampled default maps
and uncertainty masks remain unchanged for all 75 systems at 298.15 K
and at both checked higher temperatures. Three fluoride-buffered Al maps
and 18 supported balances retain their behaviour. The sixth-step free-fluoride
activity ratio and full-formula charge/electron basis also pass.

## Reuse and remaining requirements

The four adaptations carry the established isolated-original-numerical-facts
route. They use a narrow selection of original calorimetric inputs and the
separately reviewed G model. Neither the complete 1953 article nor PSI/Nagra
report is asserted open licensed. Publications, whole tables, prose, figures
and database exports remain external. The separate openly released non-SRD
NBS data retain their attribution, licence and warranty notice. OECD
attribution and downstream acknowledgment requirements remain applicable
to the database's NEA material.

- [ ] **R11r1:** rigorous finite-medium calorimetric extrapolation, covariance
  and pressure uncertainty; the qualified class E approximation remains explicit.
- [ ] **R11r2:** obtain the original full-resolution article as an evidence
  upgrade; the present numerical/convention checks retain their exact access basis.

R11l6's finite source/convention/eligibility review is complete with these
qualified adaptations. Earlier radium, niobium, manganese, aluminium-silicate
and independent permission holds retain their own status. The fixed 100-value
audit carries forward. Historical requested coverage remains 116/131
(NEA 28/28, NIST 88/103), with six original crystalline-G gaps.
