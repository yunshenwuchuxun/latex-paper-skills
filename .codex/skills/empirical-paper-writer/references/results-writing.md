# Results Writing Rules

## Allowed Result States
- `verified`: may be written as a factual result
- `placeholder`: may be described as a reserved slot for a future result
- `planned`: may be described as an intended experiment, not an outcome

## Safe Language
- For `verified`: state the finding precisely and cite the corresponding table/figure/experiment block.
- For `placeholder`: say the experiment is reserved and the corresponding conclusion is pending evidence.
- For `planned`: describe the design intent only.

## Writing with Confidence When Data Supports Claims

When a claim's supporting experiments are ALL `verified`, write with
factual confidence — do not hedge unnecessarily.

| Evidence state | Language style |
|----------------|---------------|
| All verified | Factual: "achieves X", "reduces Y by Z%" |
| Some verified | Mixed: factual for verified parts, "planned" for the rest |
| None verified | Hypothesis-safe: "is designed to", "we hypothesize" |

**Specific numbers are mandatory** for verified claims. Never write
"improves over baselines" when you have the exact numbers available.

BAD (verified result, vague language):
> "Our method shows improvement over baselines in violation rate."

GOOD (verified result, specific):
> "Our method achieves 0.27% violation rate, compared to 1.61% for SAC
> and 27.75% for PPO (Table 1), while maintaining cost within 0.8%
> of the MPC optimum."

## Claim Upgrade Procedure

When experiment results transition from `planned` → `verified`:
1. Run through the claim upgrade decision tree
   (see `references/abstract-conclusion-guide.md` Section 3).
2. For EACH upgraded claim, update these four locations:
   - Introduction → Contributions list
   - Abstract → key result sentence
   - Conclusion → Paragraph 2 (key findings)
   - Results section → analysis text
3. Remove `(hypothesis)` tags from upgraded claims.
4. Verify that the upgrade language uses bounded statements with specific
   numbers, not unbounded superlatives.

## Avoid
- Overselling incremental gains
- Writing stronger takeaways than the evidence state supports
- Hiding missing evidence; state it explicitly in results or limitations
- Using vague language when specific numbers are available

## Linking to the Issues CSV

The `Result_Status` column in the empirical issues CSV tracks the evidence state for each issue:
- When drafting a Writing issue, check its `Result_Status` before choosing language.
- When marking an issue `DONE`, verify that `Result_Status` matches the actual prose:
  - `verified` issues must cite concrete evidence (table, figure, or experiment block).
  - `placeholder` issues must use explicitly hedged language (e.g., "results pending").
- The `Must_Verify` column indicates whether the issue requires evidence verification before completion. Issues with `Must_Verify=yes` and `Result_Status=placeholder` cannot be marked `DONE` until the result is either verified or the issue is split into a verified portion and a remaining placeholder.
