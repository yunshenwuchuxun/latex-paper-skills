---
name: check-collaborators
description: >
  Verify that Gemini CLI and Claude Code CLI are installed, authenticated,
  and API-reachable before starting collaboration workflows.
metadata:
  short-description: Collaborator CLI health check
---

# Collaborator CLI Health Check

## When to use
- Before starting any collaboration workflow that depends on Gemini or Claude Code.
- When diagnosing CLI connectivity or authentication issues.
- After installing or reconfiguring either CLI.

## When not to use
- Both CLIs are already confirmed working in the current session.
- The task does not involve cross-agent collaboration.

## Inputs
- Current OS environment (auto-detected).

## Outputs
- Summary table: Collaborator x CLI / Version / Auth / API / Status.
- Actionable remediation advice for any failed step.

## Workflow

Run the Gemini and Claude detection chains **in parallel** where possible.
For each collaborator, execute steps sequentially and **short-circuit on the first failure** — skip subsequent steps and mark the failure reason.

### Step 0: Detect OS

Determine the platform to choose the correct binary-lookup command:
- **Windows** (`win32`): use `where`
- **Unix/macOS**: use `which`

Detect via `uname -s 2>/dev/null` (returns nothing or errors on Windows) or check `$OSTYPE`.

---

### Gemini Detection Chain

#### 1. CLI Exists

```bash
# Unix
which gemini
# Windows
where gemini
```

**Pass**: command exits 0 and outputs a path.
**Fail**: command not found — suggest: `npm install -g @anthropic-ai/gemini-cli` or see https://github.com/google-gemini/gemini-cli

#### 2. Version

```bash
timeout 15 bash -c 'GEMINI_CLI_NO_RELAUNCH=true gemini --version'
```

On Windows (no `timeout` command), run directly:
```bash
GEMINI_CLI_NO_RELAUNCH=true gemini --version
```

`GEMINI_CLI_NO_RELAUNCH=true` is **required** to prevent the CLI from hanging.

**Pass**: output contains a version string (e.g., `0.32.1`).
**Fail**: timeout or no version output.

#### 3. Auth

Check for any of the following (any one is sufficient):
1. Environment variable `GEMINI_API_KEY` is set and non-empty.
2. Environment variable `GOOGLE_API_KEY` is set and non-empty.
3. File `~/.gemini/oauth_creds.json` exists.

```bash
[[ -n "$GEMINI_API_KEY" ]] || [[ -n "$GOOGLE_API_KEY" ]]
test -f "$HOME/.gemini/oauth_creds.json"
```

**Pass**: any one condition is true.
**Fail**: none found — suggest: `export GEMINI_API_KEY=<key>` or run `gemini` interactively to complete OAuth.

#### 4. API Connectivity

```bash
timeout 30 gemini --prompt "Reply with exactly: HEALTH_OK"
```

**Pass**: stdout contains `HEALTH_OK`.
**Fail**: timeout or no `HEALTH_OK` in output — suggest checking network, API key validity, or quota.

**Note**: Gemini CLI may emit warnings (e.g., skill conflict notices) in its output. These are benign and do not affect the health check. The pass/fail criterion is solely whether `HEALTH_OK` appears in stdout.

---

### Claude Code Detection Chain

#### 1. CLI Exists

```bash
# Unix
which claude
# Windows
where claude
```

**Pass**: command exits 0 and outputs a path.
**Fail**: command not found — suggest: `npm install -g @anthropic-ai/claude-code` or see https://docs.anthropic.com/en/docs/claude-code

#### 2. Version

```bash
timeout 15 claude --version
```

**Pass**: output contains a version string (e.g., `2.1.74`).
**Fail**: timeout or no version output.

#### 3. Auth

```bash
claude auth status
```

**Pass**: output contains `Logged in` or JSON field `loggedIn: true`.
**Fail**: not logged in — suggest: run `claude` interactively and use `/login`.

#### 4. API Connectivity

```bash
timeout 30 claude --print "Reply with exactly: HEALTH_OK" --output-format text --no-session-persistence --max-budget-usd 0.50
```

**Pass**: stdout contains `HEALTH_OK`.
**Fail**: timeout or no `HEALTH_OK` — suggest checking API key, network, or account quota.

**Note**: `--max-budget-usd` must be at least `0.50`. Lower values (e.g., `0.01`, `0.05`) cause immediate `Exceeded budget` errors because model inference has a minimum cost floor.

---

## Output Format

Present a summary table after all checks:

```
| Collaborator | CLI | Version | Auth | API | Status    |
|--------------|-----|---------|------|-----|-----------|
| Gemini       | ✓/✗ | x.y.z   | ✓/✗  | ✓/✗ | Available / Failed |
| Claude Code  | ✓/✗ | x.y.z   | ✓/✗  | ✓/✗ | Available / Failed |
```

- Use `✓` for passed steps, `✗` for failed steps, `—` for skipped steps (due to short-circuit).
- **Status** is `Available` only if all 4 steps pass; otherwise `Failed`.
- Version column shows the detected version string, or `—` if not reached.

For any failed step, append actionable remediation advice below the table:

```
### Issues Found

**Gemini — Auth failed**
No API key or OAuth credentials detected.
→ Set `GEMINI_API_KEY` environment variable, or run `gemini` to complete OAuth login.

**Claude Code — CLI not found**
Claude Code CLI is not installed.
→ Install: `npm install -g @anthropic-ai/claude-code`
→ Docs: https://docs.anthropic.com/en/docs/claude-code
```

If both collaborators pass all checks:

```
Both collaborators are available and ready for collaboration workflows.
```

## Verification
- Run this skill and confirm the summary table appears with correct status for each collaborator.

## Safety and guardrails
- Read-only checks only; no configuration files are modified.
- API connectivity tests consume minimal tokens (~$0.01 per check).
- Steps 2-4 spawn external CLI processes; run them outside sandbox (escalated permissions) to avoid hangs or `EPERM` errors.
- On Windows, `timeout` may not be available; run commands directly and watch for hangs.
- Gemini `--version` **must** use `GEMINI_CLI_NO_RELAUNCH=true` to prevent the CLI from relaunching itself.
