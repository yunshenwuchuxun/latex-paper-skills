#!/usr/bin/env python3
"""Bootstrap an IEEE empirical paper project (scaffold + plan/issues)."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from paper_utils import ensure_paper_config, now_timestamp, slugify, validate_slug, validate_timestamp  # noqa: E402


def run(cmd: list[str]) -> int:
    return subprocess.run(cmd).returncode


def empirical_skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def review_template_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "arxiv-paper-writer" / "assets" / "template"


def empirical_template_dir() -> Path:
    return empirical_skill_root() / "assets" / "template"


def _scaffold_paper_dir(paper_dir: Path) -> None:
    if paper_dir.exists():
        raise SystemExit(f"Destination already exists: {paper_dir}")

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
    shutil.copytree(base_template, paper_dir, ignore=ignore)

    for file_path in empirical_template_dir().glob("*"):
        if file_path.is_file():
            shutil.copy2(file_path, paper_dir / file_path.name)

    main_template = paper_dir / "main.template.tex"
    bib_template = paper_dir / "references.template.bib"
    main_tex = paper_dir / "main.tex"
    ref_bib = paper_dir / "ref.bib"

    if main_template.exists():
        main_template.rename(main_tex)
    if bib_template.exists():
        bib_template.rename(ref_bib)

    print(f"Created empirical paper scaffold at: {paper_dir}")


def _read_asset_text(name: str) -> str:
    path = empirical_skill_root() / "assets" / name
    if not path.exists():
        raise SystemExit(f"Missing asset template: {path}")
    return path.read_text(encoding="utf-8").lstrip("\ufeff")


def scaffold_experiments_dir(experiments_dir: Path, *, project_name: str) -> None:
    if experiments_dir.exists():
        raise SystemExit(f"Destination already exists: {experiments_dir}")
    experiments_dir.mkdir(parents=True, exist_ok=False)

    templates: list[tuple[str, str]] = [
        ("experiments-template.README.md", "README.md"),
        ("experiments-template.requirements.txt", "requirements.txt"),
        ("experiments-template.configs.default.yaml", "configs/default.yaml"),
        ("experiments-template.run_all.py", "run_all.py"),
        ("experiments-template.train.py", "train.py"),
        ("experiments-template.evaluate.py", "evaluate.py"),
        ("experiments-template.utils.config.py", "utils/config.py"),
        ("experiments-template.utils.io.py", "utils/io.py"),
        ("experiments-template.utils.paths.py", "utils/paths.py"),
        ("experiments-template.models.model_stub.py", "models/model_stub.py"),
        ("experiments-template.data.dataset_stub.py", "data/dataset_stub.py"),
        ("experiments-template.metrics.metrics_stub.py", "metrics/metrics_stub.py"),
    ]

    for src_name, rel_dest in templates:
        content = _read_asset_text(src_name).replace("<PROJECT_NAME>", project_name)
        dest_path = experiments_dir / rel_dest
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(content, encoding="utf-8")

    print(f"Created experiment code scaffold at: {experiments_dir}")


def scaffold_project(folder_name: str, out_dir: Path, *, layout: str) -> tuple[Path, Path]:
    root_dir = out_dir / folder_name
    if layout == "flat":
        _scaffold_paper_dir(root_dir)
        return root_dir, root_dir

    if root_dir.exists():
        raise SystemExit(f"Destination already exists: {root_dir}")

    paper_dir = root_dir / "paper"
    experiments_dir = root_dir / "experiments"
    paper_dir.parent.mkdir(parents=True, exist_ok=True)
    _scaffold_paper_dir(paper_dir)
    scaffold_experiments_dir(experiments_dir, project_name=folder_name)
    return root_dir, paper_dir


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
    parser.add_argument("--layout", default="flat", choices=["flat", "project"])
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
    root_dir = out_dir / folder_name
    paper_dir = root_dir if args.layout == "flat" else root_dir / "paper"
    if args.stage == "issues" and args.layout == "flat":
        # Convenience auto-detection: if the root contains a "paper/" subdir and no main.tex at root,
        # treat it as a project-layout bootstrap.
        if (root_dir / "paper").exists() and not (root_dir / "main.tex").exists():
            paper_dir = root_dir / "paper"

    create_script = empirical_skill_root() / "scripts" / "create_empirical_plan.py"

    if args.stage in {"kickoff", "outline"}:
        _, paper_dir = scaffold_project(folder_name, out_dir, layout=args.layout)
        workflow_mode = "outline-only" if args.stage == "outline" else "standard"
        ensure_paper_config(
            project_dir=paper_dir,
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
            str(paper_dir),
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
        if not paper_dir.exists():
            print(f"error: project directory not found: {paper_dir}", file=sys.stderr)
            return 1
        if not args.timestamp:
            inferred = infer_latest_plan_timestamp_and_slug(paper_dir / "plan")
            if inferred is None:
                print("error: could not infer timestamp/slug from latest plan", file=sys.stderr)
                return 1
            timestamp, slug = inferred

        ensure_paper_config(
            project_dir=paper_dir,
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
            str(paper_dir),
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
