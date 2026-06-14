#!/usr/bin/env python3
"""Idea-2 battery-NEB reproduction: MACE-MP NEB barrier vs dataset GGA Em ($0, CPU-OK).

Reads battery_repro_manifest.json (JARVIS endpoints + gate predictions), runs
MACE-MP foundation-model CI-NEB between the two endpoints, and compares the barrier
to the dataset's reported Em. Spin-blind MLIP -> this validates the GEOMETRIC/PATH
gates + barrier reproduction for ion migration; the magnetic gate was scored in prep.

Per-candidate incremental JSON write so a slow CPU run is monitorable/resumable.
Usage:  python mlip_battery_neb.py --only MgFe2S4         # one candidate
        python mlip_battery_neb.py                         # all in manifest
Gotcha [feedback_ase_idpp_mic_fix_required]: migrating ion hops 3-4.5 A across PBC ->
IDPP interpolate with mic=True is MANDATORY (stock ASE default mic=False breaks it).
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path

import numpy as np
from ase import Atoms
from ase.optimize import FIRE
from ase.mep import NEB  # ASE 3.28: ase.mep.NEB


class SafeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.bool_):    return bool(obj)
        if isinstance(obj, np.integer):  return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray):  return obj.tolist()
        if isinstance(obj, Path):        return str(obj)
        return super().default(obj)


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "battery_repro_manifest.json"
OUT = HERE / "battery_repro_neb_results.json"


def jarvis_to_atoms(s: dict) -> Atoms:
    cell = np.array(s["lattice_mat"], float)
    frac = np.array(s["coords"], float)
    els = s["elements"]
    if bool(s.get("cartesian", False)):
        return Atoms(symbols=els, positions=frac, cell=cell, pbc=True)
    return Atoms(symbols=els, scaled_positions=frac, cell=cell, pbc=True)


def align_fin_to_ini(ini: Atoms, fin: Atoms) -> Atoms:
    """Place each fin atom at ini + minimum-image displacement so NO atom is wrapped
    across a periodic boundary relative to ini. Makes the subsequent IDPP path
    contiguous in real space (fixes the b-Li3PS4 PBC-crossing seen with raw scaled
    coords). No-op for endpoints already in the same periodic image."""
    from ase.geometry import find_mic
    d = fin.get_positions() - ini.get_positions()
    dmic, _ = find_mic(d, ini.cell, ini.pbc)
    out = fin.copy()
    out.set_positions(ini.get_positions() + dmic)
    return out


def make_calc():
    from mace.calculators import mace_mp
    return mace_mp(model="medium", default_dtype="float64", device="cpu")


def relax(atoms: Atoms, calc, fmax=0.05, steps=200, label=""):
    atoms = atoms.copy()
    atoms.calc = calc
    opt = FIRE(atoms, logfile=None)
    conv = bool(opt.run(fmax=fmax, steps=steps))
    e = float(atoms.get_potential_energy())
    fmax_final = float(np.linalg.norm(atoms.get_forces(), axis=1).max())
    print(f"    relax {label}: E={e:.4f} eV, fmax={fmax_final:.4f}, steps={opt.nsteps}, conv={conv}", flush=True)
    return atoms, e, fmax_final, int(opt.nsteps)


def run_neb(ini: Atoms, fin: Atoms, calc, n_interior=5, fmax=0.05, steps=300):
    images = [ini]
    for _ in range(n_interior):
        images.append(ini.copy())
    images.append(fin)
    neb = NEB(images, climb=True, allow_shared_calculator=True)
    neb.interpolate(method="idpp", mic=True)   # MIC mandatory (PBC ion hop)
    # PATH-SANITY (verify MIC actually applied; stock ASE default is mic=False):
    # max per-atom Cartesian step between consecutive images. If MIC failed, the
    # migrating ion shows one ~cell-length jump. Contiguous path => all steps small.
    seg_max = 0.0
    for a, b in zip(images[:-1], images[1:]):
        step = float(np.linalg.norm(b.get_positions() - a.get_positions(), axis=1).max())
        seg_max = max(seg_max, step)
    cell_min = float(min(np.linalg.norm(images[0].cell, axis=1)))
    mic_ok = seg_max < 0.4 * cell_min   # a PBC-crossing jump would be ~cell_min
    print(f"    path-sanity: max consecutive-image atom step = {seg_max:.2f} A "
          f"(cell_min={cell_min:.2f}, MIC_ok={mic_ok})", flush=True)
    if not mic_ok:
        raise RuntimeError(f"MIC interpolation FAILED: seg_max {seg_max:.2f} A ~ cell "
                           f"{cell_min:.2f} A (PBC-crossing linear path). Use gitlab/ase.")
    for img in images:
        img.calc = calc
    opt = FIRE(neb, logfile=None)
    t0 = time.time()
    converged = bool(opt.run(fmax=fmax, steps=steps))
    dt = time.time() - t0
    energies = [float(img.get_potential_energy()) for img in images]
    e0 = energies[0]
    barrier_fwd = max(energies) - energies[0]
    barrier_rev = max(energies) - energies[-1]
    band_fmax = float(np.linalg.norm(
        np.concatenate([img.get_forces() for img in images[1:-1]]), axis=1).max())
    return {
        "converged": converged, "neb_steps": int(opt.nsteps), "wall_s": round(dt, 1),
        "energies_eV": [round(e - e0, 4) for e in energies],
        "barrier_fwd_eV": round(barrier_fwd, 4), "barrier_rev_eV": round(barrier_rev, 4),
        "saddle_image": int(np.argmax(energies)), "n_images": len(images),
        "band_fmax": round(band_fmax, 4), "E_rxn_eV": round(energies[-1] - energies[0], 4),
        "path_seg_max_A": round(seg_max, 3), "mic_ok": mic_ok,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="single candidate label")
    ap.add_argument("--manifest", default=None, help="override manifest path (default battery_repro_manifest.json)")
    ap.add_argument("--n-interior", type=int, default=5)
    ap.add_argument("--fmax", type=float, default=0.05)
    ap.add_argument("--steps", type=int, default=300)
    args = ap.parse_args()

    manifest_path = Path(args.manifest) if args.manifest else MANIFEST
    out_path = (manifest_path.with_name(manifest_path.stem.replace("_manifest", "") + "_neb_results.json")
                if args.manifest else OUT)
    manifest = json.load(open(manifest_path, encoding="utf-8"))
    if args.only:
        manifest = [m for m in manifest if m["label"] == args.only]
        if not manifest:
            print(f"no candidate {args.only!r} in manifest"); sys.exit(1)

    results = json.load(open(out_path, encoding="utf-8")) if out_path.exists() else {}
    calc = make_calc()
    print(f"MACE-MP medium loaded (CPU). candidates: {[m['label'] for m in manifest]}", flush=True)

    for m in manifest:
        lab = m["label"]
        print(f"\n=== {lab}  (nat={m['nat']}, Em_dataset={m.get('Em_dataset')} eV, "
              f"ep={m.get('ep_verdict','N/A')}, mig={m.get('migrating_ion')} {m.get('max_disp_A')} A) ===", flush=True)
        try:
            ini = jarvis_to_atoms(m["structure_ini"])
            fin = align_fin_to_ini(ini, jarvis_to_atoms(m["structure_fin"]))
            ini_r, e_i, fi, si = relax(ini, calc, fmax=args.fmax, label="ini")
            fin_r, e_f, ff, sf = relax(fin, calc, fmax=args.fmax, label="fin")
            neb = run_neb(ini_r, fin_r, calc, n_interior=args.n_interior,
                          fmax=args.fmax, steps=args.steps)
            em_ds = m["Em_dataset"]
            rec = {
                "label": lab, "nat": m["nat"], "formula": m["formula"], "sg": m["sg"],
                "XC_dataset": m.get("XC"), "Em_dataset_eV": em_ds, "ep_verdict": m.get("ep_verdict", "N/A"),
                "migrating_ion": m.get("migrating_ion"), "max_disp_A": m.get("max_disp_A"),
                "mlip": "MACE-MP-0 medium (spin-blind, CPU float64)",
                "endpoint_relax": {"E_ini": round(e_i, 4), "fmax_ini": round(fi, 4),
                                   "E_fin": round(e_f, 4), "fmax_fin": round(ff, 4),
                                   "steps_ini": si, "steps_fin": sf},
                **neb,
                "barrier_vs_Em": {
                    "mlip_barrier_fwd_eV": neb["barrier_fwd_eV"], "Em_dataset_eV": em_ds,
                    "abs_diff_eV": round(abs(neb["barrier_fwd_eV"] - em_ds), 4) if em_ds else None,
                    "ratio": round(neb["barrier_fwd_eV"] / em_ds, 2) if em_ds else None,
                },
            }
            _dd = rec['barrier_vs_Em']['abs_diff_eV']
            print(f"  -> MLIP barrier_fwd={neb['barrier_fwd_eV']} eV vs Em_dataset={em_ds} eV "
                  f"(|d|={_dd}, conv={neb['converged']}, band_fmax={neb['band_fmax']})", flush=True)
        except Exception as e:
            import traceback; traceback.print_exc()
            rec = {"label": lab, "error": f"{type(e).__name__}: {e}"}
        results[lab] = rec
        json.dump(results, open(out_path, "w", encoding="utf-8"), indent=1, cls=SafeJSONEncoder)
        print(f"  wrote {out_path}", flush=True)

    print("\nDONE.", flush=True)


if __name__ == "__main__":
    main()
