#!/usr/bin/env python3
"""Bootstrap an IEEE empirical paper project (scaffold + plan/issues)."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def review_scripts_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "arxiv-paper-writer" / "scripts"


sys.path.insert(0, str(review_scripts_dir()))

from paper_utils import ensure_paper_config, now_timestamp, slugify, validate_slug, validate_timestamp  # type: ignore  # noqa: E402


def run(cmd: list[str]) -> int:
    return subprocess.run(cmd).returncode


def empirical_skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def review_template_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "arxiv-paper-writer" / "assets" / "template"


def empirical_template_dir() -> Path:
    return empirical_skill_root() / "assets" / "template"


def scaffold_project(folder_name: str, out_dir: Path) -> Path:
    dest_dir = out_dir / folder_name
    if dest_dir.exists():
        raise SystemExit(f"Destination already exists: {dest_dir}")

    base_template = review_template_dir()
    if not base_template.exists():
        raise SystemExit(
            "Review template directory not found. This skill expects the shared IEEE template from "
            f"arxiv-paper-writer at: {base_template}"
        )

    ignore = shutil.ignore_patterns(
        "*.aux",
        "*.bbl",
        "*.blg",
        "*.fdb_latexmk",
        "*.fls",
        "*.lof",
        "*.log",
        "*.lot",
        "*.out",
        "*.synctex",
        "*.synctex.gz",
        "*.toc",
        "main.template.pdf",
    )
    shutil.copytree(base_template, dest_dir, ignore=ignore)

    for file_path in empirical_template_dir().glob("*"):
        if file_path.is_file():
            shutil.copy2(file_path, dest_dir / file_path.name)

    main_template = dest_dir / "main.template.tex"
    bib_template = dest_dir / "references.template.bib"
    main_tex = dest_dir / "main.tex"
    ref_bib = dest_dir / "ref.bib"

    if main_template.exists():
        main_template.rename(main_tex)
    if bib_template.exists():
        bib_template.rename(ref_bib)

    print(f"Created empirical paper scaffold at: {dest_dir}")
    return dest_dir


def infer_latest_plan_timestamp_and_slug(plan_dir: Path) -> tuple[str, str] | None:
    if not plan_dir.exists():
        return None
    candidates = sorted(path for path in plan_dir.glob("*.md") if path.is_file())
    if not candidates:
        return None

    for candidate in reversed(candidates):
        stem = candidate.stem
        if len(stem) < 21 or stem[19] != "-":
            continue
        timestamp = stem[:19]
        slug = stem[20:]
        try:
            validate_timestamp(timestamp)
            validate_slug(slug)
        except ValueError:
            continue
        return timestamp, slug

    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap an IEEE empirical paper project.")
    parser.add_argument("--stage", default="kickoff", choices=["kickoff", "issues", "outline"])
    parser.add_argument("--topic", required=True)
    parser.add_argument("--name", help="Folder name override (default: slugified topic).")
    parser.add_argument("--out", default=".")
    parser.add_argument("--complexity", default="medium", choices=["simple", "medium", "complex"])
    parser.add_argument("--timestamp", help="Timestamp override (YYYY-MM-DD_HH-mm-ss).")
    parser.add_argument("--slug", help="Optional slug override for filenames.")
    parser.add_argument("--check-latex", action="store_true")
    parser.add_argument("--with-literature-notes", action="store_true")
    parser.add_argument("--target-venue", default="")
    parser.add_argument("--preferred-venue", action="append", default=[])
    parser.add_argument("--style-mode", default="neutral", choices=["neutral", "target_venue"])
    parser.add_argument("--style-anchor-paper", action="append", default=[])
    args = parser.parse_args()

    topic = args.topic.strip()
    slug = args.slug.strip() if args.slug else slugify(topic)
    validate_slug(slug)

    timestamp = args.timestamp.strip() if args.timestamp else now_timestamp()
    validate_timestamp(timestamp)

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    folder_name = args.name.strip() if args.name else slug
    project_dir = out_dir / folder_name

    create_script = empirical_skill_root() / "scripts" / "create_empirical_plan.py"

    if args.stage in {"kickoff", "outline"}:
        scaffold_project(folder_name, out_dir)
        workflow_mode = "outline-only" if args.stage == "outline" else "standard"
        ensure_paper_config(
            project_dir=project_dir,
            topic=topic,
            workflow_mode=workflow_mode,
            target_venue=args.target_venue,
            preferred_venues=args.preferred_venue,
            style_mode=args.style_mode,
            style_anchor_papers=args.style_anchor_paper,
        )
        stage_name = "outline" if args.stage == "outline" else "plan"
        cmd = [
            sys.executable,
            str(create_script),
            "--topic",
            topic,
            "--stage",
            stage_name,
            "--complexity",
            args.complexity,
            "--timestamp",
            timestamp,
            "--slug",
            slug,
            "--output-dir",
            str(project_dir),
            "--target-venue",
            args.target_venue,
            "--style-mode",
            args.style_mode,
        ]
        for venue in args.preferred_venue:
            cmd.extend(["--preferred-venue", venue])
        for anchor in args.style_anchor_paper:
            cmd.extend(["--style-anchor-paper", anchor])
        if args.check_latex:
            cmd.append("--check-latex")
        return run(cmd)

    if args.stage == "issues":
        if not project_dir.exists():
            print(f"error: project directory not found: {project_dir}", file=sys.stderr)
            return 1
        if not args.timestamp:
            inferred = infer_latest_plan_timestamp_and_slug(project_dir / "plan")
            if inferred is None:
                print("error: could not infer timestamp/slug from latest plan", file=sys.stderr)
                return 1
            timestamp, slug = inferred

        ensure_paper_config(
            project_dir=project_dir,
            topic=topic,
            workflow_mode="standard",
            target_venue=args.target_venue,
            preferred_venues=args.preferred_venue,
            style_mode=args.style_mode,
            style_anchor_papers=args.style_anchor_paper,
        )

        cmd = [
            sys.executable,
            str(create_script),
            "--topic",
            topic,
            "--stage",
            "issues",
            "--timestamp",
            timestamp,
            "--slug",
            slug,
            "--output-dir",
            str(project_dir),
            "--target-venue",
            args.target_venue,
            "--style-mode",
            args.style_mode,
        ]
        for venue in args.preferred_venue:
            cmd.extend(["--preferred-venue", venue])
        for anchor in args.style_anchor_paper:
            cmd.extend(["--style-anchor-paper", anchor])
        if args.check_latex:
            cmd.append("--check-latex")
        if args.with_literature_notes:
            cmd.append("--with-literature-notes")
        return run(cmd)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
