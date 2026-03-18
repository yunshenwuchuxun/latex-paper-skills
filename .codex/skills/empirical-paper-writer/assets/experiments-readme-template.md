# Experiments — <PROJECT_NAME>

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

## Environment Setup

1. Create/activate conda environment:
   ```bash
   conda activate <CONDA_ENV>
   ```
   Or use the configured Python interpreter: `<PYTHON_PATH>`

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Project Structure
```
experiments/
├── run_all.py          # Main experiment orchestrator
├── configs/
│   └── default.yaml    # Default experiment configuration
├── train.py            # Training script
├── evaluate.py         # Evaluation script
├── models/             # Model implementations
├── data/               # Data loading utilities
└── utils/              # Shared utilities
```

## Running Experiments

### Run all experiments
```bash
python run_all.py --config configs/default.yaml
```

### Run specific experiment type
```bash
python run_all.py --config configs/default.yaml --type main_comparison
python run_all.py --config configs/default.yaml --type ablation
python run_all.py --config configs/default.yaml --type robustness
```

## Configuration
See `configs/default.yaml` for all configurable parameters:
- `data`: dataset paths, splits, preprocessing
- `model`: architecture, hyperparameters
- `training`: epochs, optimizer, learning rate
- `evaluation`: metrics, seeds, num_runs

## Output
Results are saved to `../paper/results/`:
- `main_results.csv` — main comparison table
- `ablation_results.csv` — ablation study results
- `robustness_results.csv` — robustness analysis
- `efficiency_results.csv` — efficiency comparison

## Reproducibility Notes

- **Random seeds**: All experiments use seeds defined in config YAML → `evaluation.seeds`
- **Hardware**: Record GPU model, CUDA version, driver version in results metadata
- **Expected runtime**: ~X hours per `main_comparison` run on `<GPU_MODEL>`
- **Checkpoints**: Saved to `checkpoints/` (gitignored); best model selected by validation metric

## After Experiments Complete
Invoke the `results-backfill` SKILL to:
1. Auto-detect verified results
2. Replace placeholders in the paper draft
3. Generate LaTeX tables/figures
4. Draft the abstract
5. Compile final PDF
