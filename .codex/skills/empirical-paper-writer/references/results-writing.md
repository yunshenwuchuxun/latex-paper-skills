# Results Writing Rules

## Allowed Result States
- `verified`: may be written as a factual result
- `placeholder`: may be described as a reserved slot for a future result
- `planned`: may be described as an intended experiment, not an outcome

## Safe Language
- For `verified`: state the finding precisely and cite the corresponding table/figure/experiment block.
- For `placeholder`: say the experiment is reserved and the corresponding conclusion is pending evidence.
- For `planned`: describe the design intent only.

## Avoid
- Overselling incremental gains
- Writing stronger takeaways than the evidence state supports
- Hiding missing evidence; state it explicitly in results or limitations

## Linking to the Issues CSV

The `Result_Status` column in the empirical issues CSV tracks the evidence state for each issue:
- When drafting a Writing issue, check its `Result_Status` before choosing language.
- When marking an issue `DONE`, verify that `Result_Status` matches the actual prose:
  - `verified` issues must cite concrete evidence (table, figure, or experiment block).
  - `placeholder` issues must use explicitly hedged language (e.g., "results pending").
- The `Must_Verify` column indicates whether the issue requires evidence verification before completion. Issues with `Must_Verify=yes` and `Result_Status=placeholder` cannot be marked `DONE` until the result is either verified or the issue is split into a verified portion and a remaining placeholder.
