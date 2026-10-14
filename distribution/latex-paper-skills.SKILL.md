---
name: latex-paper-skills
description: >
  Write, revise, and validate ML/AI research papers in LaTeX. Use for topic-to-paper
  planning, review papers, empirical papers, verified result backfill, citation
  audits, and academic prose refinement.
license: MIT
metadata:
  version: "0.1.0"
  source: https://github.com/yunshenwuchuxun/latex-paper-skills
  runtime: Python 3.10+ and web research; LaTeX for PDF compilation; optional Gemini and Claude CLIs.
---

# LaTeX Paper Skills

This package includes eight workflows, their shared Python tools, and IEEE LaTeX
templates. Select the workflow that matches the user's deliverable and read its
instructions before starting. Read further references only as that workflow
requires them.

| Request | Workflow to read |
| --- | --- |
| A research topic needs contribution framing, evidence planning, and a paper route | [paper-from-zero](references/skills/paper-from-zero/workflow.md) |
| Write or revise a review or survey; validate citations in an existing LaTeX project | [arxiv-paper-writer](references/skills/arxiv-paper-writer/workflow.md) |
| Plan or draft an empirical paper, including experiment contracts and placeholders | [empirical-paper-writer](references/skills/empirical-paper-writer/workflow.md) |
| Fill an empirical draft with real, verified experiment results | [results-backfill](references/skills/results-backfill/workflow.md) |
| Improve sentence and paragraph rhythm while preserving meaning and citations | [latex-rhythm-refiner](references/skills/latex-rhythm-refiner/workflow.md) |
| Check optional Gemini and Claude collaborators | [check-collaborators](references/skills/check-collaborators/workflow.md) |
| Expand candidate directions or literature using Gemini | [collaborating-with-gemini](references/skills/collaborating-with-gemini/workflow.md) |
| Audit claims and evidence using Claude | [collaborating-with-claude](references/skills/collaborating-with-claude/workflow.md) |

## Resolve installed resources

Determine the absolute directory containing this `SKILL.md`; call it
`<package-root>`. The bundled skill tree is
`<package-root>/references/skills/`. All eight workflows and `_shared/` are
included there; no separate sibling-skill installation is needed.

When following a bundled workflow:

- Resolve `scripts/`, `assets/`, and `references/` relative to that workflow's
  directory, rather than the user's current working directory.
- Resolve `../<other-skill>/` relative to the same directory. A reference to
  another workflow means read its bundled `workflow.md`.
- Replace legacy `.codex/skills/` command prefixes with the absolute bundled
  skill-tree path. Run Python scripts by absolute path.
- Keep the user's paper directory as the working directory, and pass explicit
  absolute output/project paths when the script supports them. Do not create
  papers or caches inside this installed package.

For example, validate a router handoff with:

```bash
python3 "<package-root>/references/skills/paper-from-zero/validate_handoff.py" \
  --project-dir "<paper-dir>"
```

Python helpers use the standard library. Generated experiment projects declare
their own dependencies. Compile with `latexmk`, or `pdflatex` plus `bibtex`, when
available. Gemini and Claude collaboration is optional: if their CLIs or accounts
are unavailable, continue the evidence and writing workflow using the current
agent.

## Preserve evidence gates

Follow the selected workflow's plan approval and issues CSV gates. Verify every
citation against its source. Never fabricate references, measurements, or
significance claims. Keep planned experiments and placeholders distinct from
verified results; bound every paper claim by the available evidence.

## Licenses

The skill instructions and Python tools are distributed under the included
[MIT license](LICENSE). The unmodified `IEEEtran.cls` template retains its own
LPPL 1.3 notices; see [third-party notices](THIRD_PARTY_NOTICES.md).
