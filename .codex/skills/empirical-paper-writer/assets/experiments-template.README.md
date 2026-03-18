# Experiments — <PROJECT_NAME>

This folder is **generated scaffolding**. The `empirical-paper-writer` skill does **not** run experiments; it only
creates a runnable code skeleton that you execute locally.

## Runtime source of truth

Read `../paper/paper.config.yaml` → `runtime.*` to decide whether you use a conda env or a specific Python interpreter.

## Upstream Repository (if applicable)

If this project extends or builds upon an existing open-source codebase:

| Field | Value |
|-------|-------|
| Upstream repo | `<URL>` |
| Forked commit / tag | `<COMMIT_HASH or TAG>` |
| License | `<LICENSE>` |
| Our modifications | See `CHANGES_FROM_UPSTREAM.md` or diff summary below |

Key differences from upstream:
- `models/` — added `<OUR_MODULE>` alongside original architectures
- `data/` — extended data pipeline for `<ADDITIONAL_DATASET>`
- `configs/` — added experiment configs for our method variants

## Install deps

Create/activate your environment, then:
```bash
pip install -r requirements.txt
```

## What to implement

The files `train.py` and `evaluate.py` contain **TODO** stubs. You should implement:
- dataset loading in `data/`
- model in `models/`
- metrics in `metrics/`
- training loop in `train.py`
- evaluation loop in `evaluate.py`

## Experiment matrix contract

Experiments are defined in:
- `../paper/notes/design/experiment-matrix.csv`

The runner reads that CSV and orchestrates experiments by `type`:
- `main_comparison`
- `ablation`
- `robustness`
- `efficiency`

## Run (dry-run recommended)

Show what would run:
```bash
python run_all.py --config configs/default.yaml --dry-run
python run_all.py --config configs/default.yaml --type main_comparison --dry-run
```

Execute (requires you to implement the TODOs first):
```bash
python run_all.py --config configs/default.yaml --type main_comparison
```

## Outputs (results-backfill interface)

Write verified results to `../paper/results/` (relative to this folder), using these canonical files:
- `main_results.csv`
- `ablation_results.csv`
- `robustness_results.csv`
- `efficiency_results.csv`

After you have real result CSVs, run the `results-backfill` skill to replace placeholders in `../paper/main.tex`.

## Reproducibility Notes

- **Random seeds**: All experiments use seeds defined in config YAML → `evaluation.seeds`
- **Hardware**: Record GPU model, CUDA version, driver version in results metadata
- **Expected runtime**: ~X hours per `main_comparison` run on `<GPU_MODEL>`
- **Checkpoints**: Saved to `checkpoints/` (gitignored); best model selected by validation metric

