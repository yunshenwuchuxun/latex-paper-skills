#!/usr/bin/env python3
"""Build a self-contained installable skill from tracked source files.

The source skills share scripts and templates outside individual skill folders.
Ship them together, and use workflow.md for nested instruction files so skill
installers discover just the public package entry point.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / ".codex" / "skills"
DEST = REPO / "skills" / "latex-paper-skills"
VERSION = "0.1.0"


def expected_files() -> dict[Path, bytes]:
    tracked = subprocess.check_output(
        ["git", "ls-files", "-z", "--", ".codex/skills"], cwd=REPO
    ).decode("utf-8").split("\0")
    files = {
        Path("SKILL.md"): (REPO / "distribution/latex-paper-skills.SKILL.md").read_bytes(),
        Path("LICENSE"): (REPO / "LICENSE").read_bytes(),
        Path("THIRD_PARTY_NOTICES.md"): (REPO / "distribution/THIRD_PARTY_NOTICES.md").read_bytes(),
    }
    for name in tracked:
        if not name:
            continue
        source = REPO / name
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Distribution source must be a regular file: {name}")
        relative = source.relative_to(SOURCE)
        if "__pycache__" in relative.parts or source.suffix == ".pyc":
            continue
        data = source.read_bytes()
        if source.suffix in {".md", ".yaml"}:
            data = data.decode("utf-8").replace("SKILL.md", "workflow.md").encode("utf-8")
        if relative.name == "SKILL.md":
            relative = relative.with_name("workflow.md")
        files[Path("references/skills") / relative] = data
    return files


def check(files: dict[Path, bytes]) -> bool:
    actual = {p.relative_to(DEST) for p in DEST.rglob("*") if p.is_file()}
    expected = set(files)
    differences = sorted(actual ^ expected)
    differences += sorted(p for p in actual & expected if (DEST / p).read_bytes() != files[p])
    if differences:
        print("Distribution is out of date; run python3 scripts/build_distribution.py", file=sys.stderr)
        for path in differences:
            print(f"  {path}", file=sys.stderr)
        return False
    print(f"Distribution matches {len(files)} source files.")
    return True


def build_clawhub_bundle(files: dict[Path, bytes], scope: str) -> Path:
    dest = REPO / "dist" / "clawhub-bundle"
    if dest.exists():
        shutil.rmtree(dest)
    for relative, data in files.items():
        output = dest / "skills/latex-paper-skills" / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
    manifests = {
        "package.json": {
            "name": f"@{scope}/latex-paper-skills",
            "version": VERSION,
            "description": "ML/AI academic LaTeX paper workflows, tools, and templates",
            "license": "MIT",
            "repository": {
                "type": "git",
                "url": "https://github.com/yunshenwuchuxun/latex-paper-skills.git",
            },
        },
        "openclaw.plugin.json": {
            "id": "latex-paper-skills",
            "name": "LaTeX Paper Skills",
            "version": VERSION,
            "description": "ML/AI academic LaTeX paper workflows, tools, and templates",
            "skills": ["skills"],
            "configSchema": {"type": "object", "additionalProperties": False, "properties": {}},
        },
        ".claude-plugin/plugin.json": {
            "name": "latex-paper-skills",
            "version": VERSION,
            "description": "ML/AI academic LaTeX paper workflows, tools, and templates",
            "license": "MIT",
            "skills": ["./skills/"],
        },
    }
    for name, manifest in manifests.items():
        path = dest / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (dest / "LICENSE").write_bytes(files[Path("LICENSE")])
    (dest / "THIRD_PARTY_NOTICES.md").write_text(
        "# Third-party notices\n\n"
        "See skills/latex-paper-skills/THIRD_PARTY_NOTICES.md for the bundled "
        "IEEEtran class's LPPL 1.3 license and retained source notices.\n",
        encoding="utf-8",
    )
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check generated files without modifying them.")
    parser.add_argument("--archive", action="store_true", help="Also write a root-SKILL.md ZIP in dist/.")
    parser.add_argument("--clawhub", action="store_true", help="Also build a ClawHub bundle plugin in dist/.")
    parser.add_argument("--clawhub-scope", default="yunshenwuchuxun", help="ClawHub publisher handle for the package scope.")
    args = parser.parse_args()
    if args.check and (args.archive or args.clawhub):
        parser.error("--check cannot be combined with archive/bundle generation")
    files = expected_files()
    if args.check:
        return 0 if check(files) else 1
    if DEST.exists():
        shutil.rmtree(DEST)
    for relative, data in files.items():
        output = DEST / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
    print(f"Built {DEST.relative_to(REPO)}: {len(files)} files, {sum(map(len, files.values())):,} bytes.")
    if args.archive:
        archive = REPO / "dist" / f"latex-paper-skills-{VERSION}.zip"
        archive.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
            for relative, data in sorted(files.items()):
                info = zipfile.ZipInfo(relative.as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                bundle.writestr(info, data)
        print(f"Archive: {archive.relative_to(REPO)}")
    if args.clawhub:
        if not args.clawhub_scope or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in args.clawhub_scope):
            parser.error("--clawhub-scope must be a lowercase publisher handle")
        bundle = build_clawhub_bundle(files, args.clawhub_scope)
        print(f"ClawHub plugin: {bundle.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
