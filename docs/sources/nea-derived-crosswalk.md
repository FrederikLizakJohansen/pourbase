# NEA-derived database crosswalk, 14 October 2026

NEA02e compares the retained PSI/Nagra 12/07, eight SUPCRT variants and
MINES16/19/23.1 inventories with the completed direct NEA reviews. The screen
covers **42,009 G/H/S property slots across 12 files/releases** and assigns
routes to all **440 PSI/Nagra reactions**. These are screening and routing
counts. The wider R11/R12 original-source and version reviews remain open.
Previously completed numerical and permission reviews are carried forward.
The external overlay preserves each candidate's earlier source decision,
retained observation links and independently derived alternatives.

## Admitted observation

The crosswalk found a missing selected Gibbs energy for Ni(OH)₃⁻ in
Gamsjäger et al. (2005), *Chemical Thermodynamics of Nickel*, OECD Nuclear
Energy Agency volume 6, Table III-1, printed p.44 (PDF p.72):
**−590,519 ±9,735 J/mol**. Section V.3.2.1.2, pp.101–102, discusses the
underlying hydrolysis evaluation; Table III-2 selects log10β = −29.2 ±1.7.

The existing aqueous HNiO₂⁻ record represents this hydrolysis component in a
basis with one less water unit. At unit water activity the change of basis is

```
Ni(OH)3− = HNiO2− + H2O(l)
G(HNiO2−) = −590519 − (−237129) = −353390 J/mol
```

The subtracted quantity is the pinned project water reference at 298.15 K.
Both representations retain one nickel, charge −1, two electrons and three
protons in their metal/water reactions. The conversion preserves transformed
energies over the checked pH, potential and aqueous activities. It defines an
aqueous component basis; it supplies no physical dehydration equilibrium.
Changing the water convention requires re-normalization. The source total
uncertainty interval is retained under this deterministic reference change;
independent water covariance and a one-standard-deviation interpretation are
unavailable.

One observation is added to the existing record. The unchanged policy
selects the NEA evaluation; the older Gibbs values and independent H/S
estimates remain stored. These mixed properties supply no complete NEA
reference model or newly validated temperature dependence. Of 7,371 sampled
default nickel diagram points, 412 change (5.59%); the other 73 default
diagrams are unchanged. Six ideal/Davies closed-balance checks conserve
metal, and the aligned pymatgen comparison agrees beyond numerical ties.

## Repeated evaluations and remaining routes

| Inventory result | Disposition |
| --- | --- |
| 874 native property slots with a stored same-formula NEA property and different values | Keep the direct evaluation and carried original-source decisions, including already retained alternatives; pursue remaining native reference/version checks. |
| 16 native numerical matches | Retain links as screening leads; equal numbers alone establish no shared ancestry. |
| 2,571 Fe/Ni/Sn/Zr slots with unresolved identity or no stored same-formula NEA property | Carry source-property, hydration, phase and component checks forward. These are source-file slots, including repetitions across releases. |
| Three neutral Ni(OH)₂(aq) property slots | Hold the supplemental equilibrium bound and rough estimates. The NEA review selects no G/H/S for this species. |
| Three PSI SnO₂(am) property slots | Map to the amorphous phase; preserve the native older-source variant review. The historical formula-only cassiterite match is superseded in the external crosswalk. |
| 45 absent native properties | Preserve as missing. |
| 38,496 slots outside the completed-volume crosswalk | Keep their original R05/R11/R12 routes. |
| One Ni(OH)₃⁻ Gibbs slot | Use the admitted original NEA evaluation with the explicit water conversion. |

All 440 PSI reactions have explicit routes: 17 match checked nickel NEA
reaction constants, 29 retain zirconium reference/model follow-ups, 20 route
to the original selenium review, eight use PSI's independent amine/sulfide
reviews, one contains the neutral-hydroxide upper bound, 308 concern
unsupported actinide/Tc systems, and 57 retain other original-source checks.
Reaction Gibbs energies remain reaction quantities; formation energies need
verified anchors and conventions.

The retained MINES completion ledger has 1,621 held property rows. Its
source labels and publication groups identify no additional explicit NEA
permission-only hold. This marker result leaves unresolved numerical
ancestry intact. SUPCRT's formatted files also need property-specific source
routes; NEA permission supplies no bulk grant for these compilations.

The PSI [nickel selection report](https://www.psi.ch/en/media/47948/download),
TM-44-14-05 (2014), pp.3–4 and26–27, documents the hydrolysis and cyanide
routes and distinguishes its independent sulfide/amine work. The
[update report](https://www.psi.ch/sites/default/files/import/les/DatabaseEN/TM-44-12-06.pdf),
TM-44-12-06 (2012), p.2 and Tables7–9, identifies the NEA-derived Ni/Se/Zr
routes and source exceptions. These reports support ancestry checks; their
calculated native formation variants require their own numerical review.

The external checkpoint `nea02e-derived-crosswalk/` retains the full property
and reaction CSVs, source hashes, exact locators, stage/import package,
validation and release evidence. The earlier 29 solid/model holds, 27
zirconium holds and Cp routes remain separate. Original request coverage
stays **116/131** (NEA28/28, NIST88/103); the six original crystalline Gibbs
gaps remain open.

The admitted observation uses the clarified OECD terms and original NEA
citation. OECD and NEA are acknowledged. Every sublicense of work using the
data must include the same OECD acknowledgment requirement and require
further sublicensees to pass it on. See [the source instructions](nea-tdb-reuse.md)
and [distributed notices](https://github.com/FrederikLizakJohansen/pourbase/blob/main/THIRD_PARTY_NOTICES.md). Independent restricted
compilations retain their own permission status.

## R11l checkpoint — 20 October 2026

The [final 13 original-source routes](final-original-routes.md) now have
explicit decisions, completing the remaining unreviewed original-route queue.
Eleven routes yield eligible additions; finite-I niobium and less-stable
synthetic MnCO3 retain specific scientific requirements. The batch adds
46 observations and 10 species, fills 26 properties, and introduces radium
as the 75th system. Every previous observation remains. The unchanged policy
selects new NEA G for sulfide and iodic acid; free sulfide/cyanide references
align with selected ion values, with complete old pins retained in metadata.
All 440 reactions and 3,830 PSI property slots are reconciled in external
checkpoint `r11l-final-13-source-routes/`. Earlier reviews and separate holds
remain, and the wider R11 parent stays open. Historical request coverage and
the six original crystalline G gaps are unchanged.
