#!/usr/bin/env python3
"""
Gemini Bridge Script for Codex Skills.

Wraps the Gemini CLI to provide a JSON-based interface and multi-turn sessions via SESSION_ID.
"""

import argparse
import json
import os
import queue
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def run_shell_command(
    cmd: List[str],
    *,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout_s: int = 600,
) -> Tuple[List[str], List[str], int]:
    """Execute a command and return stdout/stderr as lists of lines."""
    popen_cmd = cmd.copy()
    gemini_path = shutil.which("gemini") or cmd[0]
    popen_cmd[0] = gemini_path

    process = subprocess.Popen(
        popen_cmd,
        shell=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding="utf-8",
        cwd=cwd,
        env=env,
    )

    output_queue: "queue.Queue[Optional[str]]" = queue.Queue()
    GRACEFUL_SHUTDOWN_DELAY = 0.3
    stdout_lines: List[str] = []
    stderr_lines: List[str] = []

    def is_turn_completed(line: str) -> bool:
        try:
            data = json.loads(line)
            return data.get("type") == "turn.completed"
        except (json.JSONDecodeError, AttributeError, TypeError):
            return False

    def read_output() -> None:
        if process.stdout:
            for line in iter(process.stdout.readline, ""):
                stripped = line.strip()
                output_queue.put(stripped)
                if is_turn_completed(stripped):
                    time.sleep(GRACEFUL_SHUTDOWN_DELAY)
                    process.terminate()
                    break
            process.stdout.close()
        output_queue.put(None)

    def read_stderr() -> None:
        if process.stderr:
            for line in iter(process.stderr.readline, ""):
                stderr_lines.append(line.rstrip("\n"))
            process.stderr.close()

    stdout_thread = threading.Thread(target=read_output)
    stderr_thread = threading.Thread(target=read_stderr)
    stdout_thread.start()
    stderr_thread.start()

    deadline = time.time() + max(1, timeout_s)
    while True:
        try:
            line = output_queue.get(timeout=0.5)
            if line is None:
                break
            stdout_lines.append(line)
        except queue.Empty:
            if time.time() > deadline:
                process.terminate()
                break
            if process.poll() is not None and not stdout_thread.is_alive():
                break

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    stdout_thread.join(timeout=5)
    stderr_thread.join(timeout=5)

    while not output_queue.empty():
        try:
            line = output_queue.get_nowait()
            if line is not None:
                stdout_lines.append(line)
        except queue.Empty:
            break

    return stdout_lines, stderr_lines, process.returncode or 0


def windows_escape(prompt: str) -> str:
    """Windows style string escaping."""
    result = prompt.replace("\\", "\\\\")
    result = result.replace('"', '\\"')
    result = result.replace("\n", "\\n")
    result = result.replace("\r", "\\r")
    result = result.replace("\t", "\\t")
    result = result.replace("\b", "\\b")
    result = result.replace("\f", "\\f")
    result = result.replace("'", "\\'")
    return result


def seed_user_auth_into_home(*, gemini_cli_home: Path, user_profile: Path) -> None:
    """
    Copy a minimal set of auth/config files from the user's `~/.gemini` into the selected
    GEMINI_CLI_HOME so headless runs can reuse OAuth without pointing GEMINI_CLI_HOME at the full
    user home (which can hang in some runners).
    """
    src_dir = (user_profile / ".gemini").resolve()
    if not src_dir.exists():
        return

    dst_dir = (gemini_cli_home / ".gemini").resolve()
    dst_dir.mkdir(parents=True, exist_ok=True)

    for name in ("settings.json", "oauth_creds.json", "google_accounts.json", "state.json", "trustedFolders.json"):
        src = src_dir / name
        dst = dst_dir / name
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini Bridge")
    parser.add_argument("--PROMPT", required=True, help="Instruction for the task to send to gemini.")
    parser.add_argument("--cd", required=True, type=Path, help="Set the workspace root for gemini before executing the task.")
    parser.add_argument("--sandbox", action="store_true", default=False, help="Run in sandbox mode. Defaults to `False`.")
    parser.add_argument(
        "--prefer-oauth",
        action="store_true",
        default=False,
        help="Unset API-key env vars (e.g., GEMINI_API_KEY) so Gemini CLI can use existing OAuth creds in the selected home.",
    )
    parser.add_argument(
        "--seed-user-auth",
        action="store_true",
        default=False,
        help="Seed OAuth/settings files from your `~/.gemini` into the selected GEMINI_CLI_HOME (avoids `--use-user-home` hangs).",
    )
    parser.add_argument(
        "--use-user-home",
        action="store_true",
        default=False,
        help="Use USERPROFILE as GEMINI_CLI_HOME (reuses existing ~/.gemini). Not recommended in sandboxed runners if it hangs.",
    )
    parser.add_argument(
        "--fake-responses",
        default="",
        help="Optional path to a JSONL file with fake model responses (Gemini CLI `--fake-responses`).",
    )
    parser.add_argument(
        "--SESSION_ID",
        default="",
        help="Resume the specified session of gemini. Defaults to empty string (start a new session).",
    )
    parser.add_argument(
        "--return-all-messages",
        action="store_true",
        help="Return all messages (e.g. tool calls, traces) from the gemini session. By default only returns the assistant message text.",
    )
    parser.add_argument("--model", default="", help="Override the Gemini model.")

    args = parser.parse_args()

    if shutil.which("gemini") is None:
        result = {
            "success": False,
            "error": "Gemini CLI not found in PATH. Install it and ensure `gemini` is available before using this skill.",
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    cd: Path = args.cd
    if not cd.exists():
        result = {
            "success": False,
            "error": f"The workspace root directory `{cd.absolute().as_posix()}` does not exist. Please check the path and try again.",
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prompt = args.PROMPT

    # Gemini CLI uses a "global" home directory for registry/locks/caches via os.homedir(). In
    # some sandboxed runners this can point to an unwritable or lock-hostile location, causing the
    # CLI to hang very early (even for `--version`). Default to a writable, repo-local home.
    # Callers can override by setting GEMINI_CLI_HOME explicitly or by passing --use-user-home.
    env = os.environ.copy()
    if not env.get("GEMINI_CLI_HOME"):
        if args.use_user_home and env.get("USERPROFILE"):
            env["GEMINI_CLI_HOME"] = str(Path(env["USERPROFILE"]).resolve())
        else:
            gemini_cli_home = (cd / ".gemini_cli_home").resolve()
            gemini_cli_home.mkdir(parents=True, exist_ok=True)
            env["GEMINI_CLI_HOME"] = str(gemini_cli_home)

    if args.prefer_oauth:
        env.pop("GEMINI_API_KEY", None)
        env.pop("GOOGLE_API_KEY", None)

    if args.seed_user_auth and env.get("USERPROFILE") and env.get("GEMINI_CLI_HOME"):
        seed_user_auth_into_home(
            gemini_cli_home=Path(env["GEMINI_CLI_HOME"]).resolve(),
            user_profile=Path(env["USERPROFILE"]).resolve(),
        )

    # Avoid child-process relaunch behavior (e.g., for memory heuristics). Some sandboxed runners
    # disallow spawning a new child, which manifests as `spawn EPERM` and prevents any output.
    env.setdefault("GEMINI_CLI_NO_RELAUNCH", "true")

    # Use `--prompt/-p` to force non-interactive mode. Positional prompts may enter interactive
    # mode depending on Gemini CLI headless detection, which can hang under non-TTY runners.
    #
    # NOTE: Gemini CLI expects a string argument to `--prompt/-p` (it is not a boolean flag).
    cmd = ["gemini", "-o", "stream-json"]

    if args.sandbox:
        cmd.extend(["--sandbox"])

    if args.fake_responses:
        cmd.extend(["--fake-responses", str(Path(args.fake_responses).resolve())])

    if args.model:
        cmd.extend(["--model", args.model])

    if args.SESSION_ID:
        cmd.extend(["--resume", args.SESSION_ID])

    cmd.extend(["--prompt", prompt])

    all_messages = []
    agent_messages = ""
    success = True
    err_message = ""
    session_id = None
    non_json_stdout: List[str] = []

    stdout_lines, stderr_lines, returncode = run_shell_command(
        cmd,
        cwd=cd.absolute().as_posix(),
        env=env,
        timeout_s=600,
    )

    for line in stdout_lines:
        raw = (line or "").strip()
        if not raw:
            continue

        line_dict = None
        try:
            line_dict = json.loads(raw)
        except json.JSONDecodeError:
            # Gemini CLI may occasionally prefix a JSON object with a human-readable warning.
            # Try to recover by parsing from the first `{` onward.
            brace_idx = raw.find("{")
            if brace_idx != -1:
                try:
                    line_dict = json.loads(raw[brace_idx:])
                except json.JSONDecodeError:
                    line_dict = None

        if line_dict is None:
            non_json_stdout.append(raw)
            continue

        try:
            all_messages.append(line_dict)

            item_type = line_dict.get("type", "")
            item_role = line_dict.get("role", "")

            if item_type == "message" and item_role == "assistant":
                agent_messages += line_dict.get("content", "")

            if line_dict.get("session_id") is not None:
                session_id = line_dict.get("session_id")

        except Exception as error:
            err_message += "\n\n[unexpected error] " + f"Unexpected error: {error}. Line: {raw!r}"
            continue

    result = {}

    # Treat SIGTERM (-15 on Unix, 15 on Windows) as success since we terminate Gemini ourselves.
    success = returncode in (0, -15, 15)
    if not success and not err_message:
        err_message = f"Gemini CLI exited with non-zero status: {returncode}"

    if session_id is None:
        success = False
        err_message = "Failed to get `SESSION_ID` from the gemini session.\n\n" + err_message
    else:
        result["SESSION_ID"] = session_id

    stderr_text = "\n".join(stderr_lines).strip()
    if stderr_text:
        err_message = (err_message + "\n\n" if err_message else "") + "[stderr]\n" + stderr_text

    if not success and non_json_stdout:
        err_message += "\n\n[stdout]\n" + "\n".join(non_json_stdout[-20:])

    if not success and stderr_text and ("API key expired" in stderr_text or "API_KEY_INVALID" in stderr_text):
        err_message += (
            "\n\n[hint]\n"
            "Your environment appears to be using an invalid/expired API key. Either renew/unset `GEMINI_API_KEY`, "
            "or run with `--prefer-oauth` (and usually `--use-user-home` to reuse your existing login)."
        )

    result["agent_messages"] = agent_messages
    if not success:
        result["error"] = err_message

    result["success"] = success

    if args.return_all_messages:
        result["all_messages"] = all_messages

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
