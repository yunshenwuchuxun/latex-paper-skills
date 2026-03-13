#!/usr/bin/env python3
"""Create a plan and/or issues CSV for an empirical IEEE paper project."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


def review_scripts_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "arxiv-paper-writer" / "scripts"


sys.path.insert(0, str(review_scripts_dir()))

from paper_utils import (  # type: ignore  # noqa: E402
    build_issues_filename,
    build_plan_filename,
    check_latex_available,
    load_paper_config,
    now_iso,
    now_timestamp,
    slugify,
    validate_slug,
    validate_timestamp,
)


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def assets_dir() -> Path:
    return skill_root() / "assets"


def read_template(template_name: str) -> str:
    template_path = assets_dir() / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    text = template_path.read_text(encoding="utf-8")
    return text.lstrip("\ufeff")


def init_innovation_notes(output_dir: Path) -> None:
    notes_dir = output_dir / "notes" / "innovation"
    notes_dir.mkdir(parents=True, exist_ok=True)

    templates = {
        "innovation-candidates.md": "innovation-candidates-template.md",
        "decision-log.md": "innovation-decision-log-template.md",
        "evidence-links.csv": "innovation-evidence-links-template.csv",
    }
    for dest_name, template_name in templates.items():
        dest_path = notes_dir / dest_name
        if dest_path.exists():
            continue
        dest_path.write_text(read_template(template_name), encoding="utf-8")


def refresh_literature_notes(output_dir: Path) -> int:
    script = skill_root() / "scripts" / "generate_literature_notes.py"
    if not script.exists():
        print(f"warning: literature notes generator not found: {script}", file=sys.stderr)
        return 0
    cmd = [sys.executable, str(script), "--project-dir", str(output_dir), "--mode", "cited"]
    return subprocess.run(cmd).returncode


def replace_placeholders(
    content: str,
    *,
    topic: str,
    timestamp: str,
    slug: str,
    latex_available: bool,
    config: dict,
    workflow_mode: str,
) -> str:
    preferred_venues = config.get("preferred_venues") or []
    preferred_text = ", ".join(str(item) for item in preferred_venues) if preferred_venues else "TBD"
    content = content.replace("<paper topic>", topic)
    content = content.replace("<topic>", topic)
    content = content.replace("<ISO8601 timestamp>", now_iso())
    content = content.replace("<YYYY-MM-DD_HH-mm-ss>", timestamp)
    content = content.replace("<slug>", slug)
    content = content.replace("<true|false>", "true" if latex_available else "false")
    content = content.replace("<workflow mode>", workflow_mode)
    content = content.replace("<target venue>", str(config.get("target_venue") or "TBD"))
    content = content.replace("<preferred venues>", preferred_text)
    content = content.replace("<style mode>", str(config.get("style_mode") or "neutral"))
    return content


def kickoff_gate_confirmed(plan_path: Path) -> bool:
    if not plan_path.exists():
        return False
    text = plan_path.read_text(encoding="utf-8")
    return any(
        re.search(r"^\s*-\s*\[\s*[xX]\s*\]\s*User confirmed scope \+ outline", line)
        for line in text.splitlines()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a plan or issues CSV for an empirical IEEE paper project.")
    parser.add_argument("--topic", required=True, help="Paper topic description.")
    parser.add_argument("--stage", default="plan", choices=["plan", "issues", "outline"])
    parser.add_argument("--complexity", default="medium", choices=["simple", "medium", "complex"])
    parser.add_argument("--timestamp", help="Optional timestamp override (YYYY-MM-DD_HH-mm-ss).")
    parser.add_argument("--slug", help="Optional slug override for filenames.")
    parser.add_argument("--output-dir", default=".", help="Output directory for plan/issues files.")
    parser.add_argument("--check-latex", action="store_true")
    parser.add_argument("--with-literature-notes", action="store_true")
    parser.add_argument("--target-venue", default="")
    parser.add_argument("--preferred-venue", action="append", default=[])
    parser.add_argument("--style-mode", default="neutral", choices=["neutral", "target_venue"])
    parser.add_argument("--style-anchor-paper", action="append", default=[])
    args = parser.parse_args()

    topic = args.topic.strip()
    if not topic:
        print("error: Topic cannot be empty.", file=sys.stderr)
        return 1

    slug = args.slug.strip() if args.slug else slugify(topic)
    try:
        validate_slug(slug)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    timestamp = args.timestamp.strip() if args.timestamp else now_timestamp()
    try:
        validate_timestamp(timestamp)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    config = load_paper_config(output_dir) if (output_dir / "paper.config.yaml").exists() else {
        "target_venue": args.target_venue,
        "preferred_venues": args.preferred_venue,
        "style_mode": args.style_mode,
        "workflow_mode": "standard",
    }

    latex_status = check_latex_available() if args.check_latex else {"available": False}
    workflow_mode = "outline-only" if args.stage == "outline" else str(config.get("workflow_mode") or "standard")

    plan_dir = output_dir / "plan"
    issues_dir = output_dir / "issues"
    plan_dir.mkdir(parents=True, exist_ok=True)
    issues_dir.mkdir(parents=True, exist_ok=True)
    init_innovation_notes(output_dir)

    plan_filename = build_plan_filename(timestamp, slug)
    issues_filename = build_issues_filename(timestamp, slug)
    plan_path = plan_dir / plan_filename
    issues_path = issues_dir / issues_filename

    if args.stage in {"plan", "outline"}:
        plan_template = read_template("paper-plan-template.md")
        plan_content = replace_placeholders(
            plan_template,
            topic=topic,
            timestamp=timestamp,
            slug=slug,
            latex_available=bool(latex_status.get("available")),
            config=config,
            workflow_mode=workflow_mode,
        )
        plan_path.write_text(plan_content, encoding="utf-8")
        print(f"Created plan: {plan_path}")

    if args.stage == "issues":
        if not kickoff_gate_confirmed(plan_path):
            print(f"error: kickoff gate unchecked in plan: {plan_path}", file=sys.stderr)
            return 1
        issues_template = read_template("paper-issues-template.csv")
        issues_content = replace_placeholders(
            issues_template,
            topic=topic,
            timestamp=timestamp,
            slug=slug,
            latex_available=bool(latex_status.get("available")),
            config=config,
            workflow_mode=workflow_mode,
        )
        with issues_path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(issues_content)
        print(f"Created issues CSV: {issues_path}")

        if args.with_literature_notes:
            notes_path = output_dir / "notes" / "literature-notes.md"
            if not notes_path.exists():
                notes_path.parent.mkdir(parents=True, exist_ok=True)
                notes_path.write_text(read_template("literature-notes-template.md"), encoding="utf-8")
                print(f"Created literature notes: {notes_path}")
            rc = refresh_literature_notes(output_dir)
            if rc != 0:
                print("warning: failed to refresh literature notes from ref.bib", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
