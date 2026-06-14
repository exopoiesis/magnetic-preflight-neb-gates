# Data

Harvested gate verdicts, magnetic moments, confusion matrices, and migration barriers behind the
manuscript's tables and figures. Raw DFT wavefunction/charge-density dumps are not archived (multi-GB,
regenerable from the inputs); the numbers here are what every table/figure reads.

License: CC-BY-4.0.

## `corpus/` — large-scale validation of the two magnetic screening gates (§7.1, §7.2, §7.5)

The `electron_parity` → `spin_collapse` cascade validated against an external corpus.

| File | Contents |
|---|---|
| `mp_confusion_N137.json` | confusion matrix on the deduplicated **N = 137** Materials-Project corpus (50 magnetic / 87 non-magnetic) — the primary table |
| `mp_confusion_N191.json` | robustness extension to **N = 191** (63 magnetic / 128 non-magnetic) |
| `phase0_mp_confusion.json` | earlier in-house MP confusion snapshot |
| `phase0_confusion_electron_parity.json` | `electron_parity`-alone confusion (high sensitivity, low specificity) |
| `phase0_groundtruth.json` | per-structure ground-truth labels used for the confusion matrices |
| `magndata_harvest.json` | experimental magnetic structures from MAGNDATA (Bilbao) used for the computed-vs-experimental cross-check |
| `MAGNDATA_CROSSCHECK.md` | the computed (MP) vs experimental (MAGNDATA) magnetic-*type* disagreement (~77 %) write-up |

Provenance: Materials Project Summary/magnetism API (Jain et al. 2013), `energy_above_hull ≤ 0.10
eV/atom`, deduplicated by (formula, space group); MAGNDATA (Gallego et al. 2016) parsed from magCIF.

## `battery/` — foundation-MLIP barrier reproduction (§7.4)

Seven published battery-cathode migration barriers reproduced with spin-blind MACE-MP-0, against the
spin-polarized-GGA reference of the literature-derived NEB-endpoint dataset of Devi et al. 2025
([Zenodo 10.5281/zenodo.17240095](https://doi.org/10.5281/zenodo.17240095)).

| File | Contents |
|---|---|
| `battery_repro_neb_results.json` | per-candidate MACE-MP-0 CI-NEB barrier vs dataset GGA E_m (the Table 4 numbers; MAE 0.15 eV) |
| `battery_repro_manifest.json` | full provenance manifest (endpoints, alignment, IDPP path) |

## `cases/` — case-study gate verdicts (§6)

Per-mineral machine-readable gate-verdict records (tm-spec-style JSON) plus the NEB manifests/results
for the two cases reported in depth.

- `*.tm.json` — gate-verdict records for the mineral set (pyrite, marcasite, mackinawite, greigite,
  troilite, sphalerite/ZnS, chalcopyrite, cattierite, vaesite, greenockite, wurtzite).
- `troilite_prodromos_verdict.json` — the **retrospective V_S+H** band (QE, PBE/U=0, 375 meV): the
  endpoint-gate-vs-band-gate divergence (endpoint `NO-GO_SINGLE_SHEET` on the 0.52 µB end-to-end drift;
  band `GO` because no adjacent jump exceeds the 0.5 µB threshold) — the worked example behind §6's
  "the layered design is not redundant".
- `troilite_vfe_manifest.json`, `troilite_vfe_neb_results.json` — a **different**, *prospective*
  troilite case: the **inter-plane V_Fe** hop (Fe₁₁S₁₂, MACE-MP-0), where the donor and acceptor Fe sit
  on opposite AFM spin planes (spin +1 → −1). Predicted `NO-GO_SINGLE_SHEET` (cross-sublattice); the
  MACE band does not converge (band_fmax 1.62 eV/Å) — the gate's own REVIEW case (§6.7 / SI §B.6),
  reported honestly as unconverged, not a quotable barrier.
- `zns_vznh_manifest.json`, `zns_vznh_neb_results.json` — the diamagnetic ZnS V_Zn+H negative control
  (MACE-MP-0, ~0.30 eV, converged).

The featured cases are additionally provided as full tm-spec/0.3 records with a filled `preflight:`
gate-verdict block in [`../tm-spec/`](../tm-spec/) (troilite V_S+H, ZnS control, greigite self-audit).

## DFT protocol note (authoritative: manuscript Methods)

All iron-sulfide case-study barriers were run under a **uniform PBE protocol with no Hubbard U**
(`U = 0`): an intended on-site U silently failed to write through the ASE ≥ 3.23 Quantum-ESPRESSO
interface, and zero Hubbard energy was verified in every output (pyrite, mackinawite, greigite,
marcasite, troilite — the troilite V_S+H band confirmed zero Hubbard energy in all seven images,
2026-06-04). The gate **verdicts** key on the magnetization sign/pattern, not the barrier height, so
they are insensitive to the U = 0 ↔ U ≈ 2 eV choice (§7.5).
