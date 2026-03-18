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

> **Shared rules**: This skill inherits all shared rules from
> `../../_shared/collaboration-base.md` (core rules, candidates-only
> constraint, fallback code-collaboration mode, safety guardrails, and
> collaboration state capsule format).  Only Gemini-specific additions
> are listed below.

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

## Gemini-Specific Rules
- Optional: pass `--sandbox` to run Gemini in sandbox mode.
- Auth/home notes:
  - The bridge defaults `GEMINI_CLI_HOME` to a writable repo-local directory
    (`<repo>/.gemini_cli_home/`) to avoid Gemini CLI hanging in some runners.
  - If your local `gemini` is already logged in, reuse that login with
    `--use-user-home`.
  - If you have `GEMINI_API_KEY` set but want to use OAuth creds, add
    `--prefer-oauth` to unset API-key env vars for this run.

## Quick Start (shell-safe)

If your prompt contains Markdown backticks, use a heredoc; see `references/shell-quoting.md`.

```bash
PROMPT="$(cat <<'EOF'
Review src/auth.py around login() and propose fixes.
OUTPUT: Unified Diff Patch ONLY.
EOF
)"
python3 .codex/skills/collaborating-with-gemini/scripts/gemini_bridge.py --cd "." --PROMPT "$PROMPT"
```

**Output:** JSON with `success`, `SESSION_ID`, `agent_messages`, and optional `error` / `all_messages`.

## Multi-turn Sessions

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

## Prompting Patterns (Paper Mode)

Use `assets/prompt-template.md` as a starter when crafting `--PROMPT`.
Paper-mode templates (top of the file):
- **`literature-map`** — expand candidate papers and adjacent research areas
- **`innovation-candidates`** — generate 3-5 candidate contribution framings
- **`evidence-matrix-gap-check`** — audit evidence coverage gaps

Each template specifies its input sources, output artifact mappings, and constraints.

## Advanced Flags
- `--sandbox`: Run Gemini in sandbox mode.
- `--model <name>`: Override the default Gemini model.
- `--return-all-messages`: Include all raw messages (tool calls, traces) in output JSON.
- `--use-user-home`: Reuse your normal home (and existing `~/.gemini` login) for this run.
- `--prefer-oauth`: Unset `GEMINI_API_KEY`/`GOOGLE_API_KEY` so OAuth creds can be used (if present in the selected home).
- `--seed-user-auth`: Copy OAuth/settings files from your `~/.gemini` into `<repo>/.gemini_cli_home/.gemini/` (avoids `--use-user-home` hangs).
- `--fake-responses <path.jsonl>`: Offline deterministic run using Gemini CLI fake responses (for smoke tests).

## Verification
- Cross-check both collaborators: use the `check-collaborators` skill
- Smoke-test the bridge: `python3 .codex/skills/collaborating-with-gemini/scripts/gemini_bridge.py --help`

## References
- `../../_shared/collaboration-base.md` (shared rules)
- `assets/prompt-template.md` (prompt patterns)
- `references/shell-quoting.md` (shell quoting/backticks)
