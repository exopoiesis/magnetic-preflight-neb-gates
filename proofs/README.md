# Machine-checked core of the pre-flight gates (Lean 4 / mathlib)

`PreflightGates.lean` formalizes the algebraic, combinatorial, and order-theoretic core of the four
pre-flight gate families. It compiles with **0 errors, 0 warnings, no `sorry`**; the axiom audit
(`#print axioms`) shows every one of the **20 theorems/lemmas** depends only on the standard
`[propext, Classical.choice, Quot.sound]` (`vacancy_preserves_parity` on `[propext, Quot.sound]`) —
`sorryAx` is absent.

**Scope (honest boundary).** The proofs certify the *logic* of the gate rules under explicitly
stated hypotheses. They do **not** certify the empirical confusion-matrix numbers (those are data),
the bimodality of the actual Materials-Project moment distribution (a hypothesis the §2 theorems are
conditional on), or any DFT result. The physical hypotheses A1–A3 (below) are taken as given. The
theorem statements are written to match the *code* of each gate in
[Prodromos](https://github.com/exopoiesis/prodromos), so the proofs cover the operator that actually
runs, not an idealized caricature.

## Physical hypotheses (given, not proved)

- **A1 (spin–statistics as a parity identity).** `M_total = n_up − n_down` has the same parity as
  `N_e = n_up + n_down` (difference `2·n_down`). Formalized as the parity identity; no notion of total
  spin is needed.
- **A2 (open shell).** A collinear local-moment magnetic ground state implies an open-shell TM is
  present — not universal (defect-induced moments, itinerant/Pauli paramagnets), so the parity
  false-negative argument that rests on A2 is kept pen-and-paper, not machine-checked.
- **A3 (compensated swap).** An AFM sublattice swap preserves per-site `|m|`; exact only for
  symmetry-equivalent sublattices (e.g. troilite). The "scalars are blind" theorem is therefore read
  as "there exists a realizable compensated swap invisible to the scalar gates".

## Theorems

### 1 — electron-parity gate
| Lean name | statement |
|---|---|
| `parity_valence_invariant` | even per-species valence shift (semicore vs valence-only PP) preserves `N_e mod 2` |
| `vacancy_preserves_parity` | removing an even-valence cation preserves parity |
| `proton_flips_parity` | adsorbing one H (`Z=1`) flips parity |
| `defect_flips_parity` | the `V_cation+H` defect flips parity relative to the host (ZnS V_Zn+H) |
| `fixed_occ_odd_forces_moment` | **at fixed occupations** `Odd N_e ⇒ \|M_total\| ≥ 1`: `nspin=1` (S=0) is impossible |

### 2 — `spin_collapse` cascade as a separated threshold classifier
Separation hypothesis (H-sep): `sup_NM mbar < inf_MAG mbar`, i.e. `∃ a<b` with NM `≤ a`, MAG `≥ b`.
| Lean name | statement |
|---|---|
| `cascade_window_invariant` | under separation, the verdict is identical for any cutoff in `(a, b]` (the structural reason for the threshold window) |
| `cascade_no_false_positive` | `t∈(a,b]` ⇒ no NM over-flagged (FP=0) — with the circularity caveat below |
| `cascade_no_false_negative_above` | `t≤b` ⇒ every magnet with `mbar≥b` flagged |
| `collapsed_count_mono` | collapsed count is monotone in the cutoff (ROC plateau) |
| `no_threshold_if_overlap` | overlap ⇒ no cutoff classifies both correctly (converse: invariant window ⟺ separation) |
| `separation_robust` | gap `> 2ε` ⇒ separation survives moment noise `\|δ\| < ε` |
| `cascade_refines_parity` | the cascade strictly refines parity-alone (the FP→0 reclassification) |

> **Circularity caveat** (also in the proof docstring): on the Materials-Project corpus the label
> `NM` is *defined* from the same computed moment that feeds the gate, so (H-sep) holds tautologically
> and `cascade_no_false_positive` does **not** evidence predictive specificity — the independent check
> is the experimental MAGNDATA anchor.

### 3 — endpoint vs band gate: L¹/L∞ non-redundancy
| Lean name | statement |
|---|---|
| `telescoping_endpoint_le` | `\|M(n)−M(0)\| ≤ Σ adjacent jumps` |
| `layered_endpoint_needed` | band-GO ⊬ endpoint-GO (two-channel witness; real troilite 0.52 µB drift, M_total≡0) |
| `layered_band_needed` | endpoint-GO ⊬ band-GO (sheet crossing with return) — together: the two gates are mutually non-dominating |
| `relative_drift_below` | a diffuse drift `D≤t` over `N_mag≥1` atoms gives per-atom `D/N_mag ≤ t` |
| `coherent_shift_flagged` | a coherent same-sign sublattice change still exceeds the per-atom criterion |

### 4 — sign-vector gate: scalars blind, S not
| Lean name | statement |
|---|---|
| `scalars_blind_to_balanced_swap` | a balanced AFM swap leaves **both** `M_abs` and `M_total` invariant |
| `signvector_detects_swap` | one above-noise sign flip ⇒ `S < 1` (S detects what the scalars cannot) |
| `signvector_bounds` | `S ∈ [−1, 1]` |

`scalars_blind_to_balanced_swap` + `signvector_detects_swap` together prove the sign-vector gate is
*necessary*: the scalar gates provably cannot see a compensated AFM swap, and the per-site
sign-vector provably can.

## Reproduction

Verified with Lean 4 + mathlib (prebuilt `mathlib` oleans via `lake exe cache get`). With a
`lake`-configured mathlib project on PATH:

```bash
lake env lean PreflightGates.lean
# Expected: no output other than the #print axioms block at the end of the file:
#   20 lines "... depends on axioms: [propext, Classical.choice, Quot.sound]"
#   (vacancy_preserves_parity: [propext, Quot.sound]); no `sorryAx`.
```

### mathlib gotchas (for re-verification against a moving mathlib)
- `Int.ModEq.comm` and `Int.even_iff_not_odd` do not exist — build the `ModEq` from divisibility via
  `Int.modEq_iff_dvd` + `dvd_neg`; use `Int.odd_iff` + `norm_num` for `¬ Odd 0`.
- `Finset.filter_subset_filter` fixes the *predicate* — prove the subset by hand for a monotone predicate.
- a `def` using `<` on `ℝ` must be `noncomputable` (`Real.decidableLT`).
