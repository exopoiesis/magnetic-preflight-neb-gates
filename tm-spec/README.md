# TM-Spec records — pre-flight gate verdicts (tm-spec/0.3)

[TM-Spec v0.3](https://github.com/exopoiesis/tm-spec) declarative records of the case-study
calculations, each with a filled top-level **`preflight:` block** — the forward-looking gate verdicts
(`electron_parity`, `spin_collapse`, `endpoint_dM`, `inband_dM`, `sign_vector`) that the manuscript's
§8 / SI §B promise as the machine-readable record of the problem statement. The `preflight` block
speaks the same gate-ID vocabulary as the post-hoc `sanity` array: `sanity` records what *was* checked
after the run; `preflight` records what the gate *predicted/routed* before (or around) the band.

| Record | Case | Pre-flight story | Source data |
|---|---|---|---|
| `troilite_VS_H_neb.tm.yaml` | troilite FeS V_S+H (§6) | **endpoint gate vs band gate**: endpoint NO-GO on the 0.52 µB drift, band GO (no adjacent jump > 0.5 µB, M_total≡0) — the layered design is not redundant | `data/cases/troilite_prodromos_verdict.json` |
| `zns_VZn_H_neb.tm.yaml` | sphalerite ZnS V_Zn+H (§6) | **negative control**: parity flags NSPIN2 (vacancy+H odd-electron), the cascade clears it (d¹⁰, moment→0) to NSPIN1_OK → GO; MLIP barrier valid because nspin=1 certified | `data/cases/zns_vznh_neb_results.json` |
| `greigite_VFe_selfaudit.tm.yaml` | greigite Fe₃S₄ V_Fe (§6) | **in-band self-audit**: our own 1.86 eV band returns GO — |M_abs| flat, sign-vector **S = 1.0** over 23 Fe (no sign flip) — the gate validates, not only vetoes | manuscript §6 + companion structure record |

These complement the **NEBCalculation** records of the companion DFT/MLIP benchmark
([mlip-vs-dft-iron-sulfides](https://github.com/exopoiesis/mlip-vs-dft-iron-sulfides) `tm-spec/`),
which carry the *barriers* (greigite, mackinawite, marcasite, pyrite, pentlandite) but predate the
`preflight:` block; the records here foreground the *gate verdicts* that are this paper's subject.

The MP-imported, structure-level magnetism records for the full mineral set (`SinglePointCalculation`
kind, e.g. the mp-2099 troilite entry that the §7.2 trap is built on) are in `data/cases/*.tm.json`.

DFT protocol: uniform **PBE, U = 0** for the iron-sulfide cases (an intended on-site U silently
dropped through the ASE≥3.23 QE interface; zero Hubbard energy verified). The gate *verdicts* key on
the magnetization sign/pattern, not the barrier height, so they are insensitive to the U choice (§7.5).
