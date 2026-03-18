# Experiment Design Reference

A guide for designing experiments in empirical ML/AI papers. Use this during
Phase 0.5 (Method & Experiment Design) to make systematic design decisions
before any prose is written.

## 1. Baseline Selection Criteria

Select 4-8 baselines from three categories:

**Direct competitors** (2-4): methods that tackle the same task with similar inputs.
- Prioritize last 2 years of publications.
- Prefer methods with public code or official implementations.
- Include the current SOTA if identifiable.

**Foundational methods** (1-2): well-known classics that define the field baseline.
- These anchor the lower bound of comparison.
- Often cited in most papers on the topic.

**Ablation anchors** (1-2): simplified or degraded versions of the proposed method.
- E.g., the proposed method minus its core innovation module.
- These directly test whether the novel component matters.

**Selection checklist** for each candidate baseline:
- [ ] Paper is accessible (arXiv, venue proceedings, or preprint).
- [ ] Code or pretrained weights are publicly available (preferred).
- [ ] Can be evaluated on the same datasets with the same metrics.
- [ ] Results are either reproducible or reported in the original paper.

Record all candidates in `notes/design/baselines.csv`.

## 2. Experiment Matrix Design Patterns

### Main comparison table structure

Rows = methods (ours + baselines). Columns = metrics per dataset.

```
           Dataset A          Dataset B
Method   | Metric1  Metric2 | Metric1  Metric2
---------|---------|---------|---------|--------
Baseline1|         |         |         |
Baseline2|         |         |         |
...      |         |         |         |
Ours     |         |         |         |
```

**Design rules:**
- Use the same data splits, preprocessing, and evaluation protocol for all methods.
- For baselines without public code, use results reported in their papers and
  note this clearly (e.g., "†" = results from original paper).
- Report mean ± std over multiple runs when possible (≥3 runs recommended).

### Per-dataset vs unified evaluation
- Per-dataset: when datasets have different characteristics worth analyzing.
- Unified (average across datasets): when a single aggregate number is meaningful.
- When in doubt, report both.

### Metric selection
- Primary metric: the main metric the community uses for this task.
- Secondary metrics: complementary metrics that capture different aspects
  (e.g., precision + recall alongside F1; latency alongside accuracy).
- Justify every metric selection in the experimental setup section.

Record the full matrix in `notes/design/experiment-matrix.csv`.

## 3. Ablation Design Patterns

### Factor identification
Walk through `notes/design/method-components.csv` and identify:
1. **Core innovation components** (ablation_priority = high): MUST be ablated.
2. **Architecture choices** (medium): worth testing if space allows.
3. **Hyperparameter choices** (low): include only if they significantly affect results.

### Replacement strategies
For each factor, define how to ablate it:
- **Remove**: disable the component entirely (e.g., skip the module).
- **Degrade**: replace with a simpler baseline version (e.g., replace attention with average pooling).
- **Random**: replace with random initialization or random outputs.

### Ablation table structure

Rows = method variants. Columns = metrics.

```
Variant                | Metric1 | Metric2 | Δ from full
-----------------------|---------|---------|------------
Full model (ours)      |         |         | —
w/o component A        |         |         |
w/o component B        |         |         |
A replaced by simple X |         |         |
```

### Best practices
- Ablate one factor at a time (single-factor ablation) as the default.
- Combination ablations only when factors interact (justify the interaction hypothesis).
- Always include the full model as the first row for reference.

## 4. Statistical Rigor

### Multi-run reporting
- Run experiments ≥3 times with different random seeds.
- Report: mean ± standard deviation.
- For deterministic methods, state that no variance is applicable.

### When to use significance tests
- When the improvement margin is small (< 2% relative).
- When comparing against a strong baseline on a well-established benchmark.
- Common tests: paired t-test, Wilcoxon signed-rank test, bootstrap confidence intervals.
- Report p-values; state the significance threshold (typically p < 0.05).

### Results reporting format
- Bold the best result per column.
- Underline the second-best (optional but common).
- Use consistent decimal places (typically 1-2 for percentages, 3-4 for loss values).
- Mark placeholder results clearly: use `—` or `[placeholder]`, never fake numbers.

## 5. Placeholder-Safe Experiment Writing

### For `planned` experiments
- Describe the experiment design intent: what will be measured, why, and how.
- Do NOT describe expected outcomes as if they are results.
- Use language like: "We plan to evaluate...", "This experiment will test whether...".

### For `placeholder` results
- Reserve table/figure slots with clear labels: `[Results pending]`.
- In text, use: "Results for this comparison are reserved and will be reported
  upon completion of experiments."
- Do NOT write conclusions based on placeholder results.

### In conclusions
- Bound takeaways to verified results only.
- If core results are still placeholder, state explicitly:
  "The conclusions above are contingent on the completion of experiments X, Y, Z."
- Never claim superiority, novelty validation, or statistical significance
  based on placeholder data.

## 6. Using Existing Baseline Code

When your experiments build on an existing open-source implementation:

### Selecting the upstream repo
- Prefer official author implementations over third-party reproductions.
- Verify: code runs on current CUDA/Python versions, results match paper claims.
- Check license compatibility (MIT/Apache/BSD preferred; GPL may restrict).

### Fork & Extend workflow
1. Clone or fork the upstream repo into `experiments/`.
2. Record the exact commit hash in README → "Upstream Repository" table.
3. Create our method as an **additive module** — minimize changes to upstream code.
4. Keep upstream evaluation scripts intact for fair comparison.
5. Add our configs in `configs/` without modifying upstream defaults.

### Fair comparison protocol
- Same data splits, preprocessing, tokenization for all methods.
- Same hardware and batch size (or document differences and normalize).
- For baselines without code: cite paper-reported numbers with "†" marker.
- For baselines with code: re-run in our environment; report both our-run and paper-reported.

### Documentation requirements
- `CHANGES_FROM_UPSTREAM.md`: list every file modified and why.
- `requirements.txt`: merge upstream deps with ours, mark origin of each.
- `baselines.csv` → `code_url`: fill for every baseline with public code.
