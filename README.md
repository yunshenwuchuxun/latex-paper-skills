# latex-paper-skills

New: [Beginner Workflow Guide (Chinese)](BEGINNER_WORKFLOW.zh-CN.md)

English | [简体中文](README.zh-CN.md)

> Portable **AI agent skill bundle** for writing ML/AI academic papers —
> from topic to compiled PDF, with verified BibTeX citations, gated
> workflows, and multi-agent collaboration.

## What This Repo Is

This repository is not a single paper project. It is a reusable skill bundle for AI-assisted academic writing.

In this public snapshot, the repo keeps:

- the reusable writing skills under `.codex/skills/`
- the repo-level workflow and documentation
- two curated showcase projects: one empirical and one review

The repo intentionally does **not** keep bulky local datasets, machine-local settings, or cache databases. For the empirical showcase, the raw dataset used during development has been removed, but the retained code, result files, figures, and final PDF still show that the workflow completed a real data-and-experiment loop.

## Status & Tested Models

The showcases in this repo were developed and tested with **GPT-5.2 xhigh**. Using **GPT-5.4** is expected to yield better results. Test coverage is still limited — the workflow has significant untapped potential, though undiscovered bugs may exist.

## How It Works

<p align="center">
  <img src="picture/pipeline-en.svg" alt="Pipeline Overview" />
</p>

**Optional multi-agent collaboration:**

| Agent | Role | Tool |
|-------|------|------|
| Gemini | Breadth — literature expansion, keyword clusters, alternative framings | `gemini_bridge.py` |
| Claude | Depth — claim stress-testing, evidence audit, routing judgment | `claude_bridge.py` |
| Health check | Verify both CLIs are installed and API-reachable | `check-collaborators` |

## Skill Catalog

All skills live under `.codex/skills/`. Each has a `SKILL.md` (the executable spec an agent follows), plus optional `scripts/`, `assets/`, and `references/`.

### Core Pipeline

| Skill | What it does |
|-------|-------------|
| **paper-from-zero** | Router. Topic → literature search → innovation framing → contribution map → evidence matrix → route to writer. |
| **arxiv-paper-writer** | Review/survey executor. Gated IEEEtran LaTeX workflow with issues CSV contract, per-issue writing loop, citation verification, and QA. |
| **empirical-paper-writer** | Experimental paper executor. Extends the review workflow with experiment matrices, result status tracking (`planned`/`placeholder`/`verified`), and evidence-claim mapping. |
| **latex-rhythm-refiner** | Prose polisher. Varies sentence/paragraph rhythm, removes filler, strictly preserves all `\cite{}` positions. |
| **results-backfill** | Back-fills real experiment results into an existing draft. Resolves placeholders, upgrades hypotheses to factual claims, generates figures. |

### Collaboration Layer

| Skill | What it does |
|-------|-------------|
| **collaborating-with-gemini** | Breadth co-pilot via Gemini CLI. Structured JSON + session persistence. |
| **collaborating-with-claude** | Depth co-pilot via Claude Code CLI. Claim stress-testing and evidence audit. |
| **check-collaborators** | Health check — verifies CLI installation, auth, and API reachability. |

## Gated Workflow

Both writer skills enforce strict gates:

<p align="center">
  <img src="picture/gated-workflow-en.svg" alt="Gated Workflow" />
</p>

## Quick Start

### Prerequisites

- Python 3.8+
- LaTeX environment (`pdflatex` + `bibtex`, or `latexmk`)
- AI agent runtime that reads `SKILL.md` (Codex CLI, Claude Code, etc.)

### Full pipeline (topic → PDF)

```text
Use the paper-from-zero skill. My topic is: <your topic>
```

### Direct review paper

```text
Use the arxiv-paper-writer skill. Write a review article about <topic>.
```

### Direct empirical paper

```text
Use the empirical-paper-writer skill. Write an experimental paper about <topic>.
```

### Prompt templates: specify datasets and cloud execution

You can specify datasets, runtime budget, and an intended cloud platform directly in natural language.

```text
Use the empirical-paper-writer skill.
Topic: <topic>.
Mandatory datasets: <Dataset A>, <Dataset B>.
Primary dataset: <Dataset A>.
Do not use private data.
Design a compute-aware experiment plan for a single A100 80GB.
```

```text
Use the empirical-paper-writer skill.
Topic: <topic>.
Dataset: <dataset name> from local path <path>.
Target runtime: cloud A100 x1, max 8 hours.
Need a local smoke run first, then a full cloud run.
Keep the claims bounded by this compute budget.
```

```text
Use the empirical-paper-writer skill.
Topic: <topic>.
Mandatory datasets: <dataset names>.
Target platform: AutoDL / Lambda / Slurm cluster.
Generate experiments/, configs/default.yaml, and an experiments README for cloud execution.
Assume I will run the jobs myself and then use results-backfill after real CSVs are available.
```

Notes:
- The skill can design for your dataset and cloud budget.
- The skill does not automatically provision or submit cloud jobs for you.
- Real results still need to be produced outside the AI session and written to `paper/results/`.

## Shared Script Engine

`.codex/skills/arxiv-paper-writer/scripts/` contains the core tooling shared by both writers:

| Script | Purpose |
|--------|---------|
| `arxiv_registry.py` | arXiv metadata/BibTeX cache (SQLite) |
| `compile_paper.py` | LaTeX compilation (latexmk or pdflatex+bibtex) |
| `citation_policy.py` | Citation audit (bib/tex consistency, lint) |
| `source_ranker.py` | Source quality scoring |
| `style_profile.py` | Target venue style checking |
| `issue_workflow.py` | Issue execution helpers |
| `bootstrap_ieee_review_paper.py` | Scaffold IEEEtran project skeleton |
| `create_paper_plan.py` | Generate paper plan from outline |
| `validate_paper_issues.py` | Validate issues CSV integrity |

Shared utilities (`paper_utils.py`, `source_policy_utils.py`) live in `.codex/skills/_shared/`.

## Non-Negotiable Rules

- **No prose before approval** — `main.tex` stays skeleton-only until the plan is approved and the issues CSV exists.
- **Issues CSV is the contract** — update status per issue; only mark `DONE` when acceptance criteria are met.
- **Citations must be verified** — every citation is checked against an online source before entering `ref.bib`.
- **Never fabricate** citations, results, or significance claims.

## Public Showcases

This public snapshot keeps two curated showcase projects:

| Project | Type | What it demonstrates | Start here |
|--------|------|----------------------|------------|
| `projects/rt-inflow-forecast-closed-loop` | Empirical paper | Topic framing, experiment design artifacts, local dataset integration, verified result files, figures, and back-filled paper writing | `README.md`, `paper/main.pdf`, `paper/results/`, `experiments/README.md` |
| `projects/peft-survey-2022-2026` | Review paper | Topic framing, outline/plan approval, issues-driven writing, literature organization, citation-verified review drafting, and final paper | `README.md`, `main.pdf`, `plan/`, `issues/` |

If you only want the fastest tour:

1. Open `projects/rt-inflow-forecast-closed-loop/README.md` for the empirical route.
2. Open `projects/peft-survey-2022-2026/README.md` for the review route.
3. Read `BEGINNER_WORKFLOW.zh-CN.md` if you want the end-to-end workflow explanation in Chinese.

## Project Structure

```
latex-paper-skills/
├── .codex/skills/
│   ├── paper-from-zero/              # Router: topic → writer skill
│   ├── arxiv-paper-writer/           # Review paper executor + shared scripts
│   ├── empirical-paper-writer/       # Empirical paper executor
│   ├── results-backfill/             # Back-fill real results into draft
│   ├── latex-rhythm-refiner/         # Prose polisher
│   ├── collaborating-with-claude/    # Claude Code bridge
│   ├── collaborating-with-gemini/    # Gemini CLI bridge
│   ├── check-collaborators/          # CLI health check
│   ├── _shared/                      # Shared utilities across skills
│   └── _orchestration/               # Workflow orchestration config
├── projects/
│   ├── rt-inflow-forecast-closed-loop/  # Empirical showcase
│   └── peft-survey-2022-2026/           # Review showcase
├── picture/                          # SVG diagrams for README
├── ARCHITECTURE.md                   # Detailed architecture analysis
├── BEGINNER_WORKFLOW.zh-CN.md        # Beginner workflow guide (Chinese)
├── README.md
└── README.zh-CN.md
```

## Related

- Forked from [renocrypt/latex-arxiv-SKILL](https://github.com/renocrypt/latex-arxiv-SKILL)
- Workflow inspired by [appautomaton/agent-designer](https://github.com/appautomaton/agent-designer) (issue-driven development)
- Uses [IEEEtran](https://ctan.org/pkg/ieeetran) LaTeX class

## Star History

<p align="center">
  <a href="https://www.star-history.com/#yunshenwuchuxun/latex-paper-skills&renocrypt/latex-arxiv-SKILL&Date">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=yunshenwuchuxun/latex-paper-skills,renocrypt/latex-arxiv-SKILL&amp;type=Date&amp;theme=dark" />
      <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=yunshenwuchuxun/latex-paper-skills,renocrypt/latex-arxiv-SKILL&amp;type=Date" />
      <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=yunshenwuchuxun/latex-paper-skills,renocrypt/latex-arxiv-SKILL&amp;type=Date" />
    </picture>
  </a>
</p>

## License

This repository is released under the [MIT License](LICENSE).
