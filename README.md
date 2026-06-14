# Magnetic-first pre-flight gates for well-posed DFT NEB

Code, data, and machine-checked proofs accompanying the manuscript:

> **Magnetic-First Pre-Flight Gates for Well-Posed DFT Nudged Elastic Band Calculations in
> Transition-Metal Sulfides**
>
> Igor N. Morozov. Independent Researcher, Ukraine.
> ORCID: [0009-0007-3863-1747](https://orcid.org/0009-0007-3863-1747) · igor@exopoiesis.space · exopoiesis.space

A DFT nudged-elastic-band (NEB) calculation in a magnetic transition-metal sulfide can converge
numerically and still answer an **ill-posed** question — most insidiously when the band crosses
spin sheets. This work operationalizes a layered, machine-readable **pre-flight** operator that runs
*before* the expensive band: it certifies endpoint topology, structural-motif integrity, and
spin-sheet continuity, and emits a structured routing verdict (`GO` / `REVIEW` /
`NO-GO_SINGLE_SHEET`) rather than a crash. The gates ship in the open-source
[**Prodromos**](https://github.com/exopoiesis/prodromos) package; this repository holds the
paper's validation data, the drivers that generate it, and a **machine-checked core** of the gate
rules in Lean 4 / mathlib.

## Highlights

- **Two-gate magnetic screen validated on external data.** `electron_parity` → `spin_collapse`
  cascade on 137 Materials-Project magnetic ground states (robustness extension N = 191) and 47
  MAGNDATA experimental structures: the cascade recovers near-perfect specificity, while the
  *computed* magnetic type disagrees with neutron diffraction ~77 % of the time (so a computed label
  alone cannot calibrate the gate).
- **Foundation-MLIP barrier reproduction.** Seven published battery-cathode migration barriers
  (Devi et al. 2025) with spin-blind MACE-MP-0: 0.15 eV MAE — useful for path triage, not as a final
  magnetic-host estimator.
- **Machine-checked gate core** (`proofs/`). The algebraic / combinatorial / order-theoretic core of
  the gate rules is proved in Lean 4 / mathlib — `sorry`-free, depending only on the standard axioms.
  Four architectural claims become theorems: parity robustness, the structural reason for the
  threshold window, endpoint/band non-redundancy, and the necessity of the sign-vector gate. See
  [`proofs/README.md`](proofs/README.md).

## Repository layout

```
proofs/    machine-checked gate core (Lean 4/mathlib): PreflightGates.lean + verification README
data/
  corpus/  Materials-Project confusion matrices (N=137 / N=191), electron-parity confusion,
           ground-truth, and the MAGNDATA experimental cross-check
  battery/ seven-path foundation-MLIP-vs-DFT migration reproduction (Devi et al. 2025)
  cases/   per-mineral MP-magnetism records (tm-spec) + troilite (V_S+H and prospective V_Fe) and ZnS NEB results
tm-spec/   tm-spec/0.3 records of the featured cases with a filled `preflight:` gate-verdict block
scripts/   drivers that generate the data by calling the Prodromos gate functions
figures/   figure-generation script (fig1) + figure PDFs
```

## Reproducing

```bash
pip install -r requirements.txt
```

- **Gate / corpus / battery drivers** (`scripts/`) call the [Prodromos](https://github.com/exopoiesis/prodromos)
  gate functions and require network access to the Materials Project (`MP_API_KEY`) and MAGNDATA for a
  fresh harvest; the harvested JSON behind every table is already in `data/`.
- **Battery MLIP reproduction** additionally needs `mace-torch` (MACE-MP-0 medium) and reads the
  literature-derived NEB-endpoint dataset of Devi et al. 2025
  ([Zenodo 10.5281/zenodo.17240095](https://doi.org/10.5281/zenodo.17240095)).
- **Figures** require only `matplotlib` + `numpy`.
- **Proofs** (`proofs/`) are verified with Lean 4 + mathlib; see `proofs/README.md` for the exact
  toolchain and the one-command axiom audit.

Raw DFT wavefunction/charge-density dumps are **not** archived (multi-GB, regenerable from the
provided inputs); `data/` holds the harvested gate verdicts, moments, and barriers behind the paper's
tables and figures.

## Related

- **Prodromos** (the gate package): https://github.com/exopoiesis/prodromos
- **TM-Spec** (the machine-readable calculation-spec format): https://github.com/exopoiesis/tm-spec
- **Companion DFT/MLIP benchmark (Paper #1):** https://github.com/exopoiesis/mlip-vs-dft-iron-sulfides

## Citing

See `CITATION.cff`. Archived release: Zenodo DOI [10.5281/zenodo.20690940](https://doi.org/10.5281/zenodo.20690940).

## License

Code (`scripts/`, `figures/`, `proofs/`): MIT (`LICENSE`). Data (`data/`): CC-BY-4.0.

## Acknowledgements

Trelis Research; compute on Vast.ai (A100 PCIe 40 GB) and a local RTX 4070 node. Lean proofs verified
in a pinned `mathlib` toolchain.
