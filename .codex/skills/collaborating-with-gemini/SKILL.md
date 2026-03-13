---
name: collaborating-with-gemini
description: >
  Use the Gemini CLI as a breadth-exploration co-pilot for paper-from-zero.
  Primary role: candidate direction expansion, adjacent work scanning,
  keyword cluster generation, and alternative framing proposals.
  Also supports generic code collaboration as fallback.
metadata:
  short-description: Breadth co-pilot (Gemini) for paper-from-zero
---

# Collaborating with Gemini (Codex)

Use Gemini CLI as a **breadth-exploration** collaborator for paper-from-zero,
or as a generic code collaborator in fallback mode.

This skill provides a lightweight bridge script that returns structured JSON
and supports multi-turn sessions via `SESSION_ID`.

## When to Use
- paper-from-zero needs to expand the candidate literature pool.
- topic-brief initial draft exists but adjacent research areas are uncovered.
- contribution-map needs 3-5 alternative framing candidates.
- evidence-matrix has coverage gaps that need broader search directions.
- Fallback: generic code collaboration tasks (analysis, patch, review).

## When NOT to Use
- Claim-level logical analysis or reviewer objection stress tests (use Claude).
- Final routing judgment between review/empirical (use Claude).
- Generating `ref.bib` entries or verified citations.
- Tasks requiring depth reasoning rather than breadth scanning.

## Core rules
- Gemini is a collaborator; you own the final result and must verify changes locally.
- Do not invoke `gemini` directly; always use the bridge script (`scripts/gemini_bridge.py`) so output/session handling stays consistent.
- Prefer file/line references over pasting snippets. Run the bridge with `--cd` set to the repo root (it sets the `gemini` process working directory). Use `--cd "."` only if your CWD is the repo root.
- For code changes, request **Unified Diff Patch ONLY** and forbid direct file modification.
- Always capture `SESSION_ID` and reuse it for follow-ups to keep the collaboration conversation-aware.
- Keep a short **Collaboration State Capsule** updated while this skill is active.
- Default timeout: when invoking via the Codex command runner, set `timeout_ms` to **600000 (10 minutes)** unless a shorter/longer timeout is explicitly required.
- Optional: pass `--sandbox` to run Gemini in sandbox mode.
- Auth/home notes:
  - The bridge defaults `GEMINI_CLI_HOME` to a writable repo-local directory (`<repo>/.gemini_cli_home/`) to avoid Gemini CLI hanging in some runners.
  - If your local `gemini` is already logged in, reuse that login with `--use-user-home`.
  - If you have `GEMINI_API_KEY` set but want to use OAuth creds, add `--prefer-oauth` to unset API-key env vars for this run.

## Candidates-Only Hard Constraint (Paper Mode)
All paper-mode outputs are **unverified candidates**, not citable facts.
They must pass through the downstream citation verification pipeline
(arxiv_registry.py → source_ranker.py → citation_policy.py) before
entering ref.bib or artifact final fields. See template-level constraints
in `assets/prompt-template.md` for output format rules.

## Quick start (shell-safe)

⚠️ If your prompt contains Markdown backticks (`` `like/this` ``), do **not** pass it directly via `--PROMPT "..."` (your shell may treat backticks as command substitution). Use a heredoc instead; see `references/shell-quoting.md`.

```bash
PROMPT="$(cat <<'EOF'
Review src/auth.py around login() and propose fixes.
OUTPUT: Unified Diff Patch ONLY.
EOF
)"
python3 .codex/skills/collaborating-with-gemini/scripts/gemini_bridge.py --cd "." --PROMPT "$PROMPT"
```

**Output:** JSON with `success`, `SESSION_ID`, `agent_messages`, and optional `error` / `all_messages`.

## Multi-turn sessions

```bash
# Start a session
PROMPT="$(cat <<'EOF'
Analyze the bug in foo(). Keep it short.
EOF
)"
python3 .codex/skills/collaborating-with-gemini/scripts/gemini_bridge.py --cd "." --PROMPT "$PROMPT"

# Continue the same session
PROMPT="$(cat <<'EOF'
Now propose a minimal fix as Unified Diff Patch ONLY.
EOF
)"
python3 .codex/skills/collaborating-with-gemini/scripts/gemini_bridge.py --cd "." --SESSION_ID "<SESSION_ID>" --PROMPT "$PROMPT"
```

## Prompting patterns (paper mode)

Use `assets/prompt-template.md` as a starter when crafting `--PROMPT`.
Paper-mode templates (top of the file):
- **`literature-map`** — expand candidate papers and adjacent research areas
- **`innovation-candidates`** — generate 3-5 candidate contribution framings
- **`evidence-matrix-gap-check`** — audit evidence coverage gaps

Each template specifies its input sources, output artifact mappings, and constraints.

### Fallback: Code collaboration mode

For generic code tasks, use the templates in the `## Fallback: Code Collaboration Mode` section of `assets/prompt-template.md`:

1. **Ask Gemini to open files itself** — provide entry file(s), line numbers, objective, constraints, and output format (diff vs analysis). Avoid pasting large code blocks.
2. **Enforce safe output for code changes** — append: `OUTPUT: Unified Diff Patch ONLY. Strictly prohibit any actual modifications.`
3. **Use Gemini for what it's good at** — alternative solution paths, edge cases, UI/UX feedback, patch review.
4. **Sharing clipboard screenshots** — copy images into `.codex_uploads/`, then reference that path in your prompt. Delete when done. Do not add `.codex_uploads/` to `.gitignore`.

```bash
mkdir -p .codex_uploads && cp "${TMPDIR:-/tmp}"/codex-clipboard-<id>.png .codex_uploads/
```

## Advanced flags
- `--sandbox`: Run Gemini in sandbox mode.
- `--model <name>`: Override the default Gemini model.
- `--return-all-messages`: Include all raw messages (tool calls, traces) in output JSON.
- `--use-user-home`: Reuse your normal home (and existing `~/.gemini` login) for this run.
- `--prefer-oauth`: Unset `GEMINI_API_KEY`/`GOOGLE_API_KEY` so OAuth creds can be used (if present in the selected home).
- `--seed-user-auth`: Copy OAuth/settings files from your `~/.gemini` into `<repo>/.gemini_cli_home/.gemini/` (avoids `--use-user-home` hangs).
- `--fake-responses <path.jsonl>`: Offline deterministic run using Gemini CLI fake responses (for smoke tests).

## Unavailability
Collaboration hooks are non-blocking. If Gemini CLI is unreachable,
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
[Gemini Collaboration Capsule]
Goal:
Gemini SESSION_ID:
Files/lines handed off:
Last ask:
Gemini summary:
Next ask:
```

## References
- `assets/prompt-template.md` (prompt patterns)
- `references/shell-quoting.md` (shell quoting/backticks)
