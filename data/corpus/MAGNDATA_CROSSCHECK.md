# MAGNDATA (experiment) vs Materials Project (computed) — magnetic-ordering cross-check

> **UPDATE 2026-06-02 (f): EXPANDED harvest (consilium b: N=27 too small).** Added 9 TM-S families
> (Mn-S/Cr-S/V-S/Ti-S/Cu-S + Fe-Ni-S/Fe-Co-S/Co-Ni-S/Mn-Fe-S) → harvest **47→85 structures**
> (0 errors, 0 "Unknown" — the `294c144` formula-fallback works), sg-matched pairs **27→47**.
> Results (`magndata_harvest_expanded.json`, `tmp/magndata_vs_mp_sg_v2.py`):
> - **type-mismatch robust across composition:** ALL 36/47 = **77%** [0.63,0.86]; **pure sulfides
>   (no O) 23/30 = 77%** [0.59,0.88]; sulfates/oxysulfides 13/17 = 76% [0.53,0.90]. The ~3/4
>   experiment-vs-MP type-disagreement is NOT an artifact of sulfate contamination — it holds on the
>   clean sulfide subset. **This is the headline number for the paper (pure-sulfide 30 pairs).**
> - **binary magnetic/NM: 2/47** (4.3% [0.01,0.14]) — was 0/27. ⚠️ BOTH are MAGNDATA-side **zero-
>   moment data gaps**, NOT genuine experimental NM: **K2MnS2 (1.1.64)** and **MnSb2S4 (1.1.139)**
>   list `moment magnitude = 0.000` for a Mn²⁺ (d⁵, HS) ion that is chemically obliged to carry a
>   moment — verified by inspecting the raw magCIF (`tmp/inspect_nm_codes.py`). Here MP (calls them
>   magnetic) is closer to truth than the incomplete MAGNDATA entry. Symmetric to the 5 MP-side FN
>   data gaps in the N=137 MP corpus. Excluding the 2 data gaps: binary 0/45 [0,0.079].
> - sulfate split addresses consilium B3 (LiFe(SO₄)₂/CoSO₄/BaCoSO… moment on O-coord TM, S⁶⁺
>   diamagnetic): 17 of the 47 pairs are sulfates/oxysulfides, now reported separately.
> - Backup of the original 47-structure harvest: `magndata_harvest.orig47.json`.
>
> **UPDATE 2026-06-02 (e): SG-MATCHED rate added** (was formula-only 14/21). Matching the SAME
> (formula, space group) via the magCIF parent space group: **27 comparable pairs, 20/27 (74%)
> disagree on ordering TYPE, but 0/27 disagree on binary magnetic-vs-NM.** I.e. MP reliably knows
> *whether* a TM sulfide is magnetic but gets FM/AFM/ferri *type* wrong ~3/4 of the time vs neutron
> diffraction. CuFeS2 sg122 AFM vs MP FM (clean). NiS2 sg205 agrees AFM=AFM once sg-matched (the
> formula-only mismatch was a different polymorph). Script: `tmp/magndata_vs_mp_sg.py`; parser now
> captures `_parent_space_group.IT_number`. The formula-only 14/21 below is the looser upper bound.
>
> 2026-06-02. Closes campaign finding #9. Harvester: `dft-neb/magndata_harvest.py`
> (reuses AgentMaterial spider's element-search idea + `tm_spec.importers.magndata`).
> Cross-check: `tmp/magndata_vs_mp.py`. Data: `magndata_harvest.json`.

## What was done
- **Discovery:** MAGNDATA `search.php` element search (Fe-S / Cu-Fe-S / Co-S / Ni-S, AND) →
  entry codes (MAGNDATA has no GET listing; search.php POST is the only element query).
- **Harvest:** 47 experimental magnetic structures fetched (.mcif) + converted via the
  new `import-magndata` importer (0 errors). FM/AFM/ferri from the magCIF's own magnetic
  symmetry operations (axial-vector projector). State distribution: AFM-G 28, ferri 10, FM 9.
- **Cross-check:** experimental ordering (MAGNDATA) vs computed ground-state ordering (MP),
  by formula, for the 21 entries whose formula parsed + has an MP entry.

## Headline (finding #9 — confirmed against EXPERIMENT)
- **CuFeS₂ (chalcopyrite), MAGNDATA 0.802 = AFM-G, BNS I-42̄d** (Fe antiparallel along c,
  ~3.85 μB — classic neutron result) **vs MP mp-3497 = FM**. This is a SAME-STRUCTURE
  mismatch (mp-3497 is the I-4̄2d chalcopyrite): MP's computed collinear ground state is
  ferromagnetic where experiment is antiferromagnetic. The MP-pivot's caveat is real.
- **NiS₂ (vaesite) Pa-3̄ = AFM-G** experimentally (matches the sg205 MP AFM from Phase 0).
- **Co₃Sn₂S₂ = FM** experiment ↔ MP FM (agree) — the known ferromagnetic Weyl semimetal.

## Aggregate
14 of 21 formula-matched cases disagree between experiment and MP computed ground state;
MP systematically tends to **FM** where experiment is AFM/ferri (CoSO₄, LiFe(SO₄)₂,
Tl₃Fe₂S₄, BaCoSO, Co₁Nb₃S₆, …).

⚠️ **Honest caveat — 14/21 is an UPPER BOUND.** MP "ground state" was picked as the
lowest-`energy_above_hull` entry for the formula WITHOUT space-group matching, so some
mismatches compare different polymorphs (e.g. NiS₂: the formula-GS MP pick is a non-magnetic
polymorph, although MP's sg205 vaesite is AFM and agrees). The rigorous rate needs
space-group-matched comparison (TODO). The clean same-structure case (CuFeS₂ I-4̄2d) is a
true mismatch and is sufficient to establish the point.

## Why this matters for the paper
- The experimental anchor (MAGNDATA) is **necessary**: validating/calibrating the magnetic
  gates against MP-computed ordering ALONE would be unreliable — computed magnetic ground
  states disagree with experiment frequently (even MP's curated set). MAGNDATA gives the
  independent experimental truth that breaks the circularity.
- `import-magndata` reproduces known experimental orderings (CuFeS₂ AFM, Co₃Sn₂S₂ FM,
  NiS₂ AFM) from the magCIF symmetry alone — the importer is validated at scale (47 entries).

## Minor gaps observed
- 13/47 mcifs parsed formula="Unknown" (the `_chemical_formula_sum` tag absent/variant in
  some entries) → parser robustness TODO (fall back to summing `_atom_site_type_symbol`).
- FM vs ferri boundary is by moment-spread heuristic (Fe₃S₄ greigite called FM; MP/expt = ferri).
- Cross-check should be space-group-matched for a rigorous experiment-vs-computed disagreement rate.
