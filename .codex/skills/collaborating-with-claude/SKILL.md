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

## Core rules
- Claude is a collaborator; you own the final result and must verify changes locally.
- Do not invoke `claude` directly; always use the bridge script (`scripts/claude_bridge.py`) so output/session handling stays consistent.
- Prefer file/line references over pasting snippets. Run the bridge with `--cd` set to the repo root (it sets the `claude` process working directory); use `--add-dir` when Claude needs access to additional directories.
- For code changes, request **Unified Diff Patch ONLY** and forbid direct file modification.
- Always run the bridge script with `--help` first if you are unsure of parameters.
- Always capture `SESSION_ID` and reuse it for follow-ups to keep the collaboration conversation-aware.
- For automation, prefer `--SESSION_ID` (resume). Session selectors are mutually exclusive: choose one of `--SESSION_ID`, `--continue`, or `--session-id`.
- Keep a short **Collaboration State Capsule** updated while this skill is active.
- Default timeout: when invoking via the Codex command runner, set `timeout_ms` to **600000 (10 minutes)** unless a shorter/longer timeout is explicitly required.
- Ensure Claude Code is logged in before running headless commands (run `claude` and `/login` once if needed).
- Streamed JSON requires `--verbose`; the bridge enables this automatically.

## Candidates-Only Hard Constraint (Paper Mode)
All paper-mode outputs are **unverified candidates**, not citable facts.
They must pass through the downstream citation verification pipeline
(arxiv_registry.py → source_ranker.py → citation_policy.py) before
entering ref.bib or artifact final fields. See template-level constraints
in `assets/prompt-template.md` for output format rules.

## Model selection

Claude Code supports model aliases, so you can use `--model sonnet` / `--model opus` instead of hard-coding versioned model IDs.

- If you omit `--model`, Claude Code uses its configured default (typically from `~/.claude/settings.json`, optionally overridden by `.claude/settings.json` and `.claude/settings.local.json`).
- If you need strict reproducibility, pass a full model name via `--model <full-name>`.
- For `claim-stress-test` and `route-review-vs-empirical` templates, prefer `opus`.
- For `evidence-sufficiency-audit`, `sonnet` is sufficient.

## Quick start (shell-safe)

⚠️ If your prompt contains Markdown backticks (`` `like/this` ``), do **not** pass it directly via `--PROMPT "..."` (your shell may treat backticks as command substitution). Use a heredoc instead; see `references/shell-quoting.md`.

```bash
PROMPT="$(cat <<'EOF'
Review src/auth.py around login() and propose fixes.
OUTPUT: Unified Diff Patch ONLY.
EOF
)"
python3 .codex/skills/collaborating-with-claude/scripts/claude_bridge.py --cd "." --model sonnet --PROMPT "$PROMPT" --output-format stream-json
```

**Output:** JSON with `success`, `SESSION_ID`, `agent_messages`, and optional `error` / `all_messages`.

## Multi-turn sessions

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

## Prompting patterns (paper mode)

Use `assets/prompt-template.md` as a starter when crafting `--PROMPT`.
Paper-mode templates (top of the file):
- **`claim-stress-test`** — adversarial review of contribution-map (use `--model opus`)
- **`route-review-vs-empirical`** — routing recommendation with adversarial self-challenge (use `--model opus`)
- **`evidence-sufficiency-audit`** — per-claim evidence sufficiency assessment (use `--model sonnet`)

Each template specifies its input sources, output artifact mappings, and constraints.

### Fallback: Code collaboration mode

For generic code tasks, use the templates in the `## Fallback: Code Collaboration Mode` section of `assets/prompt-template.md`:

1. **Ask Claude to open files itself** — provide entry file(s), line numbers, objective, constraints, and output format (diff vs analysis). Avoid pasting large code blocks.
2. **Enforce safe output for code changes** — append: `OUTPUT: Unified Diff Patch ONLY. Strictly prohibit any actual modifications.`
3. **Use Claude for what it's good at** — alternative solution paths, edge cases, UI/UX feedback, patch review.

## Verification
- Smoke-test the bridge: `python3 .codex/skills/collaborating-with-claude/scripts/claude_bridge.py --help`.
- If you need a session: run one prompt with `--output-format stream-json` and confirm the JSON contains `success: true` and a `SESSION_ID`.
- Note: `--output-format text` won't include a newly generated session id; use `stream-json`/`json` to capture it. If you resume with `--SESSION_ID` in `text` mode, the bridge echoes that `SESSION_ID` in its JSON output.

## Safety & guardrails
- Never paste secrets (private keys, API keys, seed phrases) into prompts.
- For code changes, request **Unified Diff Patch ONLY** and apply changes yourself.
- Treat Claude output as suggestions; verify locally (tests, lint, build) before merging.

## Unavailability
Collaboration hooks are non-blocking. If Claude Code CLI is unreachable,
the orchestrator decides the fallback (skip, self-execute, or ask user).
Candidates-Only constraint applies regardless of who executes the template.

## Collaboration State Capsule

### Paper Mode Capsule (default)
Keep this block updated near the end of your reply while collaborating:

```text
[Paper Collaboration Capsule]
Topic:
Current_Mode_Hypothesis: review | empirical | undecided
Current_Artifact: topic-brief | contribution-map | evidence-matrix | outline-contract | router-decision
Artifact_Version: draft-N
Open_Gaps:
Rejected_Framings:
Evidence_Risks:
Next_Validation_Step:
SESSION_ID:
```

### Legacy Capsule (Code Mode)
For generic code collaboration, use the legacy capsule:

```text
[Claude Collaboration Capsule]
Goal:
Claude SESSION_ID:
Files/lines handed off:
Last ask:
Claude summary:
Next ask:
```

## References
- `assets/prompt-template.md` (prompt patterns)
- `references/shell-quoting.md` (shell quoting/backticks)
