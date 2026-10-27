# R13: Specialized PHREEQC files and open NBS salts

Reviewed 24 October 2026. This batch adds **26 observations and 12 crystalline
salt records**, making 26 properties available. Every earlier observation
and preferred value remains under the unchanged policy. Five new records
retain enthalpy only; their Gibbs energies and entropies remain missing.

## Review scope and model distinctions

The pinned Reaktoro commit
`f587235e692b7168faa272c8892a4c079a1f7dd9` contains fourteen PHREEQC files.
R13 reviews every record in **ColdChem, core10, frezchem, iso and
Tipping_Hurley**, plus specialized model sections in the other nine files.
The external `phreeqc-specialized-review.csv` classifies **4,524 reaction
blocks and all 15,298 scoped noncomment lines**, with exact file hashes,
line locations, original terms and source comments. Earlier R07 reaction
decisions and independently verified formation anchors carry forward.
Ordinary reactions in the other nine files remain with R07.

The finite scope review is complete. Original source, reuse, phase and model
follow-ups stay visible as separate holds. A file distributed with a solver
supplies comparison material; individual numerical routes retain their own
terms and provenance.

- **ColdChem and frezchem:** coupled low-temperature brine, salt and freezing
  models with Pitzer interactions and water-activity requirements. ColdChem
  explicitly labels its water-dissociation constant arbitrary and needed for
  pH convergence; that term creates no thermochemical observation.
- **core10:** ordinary equilibrium reactions mixed with pressure/volume and
  inherited SUPCRT/LLNL or compilation data. Source, reaction anchors,
  standard state, temperature range and exact phase require review before
  any formation-property conversion.
- **iso:** isotope identities, hydronium conventions, fractionation
  expressions and BASIC functions require isotope-specific references and
  balances. They remain separate from ordinary H/O or proton records.
- **Tipping_Hurley:** ordinary WATEQ-derived reactions coexist with fulvate,
  humate, surface sites and exchange models. Site-normalized binding data
  require the corresponding chemical and electrostatic model.
- **Other specialized sections:** activity, diffusion, volume/EOS, kinetic
  and site parameters retain their raw-file links and named model needs.

The [USGS PITZER documentation](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-37.htm)
defines its coefficients as ion-interaction parameters. The
[CALCULATE_VALUES](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-7.htm)
and [ISOTOPE_ALPHAS](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-22.htm)
documentation describes the isotope functions and fractionation factors.
None supplies an independent compound formation G/H/S observation here.
No native PHREEQC number is imported in this batch.

## Independently verified open NBS observations

The source is [Wagman et al. (1982), NBS Tables, digitized with errata](https://doi.org/10.18434/M32124),
the explicitly open **non-SRD NIST Public Data Repository release**. Its
completed release and licence review carry forward. The new numerical cells
were independently checked in the pinned CSV. The original header gives
**298.15 K and 0.1 MPa (1 bar)**. Columns 7/8/10, counted from zero, contain
standard H/G/S; the separate 0 K enthalpy column is excluded.

| Source crystal | Logical CSV record | Retained properties |
|---|---:|---|
| KCl | 12202 | G/H/S |
| MgCl2 | 8880 | G/H/S |
| MgCl2·H2O | 8906 | G/H/S |
| MgCl2·2H2O | 8907 | G/H/S |
| MgCl2·4H2O | 8908 | G/H/S |
| MgCl2·6H2O | 8909 | G/H/S |
| CaCl2 | 9215 | G/H/S |
| CaCl2·H2O | 9242 | H only |
| CaCl2·2H2O | 9243 | H only |
| CaCl2·4H2O | 9244 | H only |
| CaCl2·6H2O | 9245 | H only |
| Na2Ca(SO4)2 | 12054 | H only |

G/H convert from kJ/mol to J/mol; S retains J/(mol K), per complete original
formula unit. Missing source cells create no observation. For example,
CaCl2·6H2O retains H = −2607.9 kJ/mol with G/S unavailable. MgCl2 retains
the 298.15 K H = −641.32 kJ/mol, separately from its excluded 0 K column.
The source CSV gives no uncertainty for these cells; NULL is retained.
The unchanged policy recognizes the NBS evaluation as class B.

Six nominal salt phases have comparisons in the five specialized files;
six mono/di/tetrahydrate records are an adjacent original NBS extension.
Matching native composition and hydration establishes a comparison route;
it supplies no shared numerical ancestry or exact specimen match.

USGS Bulletin 2131, Table 2 p. 23 independently names the three anhydrous
compositions sylvite, chloromagnesite and hydrophilite. Their mineral
identifications are retained with unspecified space groups. The other nine
records preserve NBS's crystalline formula with unresolved structural/native
phase correspondence. No interlayer-water count or polymorph is invented.

No new numerical value is copied from the shortlisted USGS halide cells.
Their bibliography includes JANAF 1985 (reference 67), commercial CODATA
1987/1989 (117/85) and federal Pankratz 1984 (320). These property-specific
routes retain their own source holds; a new federal original-table route
requires its own numerical verification. Existing implemented reviews carry
forward. The independent open NBS observations remain eligible.

NIST is acknowledged; the data retain the open-release attribution and
warranty notice in [distributed notices](https://github.com/FrederikLizakJohansen/pourbase/blob/main/THIRD_PARTY_NOTICES.md).
No JANAF, WebBook, SRD 46, commercial CODATA, entire PHREEQC file, complete
publication or private correspondence is included in the numerical additions.
Existing OECD attribution and downstream acknowledgment requirements for
NEA data remain applicable, alongside other independent source conditions.

## Formula units, calculation scope and validation

The chloride salts require the existing free chloride reservoir. Hydrate
waters remain in the residual core once, with O/H counts n/2n. They produce
zero proton coefficient; the metal reaction uses one electron per K and two
per Mg or Ca. Their primary inventory remains closed while chloride is
externally prescribed.

Na2Ca(SO4)2 belongs to the Ca system and requires both the existing sulfate
and free Na+ references, with two of each component per complete formula.
Its available enthalpy remains accessible; calculation excludes it while G
is missing. The calcium hydrates are excluded for the same stated reason.

The new observations supply no concentrated-brine Pitzer, freezing,
nonunit-water-activity, joint secondary-element inventory or general
component temperature model. Source identity and these calculation limits
remain explicit even where numerical observations are eligible.

Validation checks 63 full-formula energy evaluations, twelve buffered
diagram scenarios and 48 primary-metal balances with ideal and Davies
activities. All 75 default maps and 1σ/3σ masks remain unchanged, as do all
earlier SQL rows, preferred candidates, historical request coverage and the
six original crystalline Gibbs gaps.

Metadata `R13_PHREEQC_specialized_review`, `R13_NBS_observations` and
`R13_source_and_model_holds` retain source hashes, exact cells, qualifications
and separate original-source/model work.
