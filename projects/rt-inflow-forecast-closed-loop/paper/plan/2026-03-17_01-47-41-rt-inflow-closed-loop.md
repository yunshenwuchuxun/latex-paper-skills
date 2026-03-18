# Paper Plan: Rolling Calibration for Real-Time Reservoir Inflow Forecasting and Closed-Loop Forecast-Dispatch-Implementation Coupling

## Goal
- Produce an empirical ML/AI paper on Rolling Calibration for Real-Time Reservoir Inflow Forecasting and Closed-Loop Forecast-Dispatch-Implementation Coupling using the IEEEtran LaTeX template
- Target a near-submission draft with verified citations and explicit result status tracking
- Keep all quantitative claims tied to verified evidence or marked placeholders

## Project Config
- Workflow mode: standard
- Target venue: arXiv
- Preferred venues: arXiv
- Style mode: neutral
- Use `paper.config.yaml` as the machine-readable source policy and venue preference file

## Scope
- In: Problem framing, method narrative, experimental setup, results placeholders/verified results, limitations
- Out: Fabricated results, unsupported superiority claims, non-academic formats

## Kickoff Gate (must be confirmed before writing)
- **STOP**: Do not write prose into `main.tex` until this gate is confirmed and the issues CSV exists.
- [x] User confirmed scope + outline in chat
- Venue/template: IEEEtran (arXiv or workshop-preprint style)
- Target length: 6-10 pages of main text (references excluded)
- "Latest" definition: as-of date = 2026-03-17_01-47-41
- Result policy: only verified results may be stated as factual outcomes

## Clarification Q&A (record answers)
| Question | Answer |
|---|---|
| What is the primary contribution claim? | TBD |
| Which datasets/baselines are mandatory? | TBD |
| Which ablations are non-negotiable? | TBD |
| What counts as acceptable evidence for the main claim? | TBD |
| What results are already known vs still placeholders? | TBD |

## Contribution Contract
- Primary claim:
- Secondary claims:
- Non-claims / out-of-scope statements:
- Strongest reviewer objection we must survive:

## Experiment Contract
- Datasets:
  - Name, size, splits (train/val/test), source URL
  - Selection reason: why this dataset tests the primary claim
- Baselines: (see `notes/design/baselines.csv` for full details)
  - Direct competitors (2-4): current SOTA on same task, last 2 years
  - Foundational methods (1-2): well-known classics anchoring the lower bound
  - Ablation anchors (1-2): our method minus core innovation
  - For each: name, category, code availability, reported results
- Metrics:
  - Primary metric: main community metric for this task + selection reason
  - Secondary metrics: complementary aspects (e.g., precision + recall alongside F1)
- Ablations: (see `notes/design/method-components.csv` for component list)
  - Factor × replacement strategy matrix (remove / degrade / random replace)
  - Expected impact direction for each factor
  - Minimum 4 factors; prioritize core innovation components
- Error analysis / robustness checks:
  - Robustness: noise levels, distribution shift, domain transfer
  - Error analysis: failure case categories, sampling protocol
  - Efficiency: params (M), FLOPs (G), inference latency (ms)
- Statistical tests or confidence reporting:
  - Number of runs (≥3 recommended), random seeds
  - Test type (paired t-test / Wilcoxon / bootstrap CI), significance threshold
- Result status policy (`planned` / `placeholder` / `verified`):
  - Which results are already available vs planned
  - Timeline for verification (if known)

## Confirmed Outline
1. Introduction - motivation, gap, contribution statement, roadmap
2. Related Work - closest methods and distinction from prior work
3. Method - formulation, architecture/training logic, design rationale
4. Experimental Setup - datasets, baselines, metrics, implementation details
5. Results - main results, ablations, analysis, explicit result status
6. Limitations - caveats, failure modes, unresolved risks
7. Conclusion - bounded takeaways only

## Plan Notes
- Keywords used for discovery:
- Candidate titles proposed:
- Baseline shortlist: (summary; full details in `notes/design/baselines.csv`)
- Visualization plan (types + placement):
- Claims requiring verified evidence before finalization:
- Placeholder policy notes:

## Phase 0.5 Design Artifacts
- `notes/design/baselines.csv`: baseline & SOTA competitive landscape
- `notes/design/experiment-matrix.csv`: full experiment design matrix
- `notes/design/method-components.csv`: pipeline component inventory
- These CSVs are the design contract for Gate 1 issue creation.

## Issue CSV
- Path: <paper_dir>/issues/2026-03-17_01-47-41-rt-inflow-closed-loop.csv
- Must share the same timestamp/slug as this plan
- This CSV is the execution contract
- Experiment and writing rows must include claim/evidence/result-status fields
