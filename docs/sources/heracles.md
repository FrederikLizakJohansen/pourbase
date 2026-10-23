# R10: Heracles original-source routes

Reviewed 23 October 2026. This batch adds **60 observations and 25 species**,
making 60 additional properties available. It retains 57 original NEA
selenide observations and three newer RuTe2 author evaluations. Every
earlier observation and preferred value remains; the policy is unchanged.

## Bibliography and version scope

The [ThermoHub mirror](https://github.com/thermohub/thermohub/tree/c3e4acf4531204e4c2974c2d4ac5a1b96f37d5ba)
contains an **888-record Heracles export**, with 2,664 direct G/H/S slots
and no reactions. The external `heracles-review.csv` gives every slot a
source and scope disposition. The GPL-3.0 licence, data and metadata were
verified against pinned Git blobs. ThermoHub contributors and the ETH Board
Open Research Data Program are acknowledged.

The larger archive supplies 277 bibliography records, 949 Heracles records
and 955 source edges. Of the original export records, 869 match a unique
graph record with exactly the same G/H/S. All Heracles edges associate a
source with the whole record's properties; none identifies a separate
G, H or S source. The 949-record graph retains its separate version scope.

The external `heracles-bibliography.csv` records all 39 source strings:
9 resolve through record sources, 18 have reused or ambiguous codes that
require the record graph, 5 resolve through explicit volume/author aliases,
and 7 retain precise citation holds. Codes 15, 16, 17 and 27 lack keyword
mappings in the source records. Web bibliography order supplies no code
mapping. Nineteen export records lack a unique graph match.

[PSI's original documentation](https://www.psi.ch/en/heracles/gems-specific-heracles-database)
states that most formation Gibbs energies were calculated from H/S and
auxiliary elemental entropies. Its bibliography includes restricted
compilations alongside NEA reviews and original studies. The mirror licence
does not establish reuse permission for all inherited numbers.

## NEA selected binary selenides

[Olin et al. (2005), Chemical Thermodynamics of Selenium, volume 7](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/chemical_thermodynamics_of_selenium_volume_7.pdf),
**Table III-1, pp. 43–49 / PDF pp. 84–90**, supplies 57 independently checked
selected G/H/S cells for 24 phases. These use the carried NEA-TDB OECD
permission and source-specific review. OECD credit and the acknowledgment
requirement must pass through sublicences and further sublicences. The
existing permission email, terms evidence and errata review are preserved.
See [the NEA reuse guide](nea-tdb-reuse.md) and
[distributed notices](../../THIRD_PARTY_NOTICES.md).

Values retain 298.15 K, 1 bar, full formula units and the source's quoted
intervals, approximately 95% confidence. G/H are converted from kJ/mol to
J/mol; S remains J/(mol K). Confidence widths are retained as quoted,
without an assumed conversion to one standard deviation or joint covariance.
The policy recognizes these critical NEA evaluations as class A.

Blank selected cells remain missing. For example, RuSe2 has selected S only;
alpha-SnSe has selected H only. The mirror's RuSe2 G/H and alpha-SnSe entropy
proxy are held. The mirror also gives La2Se3 charge +12; the admitted neutral
crystal entropy follows the original NEA table. Bi2Se3 and other mirror
values differ from the original selections; the original cells are retained.

The new `elemental-se-cr` reference pins the existing NEA standard-state
G = 0 observation for stable trigonal selenium. Its addition creates no
duplicate reported observation. Selenides require explicit selection of
this reference and a prescribed activity, normally one for pure Se. The
formation reaction uses the primary metal and neutral Se reservoir, so its
electron and proton coefficients are zero. Formal oxidation bookkeeping is
qualified separately from that complete reaction balance; it is not a
spectroscopic assignment. Nonintegral and polynuclear formula units remain
complete. Alpha/beta copper selenides and the named iron phases stay distinct.

Four gas records also require explicit optional-gas selection and external
fugacity. BiSe(g) retains entropy only. Closed balances conserve the primary
metal inventory while Se stays buffered externally. A closed total-selenium
inventory and component-bearing temperature models remain separate work.

## Independent RuTe2 follow-up

[Osadchii and Voronin (2024)](https://doi.org/10.1134/S0020168524701061),
*Inorganic Materials* 60, 832–837, publish G = **−126.9 kJ/mol**,
H = **−136.6 kJ/mol** and S = **94.94 J/(mol K)** at 298.15 K and 1 bar
in their author abstract. These are standard-state evaluations from
747–884 K EMF measurements and enter class E as fitted estimates.
The abstract supplies no uncertainty; it remains NULL.

This route uses the project's established individual numerical-fact policy
for original research. The article is subscription content; no open article
licence is asserted. The public publisher abstract and metadata are preserved
externally as verification evidence. No article, figure or protected prose
is distributed. NEA permission is independent of this original-paper route.

RuTe2 uses the existing neutral tellurium buffer. Its original specimen
polymorph remains unresolved in the accessible evidence; pyrite/marcasite
possibilities and nominal ditelluride oxidation bookkeeping remain qualified.
The historical 1977 values require their own original-table, temperature,
pressure and phase checks before admission. They are not averaged with the
new evaluation.

## Validation and remaining work

All 75 default phase maps and 1σ/3σ masks remain unchanged. Validation checks
90 neutral-component reaction evaluations, six buffered diagrams, three
optional-gas scenarios at three fugacities each, and 24 conserved primary
inventory balances with ideal and Davies activity models. Buffered Se/Te
can make the new phases stable; these are explicitly selected conditions.

Remaining citation/version work, original property/phase ancestry,
restricted compilations, gas-ion energy conventions and unsupported
actinide systems retain named holds. Completed source reviews carry forward.
The six crystalline-G gaps and historical request coverage remain unchanged.

Metadata `R10_Heracles_source_review`, `R10_Heracles_observations` and
`R10_Heracles_source_holds` retain hashes, derivations, source scope and holds.
