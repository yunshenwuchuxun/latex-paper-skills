# Experiments (rt-inflow-forecast-closed-loop)

This folder contains runnable code for the empirical paper in `../paper/`.

## Environment

Install dependencies:
```bash
pip install -r requirements.txt
```

Python 3.7+ is supported; CPU runs are the default for deterministic results.

## Data

The default config uses the ResOpsUS v2 time series under:
- `data/raw/ResOpsUS2/ResOpsUS/time_series_all/ResOpsUS_<DAM_ID>.csv`
- `data/raw/ResOpsUS2/ResOpsUS/attributes/reservoir_attributes.csv`

If you change the dataset location, update `configs/default.yaml`.

## Public repo note

The development workflow identified ResOpsUS v2 as the target public dataset, downloaded it locally, and used it to generate the retained result files in `../paper/results/`.

The raw dataset is intentionally not shipped in this public GitHub snapshot because it is large and belongs in a local data directory. To reproduce the retained experiments, download ResOpsUS v2 yourself, place it under the paths above (or update `configs/default.yaml`), and rerun `run_all.py`.

## Experiment Contract

The experiment contract is encoded in:
- `../paper/notes/design/experiment-matrix.csv`

The runner supports the following experiment types:
- `main_comparison`
- `ablation`
- `robustness`
- `efficiency`

## Run

Dry-run (recommended):
```bash
python run_all.py --config configs/default.yaml --dry-run
python run_all.py --config configs/default.yaml --type main_comparison --dry-run
```

Execute:
```bash
python run_all.py --config configs/default.yaml --type main_comparison
python run_all.py --config configs/default.yaml --type ablation
python run_all.py --config configs/default.yaml --type robustness
python run_all.py --config configs/default.yaml --type efficiency
```

Notes:
- `evaluate.py` computes results at the suite level (it is idempotent and avoids per-row reruns).
- `train.py` is not required for the current baselines; the ML-LSTM forecaster is trained inside `evaluate.py`.

## Outputs

Verified results are written to `../paper/results/`:
- `forecast_results.csv` + `forecast_results_table.tex`
- `main_results.csv` + `main_results_table.tex`
- `ablation_results.csv` + `ablation_results_table.tex`
- `robustness_results.csv` + `robustness_table.tex`
- `efficiency_results.csv` + `efficiency_table.tex`

To regenerate the LaTeX tables from the CSVs (without rerunning simulations):
```bash
python render_tables.py
```
