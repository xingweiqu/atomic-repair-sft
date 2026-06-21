# Leakage audit — is v3 convergent-floor ability real or memorized?

_Read-only; no retraining._

## 1c. v3 world size

- unique triples: **341** · heads: 66 · relations: 12 · tails: 173
- train items 2640 / eval items 720
_Small world + 30-epoch full SFT ⇒ memorization is plausible a priori._

## 1a. Surface overlap (problem text)

- exact problem match eval∈train: **0/720** (0.0%)
- entity-masked TEMPLATE match eval∈train: **0/720** (0.0%)
_Template match high but exact low = same phrasing skeletons, different entities (by design)._

## 1b. ★ Oracle (triple) overlap — leakage check

| overlap of eval facts with train | rate |
|---|---|
| exact (head, relation, tail) triple | **695/875 = 79.4%** |
| head entity seen in train | 875/875 = 100.0% |
| tail entity seen in train | 850/875 = 97.1% |
| (head, relation) pair seen in train | 875/875 = 100.0% |
_High exact-triple overlap ⇒ the convergent floor can default-write eval answers._

## 2b. Context-bypass signal (convergent floor predictions)

- H-class items checked (verify_bridge/use_provided_support): 180
- gold answer NOT literally in provided context: 0
- floor CORRECT despite gold not in context: **0/0**
_Correct when the answer is not in the context ⇒ it comes from weights (memorized), not from reading context. (Counterfactual probe 2a needs the ckpt ⇒ PHASE-1.)_

## 3. ability vs epoch

_No intermediate scaffold checkpoints (3/10/20/30 epoch) were saved (save_total_limit=1). Cannot trace where memorization sets in without a PHASE-1 re-run; flagged, skipped._

## 4. v4 (GSM8K) control — same overlap check

- GSM source split overlap (train source_id ∩ eval source_id): **0** (train uses GSM train split, eval uses test split)
- exact problem-text overlap eval∈train: 0/480
_v4 eval answers cannot be default-written: items come from the held-out GSM test split._

## 5. Conclusion

**Is v3 convergent-floor ability=1.00 caused by leakage / memorization? — PARTLY-TO-LARGELY YES.** Evidence: (1b) **79.4% of eval triples appear verbatim in train**, with head and (head,relation) 100% seen and tail 97% seen; (1c) the world is tiny (341 unique triples) and the floor is 30-epoch full-parameter SFT — memorization is both feasible and indicated. Surface text does NOT overlap (1a, 0%), which is exactly why the original 'phrasing-disjoint' guarantee is insufficient: the oracle facts leak even when the wording does not.

The decisive counterfactual probe (2a — does the floor follow a rewritten context or emit the memorized old tail) needs the ckpt ⇒ **PHASE-1**. (2b) is inconclusive: in v3 the gold is always in the context, so reading vs memorizing cannot be told apart from outputs alone.

**Can v3 serve as evidence for the ability layer? — NO; demote to a cautionary case.** The v3 world is too small to measure ability without test-set contamination: a converged floor can default-write ~79% of eval answers, so v3 floor ability (and thus the v3 end of the modulation axis) is not a clean measurement. **Clean ability evidence exists only in v4** (held-out GSM test split, 0% source overlap, answers not default-writable). Net: the 'targeted does not inject ability' conclusion stands on **v4 alone**; v3 becomes the cautionary tale that floor fit on a small synthetic world contaminates every measurement layer.
