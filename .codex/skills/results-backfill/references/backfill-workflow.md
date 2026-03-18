# Back-fill Workflow Reference

Detailed reference for the results-backfill SKILL's workflow phases.

## Phase 1: Results Discovery — Details

### File Naming Convention
Result files must live in `paper/results/` and follow one of these naming
patterns so that `scripts/discover_results.py` can auto-match them to
`experiment-matrix.csv` rows:

| Pattern | Matches `type` column |
|---------|-----------------------|
| `main_results.csv` or `main_results_<dataset>.csv` | `main_comparison` |
| `ablation_<component>.csv` | `ablation` |
| `robustness_<dataset>.csv` | `robustness` |
| `efficiency_<dataset>.csv` | `efficiency` |
| `<experiment_id>.csv` (exact ID as stem) | any row with that ID |

If `experiment-matrix.csv` includes an optional `output_file` column, the
value there takes precedence over pattern-based matching.

Each result CSV should follow the schema in
`assets/result-file-template.csv`:

| Column | Description |
|--------|-------------|
| `method` | Method or model name |
| `dataset` | Dataset used |
| `metric_name` | Name of the metric |
| `metric_value` | Numeric value (use `±` for std, e.g., `78.3 ± 1.2`) |
| `seed` | Random seed (for reproducibility) |
| `timestamp` | ISO timestamp of the run |
| `notes` | Free-text notes |

### File Matching Strategy
Match result files to experiment-matrix rows using these conventions:
- `main_results.csv` → rows with `type=main_comparison`
- `ablation_*.csv` → rows with `type=ablation`
- `robustness_*.csv` → rows with `type=robustness`
- `efficiency_*.csv` → rows with `type=efficiency`

If naming does not match, inspect CSV headers and content to determine experiment type.

### Status Update Protocol
1. Read each result CSV.
2. Verify it contains the expected columns (metrics from experiment-matrix).
3. Verify row count matches the expected baselines/conditions.
4. If valid, update `result_status` in experiment-matrix to `verified`.
5. Update corresponding issue `Result_Status` to `verified`.

## Phase 2: Paper Back-fill — Details

### Contribution Upgrade Patterns
| Before | After |
|--------|-------|
| `We hypothesize that X reduces Y (hypothesis)` | `X reduces Y by 12.3% on average across three datasets (Table 2)` |
| `The proposed method is expected to improve Z` | `The proposed method improves Z by 8.7 ± 1.2 points (Table 3)` |

### LaTeX Table Generation
From a result CSV:
```python
# Read CSV → generate LaTeX tabular
# Bold best result per metric
# Include ± std if available
# Add \input{results/main_table.tex} to main.tex
```

### Figure Generation
Priority order:
1. TikZ/pgfplots (native LaTeX, best quality)
2. Matplotlib → PDF export (for complex plots)
3. Raw table reference `[See Table X]` (fallback)

### Placeholder Replacement Map
| Placeholder Pattern | Replacement |
|--------------------|-------------|
| `\fbox{Main comparison results}` | `\input{results/main_table.tex}` |
| `\fbox{Ablation results}` | `\input{results/ablation_table.tex}` |
| `\fbox{Robustness figure}` | `\includegraphics{results/robustness.pdf}` |
| `(hypothesis)` | Bounded factual claim with numbers |
| `[Results pending]` | Actual result text |

## Phase 3: Polish — Details

### Rhythm Refinement Checklist
- [ ] Vary sentence lengths within each paragraph
- [ ] Remove filler phrases ("It is worth noting that", "As can be seen")
- [ ] Preserve all `\cite{}` commands exactly
- [ ] Preserve all verified numbers exactly
- [ ] Check that no new placeholder language is introduced

### QA Checklist
- [ ] All citations in `ref.bib` are referenced in text
- [ ] All `\cite{}` in text have corresponding `ref.bib` entries
- [ ] No orphan figures/tables (referenced but not defined, or vice versa)
- [ ] Abstract word count <= 250
- [ ] No `\fbox` remaining (unless explicitly marked pending)
- [ ] No `(hypothesis)` remaining for verified experiments
- [ ] Paper compiles cleanly
