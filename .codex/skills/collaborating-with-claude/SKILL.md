---
name: collaborating-with-claude
description: >
  Use the Claude Code CLI as a depth-analysis co-pilot for paper-from-zero.
  Primary role: claim tree compression, logical hole detection, evidence
  sufficiency audit, and review/empirical routing judgment.
  Also supports generic code collaboration as fallback.
metadata:
  short-description: Depth co-pilot (Claude) for paper-from-zero
---

# Collaborating with Claude Code (Codex)

Use Claude Code CLI as a **depth-analysis** collaborator for paper-from-zero,
or as a generic code collaborator in fallback mode.

This skill provides a lightweight bridge script (`scripts/claude_bridge.py`)
that returns structured JSON and supports multi-turn sessions via `SESSION_ID`.

> **Shared rules**: This skill inherits all shared rules from
> `../../_shared/collaboration-base.md` (core rules, candidates-only
> constraint, fallback code-collaboration mode, safety guardrails, and
> collaboration state capsule format).  Only Claude-specific additions
> are listed below.

## When to Use
- contribution-map initial draft needs claim-level stress testing.
- evidence-matrix needs sufficiency audit (does evidence match claim strength?).
- Routing decision (review vs empirical) needs adversarial challenge.
- A specific claim needs deep falsification analysis.
- Fallback: generic code collaboration (analysis, patch, review).

## When NOT to Use
- Broad literature expansion or adjacent-area scanning (use Gemini).
- Generating candidate framing directions (use Gemini).
- Generating `ref.bib` entries or verified citations.
- Tasks requiring breadth exploration rather than depth analysis.

## Claude-Specific Rules
- Always run the bridge script with `--help` first if you are unsure of parameters.
- Prefer file/line references; run the bridge with `--cd` set to the repo root.
  Use `--add-dir` when Claude needs access to additional directories.
- For automation, prefer `--SESSION_ID` (resume). Session selectors are mutually
  exclusive: choose one of `--SESSION_ID`, `--continue`, or `--session-id`.
- Ensure Claude Code is logged in before running headless commands (run `claude`
  and `/login` once if needed).
- Streamed JSON requires `--verbose`; the bridge enables this automatically.

## Model Selection

Claude Code supports model aliases, so you can use `--model sonnet` / `--model opus` instead of hard-coding versioned model IDs.

- If you omit `--model`, Claude Code uses its configured default (typically from `~/.claude/settings.json`, optionally overridden by `.claude/settings.json` and `.claude/settings.local.json`).
- If you need strict reproducibility, pass a full model name via `--model <full-name>`.
- For `claim-stress-test` and `route-review-vs-empirical` templates, prefer `opus`.
- For `evidence-sufficiency-audit`, `sonnet` is sufficient.

## Quick Start (shell-safe)

If your prompt contains Markdown backticks, use a heredoc; see `references/shell-quoting.md`.

```bash
PROMPT="$(cat <<'EOF'
Review src/auth.py around login() and propose fixes.
OUTPUT: Unified Diff Patch ONLY.
EOF
)"
python3 .codex/skills/collaborating-with-claude/scripts/claude_bridge.py --cd "." --model sonnet --PROMPT "$PROMPT" --output-format stream-json
```

**Output:** JSON with `success`, `SESSION_ID`, `agent_messages`, and optional `error` / `all_messages`.

## Multi-turn Sessions

```bash
# Start a session
PROMPT="$(cat <<'EOF'
Analyze the bug in foo(). Keep it short.
EOF
)"
python3 .codex/skills/collaborating-with-claude/scripts/claude_bridge.py --cd "." --PROMPT "$PROMPT" --output-format stream-json

# Continue the same session
PROMPT="$(cat <<'EOF'
Now propose a minimal fix as Unified Diff Patch ONLY.
EOF
)"
python3 .codex/skills/collaborating-with-claude/scripts/claude_bridge.py --cd "." --SESSION_ID "<SESSION_ID>" --PROMPT "$PROMPT" --output-format stream-json
```

## Prompting Patterns (Paper Mode)

Use `assets/prompt-template.md` as a starter when crafting `--PROMPT`.
Paper-mode templates (top of the file):
- **`claim-stress-test`** — adversarial review of contribution-map (use `--model opus`)
- **`route-review-vs-empirical`** — routing recommendation with adversarial self-challenge (use `--model opus`)
- **`evidence-sufficiency-audit`** — per-claim evidence sufficiency assessment (use `--model sonnet`)

Each template specifies its input sources, output artifact mappings, and constraints.

## Verification
- Cross-check both collaborators: use the `check-collaborators` skill
- Smoke-test the bridge: `python3 .codex/skills/collaborating-with-claude/scripts/claude_bridge.py --help`
- For session testing: run one prompt with `--output-format stream-json` and confirm JSON contains `success: true` and a `SESSION_ID`.

## References
- `../../_shared/collaboration-base.md` (shared rules)
- `assets/prompt-template.md` (prompt patterns)
- `references/shell-quoting.md` (shell quoting/backticks)
