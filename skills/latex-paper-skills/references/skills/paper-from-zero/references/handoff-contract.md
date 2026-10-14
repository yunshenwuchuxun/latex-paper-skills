# Handoff Contract

This document defines the artifacts that paper-from-zero produces and the downstream writer (arxiv-paper-writer or empirical-paper-writer) consumes.

## Artifacts

| File | Format | Purpose |
|------|--------|---------|
| `brief/topic-brief.md` | Markdown | Topic, scope, audience, constraints, venue/page targets |
| `brief/contribution-map.yaml` | YAML | Primary claim, secondary claims, non-claims, risks, reviewer objections |
| `brief/evidence-matrix.csv` | CSV | Claim-to-evidence mapping with verification status |
| `notes/innovation/` | Folder (md/csv) | (Recommended) Innovation candidates + decision log + evidence links |
| `plan/outline-contract.md` | Markdown | Section tree with intent, citation quota, figure quota per section |
| `plan/router-decision.md` | Markdown | Chosen mode, rationale, alternative path, handoff date |

## Completeness Requirements

Before routing to a downstream writer, all five artifacts must exist and satisfy:

1. **topic-brief.md**: Topic, scope, and at least one constraint (venue or page target) filled in.
2. **contribution-map.yaml**: `primary_claim.statement` is non-empty; at least one risk or reviewer objection listed.
3. **evidence-matrix.csv**: At least one row per secondary claim; every row has a non-empty `Evidence_Type`.
4. **outline-contract.md**: Section tree has at least 4 rows; total citation quota is non-zero.
5. **router-decision.md**: `Chosen Mode` is either `review` or `empirical`; `Rationale` is non-empty.

## What Downstream Writers Expect

- The writer reads handoff artifacts as immutable context (it does not re-guess user intent).
- The writer may refine section names, citation quotas, and figure assignments during planning, but the contribution framing and evidence matrix are treated as ground truth unless the user explicitly revises them.
- If any artifact is missing or incomplete, the writer should halt and ask the user to complete the handoff via paper-from-zero.
