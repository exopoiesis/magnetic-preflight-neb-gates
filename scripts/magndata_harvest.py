#!/usr/bin/env python3
"""Back-office MAGNDATA bulk harvester (stdlib + tm_spec.importers.magndata).

Reuses the AgentMaterial spider's idea (the MAGNDATA search form) to DISCOVER
entry codes by element, then converts each .mcif with the tm-spec importer and
cross-checks the EXPERIMENTAL magnetic ordering against Materials Project's
COMPUTED ordering (campaign finding #9: MP labels troilite/chalcopyrite FM where
neutron diffraction finds AFM).

MAGNDATA has no GET listing; search.php is the only element query (POST). The
Bilbao server ships a misconfigured TLS cert -> verification disabled (public data).

Usage (prodromos venv python, which has tm_spec):
    python dft-neb/magndata_harvest.py            # Fe-S family + cross-check
    python dft-neb/magndata_harvest.py --families Fe-S Cu-Fe-S Co-S Ni-S
"""
from __future__ import annotations
import argparse, json, re, ssl, sys, time, urllib.parse, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "git" / "tm-spec" / "src"))
from tm_spec.importers.magndata import fetch_magcif, magcif_to_tm_spec, parse_magcif

UA = "Mozilla/5.0 (compatible; tm-spec-campaign/0.1; +https://github.com/exopoiesis)"
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
SEARCH = "https://www.cryst.ehu.eus/magndata/search.php"
OUT = Path("dft-neb/campaign/phase0")

FAMILIES = {
    # original 4 (harvest #1)
    "Fe-S": ["Fe", "S"], "Cu-Fe-S": ["Cu", "Fe", "S"], "Co-S": ["Co", "S"], "Ni-S": ["Ni", "S"],
    # expansion (2026-06-02): broaden the 3d TM-S series + ternaries to grow the experimental
    # anchor from 27 sg-matched pairs toward 60-100 (consilium: N=27 too small for the binary claim)
    "Mn-S": ["Mn", "S"], "Cr-S": ["Cr", "S"], "V-S": ["V", "S"], "Ti-S": ["Ti", "S"],
    "Cu-S": ["Cu", "S"],
    "Fe-Ni-S": ["Fe", "Ni", "S"], "Fe-Co-S": ["Fe", "Co", "S"], "Co-Ni-S": ["Co", "Ni", "S"],
    "Mn-Fe-S": ["Mn", "Fe", "S"],
}
# convenience preset: every family above
ALL_FAMILIES = list(FAMILIES)


def search_codes(elements: list[str]) -> list[str]:
    form = {"adser": "1", "incomm_type_srch": "all", "indices_srch": "",
            "atoms_srch": " ".join(elements), "op_srch": "AND",
            "tot_species_srch": "", "auth_srch": "", "year_srch": "",
            "comments_srch": "", "submit": "Search"}
    req = urllib.request.Request(SEARCH, data=urllib.parse.urlencode(form).encode(),
            headers={"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
        html = r.read().decode("utf-8", "replace")
    codes = sorted({m.group(1) for m in re.finditer(r"this_label=([0-9][0-9.]*)", html)},
                   key=lambda c: [int(x) for x in c.split(".")])
    return codes


def harvest(families: list[str]) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for fam in families:
        els = FAMILIES[fam]
        try:
            codes = search_codes(els)
        except Exception as e:
            print(f"# search {fam} failed: {e}"); continue
        print(f"# {fam}: {len(codes)} MAGNDATA codes")
        for code in codes:
            if code in seen:
                continue
            seen.add(code)
            try:
                text = fetch_magcif(code)
                doc = magcif_to_tm_spec(text, code=code)
                mag = doc["magnetic"]
                rows.append({"code": code, "family": fam,
                             "formula": doc["structure"]["formula"],
                             "sg": (doc["structure"].get("space_group") or {}).get("number"),
                             "state": mag.get("state"), "bns": mag.get("bns_group"),
                             "magmoms": mag.get("magmoms_uB"),
                             "k": mag.get("propagation_vector")})
            except Exception as e:
                rows.append({"code": code, "family": fam, "error": str(e)[:80]})
            time.sleep(0.4)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", nargs="+", default=["Fe-S"], choices=list(FAMILIES))
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = harvest(args.families)
    json.dump(rows, open(OUT / "magndata_harvest.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    ok = [r for r in rows if "state" in r]
    print(f"\n{'code':<9}{'family':<9}{'formula':<14}{'state':<8}{'bns':<14}{'k'}")
    print("-" * 70)
    for r in ok:
        print(f"{r['code']:<9}{r['family']:<9}{str(r['formula'])[:13]:<14}"
              f"{str(r['state']):<8}{str(r['bns'])[:13]:<14}{r.get('k')}")
    errs = [r for r in rows if "error" in r]
    print(f"\nharvested {len(ok)} ok, {len(errs)} errors; wrote {OUT/'magndata_harvest.json'}")
    # ordering distribution
    from collections import Counter
    print("state distribution:", dict(Counter(r["state"] for r in ok)))


if __name__ == "__main__":
    main()
