# rt-inflow-forecast-closed-loop

English | [简体中文](README.zh-CN.md)

Empirical showcase for the `empirical-paper-writer` + `results-backfill` workflow.

## What this example demonstrates

This project is the empirical-route example retained in the public repository.

It shows that the workflow did not stop at outline generation:

- the topic was framed into claims, evidence needs, and a paper plan
- an experiment contract was created under `paper/notes/design/` and `paper/issues/`
- a public dataset target was identified and integrated into the experiment code
- experiment results were generated, saved to `paper/results/`, and then back-filled into the paper
- the final paper and figures were compiled from those retained artifacts

## What this project keeps

- `paper/main.tex` and `paper/main.pdf`
- `paper/plan/` and `paper/issues/`
- `paper/results/*.csv` and `paper/results/*.json`
- `paper/figures/*.pdf`
- runnable experiment code under `experiments/`

## Data note

During development, the workflow identified ResOpsUS v2 as the target public dataset, downloaded it locally, and used it for the retained experiments. The raw dataset directory is intentionally removed from this public repository to keep the repo lightweight.

To reproduce:

1. Download ResOpsUS v2.
2. Place it under `experiments/data/raw/ResOpsUS2/...` or update `experiments/configs/default.yaml`.
3. Run the experiment suites from `experiments/`.

## Start here

If you want to inspect this example quickly, open these in order:

1. `paper/main.pdf` — the final paper artifact.
2. `paper/notes/design/experiment-matrix.csv` — the experiment contract.
3. `paper/results/` — the retained verified outputs.
4. `experiments/README.md` — how data and runs map into the retained results.
5. `experiments/configs/default.yaml` — the dataset paths and evaluation setup.

## Why it is a useful showcase

- It shows the full empirical route: topic framing, design artifacts, issues contract, runnable experiments, verified result files, and final paper.
- The retained `paper/results/` files and `paper/figures/` are outputs from real runs, not placeholders.
