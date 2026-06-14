# Scripts — the drivers that produced `data/`

These are the **exact drivers** used to generate the harvested results in `data/`, shipped for
provenance and as worked examples. They are **not turnkey** — like the DFT drivers of any
computational paper, they assume the authors' environment:

- the [**Prodromos**](https://github.com/exopoiesis/prodromos) package on the path (the gate
  functions `run_electron_parity_gate`, `run_spin_collapse_verdict`, the band/endpoint gates);
- [**tm-spec**](https://github.com/exopoiesis/tm-spec) for the validate-able calculation records;
- a small `mp_client` helper (project-local) that reads a Materials Project API key from a local
  secret and exposes `mp._get(...)` / `mp.mp_to_tm_spec(...)`; set your own `MP_API_KEY` and adapt the
  `sys.path` / import lines to your layout;
- the original scripts wrote into the project's `dft-neb/campaign/phase0/` tree; in this repository the
  corresponding harvested outputs live under `data/corpus/`, `data/cases/`, `data/battery/`.

| Script | Produces | Manuscript |
|---|---|---|
| `scale_mp_confusion.py` | the Materials-Project confusion matrices (`data/corpus/mp_confusion_N137.json`, `…N191.json`) — pulls TM-sulfide + diamagnetic-control chemsys, runs the parity→spin_collapse cascade, scores vs MP ordering | §7.1, §7.5 |
| `magndata_harvest.py` | the MAGNDATA experimental harvest + computed-vs-experimental cross-check (`data/corpus/magndata_harvest.json`, `MAGNDATA_CROSSCHECK.md`) | §7.2 |
| `build_cases.py` | the per-mineral gate-verdict records (`data/cases/*.tm.json`) from MP computed magnetism → tm-spec/0.3 | §6 |
| `mlip_battery_neb.py` | the foundation-MLIP (MACE-MP-0) CI-NEB barrier reproduction on the Devi et al. 2025 endpoints (`data/battery/`) | §7.4 |

To re-run from a fresh harvest you need network access (Materials Project, MAGNDATA Bilbao) and, for
`mlip_battery_neb.py`, `mace-torch` plus the Devi et al. 2025 dataset
([Zenodo 10.5281/zenodo.17240095](https://doi.org/10.5281/zenodo.17240095)). The harvested JSON in
`data/` is what every table and figure in the paper reads, so the figures reproduce without re-running
the harvest.
