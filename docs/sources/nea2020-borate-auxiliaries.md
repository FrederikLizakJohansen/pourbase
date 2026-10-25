# NEA borate auxiliaries and independent open NBS values

R11j3e adds nine observations on crystalline CaB2O4 and NaBO2, with six available
G/H/S properties. Three own NEA calcium-borate selections coexist with six
independent original open NBS G/H/S observations. The existing policy selects
NEA G/H/S for CaB2O4 and NBS G/H/S for NaBO2. Every earlier observation and
preferred candidate remains.

## Selected calcium borate and original open alternatives

Grenthe et al. (2020), *Second Update on the Chemical Thermodynamics of U, Np,
Pu, Am and Tc*, Chemical Thermodynamics 14, OECD Nuclear Energy Agency,
NEA No. 7500,
[Table 14-2, p. 606](https://www.oecd-nea.org/upload/docs/application/pdf/2020-10/7500_second_update_of_u_np_pu_am_and_tc_web.pdf)
(PDF p. 670), selects CaB2O4 G −1924.561 ±1.723 kJ/mol,
H −2031.500 ±1.700 kJ/mol and S 105.020 ±0.840 J/(mol K).
Appendix A, pp. 1205–1206 (PDF pp. 1269–1270), documents the original
1947 Torgeson/Shomate dissolution calorimetry, sample selection and recalculation.
Using its selected anchors, −634.92 −1273.5 −123.08 = −2031.50 kJ/mol;
H and formation S −358.674 J/(mol K) reproduce its selected G within 1 J/mol.
The entropy selection uses Kelley et al. (1948) low-temperature calorimetry.
Numerical equality of the selected H with a Glushko value supplies no reuse
basis here; the independent NEA recalculation is the source.

| Original open NBS species | G, kJ/mol | H, kJ/mol | S, J/(mol K) | Logical CSV record |
| --- | ---: | ---: | ---: | ---: |
| CaO·B2O3(cr) | −1924.03 | −2030.96 | 104.85 | 9509 |
| NaBO2(cr) | −920.70 | −977.0 | 73.51 | 11673 |

The original NBS cells come from columns 9/8/11 in the corrected
[open non-SRD release M32124](https://doi.org/10.18434/M32124). Missing source
uncertainty stays NULL. All values refer to 298.15 K and 1 bar. CaO·B2O3 is
CaB2O4 and retains its full two-B formula unit. NaBO2 contains one B atom.
G/H are stored in J/mol. The quoted NEA total widths retain their approximately
95% source meaning. The two exact crystal structures remain unresolved.

## Complete table dispositions and the mixed boric-acid row

All 15 Table 14-2 scalar G/H/S slots have explicit dispositions:

| Disposition | Slots |
| --- | ---: |
| Own selected CaB2O4 observations retained | 3 |
| Defined elemental G/H references, no new observation | 2 |
| Copied CODATA B(cr) S and B2O3 G/H/S, held | 4 |
| Mixed boric-acid row with CODATA ancestry, held | 3 |
| Direct Glushko NaBO2 G/H/S, held | 3 |

The original 2003 review, Table 8-1, p. 143 (PDF p. 183), identifies the
B/B2O3/boric-acid cells as directly copied bold CODATA values. Its boric-acid
aqueous row gives G −969.268 kJ/mol, H −1072.800 kJ/mol and S 162.400 J/(mol K);
the crystalline row gives G −969.667, H −1094.800 and S 89.950 in those units.
The 2020 row labelled B(OH)3(aq) combines the aqueous G with crystalline H/S.
All three cells stay held with that phase/source qualification. The earlier
independent NBS boric-acid observations remain unchanged. The 2020 NaBO2
compilation cells retain their separate hold; the original open NBS alternative
is admitted with its own values and source.

## Reuse and supported model scope

OECD and NEA are acknowledged. The supplied written NEA clarification and
[OECD data terms](https://www.oecd.org/en/about/terms-conditions.html) cover the
three own selected/recalculated CaB2O4 outputs, including commercial adaptation
and redistribution, with citation and applicable additional restrictions checked.
When sharing or licensing work using these data, include the same OECD
acknowledgment requirement in sublicences and require further sublicensees
to do the same. NIST is acknowledged for the six original NBS cells under its
[open licence](https://www.nist.gov/open/license); data are distributed without
warranty. Sources were accessed on 25 October 2026. Other source permission
holds retain their earlier status.

The salts use the existing free calcium/sodium references, one cation per full
source formula unit, and reduce by three electrons per B atom. Buffers have
independently prescribed activities. Closed sodium/calcium inventories and
ligand thermal functions remain separate model work. The existing thermal
model excludes these buffered salts.

Staging preserves every earlier SQL row and preferred candidate, verifies units,
widths and repeated-import behaviour, and checks 27 energies, four thermal
exclusions, six buffered diagrams and 24 supported primary-B balances. All 75
default maps and 1σ/3σ masks remain unchanged at 81×91 resolution. Earlier
R06/R07, the six original crystalline Gibbs gaps and all independent source/model
holds carry forward. Further own auxiliary versions continue separately.
