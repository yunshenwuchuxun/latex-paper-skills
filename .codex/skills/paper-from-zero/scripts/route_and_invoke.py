#!/usr/bin/env python3
"""Read router-decision.md, validate handoff, and emit next-step instructions.

Usage:
    python3 route_and_invoke.py --project-dir <paper_dir>
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parents[1]
_VALIDATE = _SKILL_ROOT / "validate_handoff.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def detect_route(router_text: str) -> str | None:
    """Extract the chosen route from router-decision.md."""
    m = re.search(r"(?im)^\s*Route to\s+\*\*(?P<target>[^*]+)\*\*", router_text)
    if not m:
        return None
    target = m.group("target").strip().lower()
    if "empirical" in target:
        return "empirical"
    if "review" in target or "arxiv" in target:
        return "review"
    return None


def run_validation(project_dir: Path) -> bool:
    """Run validate_handoff.py and return True if it passes."""
    result = subprocess.run(
        [sys.executable, str(_VALIDATE), "--project-dir", str(project_dir)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Handoff validation failed:", file=sys.stderr)
        print(result.stderr or result.stdout, file=sys.stderr)
        return False
    return True


def emit_instructions(route: str, project_dir: Path) -> None:
    """Print next-step instructions for the downstream writer skill."""
    skill_map = {
        "review": "arxiv-paper-writer",
        "empirical": "empirical-paper-writer",
    }
    skill = skill_map[route]

    print(f"Route: {route}")
    print(f"Downstream skill: {skill}")
    print()
    print("--- Next Steps ---")
    print()

    if route == "review":
        print(f"1. Open the {skill} skill.")
        print(f"2. Set <paper_dir> = {project_dir}")
        print("3. Skip Gate 0 scaffolding (project already exists).")
        print("4. Use the Existing Paper Workflow:")
        print(f"     python3 scripts/create_paper_plan.py \\")
        print(f'       --topic "$(head -1 {project_dir}/brief/topic-brief.md)" \\')
        print(f"       --stage plan --output-dir {project_dir}")
        print("5. After approval, create issues:")
        print(f"     python3 scripts/create_paper_plan.py \\")
        print(f'       --topic "..." --stage issues \\')
        print(f"       --timestamp <TS> --slug <slug> \\")
        print(f"       --output-dir {project_dir} --with-literature-notes")
        print("6. Proceed to Phase 1.5 (Literature Enrichment Gate).")
    else:
        print(f"1. Open the {skill} skill.")
        print(f"2. Set <paper_dir> = {project_dir}")
        print("3. Run bootstrap with --stage kickoff:")
        print(f"     python3 scripts/bootstrap_ieee_empirical_paper.py \\")
        print(f'       --stage kickoff --topic "$(head -1 {project_dir}/brief/topic-brief.md)" \\')
        print(f"       --output-dir {project_dir}")
        print("4. Import the contribution-map and evidence-matrix into the")
        print("   empirical plan (method-components, baselines, experiment-matrix).")
        print("5. Proceed to Phase 0.5 (Method Design Gate).")

    print()
    print("Handoff artifacts available:")
    for name in [
        "brief/topic-brief.md",
        "brief/contribution-map.yaml",
        "brief/evidence-matrix.csv",
        "plan/outline-contract.md",
        "plan/router-decision.md",
    ]:
        path = project_dir / name
        status = "OK" if path.exists() else "MISSING"
        print(f"  [{status}] {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Route paper-from-zero handoff to downstream writer.")
    parser.add_argument("--project-dir", type=Path, required=True, help="Project directory")
    parser.add_argument("--skip-validation", action="store_true", help="Skip handoff validation")
    args = parser.parse_args()

    project_dir: Path = args.project_dir.resolve()
    router_path = project_dir / "plan" / "router-decision.md"

    if not router_path.exists():
        print(f"error: {router_path} not found", file=sys.stderr)
        return 1

    # Validate handoff
    if not args.skip_validation:
        if not run_validation(project_dir):
            return 1

    # Detect route
    router_text = read_text(router_path)
    route = detect_route(router_text)
    if route is None:
        print("error: cannot determine route from router-decision.md", file=sys.stderr)
        print("Expected a line like: Route to **review** or Route to **empirical**", file=sys.stderr)
        return 1

    emit_instructions(route, project_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
