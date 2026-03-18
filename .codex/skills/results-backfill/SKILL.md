---
name: results-backfill
description: >
  Back-fill verified experiment results into an existing empirical paper draft.
  Resolves placeholders, upgrades hypotheses to factual claims, generates
  figures/tables, drafts abstract, and runs rhythm refinement + QA.
metadata:
  short-description: Post-experiment paper completion from verified results
---

# Results Back-fill

Use this skill **after** `empirical-paper-writer` has produced a draft with
placeholders and the user has run experiments outside the AI session.

## When to Use
- `empirical-paper-writer` has completed design + code + placeholder draft.
- The user has run experiments in their configured conda environment.
- `paper/results/` contains new CSV / data files from completed experiments.

## When NOT to Use
- The paper draft does not yet exist (use `empirical-paper-writer` first).
- Experiments have not been run yet.
- The user only wants experiment design without paper completion.

## Inputs
- `paper/main.tex` (draft with placeholders)
- `paper/results/*.csv` (experiment results)
- `notes/design/experiment-matrix.csv`
- `issues/<timestamp>-<slug>.csv`
- `brief/contribution-map.yaml`
- `paper.config.yaml` (runtime configuration)

## Outputs
- Updated `main.tex` with verified results, real figures/tables, factual claims
- Updated issues CSV with `Result_Status=verified` and `Status=DONE`
- Generated LaTeX input files under `paper/results/`
- Drafted abstract (W0)
- Refined prose (RF1)
- Compiled `main.pdf`

## Non-Negotiable Rules
1. **No fabrication**: Only use data from actual result files. Never invent numbers.
2. **Verify before claiming**: Only upgrade `(hypothesis)` to factual claim when CSV data confirms the result.
3. **Bounded claims**: Factual statements must include specific numbers from verified results (e.g., "reduces violations by 12.3%"), not vague improvements.
4. **Dependency enforcement**: Follow the same dependency rules as `empirical-paper-writer` — never mark DONE if dependencies are not DONE/SKIP.

## Workflow

### Phase 1: Results Discovery
1. Read `paper.config.yaml` for runtime configuration.
2. Scan `paper/results/` for all CSV, JSON, and data files.
3. Read `notes/design/experiment-matrix.csv` to identify all planned experiments.
4. Match result files to experiment-matrix rows:
   ```bash
   python3 scripts/discover_results.py --project-dir <paper_dir>
   ```
   See `references/backfill-workflow.md` for naming conventions and the
   `assets/result-file-template.csv` schema.
5. If matches look correct, update the matrix in-place:
   ```bash
   python3 scripts/discover_results.py --project-dir <paper_dir> --update-status
   ```
6. Read the issues CSV and update `Result_Status` for matched experiment issues (E5-E8).

### Phase 2: Paper Back-fill
Execute in order:

1. **Contribution upgrade**:
   - Read `brief/contribution-map.yaml`.
   - For each claim with verified supporting experiments, update `main.tex`:
     - Replace `(hypothesis)` with bounded factual statement.
     - Update Introduction contributions list.

2. **Results section fill**:
   - Main comparison: populate tables from `main_results.csv`.
   - Ablation studies: populate ablation table from ablation results **and** upgrade the surrounding narrative from hypothesis-safe to verified, bounded claims.
   - Robustness/error analysis: populate figures/tables **and** write verified takeaways tied to specific numbers.
   - Efficiency: populate efficiency comparison table **and** write a bounded trade-off discussion (accuracy vs cost).

3. **LaTeX table/figure generation**:
   - Convert CSV results to LaTeX `\input{}` files under `paper/results/`:
     ```bash
     python3 scripts/generate_results_table.py <results.csv> -o paper/results/<name>.tex --bold-best --caption "..." --label "tab:..."
     ```
   - Generate TikZ plots or include matplotlib-exported PDFs where appropriate.
   - Replace `\fbox{...placeholder...}` with actual `\includegraphics` or table references.

4. **Figure resolution**:
   - For each remaining `\fbox{...}` placeholder:
     - If data exists → generate the figure.
     - If data is missing → replace with `[Figure pending: <reason>]`.

5. **Abstract (W0)**:
   - Draft abstract from verified results following the rules in `experiment-evidence.md`:
     - Problem (1 sentence)
     - Method (1-2 sentences)
     - Setting (1 sentence)
     - Key result (1 sentence, verified only)
     - Implication (1 sentence)
   - Maximum 250 words. No citations. No unexpanded acronyms.

6. **Conclusion upgrade**:
   - Update the Conclusion section to remove `(hypothesis)` / `[Pending: ...]` tags for any claim now supported by verified results.
   - Ensure every factual takeaway is **bounded** by specific numbers from verified tables/figures.

7. **Mark issues DONE**:
   - Update E5-E8, W0, and any back-filled Writing issues in the issues CSV.
   - Respect dependency enforcement.

### Phase 3: Polish
1. **RF1 — Rhythm refinement**:
   - Apply `latex-rhythm-refiner` section-by-section.
   - Preserve all citations and verified numbers.

2. **QA**:
   - Run citation audit:
     ```bash
     python3 ../arxiv-paper-writer/scripts/citation_policy.py --project-dir <paper_dir> audit-bib
     python3 ../arxiv-paper-writer/scripts/citation_policy.py --project-dir <paper_dir> audit-tex --issues <issues.csv>
     ```
   - Run issue validation with tex audit:
     ```bash
     python3 ../empirical-paper-writer/scripts/validate_empirical_paper_issues.py <issues.csv> --audit-tex <paper_dir>/main.tex
     ```

3. **Compile**:
   ```bash
   python3 ../arxiv-paper-writer/scripts/compile_paper.py --project-dir <paper_dir> --check-warnings --fail-on-warnings
   ```

4. Deliver `main.tex`, `ref.bib`, figures, and `main.pdf`.

## Runtime Environment
Before running any script:
1. Read `paper.config.yaml` → `runtime.conda_env` or `runtime.python`.
2. If `conda_env` is set, activate it: `conda activate <env_name>`.
3. If `python` is set, use that interpreter directly.
4. If neither is set, ask the user which conda environment to use.

## Relationship to Other Skills
```
paper-from-zero
    ↓ routes to
empirical-paper-writer (design + code + placeholder draft)
    ↓ user runs experiments
results-backfill (this skill: back-fill results + complete paper)
```

## Success Criteria
- All `\fbox` placeholders resolved or explicitly marked `[Pending: <reason>]`.
- No `(hypothesis)` tags remain for claims with verified evidence.
- Abstract is non-placeholder, <=250 words, matches verified results.
- All DONE issues pass dependency check.
- `validate_empirical_paper_issues.py --audit-tex` produces zero warnings for verified issues.
- Paper compiles without `Overfull \hbox` warnings.
