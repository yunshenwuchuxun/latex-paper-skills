# Abstract & Conclusion Writing Guide

Rules for writing the abstract and conclusion sections of empirical papers.
These sections are written LAST (after results are available) and must
reflect the actual evidence state, not aspirations.

## 1. Abstract Template

The abstract follows a 5-sentence structure. Maximum 250 words.
No citations. No unexpanded acronyms.

| Sentence | Role | Example pattern |
|----------|------|-----------------|
| 1 | Problem | "<Domain> faces the challenge of <problem>, where <specific difficulty>." |
| 2-3 | Method | "We propose <method name>, a <type> approach that <core mechanism>. Key components include <C1>, <C2>, and optional <C3>." |
| 3-4 | Setting | "We evaluate on <dataset/environment> with <N baselines> under <conditions>." |
| 4-5 | Key result | "Our method achieves <metric: number>, a <X%> improvement over <nearest baseline> (<number>), while maintaining <secondary metric>." |
| 5 | Implication | "These results suggest <practical or scientific takeaway>." |

### Evidence rules for the abstract
- If main results are `verified`: MUST include specific numbers (the most
  compelling finding from the results table).
- If main results are `placeholder`: use "preliminary" or "expected" language
  but still describe the experimental setting concretely.
- If NO results exist: describe the experiment design and state
  "results are forthcoming."
- NEVER fabricate numbers in the abstract.

### Specific-number example
BAD: "Our method improves over baselines."
GOOD: "Our method achieves 0.27% constraint violation rate, reducing
violations by 58% compared to the nearest constrained baseline (0.65%),
while maintaining cost within 0.8% of the MPC optimum."

## 2. Conclusion Template

The conclusion has 3 paragraphs. Keep it concise (150-250 words total).

### Paragraph 1: Problem + Method Summary (2-3 sentences)
- Restate the problem in one sentence.
- Summarize the method in one sentence (what makes it different).
- Do NOT repeat the abstract verbatim.

Pattern: "In this paper, we studied <problem>. We proposed <method>,
which <key differentiator>."

### Paragraph 2: Key Findings (2-4 sentences)
- One sentence per major verified finding.
- Each sentence MUST contain specific numbers from the results.
- Bold or emphasize the most important number.
- Reference the results table/figure.

Pattern: "Our experiments on <setting> demonstrate that <method>
achieves <metric: value> (Table <N>), representing a <X%>
improvement/reduction compared to <baseline> (<value>).
Additionally, <secondary finding with number>."

**Critical rule**: Only include findings backed by `verified` results.
If a claim is still `(hypothesis)`, it goes in Paragraph 3 (future work),
not here.

### Paragraph 3: Limitations + Future Work (2-3 sentences)
- Briefly note 1-2 key limitations (reference the Limitations section).
- List 2-3 concrete future work items tied to `planned` or `placeholder`
  experiments from `experiment-matrix.csv`.

Pattern: "Current limitations include <L1> and <L2>.
Future work will extend our evaluation to include <ablation/robustness
experiments still planned>, and investigate <direction>."

## 3. Claim Upgrade Decision Tree

When experiment results become available (`planned` → `verified`),
use this decision tree to determine how to upgrade claim language
throughout the paper.

```
For each claim Cx in the contribution list:
│
├─ Find ALL supporting experiments in experiment-matrix.csv
│  (rows where claim_id = Cx)
│
├─ Check result_status for each:
│  │
│  ├─ ALL verified?
│  │  └─ UPGRADE to factual claim
│  │     • Remove "(hypothesis)" tag
│  │     • Add specific numbers from results
│  │     • Reference the results table/figure
│  │     • Use bounded language: "achieves X" not "always achieves X"
│  │
│  ├─ SOME verified, SOME planned?
│  │  └─ PARTIAL UPGRADE
│  │     • Upgrade the verified portion with numbers
│  │     • Note remaining gaps: "Further ablation is planned"
│  │     • Keep "(hypothesis)" only on the unverified sub-claim
│  │
│  └─ NONE verified?
│     └─ KEEP as (hypothesis)
│        • No numbers, no factual claims
│        • Describe as design intent or future experiment
│
└─ Update these locations:
   • Introduction > Contributions list
   • Abstract (key result sentence)
   • Conclusion (Paragraph 2 findings)
   • Method section (if claim is about design effectiveness)
```

### Upgrade language examples

| Before (hypothesis) | After (verified) |
|---------------------|------------------|
| "C1: Constraint module reduces violations (hypothesis)" | "C1: The constraint module reduces violations from 1.61% (SAC) to 0.27%, a 83% reduction" |
| "C2: Risk-aware objective improves robustness (hypothesis)" | "C2: Risk-aware training is included in the full model; isolated impact will be verified via ablation (planned)" |
| "C0: Method improves cost/violation tradeoff (hypothesis)" | "C0: Our method achieves 0.27% violation rate with cost within 0.8% of the MPC optimum, outperforming all DRL baselines on both metrics" |

## 4. Literature Sufficiency Check

Before writing the abstract (W0), verify:
- `ref.bib` has ≥ 25 entries (30-40 preferred for empirical papers).
- Every Related Work sub-area has ≥ 3 citations.
- Every selected baseline in `baselines.csv` has ≥ 1 citation.
- Method design choices reference prior work that motivates them.

If any check fails, return to Phase 1.5 (Literature Enrichment Gate)
before proceeding.

## 5. Post-Write Verification Checklist

After writing the abstract and conclusion:
- [ ] Abstract ≤ 250 words
- [ ] Abstract contains no citations
- [ ] Abstract contains specific verified numbers (if available)
- [ ] Conclusion Paragraph 2 references results table/figure
- [ ] No `(hypothesis)` tags remain for claims with verified evidence
- [ ] Future work items map to specific planned experiments
- [ ] Abstract and conclusion are not copy-pastes of each other
