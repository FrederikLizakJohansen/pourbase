# Original NEA Sr/Ba auxiliary selections

R11j3h retains 17 own selected NEA observations and three independent open NBS
alternatives. Existing Sr/Ba metals, aqueous divalent ions and crystalline chlorides
gain source alternatives. One crystalline Sr(NO3)2 record gains G, H and S.
All earlier observations remain available; the unchanged policy chooses one per property.

The NEA source is Grenthe et al. (1992), *Chemical Thermodynamics of Uranium*,
Chemical Thermodynamics 1, Table IV.1, p. 77 (PDF p. 95), and Chapter VI.5,
pp. 400–401 (PDF pp. 418–419),
[official reprint](https://www.oecd-nea.org/upload/docs/application/pdf/2019-12/uranium.pdf),
accessed 25 October 2026. These 17 original evaluated cells are repeated unchanged
in the 2020 Table 8-1, p. 161; the reprints link to the original observations.
The source explains its experimental ancestry, estimated uncertainties and 1-bar
Gibbs calculation. Quoted NEA confidence widths are retained as supplied.
G/H are converted from kJ/mol to J/mol; S remains J/(mol K), per complete formula.
Aqueous values use the conventional proton reference at infinite dilution.

The independent Sr(NO3)2 NBS G/H/S alternatives come from the explicitly open
non-SRD [NIST release M32124](https://doi.org/10.18434/M32124), logical CSV
record 9772, columns 9/8/11 (one-based). Missing uncertainties remain missing.
The original-release elemental reference entropies reproduce its formation cycle;
newly preferred elemental values are separate choices.

## Identity and calculation checks

Sr(NO3)2 contains one Sr and two nitrate groups. All six O atoms belong to the
nitrates, giving core O/H = 0, two electrons and zero protons per Sr in the
balanced reaction. The existing nitrate reference is reused. The crystalline
structure remains unresolved. Chloride/nitrate activities are externally prescribed;
the existing temperature model excludes these buffered salts.

The policy selects the 17 NEA observations, changing 14 existing preferred IDs
and supplying three properties on the new record. Twelve of the changes alter
numerical values, including both elemental entropies. The two chloride entropies
retain identical numbers with a new source. All source-specific
carbonate and association fits keep their original numerical anchors. Their
regressions use the retained original NBS anchor to test the original calibration.
The current selected mixture need not reproduce every older fitted constant.
All 31 fixed free-component references and the policy remain unchanged.

Validation covers 33 balanced energies, 14 thermal scenarios, 18 default or buffered
Sr/Ba comparisons and 72 primary-element mass balances. On the 81 × 91 default
grid, 364 Sr points change from SrOH+ to Sr2+, and 273 Ba points change from Ba2+
to BaOH+. Uncertainty masks are recomputed; the other 73 systems are unchanged.
The new nitrate is included with its buffer and is absent from the stable regions
tested at free nitrate activities 10^-6 and 10^-3. All five original NEA triplets
and the independent NBS nitrate cycle agree within 1 J/mol using their own
reference entropies. These arithmetic residuals are separate from uncertainty.

## Reuse and remaining work

The supplied NEA clarification and OECD data terms cover these own selections.
Credit OECD/NEA and the cited evaluation. Include the same acknowledgment
requirement in sublicences, and require further sublicensees to do the same.
The NBS release carries NIST credit, its open licence and warranty notice.
See [NEA reuse conditions](nea-tdb-reuse.md) and the
[distributed notices](../../THIRD_PARTY_NOTICES.md).

Metadata keys are `R11j3h_NEA_Sr_Ba_review`, `R11j3h_Sr_Ba_observations`
and `R11j3h_source_and_model_holds`. Original source evidence and the detailed
before/after review stay in the external running plan. This closes 17 of the
109 pending auxiliary cells. The remaining 92, copied CODATA/Glushko holds,
R11j3f1 policy review and other independent source/model work stay separately tracked.
