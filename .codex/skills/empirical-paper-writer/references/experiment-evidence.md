# Experiment Evidence Discipline

## Evidence Types
- `citation`: literature support only
- `experiment`: quantitative experiment backing a claim
- `figure`: diagram or visual analysis
- `table`: comparative or ablation table
- `mixed`: more than one evidence type required

## Claim-to-Evidence Rules
- Main method claim: nearest-baseline comparison + setup details + limitations
- Efficiency claim: runtime/latency/compute evidence, not vague wording
- Robustness claim: robustness experiment or failure analysis
- Ablation claim: targeted removal/change experiment

## Forbidden Patterns
- “Outperforms” without verified evidence
- “Significantly better” without an actual significance procedure or confidence reporting
- Describing placeholder values as if they are final results

## Placeholder Resolution Rules

When an experiment transitions from `planned` → `verified`:
1. Update `Result_Status` in issues CSV to `verified`.
2. Update `result_status` in `notes/design/experiment-matrix.csv` to `verified`.
3. In `main.tex`, replace placeholder language for that experiment:
   - `(hypothesis)` → bounded factual claim (e.g., “reduces violations by X%”)
   - `[Results pending]` → actual results
   - `\fbox{...placeholder...}` → real figure or `[Figure: see Table X]`
4. If the experiment supports the primary claim (C0), update Introduction contributions.
5. If all experiments for a secondary claim are verified, update that claim too.

## Figure Resolution Rules (mandatory)

Structural figures (architecture, pipeline, MDP) MUST be generated as
TikZ before Phase 2.7 (Rhythm Refinement). These figures do not depend
on experiment results.

1. **Structural \fbox → TikZ**: generate from `method-components.csv`
   using patterns in `references/figure-generation-guide.md`.
2. **Result \fbox → data-driven figure**: generate from `paper/results/`
   CSV data only when the data exists and is verified.
3. **No \fbox may survive to Phase 3 (QA)**: all must be resolved to
   either a real figure or an explicit `[Figure pending: <reason>]` marker.

Check: `grep -c 'fbox' main.tex` must return 0 at Phase 2.7 entry.

## Abstract Rules
- Abstract is written AFTER Results (W5) and Conclusion (W7) are DONE.
- Abstract must contain: problem (1 sentence), method (1-2 sentences), setting (1 sentence), key result (1 sentence, verified only), implication (1 sentence).
- Maximum 250 words. No citations. No acronyms without expansion.
- If verified results exist, the abstract MUST include specific numbers.
  See `references/abstract-conclusion-guide.md` for the full template.
