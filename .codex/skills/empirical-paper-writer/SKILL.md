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
- `main.tex`
- `ref.bib`
- `paper.config.yaml`
- `plan/<timestamp>-<slug>.md`
- `issues/<timestamp>-<slug>.csv`
- Optional `notes/literature-notes.md`
- Recommended `notes/innovation/` (candidates + decision log + evidence links)
- Figures/tables/result placeholders in the LaTeX draft
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
   python3 scripts/bootstrap_ieee_empirical_paper.py --stage kickoff --topic "<topic>"
   ```
   For a lighter entrypoint with an outline-only plan:
   ```bash
   python3 scripts/bootstrap_ieee_empirical_paper.py --stage outline --topic "<topic>"
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
   python3 scripts/bootstrap_ieee_empirical_paper.py --stage issues --topic "<topic>" --with-literature-notes
   ```
3. Validate:
   ```bash
   python3 scripts/validate_empirical_paper_issues.py <paper_dir>/issues/<timestamp>-<slug>.csv
   ```

### Phase 2: Execution Loop
For each issue:
1. Research the exact claim, baseline, or related-work gap.
2. Draft the assigned section or experiment block.
3. Keep results explicit:
   - `verified`: backed by real evidence
   - `placeholder`: reserved for future real evidence
   - `planned`: the experiment is designed but not yet filled in
4. Never write deterministic superiority claims without verified evidence.
5. Run citation audit / compile / QA before marking DONE.

### Phase 2.2: Issue Execution Helpers
- Use `python3 ../arxiv-paper-writer/scripts/issue_workflow.py --project-dir <paper_dir> render-skeleton --issues <issues.csv> --issue-id <Wx>` to render a LaTeX section skeleton for a Writing issue.
- Add `--apply-if-missing` only when the full section path is entirely absent from `main.tex`; nested insertion under an existing parent stays manual.
- Before QA or after a batch of edits, run `python3 ../arxiv-paper-writer/scripts/issue_workflow.py --project-dir <paper_dir> audit --issues <issues.csv>` to check section-path consistency, citation counts, placeholders, and lightweight figure/page signals.

### Phase 2.5: Rhythm Refinement
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

---

## Success Criteria

**Compilation**: `python3 ../arxiv-paper-writer/scripts/compile_paper.py --project-dir <paper_dir> --check-warnings --fail-on-warnings` (exit 0).

**Quality Metrics**:
- 6-10 pages of main text (references excluded)
- 30-60 total citations (fewer than review; experiment evidence replaces some citations)
- 100% citation verification rate
- 5+ visualization types (including result tables/figures)
- All issues `DONE` or `SKIP`
- All result statements either `verified` or explicitly `placeholder`

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
- `references/research-workflow.md`
- `references/experiment-evidence.md`
- `references/results-writing.md`
- `references/reviewer-loop.md`
- Also reuse common references from `../arxiv-paper-writer/references/`:
  - `bibtex-guide.md`
  - `citation-workflow.md`
  - `quality-report.md`
  - `template-usage.md`
  - `visual-templates.md`
  - `writing-style.md`
