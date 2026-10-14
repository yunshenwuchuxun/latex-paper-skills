# Reproducibility Checklist

Aligned with NeurIPS / ICML reproducibility standards. Check each item before
submission. Items marked **(required)** are non-negotiable; others are strongly
recommended.

## Code

- [ ] **(required)** Source code is included or will be released upon acceptance.
- [ ] **(required)** `requirements.txt` (or equivalent) lists all dependencies with versions.
- [ ] `requirements-lock.txt` generated via `pip freeze` is committed.
- [ ] A single entry-point script (`run_all.py`) reproduces all main results.
- [ ] README documents how to install, configure, and run experiments.

## Data

- [ ] **(required)** Dataset sources are cited with URLs or DOIs.
- [ ] Preprocessing scripts are included or described step-by-step.
- [ ] Train / validation / test split definitions are explicit (file lists or random seed).
- [ ] If proprietary data is used, a synthetic or public substitute is provided for reviewers.

## Environment

- [ ] **(required)** Python version is recorded (e.g., `python_requires` or README).
- [ ] CUDA and cuDNN versions are recorded.
- [ ] GPU model(s) used for training and evaluation are listed.
- [ ] OS and driver versions are noted (especially for non-standard setups).

## Training

- [ ] **(required)** Random seeds are fixed and documented in config YAML.
- [ ] **(required)** Hyperparameter search range and final values are reported.
- [ ] Number of epochs / steps and early-stopping criteria are stated.
- [ ] Optimizer, learning rate schedule, weight decay, and batch size are documented.
- [ ] Total training time (wall-clock) per experiment is reported.

## Evaluation

- [ ] **(required)** All metrics are formally defined (formula or reference).
- [ ] **(required)** Number of evaluation runs is stated (≥ 3 recommended).
- [ ] Mean ± std (or confidence intervals) are reported for stochastic results.
- [ ] Statistical significance tests are applied where improvement < 2% relative.
- [ ] Evaluation code is separate from training code and independently runnable.

## Hardware

- [ ] GPU model, count, and memory are listed.
- [ ] Training wall-clock time per run is reported.
- [ ] Inference latency / throughput is measured (if efficiency is claimed).

## Upstream Code (if forking)

- [ ] Upstream repo URL and exact commit hash are recorded.
- [ ] License compatibility is verified and stated.
- [ ] `CHANGES_FROM_UPSTREAM.md` lists all modifications with rationale.
- [ ] Upstream evaluation scripts are preserved for fair baseline comparison.
