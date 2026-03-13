---
name: paper-from-zero
description: >
  Route a fixed research topic into a rigorous paper-generation workflow.
  Handles active literature search, innovation framing, contribution/evidence
  planning, and routes to either the review writer or empirical writer skill.
metadata:
  short-description: Research-to-paper router for review and empirical papers
---

# Paper-From-Zero

Use this skill when the user already has a **topic/domain** and wants a
structured path from topic -> innovation framing -> evidence plan -> draft-ready
paper workflow.

This skill is the **front door** of the paper stack:
- It decides whether the work is best treated as a `review` or `empirical` paper.
- It actively searches literature and frames the contribution.
- It produces the handoff contract used by the downstream writer skill.

## When to Use
- The topic is known, but the paper structure and contribution are not yet pinned down.
- The user wants the model to search for candidate innovation angles.
- The user wants a rigorous pre-writing stage before draft generation.

## When NOT to Use
- The user already has a finished review outline and only wants review execution.
- The user already has an experimental paper contract and only wants draft execution.
- The task is non-academic or does not need citation-grounded writing.

## Outputs
- `brief/topic-brief.md`
- `brief/contribution-map.yaml`
- `brief/evidence-matrix.csv`
- `notes/innovation/` (innovation candidates + evidence links; recommended)
- `plan/outline-contract.md`
- `plan/router-decision.md`
- A routing decision to one downstream writer:
  - `../arxiv-paper-writer/SKILL.md` for review papers
  - `../empirical-paper-writer/SKILL.md` for experimental papers

## Workflow
1. Confirm the topic, constraints, and whether the user already has a preferred innovation.
2. Actively search literature and build a compact literature map.
3. Produce 3-5 candidate innovation/contribution framings unless the user already supplied one.
4. Kill weak framings early: reject ideas that lack a clear gap, evidence path, or falsifiable claim.
5. Build a contribution map:
   - primary claim
   - secondary claims
   - non-goals / out-of-scope claims
   - risk factors / likely reviewer objections
6. Build an evidence matrix for every claim:
   - required citations
   - required visuals/tables
   - required experiments (if any)
   - what may remain placeholder vs what must be verified before finalization
7. Produce an outline contract with section goals, citation quotas, and figure quotas.
8. Route:
   - `review` -> use `../arxiv-paper-writer/SKILL.md`
   - `empirical` -> use `../empirical-paper-writer/SKILL.md`

## Collaboration Hooks (Recommended)

The following hooks integrate the breadth (Gemini) and depth (Claude) co-pilots
at fixed points in the workflow. Hooks are optional but strongly recommended for
research rigor.

| # | Trigger | Call | Input | Output consumed by |
|---|---------|------|-------|--------------------|
| 1 | After step 2 (literature initial screening) | Gemini `literature-map` | topic + Key Terms from topic-brief | Candidate papers and keyword clusters feed back into literature search; not written directly into artifacts. |
| 2 | After step 5 (contribution-map initial draft) | Claude `claim-stress-test` | contribution-map.yaml full text | risks and reviewer_objections feed back into contribution-map revision. |
| 3 | After step 6 (evidence-matrix initial draft) | Gemini `evidence-matrix-gap-check` OR Claude `evidence-sufficiency-audit` | evidence-matrix.csv + claims list | Gap list or sufficiency assessment feeds back into evidence-matrix revision. |
| 4 | Before step 8 (routing decision) | Claude `route-review-vs-empirical` | contribution-map + evidence-matrix summary | Routing recommendation + adversarial challenge written into router-decision.md. |

Hooks are non-blocking. If the target model is unavailable, the orchestrator
decides the fallback. Candidates-Only constraint applies regardless of executor.

**Hook 3 selection rule:** If the average evidence rows per claim < 3, call Gemini
`evidence-matrix-gap-check` first (breadth). If coverage appears sufficient, call
Claude `evidence-sufficiency-audit` (depth). Both may be called sequentially.

**Constraint:** Collaboration outputs are **inputs** to artifact revision, not direct
writes. All candidate entries must pass the Candidates-Only constraint defined in the
co-pilot skills. `validate_handoff.py` does not check capsule state — it only validates
final artifact completeness.

## Routing Rules
- Route to `review` when the deliverable is a survey, synthesis, taxonomy, benchmark-style review, or evidence-first overview.
- Route to `empirical` when the deliverable makes a novel method/setting/evaluation claim that needs experimental validation.
- If the topic contains both, prefer the paper’s **primary contribution type**.

## Handoff Contract
Before routing, create the following artifacts in the target project folder:
- `brief/topic-brief.md`: topic, scope, audience, constraints, venue/page targets
- `brief/contribution-map.yaml`: claims, non-claims, novelty framing, risks
- `brief/evidence-matrix.csv`: claim-to-evidence mapping
- `plan/outline-contract.md`: section tree + section intent + citation/figure quotas
- `plan/router-decision.md`: chosen mode and why

The downstream writer must consume these artifacts rather than re-guessing user intent.

## Validation (recommended)
Before routing, validate the handoff artifacts:
```bash
python3 .codex/skills/paper-from-zero/validate_handoff.py --project-dir <paper_dir>
```

## Strictness Rules
- Do not invent novelty. Frame novelty as a hypothesis until grounded by evidence.
- Do not skip literature search for “obvious” topics.
- Do not allow claim language stronger than available evidence.
- For empirical work, explicitly separate `planned`, `placeholder`, and `verified` results.

## References to Read
- `references/architecture.md`
- `references/innovation-framing.md`
- `references/routing-policy.md`
