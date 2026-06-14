#!/usr/bin/env python3
"""Phase 0 SCALE-N: large MP-computed confusion matrix for the magnetic gates.

Pull TM-sulfides (+ diamagnetic-cation sulfide controls) from Materials Project
with computed ordering + batched per-site magmoms, run the electron_parity ->
spin_collapse cascade, and score both against MP's computed ordering as y_true.
Stabilises the Phase-0 N=11 result (Sens/Spec/over-conservatism) at large N.

Run with the prodromos venv python (has tm_spec/prodromos); mp_client via sys.path.
"""
from __future__ import annotations
import json, re, sys, time
from collections import Counter
from pathlib import Path
sys.path.insert(0, "dft-neb")
import mp_client as mp
from prodromos.electron_parity_gate import run_electron_parity_gate
from prodromos.spin_collapse_verdict import run_spin_collapse_verdict

OUT = Path("dft-neb/campaign/phase0")
# TM-sulfide chemsys (magnetic interest) + diamagnetic-cation sulfide controls.
CHEMSYS = [
    "Fe-S", "Co-S", "Ni-S", "Mn-S", "Cr-S", "V-S", "Ti-S", "Cu-S",
    "Cu-Fe-S", "Fe-Ni-S", "Co-Ni-S", "Fe-Co-S",
    # expansion 2026-06-02 (campaign b): more TM-S ternaries = meaningful magnetic-discrimination
    # cases (not just TN ballast). e_hull stays 0.10 to preserve ground-truth quality.
    "Mn-Fe-S", "Cr-Fe-S", "V-Fe-S", "Cu-Co-S", "Cu-Ni-S", "Cu-Mn-S", "Mn-Ni-S", "Co-Mn-S",
    "Zn-S", "Cd-S", "Pb-S",  # diamagnetic-cation controls (d10 / no open-shell TM)
    # extra diamagnetic-cation controls (strengthen the true-negative side, modestly)
    "Sn-S", "Ag-S", "Ga-S", "In-S",
]
SUM_FIELDS = ["material_id", "formula_pretty", "symmetry", "is_magnetic", "ordering",
              "total_magnetization", "num_magnetic_sites", "energy_above_hull"]
EHULL_MAX = 0.10  # eV/atom: keep (meta)stable materials, drop exotic enumerated polymorphs
MAG = {"FM", "AFM", "FiM", "FERRI"}


def parse_formula(desc):
    return {el: int(c) if c else 1 for el, c in re.findall(r"([A-Z][a-z]?)(\d*)", desc) if el}


def pull_summary():
    mats: dict[str, dict] = {}
    seen_fsg: set = set()  # (formula, sg) dedup so over-sampled families don't dominate
    for cs in CHEMSYS:
        try:
            data = mp._get("/materials/summary/", {"chemsys": cs, "_fields": ",".join(SUM_FIELDS),
                          "_limit": 1000, "_sort_fields": "energy_above_hull"}).get("data", [])
        except Exception as e:
            print(f"# summary {cs} failed: {e}"); continue
        kept = 0
        for d in data:  # sorted by energy_above_hull ascending
            eh = d.get("energy_above_hull")
            if eh is not None and eh > EHULL_MAX:
                continue
            if d.get("ordering") in (None, "Unknown"):
                continue
            sg = (d.get("symmetry") or {}).get("number")
            key = (d.get("formula_pretty"), sg)  # keep lowest-e_hull polymorph per (formula, sg)
            if key in seen_fsg:
                continue
            seen_fsg.add(key)
            mats[d["material_id"]] = d
            kept += 1
        print(f"# {cs}: {len(data)} returned, {kept} kept (e_hull<= {EHULL_MAX}, ordering known, (formula,sg)-dedup)")
        time.sleep(0.3)
    return mats


def pull_magmoms(mids):
    """Batched /magnetism/ fetch: {material_id: sum|magmom|, n_tm}."""
    out: dict[str, dict] = {}
    CH = 40
    for i in range(0, len(mids), CH):
        chunk = mids[i:i + CH]
        try:
            data = mp._get("/materials/magnetism/", {"material_ids": ",".join(chunk),
                          "_fields": "material_id,magmoms,num_magnetic_sites", "_limit": CH}).get("data", [])
        except Exception as e:
            print(f"# magnetism chunk {i} failed: {e}"); continue
        for d in data:
            mm = d.get("magmoms") or []
            mabs = sum(abs(float(x)) for x in mm) if mm else 0.0
            n_tm = sum(1 for x in mm if abs(float(x)) > 0.3)
            out[d["material_id"]] = {"mabs": mabs, "n_tm": n_tm,
                                     "mabs_per_tm": (mabs / n_tm) if n_tm else 0.0}
        time.sleep(0.3)
    return out


def confusion(pairs):
    tp = sum(1 for p, t in pairs if p and t); fp = sum(1 for p, t in pairs if p and not t)
    tn = sum(1 for p, t in pairs if not p and not t); fn = sum(1 for p, t in pairs if not p and t)
    sens = tp / (tp + fn) if (tp + fn) else float("nan")
    spec = tn / (tn + fp) if (tn + fp) else float("nan")
    return {"TP": tp, "FP": fp, "TN": tn, "FN": fn,
            "sensitivity": round(sens, 3), "specificity": round(spec, 3),
            "over_conservatism": round(fp / (fp + tn), 3) if (fp + tn) else None}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mats = pull_summary()
    mids = list(mats)
    print(f"\n# total unique (meta)stable materials with known ordering: {len(mids)}")
    mag = pull_magmoms(mids)

    rows = []
    ep_pairs = []; sc_pairs = []
    for mid, d in mats.items():
        formula = d.get("formula_pretty") or ""
        counts = parse_formula(formula)
        if not counts:
            continue
        true_mag = d.get("ordering") in MAG
        ep = run_electron_parity_gate(counts)
        ep_pred = ep["verdict"] in ("NSPIN2_RECOMMENDED", "NSPIN2_MANDATORY")
        mm = mag.get(mid)
        if mm is None:
            continue
        sc = run_spin_collapse_verdict(mabs_per_tm=mm["mabs_per_tm"])
        sc_pred = sc["verdict"] == "NSPIN2_REQUIRED"
        # cascade: parity screens; if it says nspin1 -> nonmag; else spin_collapse decides.
        casc_pred = sc_pred if ep_pred else False
        ep_pairs.append((ep_pred, true_mag))
        sc_pairs.append((casc_pred, true_mag))
        rows.append({"mp_id": mid, "formula": formula,
                     "sg": (d.get("symmetry") or {}).get("number"),
                     "ordering": d.get("ordering"), "true_mag": true_mag,
                     "mabs_per_tm": round(mm["mabs_per_tm"], 2),
                     "ep_verdict": ep["verdict"], "ep_pred": ep_pred,
                     "casc_pred": casc_pred})

    ep_cm = confusion(ep_pairs)
    casc_cm = confusion(sc_pairs)
    result = {"n_materials": len(rows), "chemsys": CHEMSYS, "ehull_max": EHULL_MAX,
              "ordering_distribution": dict(Counter(r["ordering"] for r in rows)),
              "electron_parity": ep_cm, "cascade_parity_then_spin_collapse": casc_cm}
    json.dump({"summary": result, "rows": rows},
              open(OUT / "scale_mp_confusion.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print(f"\n=== SCALE-N confusion matrix (N={len(rows)} MP materials, e_hull<= {EHULL_MAX}) ===")
    print("ordering distribution:", result["ordering_distribution"])
    print(f"\n{'gate':<34}{'TP':>5}{'FP':>5}{'TN':>5}{'FN':>5}{'Sens':>8}{'Spec':>8}{'overcons':>10}")
    for name, cm in [("electron_parity (alone)", ep_cm),
                     ("cascade parity->spin_collapse", casc_cm)]:
        print(f"{name:<34}{cm['TP']:>5}{cm['FP']:>5}{cm['TN']:>5}{cm['FN']:>5}"
              f"{cm['sensitivity']:>8}{cm['specificity']:>8}{str(cm['over_conservatism']):>10}")
    print(f"\nwrote {OUT/'scale_mp_confusion.json'}")


if __name__ == "__main__":
    main()
