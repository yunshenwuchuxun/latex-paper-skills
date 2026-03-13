# Gemini Prompt Templates — Paper-from-Zero Breadth Mode

## `literature-map` — Expand candidate papers and adjacent research areas

```
Task:
- Given the topic and key terms below, expand the candidate literature pool.
- Identify adjacent research areas, related surveys, and keyword clusters
  that a comprehensive search should cover.

Input:
- Topic: <from topic-brief.md>
- Key Terms: <from topic-brief.md Key Terms section>

Constraints:
- ALL entries are UNVERIFIED CANDIDATES. Do not assert correctness.
- Output ONLY: title / venue guess / year / arXiv-ID-or-unknown.
- Do NOT generate BibTeX entries.
- Do NOT rank or recommend; just expand the search surface.
- Group results by sub-area or keyword cluster.

Output:
- A grouped list of candidate papers with the fields above.
- A list of suggested keyword clusters for further search.
- Map to artifacts: topic-brief.md (Key Terms expansion),
  evidence-matrix.csv (Evidence_Source column candidates).
```

## `innovation-candidates` — Generate 3-5 candidate contribution framings

```
Task:
- Given the topic and known literature summary, propose 3-5 distinct
  candidate framings for the paper's primary contribution.

Input:
- Topic: <topic>
- Known literature summary: <brief overview of existing work>

Constraints:
- ALL framings must be marked status = "candidate".
- Do NOT evaluate evidence sufficiency (that is Claude's job).
- Do NOT recommend a routing decision (review vs empirical).
- For each framing provide: label, one-sentence claim, differentiation
  from nearest existing work, and 2-3 risk factors.
- Keep framings mutually distinct; avoid minor variations of the same idea.

Output:
- 3-5 numbered candidate framings with the fields above.
- Map to artifacts: contribution-map.yaml
  (primary_claim / secondary_claims / risks candidates).
```

## `evidence-matrix-gap-check` — Audit evidence coverage gaps

```
Task:
- Given the evidence matrix and the list of claims, identify coverage gaps:
  claims without supporting evidence, evidence columns with missing data,
  and claim-evidence pairs that lack verification.

Input:
- Evidence matrix: <paste or reference evidence-matrix.csv>
- Claims list: <from contribution-map.yaml>

Constraints:
- ONLY flag gaps; do NOT fill them in.
- Any candidate supplementary rows must be marked
  verification_status = "unverified".
- Do NOT evaluate evidence quality or sufficiency (that is Claude's job).
- Do NOT modify existing verified entries.

Output:
- A list of identified gaps (missing rows, empty columns, uncovered claims).
- Candidate supplementary entries (if any) with verification_status = "unverified".
- Map to artifacts: evidence-matrix.csv (gap annotations).
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

### Image Analysis (screenshot in workspace)

```
Task:
- Analyze the UI screenshot at `.codex_uploads/<filename>.png`.

Constraints:
- Describe what you see, then answer: <specific question>.
- Keep observations concise.

Output:
- Bullet list of observations and recommendations.
```
