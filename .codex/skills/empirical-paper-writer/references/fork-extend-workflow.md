# Fork & Extend Workflow

Guide for building experiments on top of an existing open-source codebase
rather than writing everything from scratch.

## 1. Selecting the Upstream Repo

Evaluate candidates against these criteria (in priority order):

| Criterion | Why it matters |
|-----------|---------------|
| Official author implementation | Closest match to paper-reported results |
| Recent maintenance (commits in last 6 months) | Fewer compatibility issues |
| Reproducible results (README shows how) | Confirms code actually works |
| Permissive license (MIT / Apache / BSD) | No redistribution restrictions |
| Stars / citations as secondary signal | Community validation, but not decisive |

**Red flags**: no license file, last commit > 2 years ago, results don't match
paper, requires deprecated frameworks.

## 2. Clone & Branch

```bash
# Option A: Fork on GitHub (preserves upstream link)
gh repo fork <UPSTREAM_URL> --clone

# Option B: Clone directly (simpler, no GitHub fork)
git clone <UPSTREAM_URL> experiments/
cd experiments/
git checkout -b our-method <UPSTREAM_COMMIT_HASH>
```

Record in README → "Upstream Repository" table:
- Exact commit hash or tag
- License
- Date of fork

## 3. Minimal Modification Principle

**Goal**: keep our changes as small and additive as possible so that:
- Upstream bugfixes can be merged easily.
- Fair comparison is credible (reviewers can verify we didn't change baseline logic).

### Do

- Add new files for our method (`models/our_method.py`).
- Add new config files (`configs/our_*.yaml`).
- Extend data loaders if needed (add a new class, don't modify existing ones).
- Add a thin wrapper script that calls upstream's `train.py` / `evaluate.py`
  with our config.

### Don't

- Modify upstream model implementations (even "small fixes").
- Change default hyperparameters in upstream configs.
- Restructure the upstream directory layout.
- Delete upstream files.

If an upstream bug must be patched, do it in a **separate commit** with a clear
message (e.g., `fix: patch upstream data loader for Python 3.11 compat`).

## 4. Marking Components in method-components.csv

Use the `source` and `replaceable_by` columns:

```csv
component_id,name,source,replaceable_by,ablation_priority
C1,Transformer Encoder,upstream,—,low
C2,Cross-Attention Module,ours,upstream_self_attn,high
C3,Loss Function,ours,upstream_ce_loss,high
C4,Data Augmentation,upstream,—,low
```

- `source = upstream` → code from the forked repo, unchanged.
- `source = ours` → new code we wrote.
- `replaceable_by` → what to swap in for ablation (links to upstream component
  or simpler alternative).

## 5. Keeping Mergeable with Upstream

```bash
# Add upstream as a remote (if using direct clone)
git remote add upstream <UPSTREAM_URL>

# Periodically fetch and check for relevant fixes
git fetch upstream
git log upstream/main --oneline -10

# Merge specific fixes (cherry-pick preferred over full merge)
git cherry-pick <COMMIT_HASH>
```

Only merge upstream changes that fix bugs or address compatibility. Do **not**
pull in new features that would invalidate your experimental comparison.

## 6. CHANGES_FROM_UPSTREAM.md Template

Create this file in `experiments/`:

```markdown
# Changes from Upstream

Upstream: <REPO_URL>
Commit: <HASH>
Date forked: <YYYY-MM-DD>

## Files Added
| File | Purpose |
|------|---------|
| `models/our_method.py` | Our proposed method implementation |
| `configs/our_main.yaml` | Config for main comparison experiments |

## Files Modified
| File | Change | Reason |
|------|--------|--------|
| `data/loader.py` | Added `OurDataset` class | Support for <DATASET> |
| `requirements.txt` | Added `wandb`, `scipy` | Tracking + statistical tests |

## Files NOT Modified
Upstream training, evaluation, and baseline model files are unchanged.
Baseline results are produced by running upstream code with upstream configs.
```

## 7. Integration with empirical-paper-writer

After forking:
1. Fill `baselines.csv` → `code_url` for each baseline with the upstream repo URL.
2. Fill `method-components.csv` with `source` = `upstream` / `ours`.
3. The `experiment-matrix.csv` should include both upstream baselines (re-run)
   and paper-reported baselines (marked with "†").
4. `experiments/README.md` → fill the "Upstream Repository" table.
5. `experiments/requirements.txt` → merge upstream deps under the
   "Upstream repo dependencies" section.
