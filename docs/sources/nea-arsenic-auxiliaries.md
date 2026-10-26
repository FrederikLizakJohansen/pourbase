# NEA arsenic auxiliary observations and water representations

R11j3k reconciles all 35 arsenic cells in the remaining auxiliary inventory.
It retains 46 observations: 29 original NEA 1992 selections, one distinct 2003
calculation, three NEA 2005 gas values, seven independent open NBS alternatives
and six local water-representation conversions. Three records gain seven properties:
monoclinic As4O6 and molecular As4O6 gas gain G/H/S, and the crystalline
(As2O5)3·5H2O hydrate gains H. Every earlier observation remains available.
The unchanged policy changes 25 earlier preferred IDs, including eight numerical changes.

## Source scope and confidence

Grenthe et al. (1992), *Chemical Thermodynamics of Uranium*, Chemical
Thermodynamics 1, OECD Nuclear Energy Agency, Table IV.1, pp.70–71 (PDF
pp.88–89), and Chapter VI.3.3, pp.389–391, describe interim NBS arsenic selections
with broad assigned uncertainties
([official reprint](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/uranium.pdf)).
The authors explicitly defer a complete arsenic reevaluation and discuss potential
errors in the inherited data. The source family's policy class records the review's
place in the existing hierarchy; its interim scientific scope remains explicit.
Confidence widths are retained as supplied, corresponding in principle to 95%.

The original monoclinic Gibbs value is −1154.008 kJ/mol. Guillaumont et al.
(2003), Table 8-1, p.140, provide −1154.009 kJ/mol
([official volume](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/update_on_the_chemical_thermodynamics_of_uranium_neptunium_plutonium_americium_and_technetium_volume_5.pdf)).
Both versions are retained. This 1 J/mol distinction records an internal-calculation
version; their quoted uncertainty remains 16.041 kJ/mol per As4O6.

Gamsjäger et al. (2005), *Chemical Thermodynamics of Nickel*, Chemical
Thermodynamics 6, Table IV-1, p.60 (PDF p.88), and Chapter VI.1.1, p.249
(PDF p.277), supply the distinct gas evaluation
([official volume](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/chemical_thermodynamics_of_nickel_volume_6.pdf)).
It adjusts Behrens and Rosenblatt's original research to the selected cubic reference:
G = −1092.716 kJ/mol, H = −1196.250 kJ/mol and S = 408.6 J/(mol K),
with quoted widths 16.116 kJ/mol, 16 kJ/mol and 6 J/(mol K).

Original NBS alternatives come from the explicitly open non-SRD
[NIST release M32124](https://doi.org/10.18434/M32124), logical CSV records
1479 (monoclinic triplet), 1480 (gas triplet) and 1482 (hydrate H).
G/H/S columns are 9/8/11, one-based. Missing uncertainties remain missing.
The older NBS gas triplet is G = −1097.8 kJ/mol, H = −1209.2 kJ/mol,
S = 381 J/(mol K). Its reference-cycle residual is approximately +351 J/mol;
source values are preserved with a warning. The gas G spread is 5.084 kJ/mol
per complete As4O6 formula. The selected NEA evaluation's source revision and
broad confidence are documented in the external review. All source URLs were
accessed on 26 October 2026.

## Formula units and aqueous representation

The existing resolved cubic arsenolite record already stores As4O6 with four As
atoms. Its formula and Fd-3m identity are preserved. The new monoclinic solid and
gas also retain complete As4O6 units. The hydrate is As6O20H10: six As atoms,
20 O atoms and 10 H atoms, with five electrons per As. Its G and S are missing.
New solid structures remain unresolved; no crystal space group is inferred.

The original 1992 discussion on p.390 explicitly identifies AsO2− + H2O with
H2AsO3− and HAsO2 + H2O with H3AsO3. Six local conversions retain the raw
G/H/S observations of both older formula representations on the existing canonical
records. Each property equals its original source value plus one liquid-water property
from open NBS record 41: G = −237129 J/mol, H = −285830 J/mol and
S = 69.91 J/(mol K). The Gibbs anchor equals the existing calculation reference.
The source locators preserve both raw and normalized quantities, formulas and citations.

These local derived alternatives enter class E with `source_verified_estimate` status.
The missing water confidence and covariance leave total widths unassigned; raw NEA
widths remain visible separately. Direct canonical NEA values stay preferred.
The conversion preserves the balanced energy at 298.15 K, using one aqueous
population per canonical form. All 31 fixed free-component references remain unchanged.
The current temperature model and its water approximation retain their existing scope.

## Scientific effects and reuse

Validation covers 45 balanced energies, six water-representation invariance checks,
22 thermal scenarios and 12 supported primary-element mass balances. On the
81 ×91 default grid, five As points change and its uncertainty masks are recomputed;
the other 74 maps and masks remain unchanged. At nominal unit aqueous activity,
453 points select the monoclinic phase, including all 448 former cubic points.
The broad source confidence remains material to that mean-value phase ranking.
A separate ideal two-phase check conserves As while producing positive four-As
precipitation; it is a mathematical model check.

The H-only hydrate makes the strict As phase inventory incomplete. Strict periodic
counts become 53 experimental systems and 56 with computational fallbacks;
the available-data screen continues to calculate all 75 systems. The six original
crystalline Gibbs gaps and historical request coverage are unchanged.

The NEA clarification and OECD data terms cover these selected/evaluated outputs.
Credit OECD/NEA and the exact source. Include the same acknowledgment requirement
in sublicences and require further sublicensees to do the same. NIST credit, its open
release licence and warranty notice apply to NBS observations and conversion inputs.
See [NEA reuse](nea-tdb-reuse.md) and [distributed notices](../../THIRD_PARTY_NOTICES.md).

Metadata keys are `R11j3k_NEA_arsenic_review`, `R11j3k_arsenic_observations`
and `R11j3k_source_and_model_holds`. Other NBS hydrate/aqueous candidates,
H2SO3 identity, policy follow-up R11j3f1 and independent source/model holds
remain separately tracked. This closes 35 cells: 32 direct source links and three
verified water-representation conversions. The other 23 auxiliary cells remain next.
