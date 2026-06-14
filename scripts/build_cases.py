#!/usr/bin/env python3
"""Phase 0 case BUILDER (token-free): for each canonical mineral, pull MP computed
magnetism -> tm-spec/0.3 doc (mp_client.mp_to_tm_spec) -> validate -> write
cases/<mineral>.tm.json. Optionally merge OPTIMADE structure-width via merge_specs.

Run as a SCRIPT (writes files); the LLM reads only the one-line-per-mineral rollup.
Usage:  <prodromos-venv-python> dft-neb/campaign/phase0/build_cases.py [--with-optimade]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, "dft-neb")
import mp_client as mp
from tm_spec.validator import validate_doc

CASES = Path("dft-neb/campaign/phase0/cases")
CANON = [
    ("pyrite", "FeS2", 205), ("marcasite", "FeS2", 58), ("troilite", "FeS", 194),
    ("mackinawite", "FeS", 129), ("greigite", "Fe3S4", 227), ("chalcopyrite", "CuFeS2", 122),
    ("cattierite", "CoS2", 205), ("vaesite", "NiS2", 205), ("sphalerite", "ZnS", 216),
    ("wurtzite", "ZnS", 186), ("greenockite", "CdS", 186),
]
SUM_FIELDS = ["material_id","formula_pretty","symmetry","is_magnetic","ordering",
              "total_magnetization","num_magnetic_sites","energy_above_hull","is_stable"]


def most_stable_at_sg(formula, sg):
    data = mp._get("/materials/summary/", {"formula": formula, "_fields": ",".join(SUM_FIELDS),
                   "_limit": 500, "_sort_fields": "energy_above_hull"}).get("data", [])
    cand = [d for d in data if (d.get("symmetry") or {}).get("number") == sg]
    cand.sort(key=lambda d: (d.get("energy_above_hull") if d.get("energy_above_hull") is not None else 9e9))
    return cand[0] if cand else None


def magmoms(mid):
    d = mp._get("/materials/magnetism/", {"material_ids": mid,
                "_fields": "material_id,ordering,magmoms,num_magnetic_sites"}).get("data", [])
    return d[0] if d else {}


def maybe_merge_optimade(doc, formula):
    """Merge OPTIMADE structure-width into the MP magnetic-depth doc (dogfoods merge_specs)."""
    try:
        from tm_spec.importers.optimade import import_optimade
        from tm_spec.merge import merge_docs
        ov = import_optimade(elements=None, reduced_formula=formula, provider="mp", page_limit=1)
        if ov:
            merged, warnings = merge_docs(doc, ov[0], fill_only=True, strict_material=False)
            return merged, warnings
    except Exception as ex:
        return doc, [f"optimade-merge skipped: {type(ex).__name__}: {ex}"]
    return doc, ["optimade-merge: no overlay returned"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-optimade", action="store_true", help="merge OPTIMADE structure width")
    args = ap.parse_args()
    CASES.mkdir(parents=True, exist_ok=True)
    print(f"{'mineral':<13}{'mp_id':<13}{'sg':<5}{'ordering':<9}{'state':<8}{'valid':<6}{'file'}")
    print("-"*78)
    n_ok = n_valid = 0
    for mineral, formula, sg in CANON:
        s = most_stable_at_sg(formula, sg)
        if not s:
            print(f"{mineral:<13}{'-':<13}{sg:<5}{'NO_MP_AT_SG'}"); continue
        mid = s["material_id"]
        doc = mp.mp_to_tm_spec(s, magmoms(mid))
        warns = []
        if args.with_optimade:
            doc, warns = maybe_merge_optimade(doc, formula)
        schema_errs, rule_issues = validate_doc(doc)
        valid = not schema_errs
        out = CASES / f"{mineral}.tm.json"
        out.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        n_ok += 1; n_valid += int(valid)
        st = (doc.get("magnetic") or {}).get("state")
        print(f"{mineral:<13}{mid:<13}{sg:<5}{str(s.get('ordering')):<9}{str(st):<8}"
              f"{('OK' if valid else 'ERR'):<6}{out.name}")
        if schema_errs:
            for p, m in schema_errs[:3]:
                print(f"    schema! {p}: {m}")
        if warns:
            for w in warns[:2]:
                print(f"    note: {w}")
    print("-"*78)
    print(f"wrote {n_ok} case docs to {CASES}/  ({n_valid} schema-valid)")


if __name__ == "__main__":
    main()
