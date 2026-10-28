# Source and elemental reference-state corrections

The 28 October 2026 correction follows the specific discrepancies recorded in
`sn-codata-entry.md`. The completed database expansion round remains closed.

## Tin and nitrogen sources

The directly cited CODATA Key Values entropy of white tin and its unused source
record were removed. The existing NEA tin evaluation, Table III-1, printed p. 44,
now supplies **51.18 ± 0.08 J/(mol K)**. Its OECD attribution and downstream
acknowledgment conditions remain applicable. The older rounded observation stays
superseded, linked to this retained NEA observation. Tin's selected entropy number
and Gibbs energy are unchanged.

Three observations derived through NIST Chemistry WebBook SRD 69 were removed
from dissolved N₂, together with their unused source and three obsolete warnings.
The default policy now selects the already retained Sander-derived estimates:

| Property | Selected value | Unit |
| --- | ---: | --- |
| Formation Gibbs energy | 18210.855 | J/mol |
| Formation enthalpy | −10563.947 | J/mol |
| Absolute entropy | 95.098840 | J/(mol K) |

The immediate source is the supplement to [Sander (2023)](https://doi.org/10.5194/acp-23-10901-2023),
released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
subroutine `ref2434` in `henry_ref2500.f90`, lines 2662–2682. Its transcription
traces Rettich, Battino and Wilhelm (1984). The completed review's molal fit,
pressure-path approximation and missing total uncertainty carry forward.
Absolute entropy includes the existing NBS N₂(g) reference of 191.610 J/(mol K):
S°(aq) = S°(gas) + (ΔfH° − ΔfG°)/298.15. The removed legacy entropy had omitted
the gas-reference contribution. Other openly reusable nitrogen alternatives stay
available. These are estimates, with their existing qualification and reuse
conditions; this correction adds no new experimental nitrogen measurements.

The HGeO₃⁻ citation now identifies Barner and Scheuerman (1978). Its existing
locator and stable source ID preserve the Materials Project transcription route.
The default classifier consequently treats this experimental compilation as
class D, rather than assigning its transcription service's computed-data family.
The value and its completed source review are unchanged.

## Elemental conventions and temperature constants

All **75 selected elemental standard states** now have ΔfH° = 0 with
`defined_reference_state` status, matching their formation Gibbs energy
convention. Forty existing zero enthalpies were relabelled, two were already
defined, and 33 missing reference enthalpies were added with the existing
[IUPAC reference-state citation](https://doi.org/10.1351/goldbook.R05233).
These defined zeros are separate from experimental coverage.

The 73 remaining absolute-entropy observations labelled `defined_reference_state`
were corrected. Existing verified matching observations support `verified`
status; other retained source values use `accepted`. Their numerical values,
sources and uncertainties are preserved. A nonzero elemental absolute entropy
is a source value; the elemental formation G/H zero is a convention.

The temperature module now uses H₂(g), O₂(g) and H₂O(l) entropies of
**130.684, 205.138 and 69.91 J/(mol K)** from the open NBS Tables with errata,
logical CSV records 27, 15 and 41 respectively, zero-based column 10.
The release is [NIST PDR M32124](https://doi.org/10.18434/M32124).
The temperature approximation and heat-capacity treatment retain their scope.

## Selection and release effects

CODATA and NIST WebBook families were removed from the default ranking and
citation patterns. Comparing the previous and revised policy on the corrected
database gives zero selection changes. No default recommendation is classified
as Materials Project data. All other source reviews and permission holds carry
forward.

The database contains **1,771 species, 5,297 observations and 1,839 source
records**. Selected G/S/H counts are **1,327/1,296/1,352**. The observation
count changes by +33 defined reference enthalpies and −4 restricted-source
observations. No species was added. Three numerical recommendations change,
all for dissolved N₂; tin changes source and gains its retained uncertainty.
The 75-system default diagram comparison changes six nitrogen grid points at
25 °C and leaves the other 74 maps unchanged.

Source-specific conditions and attribution are distributed in
[THIRD_PARTY_NOTICES.md](https://github.com/FrederikLizakJohansen/pourbase/blob/main/THIRD_PARTY_NOTICES.md).

Verification includes 580 passing tests, SQLite integrity and foreign-key checks,
a strict Zensical build, and wheel/source packaging with an installed-wheel
scientific check. The paper's statistics, references and full 200-sample selection
envelopes were regenerated for all 75 systems. The private 56-page proof compiles
in three LuaLaTeX passes. The live manuscript, its PDF, permission correspondence
and GUI runtime code are preserved.
