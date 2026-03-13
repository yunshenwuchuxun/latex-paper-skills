# Claude Prompt Templates — Paper-from-Zero Depth Mode

Note: Prefer choosing models via CLI aliases (e.g., `--model sonnet` for routine work, `--model opus` for harder tasks) instead of hard-coding versioned model IDs. If you omit `--model`, Claude Code uses its configured default.

## `claim-stress-test` — Find logical holes, weak claims, reviewer objections

```
Task:
- Given the contribution map below, perform an adversarial review.
- Identify logical gaps, unsupported assumptions, weak claim language,
  and likely reviewer objections.

Input:
- Contribution map: <paste contribution-map.yaml full text>

Constraints:
- Be adversarial. Assume a skeptical reviewer perspective.
- Do NOT propose alternative framings (that is Gemini's job).
- Do NOT generate or suggest citations.
- For each weakness found, provide:
  severity (critical / major / minor),
  the specific claim affected,
  the logical issue,
  and a suggested mitigation direction (without rewriting the claim).

Output:
- A prioritized list of weaknesses with the fields above.
- Map to artifacts: contribution-map.yaml (risks / reviewer_objections).
```

## `route-review-vs-empirical` — Recommend routing with adversarial challenge

```
Task:
- Given the contribution map and evidence matrix summary, recommend whether
  this paper should be routed as a review paper or an empirical paper.
- Then perform an adversarial self-challenge: argue against your own
  recommendation and evaluate whether the counter-argument holds.

Input:
- Contribution map: <paste or reference contribution-map.yaml>
- Evidence matrix summary: <key stats from evidence-matrix.csv>

Constraints:
- MUST include the adversarial challenge step. Do NOT skip it.
- The recommendation must include:
  Chosen Mode (review | empirical),
  Rationale (2-3 sentences),
  Alternative Path (what would need to change to justify the other mode),
  Adversarial Challenge (strongest argument against your recommendation),
  Final Verdict (confirm or revise after challenge).
- Do NOT generate citations or literature references.

Output:
- Structured recommendation with all fields above.
- Map to artifacts: router-decision.md
  (Chosen Mode / Rationale / Alternative Path).
```

## `evidence-sufficiency-audit` — Audit whether evidence supports claim strength

```
Task:
- Given the claims list and evidence matrix, evaluate whether the available
  evidence is sufficient to support each claim at its stated strength level.

Input:
- Claims list: <from contribution-map.yaml>
- Evidence matrix: <paste or reference evidence-matrix.csv>

Constraints:
- ONLY judge sufficiency; do NOT verify sources themselves.
- Do NOT propose new claims or alternative framings.
- For each claim, assess:
  claim text,
  current evidence count,
  sufficiency verdict (sufficient / insufficient / borderline),
  reasoning (1-2 sentences),
  recommended action if insufficient (weaken claim / add evidence / split claim).
- Flag any evidence entries that appear to support claims not in the claims list.

Output:
- A per-claim sufficiency assessment with the fields above.
- Map to artifacts: evidence-matrix.csv (Verification_Status),
  contribution-map.yaml (risks).
```

---

## Fallback: Code Collaboration Mode

The templates below are for generic code collaboration tasks (non-paper mode).

### Analysis / Plan (no code changes)

```
Task:
- <what to analyze>

Repo pointers:
- <file paths + approximate line numbers>

Constraints:
- Keep it concise and actionable.
- Do not paste large snippets; reference files/lines instead.

Output:
- Bullet list of findings and a proposed plan.
```

### Patch (Unified Diff only)

```
Task:
- <what to change>

Repo pointers:
- <file paths + approximate line numbers>

Constraints:
- OUTPUT: Unified Diff Patch ONLY.
- Strictly prohibit any actual modifications.
- Minimal, focused changes. No unrelated refactors.

Output:
- A single unified diff patch.
```

### Review (audit an existing diff)

```
Task:
- Review the following unified diff for correctness, edge cases, and missing tests.

Constraints:
- Return a checklist of issues + suggested fixes (no code unless requested).

Input diff:
<paste unified diff here>
```
