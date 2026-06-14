import Mathlib

/-!
# Machine-checked core of the Prodromos magnetic pre-flight gates (MagNEB_Preflight)

Formalizes the algebraic / combinatorial / order-theoretic core of the four pre-flight
gates of `paper/MagNEB_Preflight/manuscript.md` (§4.5, §4.6, §6, §7.1, §7.5), with the
consilium-corrected statements (mathematician + physicist + statmech, 2026-06-14; see
`paper/MagNEB_Preflight/THEOREM_SPEC_preflight_gates.md` §CONSILIUM v2).

Four architectural claims of the paper become theorems:
* **parity robustness** (T1): the electron-parity gate keys only on `N_e mod 2`, so it is
  invariant to the pseudopotential valence convention, a vacancy preserves parity, an
  adsorbed H flips it, and an odd-electron cell cannot run fixed-occupation `nspin=1`.
* **structural reason for the threshold window** (T2): a separated (bimodal) moment
  distribution makes the cascade verdict invariant on `(sup_NM, inf_MAG]`, monotone in the
  cutoff (ROC plateau), and robust to SCF noise; overlap makes an error unavoidable.
* **layered non-redundancy** (T4): the end-to-end ΔM drift (endpoint gate) and the max
  adjacent jump (band gate) are L¹/L∞ statistics of the same increment vector — neither
  dominates the other (two witnesses), so both layers are needed.
* **necessity of the sign-vector gate** (T5): a balanced AFM sublattice swap is provably
  invisible to both scalar gates (ΔM_abs, ΔM_total) yet detected by the per-site
  sign-vector overlap S.

Honest boundary (NOT formalized — see VERIFICATION_REPORT): empirical confusion-matrix
numbers, the bimodality of the *actual* MP distribution, the physical axioms A1/A2/A3, DFT
barriers; T3 (parity FN=0) is a pen-and-paper syllogism (diverges from the code's d⁰/d¹⁰
override) — its unconditional half is subsumed by T1.
-/

namespace ProdromosGates

open Finset

/-! ## T1 — electron-parity gate (§4.5). Integers throughout (avoids ℕ truncation). -/

/-- **T1a — parity is invariant to the valence convention.** If two valence tables `Z, Z'`
differ by an even amount on every species (semicore vs valence-only pseudopotentials shift
`Z` by an even number) and the cell charge `q` is common, the two electron counts have the
same parity. (Manuscript §4.5: "robust to the absolute valence convention".) -/
theorem parity_valence_invariant {ι : Type*} (s : Finset ι) (n Z Z' : ι → ℤ) (q : ℤ)
    (h : ∀ i ∈ s, Even (Z i - Z' i)) :
    Int.ModEq 2 ((∑ i ∈ s, Z i * n i) - q) ((∑ i ∈ s, Z' i * n i) - q) := by
  have hdvd : (2 : ℤ) ∣ ((∑ i ∈ s, Z i * n i) - (∑ i ∈ s, Z' i * n i)) := by
    rw [← Finset.sum_sub_distrib]
    refine Finset.dvd_sum ?_
    intro i hi
    have : (2 : ℤ) ∣ (Z i - Z' i) := (h i hi).two_dvd
    have hfac : Z i * n i - Z' i * n i = (Z i - Z' i) * n i := by ring
    rw [hfac]
    exact this.mul_right _
  -- a ≡ b [ZMOD 2] ↔ 2 ∣ b - a; here b - a = (∑Z'·n - q) - (∑Z·n - q) = ∑Z'·n - ∑Z·n
  rw [Int.modEq_iff_dvd]
  have hrw : (((∑ i ∈ s, Z' i * n i) - q) - ((∑ i ∈ s, Z i * n i) - q))
        = -((∑ i ∈ s, Z i * n i) - (∑ i ∈ s, Z' i * n i)) := by ring
  rw [hrw]
  exact (dvd_neg).mpr hdvd

/-- **T1e (vacancy) — removing an even-valence cation preserves parity.** A metal vacancy
keeps `N_e mod 2` (manuscript §4.5: "a metal vacancy keeps parity"). -/
theorem vacancy_preserves_parity (Ne z : ℤ) (hz : Even z) :
    Int.ModEq 2 (Ne - z) Ne := by
  have : (2 : ℤ) ∣ (Ne - (Ne - z)) := by simpa using hz.two_dvd
  exact (Int.modEq_iff_dvd).mpr this

/-- **T1e (proton) — adsorbing one H flips parity.** `Z(H) = 1`, so `N_e + 1` has the
opposite parity to `N_e` (manuscript §4.5: "an adsorbed H FLIPS it"). -/
theorem proton_flips_parity (Ne : ℤ) : ¬ Int.ModEq 2 (Ne + 1) Ne := by
  intro hmod
  have h2 : (2 : ℤ) ∣ (Ne - (Ne + 1)) := (Int.modEq_iff_dvd).mp hmod
  have he : Ne - (Ne + 1) = -1 := by ring
  rw [he] at h2
  have h1 : (2 : ℤ) ∣ 1 := (dvd_neg).mp h2
  norm_num at h1

/-- **T1b — the V_cation + H defect flips parity** (ZnS V_Zn+H, §6/§4.5): with an even
cation valence, `N_e(defect) = N_e(host) − Z_cation + 1` has the opposite parity to the
host. Combines the vacancy and proton lemmas. -/
theorem defect_flips_parity (Ne z : ℤ) (hz : Even z) :
    ¬ Int.ModEq 2 (Ne - z + 1) Ne := by
  intro hmod
  -- Ne - z + 1 ≡ Ne; but Ne - z ≡ Ne (vacancy), so Ne + 1 ≡ Ne — contradiction.
  have hvac : Int.ModEq 2 (Ne - z) Ne := vacancy_preserves_parity Ne z hz
  have hstep : Int.ModEq 2 (Ne - z + 1) (Ne + 1) := hvac.add_right 1
  have : Int.ModEq 2 (Ne + 1) Ne := hstep.symm.trans hmod
  exact proton_flips_parity Ne this

/-- **T1d — fixed-occupation parity forces a moment** (§4.5 `electron_parity` pseudocode,
restricted to FIXED occupations per the consilium fix). The collinear total magnetization
`M_total = nelup − neldwn` has the same parity as `N_e = nelup + neldwn` (axiom A1 as a
parity identity). Hence an ODD electron count forces `M_total ≠ 0` and `|M_total| ≥ 1`:
`nspin=1` (which fixes `M_total = 0`, i.e. `S = 0`) is impossible. (The metallic-smearing
branch — `electron_parity_gate.py` `_vacancy_odd_ok` → NSPIN1_OK — is OUTSIDE this theorem:
with smearing `M_total` is no longer integer.) -/
theorem fixed_occ_odd_forces_moment (nelup neldwn : ℤ)
    (hodd : Odd (nelup + neldwn)) :
    (nelup - neldwn ≠ 0) ∧ (1 ≤ |nelup - neldwn|) := by
  -- A1: (nelup+neldwn) − (nelup−neldwn) = 2*neldwn is even ⇒ same parity ⇒ M_total odd.
  have hModd : Odd (nelup - neldwn) := by
    have hb : (nelup + neldwn) - (nelup - neldwn) = 2 * neldwn := by ring
    have : Odd ((nelup + neldwn) - 2 * neldwn) := hodd.sub_even (even_two_mul neldwn)
    have heq : (nelup + neldwn) - 2 * neldwn = nelup - neldwn := by ring
    rwa [heq] at this
  have hne : nelup - neldwn ≠ 0 := by
    rintro h0
    rw [h0, Int.odd_iff] at hModd
    norm_num at hModd
  exact ⟨hne, Int.one_le_abs hne⟩

/-! ## T2 — `spin_collapse` cascade as a separated threshold classifier (§7.1, §7.5).

Corpus = a function `mbar : ι → ℝ` (per-TM moment) with a label `isMag : ι → Prop`. The
gate at cutoff `t`: `mbar x < t ⇒ NSPIN1 (collapsed)`, else `NSPIN2`. Separation hypothesis
(H-sep, the structural form of bimodality): `∀ NM, mbar ≤ a;  ∀ MAG, b ≤ mbar; a < b`. -/

section Cascade
variable {ι : Type*} (a b : ℝ) (mbar : ι → ℝ) (isMag : ι → Prop)

/-- **T2a — window invariance.** Under separation `a < b`, for ANY two cutoffs in the
half-open window `(a, b]` the gate gives the identical per-structure verdict. This is the
structural reason for the empirical "6× insensitivity window" (§7.5): the verdict, hence
the whole confusion matrix, is constant on `(a, b]`. The window is half-open because the
gate uses a STRICT comparator `mbar < t` (`spin_collapse_verdict.py:98`). -/
theorem cascade_window_invariant {t t' : ℝ}
    (ht : a < t ∧ t ≤ b) (ht' : a < t' ∧ t' ≤ b)
    (hNM : ∀ x, ¬ isMag x → mbar x ≤ a)
    (hMAG : ∀ x, isMag x → b ≤ mbar x) :
    ∀ x, (mbar x < t) ↔ (mbar x < t') := by
  intro x
  by_cases hx : isMag x
  · have hbm : b ≤ mbar x := hMAG x hx
    constructor
    · intro h; exact absurd (lt_of_lt_of_le h (le_trans ht.2 hbm)) (lt_irrefl _)
    · intro h; exact absurd (lt_of_lt_of_le h (le_trans ht'.2 hbm)) (lt_irrefl _)
  · have ham : mbar x ≤ a := hNM x hx
    constructor
    · intro _; exact lt_of_le_of_lt ham ht'.1
    · intro _; exact lt_of_le_of_lt ham ht.1

/-- **T2b — no false positives (under TRUE separation).** For `t ∈ (a, b]` no non-magnetic
structure is over-flagged: every NM is correctly collapsed. ⚠ Circularity caveat (statmech,
§7.2): on the Materials-Project corpus the label `NM` is *defined* from the same computed
moment that feeds `mbar`, so (H-sep) holds tautologically and this does NOT evidence
predictive specificity — the independent check is the experimental MAGNDATA anchor (§7.2). -/
theorem cascade_no_false_positive {t : ℝ} (ht : a < t)
    (hNM : ∀ x, ¬ isMag x → mbar x ≤ a) :
    ∀ x, ¬ isMag x → mbar x < t :=
  fun x hx => lt_of_le_of_lt (hNM x hx) ht

/-- **T2c — every magnet WITH a moment is flagged.** For `t ≤ b` any magnetic structure
with `mbar ≥ b` is routed NSPIN2. The cascade's false negatives are exactly the separate
zero-moment class (MP `magmoms` data-gap), which a single scalar `mbar` cannot distinguish
from a genuine NM collapse — that is a data limitation, not a threshold error (consilium
fix: the code returns NSPIN1_OK on a zero array, it does not route to REVIEW). -/
theorem cascade_no_false_negative_above {t : ℝ} (ht : t ≤ b)
    (hMAG : ∀ x, isMag x → b ≤ mbar x) :
    ∀ x, isMag x → ¬ (mbar x < t) :=
  fun x hx => not_lt.mpr (le_trans ht (hMAG x hx))

/-- **T2d — monotonicity of the collapsed set (ROC structure).** The collapsed count is
non-decreasing in the cutoff `t` (raising the cutoff can only pass more structures as
"non-magnetic"). Dually the flagged count is non-increasing. This single monotonicity is
the structural reason behind the §7.5 plateau: specificity saturates above `a`, sensitivity
starts dropping above `b`, and the invariant plateau is their intersection `(a, b]`. -/
theorem collapsed_count_mono (s : Finset ι) {t t' : ℝ} (h : t ≤ t') :
    (s.filter (fun x => mbar x < t)).card ≤ (s.filter (fun x => mbar x < t')).card := by
  apply Finset.card_le_card
  intro x hx
  rw [Finset.mem_filter] at hx ⊢
  exact ⟨hx.1, lt_of_lt_of_le hx.2 h⟩

/-- **T2e — overlap makes an error unavoidable (converse of separation).** If a
non-magnetic structure's moment is not strictly below a magnetic structure's
(`mbar(mag) ≤ mbar(nm)`, an overlap / no gap), then NO single cutoff classifies both
correctly. Combined with T2a this characterizes the invariant window: it is non-empty iff
the populations are separated. -/
theorem no_threshold_if_overlap {mnm mmag : ℝ} (h : mmag ≤ mnm) :
    ¬ ∃ t, mnm < t ∧ ¬ (mmag < t) := by
  rintro ⟨t, h1, h2⟩
  exact absurd (lt_of_le_of_lt (le_trans (not_lt.mp h2) h) h1) (lt_irrefl t)

/-- **T2f — separation is robust to SCF noise.** If the bimodal gap exceeds twice the
moment-noise amplitude (`2ε < b − a`), then perturbing every moment by `|δ| < ε` preserves
separation (with shrunk thresholds `a+ε < b−ε`), so the verdict is noise-invariant — the
formal content of "robust to SCF noise" (`spin_collapse_verdict.py` docstring; §7.5
`<0.1 µB residue` vs the `0.30` cutoff). -/
theorem separation_robust {ε : ℝ} (hgap : 2 * ε < b - a)
    (δ : ι → ℝ) (hδ : ∀ x, |δ x| < ε)
    (hNM : ∀ x, ¬ isMag x → mbar x ≤ a)
    (hMAG : ∀ x, isMag x → b ≤ mbar x) :
    (a + ε < b - ε) ∧
    (∀ x, ¬ isMag x → mbar x + δ x ≤ a + ε) ∧
    (∀ x, isMag x → b - ε ≤ mbar x + δ x) := by
  refine ⟨by linarith, ?_, ?_⟩
  · intro x hx
    have : δ x < ε := lt_of_le_of_lt (le_abs_self _) (hδ x)
    have := hNM x hx; linarith
  · intro x hx
    have : -ε < δ x := by
      have := (abs_lt.mp (hδ x)).1; linarith
    have := hMAG x hx; linarith

end Cascade

/-- nspin recommendation of a gate. -/
inductive Verdict | nspin1 | nspin2
deriving DecidableEq

/-- parity-alone screen: flags `nspin2` whenever the cell is odd-electron or open-shell. -/
def parityGate (flag : Bool) : Verdict := if flag then .nspin2 else .nspin1

/-- the cascade: a parity flag is *cleared* to `nspin1` when the moment collapses
(`mbar < t`); otherwise `nspin2`. A cell parity does not flag is `nspin1` directly. -/
noncomputable def cascadeGate (flag : Bool) (mbar t : ℝ) : Verdict :=
  if flag then (if mbar < t then .nspin1 else .nspin2) else .nspin1

/-- **Cascade funnel / refinement (§7.1, cascade ≠ parity-alone).** The cascade returns
`nspin1` on a parity-flagged cell exactly when the moment collapses, so it is a *strict*
refinement of parity-alone: a cell that parity flags (`parityGate true = nspin2`) but whose
moment collapses is cleared by the cascade (`cascadeGate true 0 0.3 = nspin1`). This is the
FP 67→0 reclassification of §7.1, structurally — adding `spin_collapse` cannot create a
false negative on a collapsed cell, only remove a parity false positive. -/
theorem cascade_refines_parity :
    parityGate true = Verdict.nspin2 ∧ cascadeGate true 0 0.3 = Verdict.nspin1 := by
  refine ⟨rfl, ?_⟩
  unfold cascadeGate
  norm_num

/-! ## T4 — endpoint vs band gate: L¹/L∞ non-redundancy (§4.5, §6 troilite).

Band `M : ℕ → ℝ` (per-image absolute magnetization). Adjacent jumps `|M(i+1) − M(i)|`.
endpoint gate flags on `|M(N) − M(0)|` (end-to-end); band gate flags on `max_i |M(i+1)−M(i)|`
(L∞) plus an `M_total` endpoint split. -/

/-- **T4a — telescoping bound (endpoint ≤ Σ adjacent ≤ (N)·max).** The end-to-end drift is
bounded by the sum, hence by the count times the max adjacent jump — the L¹/L∞ link of the
increment vector. -/
theorem telescoping_endpoint_le (M : ℕ → ℝ) (n : ℕ) :
    |M n - M 0| ≤ ∑ i ∈ Finset.range n, |M (i + 1) - M i| := by
  have htel : M n - M 0 = ∑ i ∈ Finset.range n, (M (i + 1) - M i) := by
    rw [Finset.sum_range_sub]
  rw [htel]
  exact Finset.abs_sum_le_sum_abs _ _

/-- A 3-image band `[c0, c1, c2]` as a function on `ℕ` (indices ≥ 2 read `c2`). -/
def band3 (c0 c1 c2 : ℝ) : ℕ → ℝ := fun i => if i = 0 then c0 else if i = 1 then c1 else c2

/-- **T4b — band-GO does NOT imply endpoint-GO (endpoint gate is needed).** A monotone
drift through small adjacent steps with zero net moment: the band gate passes (every
adjacent `|ΔM_abs| < 0.5` AND the `M_total` endpoint split is 0 < 0.3 — both band triggers
clear, the consilium 2-channel fix), yet the endpoint gate flags (`|ΔM_abs| = 0.52 > 0.5`).
Real troilite numbers (§6: 0.52 µB end-to-end, largest adjacent ≈ 0.13). -/
theorem layered_endpoint_needed :
    ∃ (Mabs Mtot : ℕ → ℝ),
      (∀ i ∈ Finset.range 2, |Mabs (i + 1) - Mabs i| < (0.5 : ℝ)) ∧   -- band: no adjacent jump
      (|Mtot 2 - Mtot 0| < (0.3 : ℝ)) ∧                               -- band: no M_total split
      ((0.5 : ℝ) < |Mabs 2 - Mabs 0|) := by                           -- endpoint: flags
  refine ⟨band3 0 0.26 0.52, fun _ => 0, ?_, ?_, ?_⟩
  · intro i hi
    rw [Finset.mem_range] at hi
    interval_cases i <;> norm_num [band3]
  · norm_num
  · norm_num [band3]

/-- **T4b′ — band-GO is NOT implied by endpoint-GO (band gate is needed).** A sheet crossing
inside the band that returns to the original sheet by the end: small net drift (endpoint
gate passes, `|ΔM_abs| = 0.05 < 0.5`) but a large single adjacent jump (band gate flags,
`0.6 > 0.5`). Together with T4b this proves the two gates are mutually non-dominating
(L¹/L∞ duality) — both layers are genuinely needed, not redundant. -/
theorem layered_band_needed :
    ∃ (Mabs : ℕ → ℝ),
      (|Mabs 2 - Mabs 0| < (0.5 : ℝ)) ∧                                  -- endpoint: GO
      (∃ i ∈ Finset.range 2, (0.5 : ℝ) < |Mabs (i + 1) - Mabs i|) := by   -- band: flags
  refine ⟨band3 0 0.6 0.05, ?_, ?_⟩
  · norm_num [band3]
  · refine ⟨0, ?_, ?_⟩
    · simp
    · norm_num [band3]

/-- **T4c (drift) — the relative endpoint criterion declines a diffuse drift.** A net drift
`D` spread over `N_mag ≥ 1` atoms gives per-atom `D / N_mag ≤ D`, so if the absolute
end-to-end drift is itself below threshold the per-atom value is too (troilite:
0.52/12 = 0.043 µB/Fe → GO). On `M_abs` (magnitudes), as the consilium required. -/
theorem relative_drift_below (D t Nmag : ℝ) (hD : 0 ≤ D) (hN : 1 ≤ Nmag) (hDt : D ≤ t) :
    D / Nmag ≤ t :=
  le_trans (div_le_self hD hN) hDt

/-- **T4c (coherent) — a coherent sublattice-wide change still exceeds the criterion.** If
every one of `s` magnetic moments shifts by `≥ μ` in the SAME direction (a genuine
single-sublattice rotation, not a sign-balanced swap), the signed net change `ΔM_total` is
at least `(#s)·μ`, so the per-atom value is `≥ μ`; for `μ > t` it is still flagged. On
`M_total` (signed), with the same-sign hypothesis the consilium required — the `|ΔM_abs|`
form is false (a sign change collapses `|m|`). -/
theorem coherent_shift_flagged {ι : Type*} (s : Finset ι) (δ : ι → ℝ) (μ : ℝ)
    (hcoh : ∀ i ∈ s, μ ≤ δ i) :
    (s.card : ℝ) * μ ≤ ∑ i ∈ s, δ i := by
  have h := Finset.sum_le_sum hcoh
  rw [Finset.sum_const, nsmul_eq_mul] at h
  exact h

/-! ## T5 — sign-vector gate: scalars are blind to a balanced AFM swap, S is not (§4.6, §9v).

Per-site moments over magnetic sites `s` (migrant excluded). A balanced swap negates a
subset of signs at constant `|m|`: modelled by `mB i = σ i · mA i` with `σ i ∈ {1, −1}`. -/

section SignVector
variable {ι : Type*} (s : Finset ι) (mA σ : ι → ℝ)

/-- **T5a — both scalar gates are blind to a balanced swap.** Under `σ i ∈ {±1}` and the
balance condition `∑ (1 − σ_i) m^A_i = 0` (compensated up/down flip):
* `M_abs` is invariant (`|σ_i m^A_i| = |m^A_i|` site-wise, since `|σ_i| = 1`);
* `M_total` is invariant (the flip contributes `−∑(1−σ_i)m^A_i = 0`).
So neither `ΔM_abs` nor `ΔM_total` can see the swap — the §4.6 "blind by construction" made
a theorem. (Exact `|m|`-preservation is the idealization A3 — measure zero in general,
exact for symmetry-equivalent AFM sublattices, e.g. troilite.) -/
theorem scalars_blind_to_balanced_swap
    (hσ : ∀ i ∈ s, σ i = 1 ∨ σ i = -1)
    (hbal : ∑ i ∈ s, (1 - σ i) * mA i = 0) :
    (∑ i ∈ s, |σ i * mA i| = ∑ i ∈ s, |mA i|) ∧
    (∑ i ∈ s, σ i * mA i = ∑ i ∈ s, mA i) := by
  constructor
  · apply Finset.sum_congr rfl
    intro i hi
    rcases hσ i hi with h | h <;> rw [h] <;> simp
  · have hsplit : ∑ i ∈ s, (1 - σ i) * mA i
        = (∑ i ∈ s, mA i) - (∑ i ∈ s, σ i * mA i) := by
      rw [← Finset.sum_sub_distrib]
      apply Finset.sum_congr rfl
      intro i _; ring
    rw [hsplit] at hbal
    linarith [hbal]

/-- **T5b — the sign-vector overlap detects the swap (implication form).** Model the per-site
contribution `c i = s(m^A_i)·s(m^B_i) ∈ {−1,0,1}` (above-noise sites vote ±1, sub-noise vote
0; `s(m)=0` if `|m|<m0`). If at least one above-noise site flipped sign (`c i₀ = −1`, with
the noise floor checked on BOTH endpoints per the consilium fix) and `s` is non-empty, then
`S = (∑ c)/#s < 1`. So S flags NO-GO exactly where T5a proved the scalars blind. (The ⟺
form is false — sub-noise sites vote 0 and dilute S below 1 without any flip — so this is an
implication, which is all the "S is necessary" claim needs.) -/
theorem signvector_detects_swap (c : ι → ℝ)
    (hc : ∀ i ∈ s, c i ≤ 1) (i₀ : ι) (hi₀ : i₀ ∈ s) (hflip : c i₀ = -1)
    (hcard : 0 < s.card) :
    (∑ i ∈ s, c i) / (s.card : ℝ) < 1 := by
  have hsum : (∑ i ∈ s, c i) < (s.card : ℝ) := by
    have hlt : (∑ i ∈ s, c i) < ∑ _i ∈ s, (1 : ℝ) := by
      apply Finset.sum_lt_sum hc
      exact ⟨i₀, hi₀, by rw [hflip]; norm_num⟩
    simpa using hlt
  have hcpos : (0 : ℝ) < (s.card : ℝ) := by exact_mod_cast hcard
  rw [div_lt_one hcpos]
  exact hsum

/-- **T5c — the sign-vector overlap is bounded `S ∈ [−1, 1]`.** Each contribution lies in
`[−1, 1]`, so the mean does (`#s > 0`). -/
theorem signvector_bounds (c : ι → ℝ)
    (hc1 : ∀ i ∈ s, -1 ≤ c i) (hc2 : ∀ i ∈ s, c i ≤ 1) (hcard : 0 < s.card) :
    -1 ≤ (∑ i ∈ s, c i) / (s.card : ℝ) ∧ (∑ i ∈ s, c i) / (s.card : ℝ) ≤ 1 := by
  have hcpos : (0 : ℝ) < (s.card : ℝ) := by exact_mod_cast hcard
  have hup : (∑ i ∈ s, c i) ≤ (s.card : ℝ) := by
    have := Finset.sum_le_sum hc2
    simpa using this
  have hlo : -(s.card : ℝ) ≤ (∑ i ∈ s, c i) := by
    have := Finset.sum_le_sum hc1
    simp only [Finset.sum_const, nsmul_eq_mul, mul_neg, mul_one] at this
    linarith [this]
  constructor
  · rw [le_div_iff₀ hcpos]; linarith
  · rw [div_le_one hcpos]; exact hup

end SignVector

/-! ## Axiom audit — confirm every theorem is `sorry`-free (only the standard
`[propext, Classical.choice, Quot.sound]`, never `sorryAx`). -/

#print axioms parity_valence_invariant
#print axioms vacancy_preserves_parity
#print axioms proton_flips_parity
#print axioms defect_flips_parity
#print axioms fixed_occ_odd_forces_moment
#print axioms cascade_window_invariant
#print axioms cascade_no_false_positive
#print axioms cascade_no_false_negative_above
#print axioms collapsed_count_mono
#print axioms no_threshold_if_overlap
#print axioms separation_robust
#print axioms cascade_refines_parity
#print axioms telescoping_endpoint_le
#print axioms layered_endpoint_needed
#print axioms layered_band_needed
#print axioms relative_drift_below
#print axioms coherent_shift_flagged
#print axioms scalars_blind_to_balanced_swap
#print axioms signvector_detects_swap
#print axioms signvector_bounds

end ProdromosGates
