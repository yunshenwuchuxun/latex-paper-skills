---
name: empirical-paper-writer
description: >
  Draft IEEE-style empirical ML/AI papers from a structured research contract.
  Builds experiment plans, section skeletons, placeholder-safe results, and a
  near-submission draft without fabricating evidence.
metadata:
  short-description: Experimental paper executor with evidence-first safeguards
---

# Empirical Paper Writer

Use this skill for **novel experimental research papers** after the topic and
contribution have already been framed.

This skill is the empirical counterpart to `../arxiv-paper-writer`.
It reuses the same high-value paper-engine pieces—citation discipline, LaTeX
compilation, source policy, and QA—but changes the paper logic from review to
experiment-driven writing.

## When to Use
- The user wants a method/experiment paper rather than a review.
- The contribution requires experiments, ablations, or quantitative comparisons.
- The user wants a near-submission draft with explicit placeholders where evidence is not yet verified.

## When NOT to Use
- Pure surveys, taxonomies, or literature syntheses.
- Non-academic reports.
- Cases where the user only wants experiment design and no paper draft.

## Inputs
- Topic / research direction
- Handoff artifacts from `../paper-from-zero` when available:
  - `brief/topic-brief.md`
  - `brief/contribution-map.yaml`
  - `brief/evidence-matrix.csv`
  - `plan/outline-contract.md`
- Optional user-provided innovation, baselines, datasets, or results

## Outputs
- `main.tex` (placeholder-safe draft)
- `ref.bib`
- `paper.config.yaml` (includes `runtime.*` for experiment execution)
- `plan/<timestamp>-<slug>.md`
- `issues/<timestamp>-<slug>.csv`
- Optional `notes/literature-notes.md`
- Recommended `notes/innovation/` (candidates + decision log + evidence links)
- `notes/design/` CSV artifacts (`baselines.csv`, `method-components.csv`, `experiment-matrix.csv`)
- Figures/tables/result placeholders in the LaTeX draft (hypothesis-safe)
- Optional `experiments/` code scaffold (PyTorch skeleton; not executed by this skill)
- `main.pdf` after compile/QA when LaTeX is available

## Non-Negotiable Rules
1. **No prose in `main.tex`** until plan approved and issues CSV exists.
2. **Do not fabricate results, numbers, or significance claims.**
3. Every experimental claim must map to an evidence item or explicit placeholder.
4. Mark result status explicitly as one of `planned`, `placeholder`, or `verified`.
5. Reuse the existing paper-engine scripts for citation verification, compile, source ranking, and QA whenever possible.

## Workflow
### Gate 0: Scaffold + Research Contract
1. Confirm venue, page target, datasets/baselines if already known, and any user-provided innovation.
2. Search literature and gather only enough papers to frame the problem, baselines, and closest related methods.
3. Create or refine:
   - contribution map
   - experiment/evidence matrix
   - outline contract
4. Scaffold the project:
   ```bash
   python3 scripts/bootstrap_ieee_empirical_paper.py --stage kickoff --topic "<topic>" --layout project
   ```
   `--layout project` creates `<project>/paper/` (LaTeX + issues) and `<project>/experiments/` (code scaffold).
   For a lighter entrypoint with an outline-only plan:
   ```bash
   python3 scripts/bootstrap_ieee_empirical_paper.py --stage outline --topic "<topic>" --layout project
   ```
5. Create a skeleton-only `main.tex` with headings, bullet placeholders, experiment slots, and seed citations.
6. **STOP** until the user approves the plan.

### Phase 0.5: Method & Experiment Design

After the user approves the initial plan, design the method and experiments
before creating the issues CSV. This phase produces structured CSV artifacts.

**Step 1: Systematic Baseline Identification**
1. From the contribution-map primary claim, search for baselines in 3 categories:
   - Direct competitors: SOTA methods on the same task (last 2 years).
   - Foundational methods: well-known classics that anchor the field.
   - Ablation anchors: our method minus its core innovation.
2. Record 10-20 candidates in `notes/design/baselines.csv` (see `assets/baselines-template.csv`).
3. Select 4-8 baselines for final comparison. Mark `selected=yes` with reason.
4. See `references/experiment-design.md` Section 1 for selection criteria.

**Step 2: Innovation Module Design**
1. From the gap analysis (nearest prior work weaknesses × improvable directions):
   - Design a minimum viable innovation: one core change that is clearly testable.
   - Make the innovation modular (pluggable component, supports ablation).
   - Define clear input/output interfaces for reproducibility.
2. Record all pipeline components in `notes/design/method-components.csv` (see `assets/method-components-template.csv`).
3. Mark `is_novel=yes` for novel components; define `replaceable_by` for ablation.

**Step 3: Pipeline Architecture Design**
1. Design the overall flow: input → preprocessing → core module(s) → postprocessing → output.
2. For each component: function, input/output format, replaceability.
3. Training flow: loss function rationale, optimizer, tuning strategy.
4. Inference flow: runtime cost estimate.
5. Sketch a pipeline architecture diagram placeholder for the Method section.

**Step 4: Comparison Experiment Matrix**
1. Design the baselines × datasets × metrics matrix.
2. Fair comparison rules:
   - Same data splits, preprocessing, and evaluation protocol for all methods.
   - Use official implementations or paper-reported results (annotate source).
   - Plan ≥3 runs with different seeds; report mean ± std.
3. Record all experiment rows in `notes/design/experiment-matrix.csv` with `type=main_comparison` (see `assets/experiment-matrix-template.csv`).

**Step 5: Ablation Experiment Design**
1. From `method-components.csv`, identify factors by `ablation_priority`:
   - High: core innovation components (must ablate).
   - Medium: architecture choices (ablate if space allows).
   - Low: hyperparameter choices (include only if impact is significant).
2. For each factor: define removal/degradation/random-replacement strategy.
3. Record in `experiment-matrix.csv` with `type=ablation`.
4. Minimum 4 ablation factors.

**Step 6: Robustness & Efficiency Analysis Plan**
1. Robustness: noise levels, distribution shift, domain transfer scenarios.
2. Error analysis: failure case categories, sampling protocol.
3. Efficiency: parameter count, FLOPs, inference latency vs baselines.
4. Record in `experiment-matrix.csv` with `type=robustness` and `type=efficiency`.

**Phase 0.5 outputs** (saved in `notes/design/`):
- `baselines.csv` — baseline & SOTA competitive landscape
- `experiment-matrix.csv` — full experiment design matrix
- `method-components.csv` — pipeline component inventory

**STOP** until the user confirms the design artifacts before proceeding to Gate 1.

### Gate 1: Create Issues CSV
1. Check the kickoff gate in the plan.
2. Create issues CSV:
   ```bash
   python3 scripts/bootstrap_ieee_empirical_paper.py --stage issues --topic "<topic>" --with-literature-notes --layout project
   ```
3. Validate:
   ```bash
   python3 scripts/validate_empirical_paper_issues.py <paper_dir>/issues/<timestamp>-<slug>.csv
   ```
   For `--layout project`, `<paper_dir>` is `<project>/paper`.

### Phase 1.5: Literature Enrichment Gate

Before starting the writing loop, ensure citation coverage is adequate.

1. **Count check**: total unique entries in `ref.bib`. If < 25, trigger enrichment.
2. **Cluster search**: for each Related Work sub-area (from the RW taxonomy), search
   for 3-5 additional relevant papers beyond the initial spine set.
3. **Baseline citations**: every selected baseline in `baselines.csv` must have at
   least one corresponding entry in `ref.bib`.
4. **Method motivation**: for each novel component in `method-components.csv`,
   find 1-2 papers that motivate the design choice (prior art or the gap it fills).
5. **Verify** all new citations via the standard verification pipeline.
6. **Gate**: do not start W1 until `ref.bib` has ≥ 25 verified entries. Target 30-40
   for the finished paper (empirical papers need fewer than reviews, but 14 is
   universally too low).

### Phase 2: Execution Loop
For each issue:
1. Research the exact claim, baseline, or related-work gap.
2. Draft the assigned section or experiment block.
3. Keep results explicit:
   - `verified`: backed by real evidence
   - `placeholder`: reserved for future real evidence
   - `planned`: the experiment is designed but not yet filled in
4. Prefer hypothesis-safe writing for any unverified outcome (e.g., `(hypothesis)` / `[Pending: ...]` tags).
5. Never write deterministic superiority claims without verified evidence.
6. Run citation audit / compile / QA before marking DONE.
7. **Dependency enforcement**: Before marking any issue DONE, verify that ALL issues listed in its `Depends_On` column are already DONE or SKIP. If any dependency is still TODO or DOING, the current issue MUST NOT be marked DONE. This rule is non-negotiable.

### Phase 2.2: Issue Execution Helpers
- Use `python3 ../arxiv-paper-writer/scripts/issue_workflow.py --project-dir <paper_dir> render-skeleton --issues <issues.csv> --issue-id <Wx>` to render a LaTeX section skeleton for a Writing issue.
- Add `--apply-if-missing` only when the full section path is entirely absent from `main.tex`; nested insertion under an existing parent stays manual.
- Before QA or after a batch of edits, run `python3 ../arxiv-paper-writer/scripts/issue_workflow.py --project-dir <paper_dir> audit --issues <issues.csv>` to check section-path consistency, citation counts, placeholders, and lightweight figure/page signals.

### Phase 2.3: Experiment Execution Checkpoint
After all experiment design issues (E0-E4) and experiment code issues (E5-E7) are DONE:

1. **Check runability**: Verify that the experiment runner script exists and is syntactically valid.
2. **STOP and instruct the user**:
   - Tell the user to run experiments in their configured environment:
     ```
     conda activate <runtime.conda_env>
     cd <project_dir>/experiments
     python run_all.py --config configs/<config>.yaml
     ```
   - Tell the user to invoke `results-backfill` SKILL after experiments complete.
3. **Do NOT attempt to run long experiments within the AI session.**
4. Mark experiment execution issues (E8-E10) as TODO with note "awaiting user execution".

### Phase 2.4: Structural Figure Generation

After all writing issues (W1-W7) reach DONE, resolve structural diagrams.
These are **non-result figures**—architecture, pipeline, formulation diagrams
that depend on method design, not on experiment outcomes.

**Step 1: Identify required figures**
Scan `main.tex` for `\fbox{...placeholder...}`. Classify each:
- **Structural** (derivable from method-components.csv / problem formulation):
  generate now.
- **Result-dependent** (needs experiment data): keep as placeholder until
  Phase 2.5.

**Step 2: Generate structural TikZ figures**
For each structural placeholder:
1. Read `notes/design/method-components.csv` to extract component names,
   is_novel flags, and data-flow edges.
2. Select a pattern from `references/figure-generation-guide.md`.
3. Generate a `.tikz` file under `paper/figures/` and replace the `\fbox`
   with `\input{figures/<name>.tikz}`.
4. Standard figures for empirical papers (generate at least 2 of 3):
   - **System overview / teaser** (`fig:teaser`): problem setting +
     where the method fits. Place in Introduction.
   - **Method architecture** (`fig:method`): pipeline with components,
     novel parts highlighted. Place in Method.
   - **Formulation diagram** (optional, `fig:formulation`): MDP / state
     machine / optimization flow. Place in Problem Formulation or Method.

**Step 3: Visual issues tracking**
Use V-prefixed issues (V1, V2, ...) in the issues CSV for each figure.
Mark DONE only when the TikZ compiles and is referenced in text.

See `references/figure-generation-guide.md` for TikZ patterns and style rules.

**Gate**: All structural `\fbox` placeholders must be resolved before
Phase 2.5. Result-dependent `\fbox` pass through to Phase 2.5.

### Phase 2.5: Claim Upgrade & Placeholder Resolution

After experiment issues (E*) reach `verified` status, perform a systematic
upgrade pass. This phase has four mandatory steps.

**Step 1: Claim Analysis** (mandatory)

For each contribution claim (C0, C1, C2, ...):
1. Map the claim to its supporting experiments in `experiment-matrix.csv`.
2. Check `result_status` for ALL supporting experiment rows.
3. Apply the upgrade decision:

| Evidence state | Action |
|----------------|--------|
| ALL experiments verified | Upgrade `(hypothesis)` → bounded factual claim with specific numbers |
| SOME verified, SOME planned | Upgrade the verified part; note remaining gaps explicitly |
| NONE verified | Keep as `(hypothesis)` |

4. When upgrading, write with the verified numbers:
   - BAD: "Our method improves the tradeoff (hypothesis)."
   - GOOD: "Our method achieves 0.27% violation rate, a 58% reduction
     vs. the nearest constrained baseline (0.65%), while maintaining
     comparable cost (0.8% higher than MPC)."
5. Update contribution list in Introduction to reflect upgrades.

See `references/abstract-conclusion-guide.md` for the claim-upgrade
decision tree and safe-language patterns.

**Step 2: Result-dependent Figure Resolution** (mandatory)

For each remaining `\fbox{...placeholder...}` in `main.tex`:
1. Check whether the required data exists in `paper/results/`.
2. If data exists: generate figure (TikZ plot, table, or pgfplots).
3. If data does not exist: replace `\fbox` with an explicit text marker
   `[Figure pending: <experiment_id> not yet verified]`.

**Step 3: Section Back-fill** (mandatory)

For each `experiment-matrix.csv` row with `result_status=verified`:
1. Check whether the corresponding section in `main.tex` contains actual
   results or is still a skeleton.
2. If skeleton: fill with verified results, tables, and analysis text.
3. For sections where only SOME experiments are verified: write verified
   portions and mark remaining as `[Results pending: <experiment_id>]`.

**Step 4: Abstract & Conclusion Completion** (mandatory)

1. **Abstract** (see `references/abstract-conclusion-guide.md`):
   - Sentence 1: Problem statement
   - Sentence 2-3: Method core idea
   - Sentence 3-4: Experimental setting
   - Sentence 4-5: Key verified result (specific numbers)
   - Sentence 5: Implication
   - Constraint: ≤250 words, no citations, no unexpanded acronyms.
   - If main results are verified, the abstract MUST contain specific
     numbers. Do not write a vague abstract when data exists.

2. **Conclusion** (see `references/abstract-conclusion-guide.md`):
   - Paragraph 1: Problem restatement + method summary (2-3 sentences)
   - Paragraph 2: Key verified findings with specific numbers from
     results tables/figures. One sentence per major finding.
   - Paragraph 3: Limitations (brief) + concrete future work items
     (tied to planned/placeholder experiments)
   - If a claim is still `(hypothesis)`, state it as future work,
     not as a finding.

**Gate**: Do not proceed to Rhythm Refinement (Phase 2.7) until:
- All `\fbox` placeholders are resolved or explicitly marked pending.
- No `(hypothesis)` tags remain for claims with verified evidence.
- Abstract is substantive (not a stub).
- Conclusion contains specific numbers from verified results.

### Phase 2.7: Rhythm Refinement
After all writing issues are `DONE`, refine prose section-by-section using the `latex-rhythm-refiner` skill. This step varies sentence/paragraph lengths and removes filler phrases while preserving all citations.

### Phase 3: QA Gate
1. Run internal QA checklist (see `../arxiv-paper-writer/references/quality-report.md`).
2. Audit source quality and venue policy:
   - `python3 ../arxiv-paper-writer/scripts/issue_workflow.py --project-dir <paper_dir> audit --issues <issues.csv> --fail-on-issues`
   - `python3 ../arxiv-paper-writer/scripts/source_ranker.py --project-dir <paper_dir> rank`
   - `python3 ../arxiv-paper-writer/scripts/citation_policy.py --project-dir <paper_dir> audit-bib`
   - `python3 ../arxiv-paper-writer/scripts/citation_policy.py --project-dir <paper_dir> audit-tex --issues <issues.csv>`
   - `python3 ../arxiv-paper-writer/scripts/style_profile.py --project-dir <paper_dir> check-draft` (if using `style_mode=target_venue`)
   - `python3 ../arxiv-paper-writer/scripts/compile_paper.py --project-dir <paper_dir> --check-warnings --fail-on-warnings`
   - `python3 ../arxiv-paper-writer/scripts/citation_policy.py --project-dir <paper_dir> lint-bib --fail-on-lint`
3. Compile; ensure no `Overfull \hbox` warnings in `main.log`.
4. Deliver `main.tex`, `ref.bib`, figures, and `main.pdf`.

### Runtime Environment
Before running any experiment or utility script:
1. Read `paper.config.yaml` → `runtime.conda_env` or `runtime.python`.
2. If `conda_env` is set, activate it: `conda activate <env_name>`.
3. If `python` is set, use that interpreter directly.
4. If neither is set, ask the user which conda environment to use.
5. All subprocess calls should use the configured interpreter, not the system default.

---

## Success Criteria

**Compilation**: `python3 ../arxiv-paper-writer/scripts/compile_paper.py --project-dir <paper_dir> --check-warnings --fail-on-warnings` (exit 0).

**Quality Metrics**:
- 6-10 pages of main text (references excluded)
- 30-60 total citations (fewer than review; experiment evidence replaces some citations)
- 100% citation verification rate
- 5+ visualization types (including result tables/figures)
- ≥2 structural TikZ figures (system overview + method architecture)
- 0 remaining `\fbox` placeholders in `main.tex`
- Abstract is substantive (≤250 words, contains verified key result)
- Conclusion contains specific numbers from verified experiments
- All issues `DONE` or `SKIP`
- All result statements either `verified` or explicitly `placeholder`
- No `(hypothesis)` tags for claims with verified evidence

---

## Safety & Guardrails
- **Never fabricate** citations, results, numbers, or significance claims; add TODO and ask user if evidence missing.
- **Result status must be accurate**: never write `verified` for a result that is actually `placeholder`.
- **Verify every citation** via web search + source page (and PDF if available) before adding to `ref.bib`.
- **Confirm before** large literature searches.
- **Do not overwrite** user files without confirmation.
- **Issues CSV** is the contract; mark `DONE` only when criteria met.
- **No submission bundles** unless user requests.

## Layout Hygiene
Fix `Overfull \hbox` warnings before marking issues `DONE`:
- Figures: start with `figure` + `\columnwidth`; switch to `figure*` + `\textwidth` if needed
- Tables: prefer `p{...}` column widths / `\tabcolsep` over `\resizebox`
- Equations: use `split`, `multline`, `aligned`, or `IEEEeqnarray` for line-breaking

---

## Issues CSV Schema

The empirical issues CSV uses an 18-column schema with experiment-specific fields.

| Column | Purpose |
|--------|---------|
| ID | Issue identifier with phase prefix (R/E/W/RF/Q + number) |
| Phase | One of: Research, Experiment, Writing, Refinement, QA |
| Title | Short description of the deliverable |
| Section_Path | Target section in `main.tex` (e.g., `Introduction > Contributions`) |
| Claim_ID | Links to evidence-matrix claim (e.g., C1, C2) |
| Evidence_Type | n/a, citation, experiment, figure, table, mixed |
| Experiment_ID | Links to experiment matrix (e.g., EXP-1) |
| Result_Status | n/a, planned, placeholder, verified |
| Description | Detailed scope of the issue |
| Source_Policy | core, standard, frontier (for citation sourcing) |
| Target_Citations | Minimum citations expected for this issue |
| Visualization | Required figure/table description |
| Acceptance | Criteria for marking DONE |
| Status | TODO, DOING, DONE, SKIP |
| Verified_Citations | Actual verified citation count |
| Depends_On | Semicolon-separated issue IDs that must complete first |
| Must_Verify | yes/no: whether this issue requires evidence verification |
| Notes | Free-form notes |

**Phase prefixes**: R (Research), E (Experiment), W (Writing), RF (Refinement), Q (QA).

Schema validated by `scripts/validate_empirical_paper_issues.py`.
- `../arxiv-paper-writer/scripts/arxiv_registry.py`
- `../arxiv-paper-writer/scripts/compile_paper.py`
- `../arxiv-paper-writer/scripts/citation_policy.py`
- `../arxiv-paper-writer/scripts/source_ranker.py`
- `../arxiv-paper-writer/scripts/style_profile.py`

## References to Read
- `references/experiment-design.md` (baseline selection, experiment matrix patterns, ablation design, statistical rigor)
- `references/figure-generation-guide.md` (TikZ patterns for structural diagrams)
- `references/abstract-conclusion-guide.md` (abstract template, conclusion template, claim upgrade decision tree)
- `references/research-workflow.md`
- `references/experiment-evidence.md`
- `references/results-writing.md`
- `references/reviewer-loop.md`
- `references/reproducibility-checklist.md`
- `references/fork-extend-workflow.md`
- Also reuse common references from `../arxiv-paper-writer/references/`:
  - `bibtex-guide.md`
  - `citation-workflow.md`
  - `quality-report.md`
  - `template-usage.md`
  - `visual-templates.md`
  - `writing-style.md`
