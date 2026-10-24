# R11: PSI/Nagra inventory and mixed minerals

Reviewed 24 October 2026. This checkpoint adds **eight observations and two
species**, making six properties available. It carries the completed R11a–u
reviews and preserves every earlier observation and preferred value.

The pinned [ThermoHub release](https://github.com/thermohub/thermohub/tree/c3e4acf4531204e4c2974c2d4ac5a1b96f37d5ba)
contains 690 substances and 440 reactions: 2,070 direct G/H/S slots and
1,760 reaction-property slots. The external `psinagra-review.csv` and
`reaction-reconciliation.csv` retain all 3,830 candidate IDs and previous
decisions, with current source and scope decisions. Fifty-seven independent
reaction-source routes were reviewed in the earlier R11 batches. Twenty-five
zirconium product routes now link to completed original NEA formation reviews;
their native reaction-reference conversions remain separate. Four calcium/Zr
or fresh-amorphous routes retain original-state and identity holds.

This completes the finite inventory review. Original-property evidence,
native-version reproduction and scientific holds remain listed separately.
In particular, 308 reaction routes require unsupported elemental systems.
Formula or numerical similarity alone establishes neither phase identity nor
source ancestry. The mirror's GPL-3.0 licence covers its compilation; each
admitted numerical route retains its own reuse basis. NEA material retains
the [OECD attribution and downstream acknowledgment](nea-tdb-reuse.md).

## Original USGS mineral evaluations

[Robie and Hemingway (1995), USGS Bulletin 2131](https://doi.org/10.3133/b2131),
Table 2, **printed p. 25 / PDF p. 31** and **printed p. 39 / PDF p. 45**,
supplies these original critical evaluations at 298.15 K and 1 bar:

| Phase and stored formula | G, kJ/mol | H, kJ/mol | S, J/(mol K) |
|---|---:|---:|---:|
| Ordered dolomite, CaMg(CO3)2 | −2161.3 ± 1.7 | −2324.5 ± 1.5 | 155.2 ± 0.3 |
| Kaolinite, Al2Si2O5(OH)4 | −3797.5 ± 1.5 | −4119.0 ± 1.5 | 200.4 ± 0.5 |

The thermal tables, printed pp. 269 and 382, corroborate the standard-state
cells. Dolomite S = 155.18 in the thermal table is the same evaluation at
greater printed precision and creates no additional observation. G/H convert
to J/mol; S retains J/(mol K), all per complete stored formula unit. Quoted
widths are retained without an assumed confidence conversion or covariance.

The source identifies ordered rhombohedral dolomite and distinguishes
kaolinite from dickite and halloysite. Space groups remain unspecified.
Dolomite G/H cite Hemingway and Robie (1994); S cites Stout and Robie (1963).
Kaolinite G/H cite Hemingway, Robie and Kittrick (1978); S cites Robie and
Hemingway (1991). These are the USGS authors' evaluated cells, with that
experimental ancestry recorded separately by property.

[Hemingway and Robie (1994), USGS Open-File Report 94-575](https://doi.org/10.3133/ofr94575),
**pp. 2 and 4**, supplies two additional ordered-dolomite observations:
G = **−2161.7 ± 1.1 kJ/mol** and H = **−2324.5 ± 1.1 kJ/mol** at
298.15 K and 1 bar. The authors correct their 300.15 K solution calorimetry
to the standard temperature and calculate G using enthalpy and entropies.
The specimen is a Binnental single crystal, with its natural composition
reported in the original study. This preliminary federal report shares
ancestry with the 1995 evaluation; its alternatives are retained as related
evidence. The unchanged policy selects the 1995 class B evaluation; the
1994 original report receives fallback class D. Its preliminary status and
unspecified interval confidence remain explicit.

The [USGS public-domain statement](https://www.usgs.gov/faqs/are-usgs-reportspublications-copyrighted)
covers USGS-authored data and asks for attribution. USGS and both author
groups are credited in [distributed notices](../../THIRD_PARTY_NOTICES.md).
The checked cells have no identified additional third-party ownership
restriction. Source PDFs, the policy snapshot and their hashes are retained
as external evidence. Complete publications stay outside distributions.
The native SLOP/GEMS variants remain held separately; none is imported here.
Disordered dolomite requires its own verified phase-specific source.

## Component reactions and validation

Ordered dolomite belongs to the Mg system and requires both the existing
free Ca2+ and CO3(2−) reservoirs. Its full formula contains one Mg, one Ca
and two carbonate components. The residual core has no O/H, and the
charge-balanced metal reaction has two electrons per Mg. Both component
activities must be prescribed.

Kaolinite belongs to the Al system and requires two existing silica
components per complete two-Al formula unit. The stored SiO2 component
is aqueous H4SiO4 minus two waters. Its residual core has five O and four H;
the reaction uses three protons and electrons per Al. An independent check
uses the physical reaction
`2Al + 2H4SiO4 + H2O = kaolinite + 6H+ + 6e−` at unit water activity.

Closed balances conserve the primary Mg or Al inventory with secondary
Ca/carbonate/silica buffered externally. A joint secondary-element inventory
and general component temperature model remain separate work.

Validation preserves all 75 default phase maps and 1σ/3σ masks, checks 18
full-formula energy evaluations, six buffered diagrams and 24 primary-metal
balances with ideal and Davies activities. Both new phases become stable
under some explicitly buffered conditions. The six crystalline Gibbs gaps
and historical requested-property coverage remain unchanged.

Metadata `R11v_PSI_Nagra_completion`, `R11v_USGS_observations` and
`R11v_source_and_scientific_holds` retain source hashes, exact cells,
alternatives and unresolved work. Earlier reviews and independent permission
holds carry forward.
