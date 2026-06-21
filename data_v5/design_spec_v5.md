# v5-clean — design spec + scale account (STEP 1, awaiting approval before full generation)

Goal: a **leak-proof** synthetic diagnostic domain to replace the oracle-contaminated v3, giving
the v4 conclusions a **second independent clean domain**. Three debts paid by construction:
**not default-writable** (vs v3's 79% triple leak), **moderate ability margin** (vs GSM's ceiling),
**large enough** (vs v3's 341-triple over/under-fit confound).

---

## 1.1 Domain: counterfactual two-hop (v3 H-column structure, all values coined)

Four real relation schemas, **all entity values coined nonsense** (absent from pretraining):

| family | hop-1 | hop-2 | question |
|---|---|---|---|
| book | `{head} was written by {bridge}` | `{bridge} is a citizen of {tail}` | nationality of author of {head}? |
| city | `{head} is located in {bridge}` | `{bridge} officially uses {tail}` | currency of province of {head}? |
| device | `{head} is produced by {bridge}` | `{bridge} primarily sources {tail}` | material sourced by maker of {head}? |
| song | `{head} is performed by {bridge}` | `{bridge} is funded by {tail}` | who funds the ensemble of {head}? |

Facts are given **in context**; the question is two-hop; the base **must read context** (values are
counterfactual, so nothing can be recalled from weights). Coinage = onset+nucleus+coda syllables,
≈1.9×10⁷ distinct 2-syllable words ⇒ the entity pool is effectively unbounded.

## 1.2 ★ Scale account (the anti-double-confound check)

For a clean floor window ("format learned, answers far from memorized") we need the unique-triple
count to dwarf what 30-epoch SFT can default-write, AND eval triples to be holdout.

| | v3 (fatal) | v5 small-sample (verified now) | **v5 full target** |
|---|---|---|---|
| unique triples (train) | 341 (whole world) | 1,600 | **~16,000** |
| eval triples | — | 600 | ~3,200 |
| **eval triple overlap w/ train** | **79.4%** | **0.0%** ✓ | 0.0% (by construction) |
| heads | 66 | 800 | ~8,000 |
| train / eval items | 2,640 / 720 | 800 / 300 | ~8,000 / ~1,600 |

Full target = 2,000 chains/family × 4 = 8,000 train + 400/family × 4 = 1,600 eval; tails 100/family.
**Unique triples ~16,000 — a 47× increase over v3's 341 (>1 order of magnitude).** Coinage pool is
not the bottleneck (1.9e7); we only raise `--*_chains_per_family` and `--tails_per_family`.

## 1.3 Operator mapping (H-column; three distinct response paths) + examples

| policy | injector (cell) | correct path | planted wrong? |
|---|---|---|---|
| use_provided_support | H-Sup: full context | compose two hops | no |
| verify_bridge | H-Bridge: wrong bridge + distractor chain | reject claimed bridge, read true bridge, follow it | yes (wrong tail via distractor) |
| override_wrong_claim | H-Cor: wrong final claim | ignore claim, resolve from context | yes (wrong tail) |
| keep_answer | H-Clean / H-Cor-True (50/50 TRUE claim) | verify, keep | no |
| retrieve_or_abstain | H-Abl: one hop deleted | abstain, no hallucination | n/a (gold null) |

Real samples (from the small-sample generation, counterfactual values):

- **H-Cor** (override): *"Reportedly the answer is **Zillvunr**. What material does the manufacturer of
  Vrunthvian source?"* ctx: Vrunthvian→Maessgliark→**Plitrunrk**. gold=Plitrunrk, planted=Zillvunr.
- **H-Bridge** (verify_bridge): *"It is claimed the ensemble of Rundbror is **Trallvria**. Who funds
  the ensemble performing Rundbror?"* ctx: Rundbror→Diandlelst→**Sarkork**; distractor Trallvria→Zunngdrun.
  gold=Sarkork, planted=Zunngdrun (the trap from following the wrong bridge).
- **H-Cor-True** (keep): *"Reportedly the answer is **Giassdor**. …"* ctx gives Giassdor → keep.
- **H-Sup**: *"Who funds the ensemble performing Pungvun?"* ctx: Pungvun→Glarrbor→Foungnoung.
- **H-Clean** (keep): tentative = true tail.
- **H-Abl** (abstain): hop-2 deleted → unsolvable → null.

resist_wrong is measurable on **H-Cor** and **H-Bridge** (both have a planted wrong tail); these are
the decision-layer cells. ability|resist on those = did it then produce the true tail (pure
context-composition, not memorizable).

## 1.4 Leak-proofing built INTO the generator (not post-hoc)

1. **Global coinage uniqueness:** train and eval share a `used` set ⇒ every head/bridge/tail is
   unique across splits ⇒ eval (head,rel,tail) triples never appear in train (verified 0.0%).
2. **Entity balance:** `TailBalancer` biases planted-false tails toward the least-used-as-false, so
   each tail appears ~50/50 as true vs false value; no single-entity feature predicts the decision.
   (Small-sample median false-share 0.29, capped by the ~33% of items that carry a planted wrong;
   the *spread* across tails is even — the shortcut gate in STEP 2.1 will confirm <0.65.)
3. **Counterfactual = no real-world match:** values are coined; STEP 2.1 will also string-check the
   pool against a real place/person list to be safe.

## Small-sample pre-audit (run now, read-only)

- eval↔train triple overlap **0.0%** (vs v3 79.4%) ✓
- world already 1,600 train triples at small scale; full target ~16,000 ✓
- policy distribution balanced; entity-balance spread even ✓

---

## STEP 2 (after approval): generate full → gate → train → evaluate

- 2.1 full generation, then a **hard gate**: `leakage_audit` (triple overlap ≈0) + shortcut gate
  (TF-IDF masked balanced-acc <0.65). **Audit fails ⇒ no training.**
- 2.2 **floor and targeted trained to EQUAL convergence** (same epochs) — no more 30-vs-3 mismatch.
- 2.3 reuse `decision_analysis.py`: resist_wrong + ability|resist on a **matched-difficulty subset**.
  Key test: if floor ability does NOT shoot to ~1.0 (leak-proof) and targeted Δability ≈ 0 ⇒
  "ability not injected" gets a **second clean domain** (non-GSM). If floor hits ~1.0 again ⇒
  scale still insufficient, return to 1.2.
- 2.4 counterfactual probe (≤30 eval): rewrite a context tail, check floor/targeted follow the new
  context (clean) vs emit the old value (still memorizing).
- 2.5 `comparison_v5_clean.md`: three-layer table + side-by-side with v4 + gate record + probe.

**PAUSED — review the scale account (1.2). Approve and I run STEP 2 generation + the hard gate.**
