# Additional thermodynamic properties and model parameters

The R18 review inventories the additional parameter groups in all **44 tracked
datasets**, preserving raw values and exact locators outside the distributed
SQLite database. This includes the 23 pinned ThermoHub graph collections and
the original MINES, NASA, PHREEQC and open non-SRD NBS records. Existing
source and numerical reviews carry forward. Every inventoried field type has
an explicit representation decision.

The current reported-property model stores formation G, formation H and
absolute S, their conditions and eligible scalar uncertainties. Additional
properties require their own source review and representation. Original arrays,
units, intervals, transition information, uncertainty fields and native sentinel
values remain preserved together. A source's numerical zero or machine sentinel
requires interpretation before it can become a measured zero or an uncertainty.

| Parameter group | Current support and required work |
| --- | --- |
| Scalar G/H/S uncertainty | Supported when the original source states its meaning. Preserve confidence level, coverage factor, asymmetric limits and correlations in provenance. A quoted approximately 95% width remains identified as such; it is not automatically a one-sigma error. |
| Temperature and pressure of an observation | Supported as observation conditions. Validity intervals, phase stability ranges and extrapolation limits need separate model records. |
| Cp and temperature functions | Preserve scalar Cp, coefficients, units, equation identifier, temperature scale and intervals. A future scalar-property extension and function evaluator must distinguish Cp from Cv and validate integration to H and S against original anchors. |
| Molar volume and pressure functions | Preserve full-formula molar basis and units; 1 J/bar equals 10⁻⁵ m³. A pressure model requires a defined equation of state, reference pressure, compressibility/expansivity and phase behavior before integrating V dP. |
| HKF and water models | Preserve complete HKF coefficient sets, scaling, charge, Born conventions, water density/dielectric model and domain. The current G/H/S temperature approximation does not evaluate native HKF functions. |
| NASA and other polynomials | Preserve every interval, coefficient convention and integration constant. Evaluate within the source range, resolve phase/reference species and construct formation properties using compatible elemental references. Keep fitted thermal functions separate from original measurements and scalar evaluations. |
| Reaction G/H/S, log K and analytical functions | Require an exact balanced reaction, activity/concentration standard, log base, units, conditions and compatible formation anchors. Reaction properties have their own molar reaction basis; they are not compound formation properties. |
| Phase transitions and critical parameters | Preserve transition temperature/pressure, latent H/S/V, critical parameters and branch identities. Future models must handle discontinuities and metastable ranges explicitly. |
| Activity and mixing parameters | Preserve complete SIT, Pitzer, extended Debye–Hückel and solid-solution definitions with interaction order, medium, convention, units and domain. Existing ideal/Davies calculations do not interpret these imported parameter sets. |
| Surface and exchange parameters | Require site definitions, normalization, capacity, electrostatic model and charge/element balances. A surface or exchange constant needs a corresponding model and distinct identity. |
| Isotope and named functions | Require isotope-specific references, fractionation definitions, units and dependency graphs. Preserve executable expressions as source data; execution needs a reviewed interpreter and explicit limits. |
| Transport and kinetics | Diffusion, viscosity and rate parameters need separate quantities, dimensions and solvers. Retain their source linkage and scope. |
| Native vectors and auxiliary quantities | Preserve MINES slot/byte locators, native unit codes and original vectors. Undecoded slots retain an explicit interpretation hold. Keep zero-K H and H(298)−H(0) distinct from formation H at 298.15 K. |

A future schema extension should use separate **scalar observations**, **model
parameter sets** and **reaction observations**. Each record needs a stable ID,
source and exact locator, original value/unit, SI conversion, formula or reaction
basis, reference conditions, applicability domain, uncertainty meaning and reuse
route. Model parameter sets additionally need an equation/version identifier,
ordered coefficients with individual units, reference-state conventions and
links to every dependent component or solvent model. Correlations belong to a
linked covariance or uncertainty record. Selection remains derived: retain all
eligible alternatives and choose one preferred observation per property and
applicable state. Model parameters require a separate compatibility decision.

Before any such model is enabled, validate its dimensions, source examples,
interval boundaries, phase transitions and thermodynamic derivatives: Cp = dH/dT,
dS/dT = Cp/T and V = dG/dP, where applicable. Reaction evaluation additionally
requires atom/charge balance and compatible anchors. Assess diagrams and the
inventories the model claims to conserve. Preserve the existing calculation
scope when introducing optional capabilities.

Source reuse remains property-specific. The NEA clarification and OECD
acknowledgment requirements apply to eligible NEA evaluations, with additional
restrictions checked. The open non-SRD NBS release and covered NASA/USGS
material retain their own notices and ancestry requirements. Thermoddem bulk
permission, inherited SRD/JANAF/CODATA and other unresolved source holds stay
separate. A wrapper's software licence supplies no blanket numerical-data grant.

R18 completes this finite inventory and specification. Additional parameter
activation and original-source verification remain tracked follow-ups. This
review adds **zero production observations**; statistics and paper numbers retain
the verified R16 snapshot of **1,326 species and 4,090 observations**.
