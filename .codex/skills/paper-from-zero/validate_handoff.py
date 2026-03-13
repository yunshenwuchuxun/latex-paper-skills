#!/usr/bin/env python3
"""Validate paper-from-zero handoff artifacts in a project directory.

Dependency-free validator to catch missing/incomplete handoff files before
routing to downstream writer skills.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


def fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def extract_yaml_block(text: str, key: str) -> str:
    pattern = re.compile(rf"(?m)^(?P<indent>\s*){re.escape(key)}\s*:\s*$")
    match = pattern.search(text)
    if not match:
        return ""
    indent = match.group("indent")
    start = match.end()
    end = len(text)
    for next_match in re.finditer(r"(?m)^(?P<indent>\s*)([A-Za-z_][\w-]*)\s*:\s*$", text[start:]):
        if len(next_match.group("indent")) <= len(indent):
            end = start + next_match.start()
            break
    return text[start:end].strip("\n")


def extract_primary_claim_statement(contribution_yaml: str) -> str:
    block = extract_yaml_block(contribution_yaml, "primary_claim")
    if not block:
        return ""
    m = re.search(r"(?m)^\s*statement\s*:\s*(?P<rest>.*)$", block)
    if not m:
        return ""
    rest = m.group("rest").strip()
    if rest and rest not in {">", "|", ">-", "|-"}:
        return rest
    after = block[m.end() :]
    lines: list[str] = []
    for line in after.splitlines():
        if not line.strip():
            if lines:
                break
            continue
        if not re.match(r"^\s{2,}", line):
            break
        lines.append(line.strip())
    return " ".join(lines).strip()


def extract_claim_ids(contribution_yaml: str) -> tuple[str, list[str]]:
    primary = ""
    secondary: list[str] = []

    primary_block = extract_yaml_block(contribution_yaml, "primary_claim")
    if primary_block:
        m = re.search(r"(?m)^\s*id\s*:\s*(?P<id>[A-Za-z0-9_-]+)\s*$", primary_block)
        if m:
            primary = m.group("id").strip()

    secondary_block = extract_yaml_block(contribution_yaml, "secondary_claims")
    if secondary_block:
        for m in re.finditer(r"(?m)^\s*-\s*id\s*:\s*(?P<id>[A-Za-z0-9_-]+)\s*$", secondary_block):
            secondary.append(m.group("id").strip())

    return primary, secondary


def has_any_list_items(contribution_yaml: str, key: str) -> bool:
    block = extract_yaml_block(contribution_yaml, key)
    if not block:
        return False
    return any(re.match(r"(?m)^\s*-\s+\S+", line) for line in block.splitlines())


def validate_topic_brief(text: str) -> list[str]:
    errors: list[str] = []
    has_venue = bool(re.search(r"(?im)^\s*-\s*\*\*Target\*\*\s*:\s*(?!TBD\b).+\S", text)) or bool(
        re.search(r"(?im)^\s*(Target|Venue)\s*:\s*(?!TBD\b).+\S", text)
    )
    has_pages = bool(re.search(r"(?im)\b(\d{1,2})\s*[-–]\s*(\d{1,2})\s*pages\b", text)) or bool(
        re.search(r"(?im)\b(\d{1,2})\s*pages\b", text)
    ) or bool(re.search(r"(?im)assumed length\s*:\s*(?!TBD\b).+\S", text))
    if not (has_venue or has_pages):
        errors.append("brief/topic-brief.md missing a concrete venue target or page/length target (non-TBD).")
    return errors


def validate_outline_contract(text: str) -> list[str]:
    errors: list[str] = []
    count = len(re.findall(r"(?m)^\s*\d+\.\s+\*\*.*\*\*", text)) or len(re.findall(r"(?m)^\s*\d+\.\s+\S+", text))
    if count < 4:
        errors.append("plan/outline-contract.md should include at least 4 top-level sections.")
    if not re.search(r"(?i)citation", text):
        errors.append("plan/outline-contract.md should mention citation quotas (non-zero total).")
    return errors


def validate_router_decision(text: str) -> list[str]:
    errors: list[str] = []
    if not re.search(r"(?im)^\s*Route to\s+\*\*.+\*\*", text):
        errors.append("plan/router-decision.md missing a clear 'Route to **...**' line.")
    if not re.search(r"(?i)arxiv-paper-writer|empirical-paper-writer", text):
        errors.append("plan/router-decision.md should mention arxiv-paper-writer or empirical-paper-writer explicitly.")
    return errors


def validate_evidence_matrix(csv_path: Path, claim_ids: list[str]) -> list[str]:
    errors: list[str] = []
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return ["brief/evidence-matrix.csv is empty."]
        claim_col = next((name for name in reader.fieldnames if name.strip().lower() in {"claim_id", "claimid"}), None)
        if claim_col is None:
            claim_col = reader.fieldnames[0]

        present: set[str] = set()
        rows = 0
        for row in reader:
            rows += 1
            raw = (row.get(claim_col) or "").strip()
            if raw:
                present.add(raw)

    if rows == 0:
        return ["brief/evidence-matrix.csv has no data rows."]
    missing = [cid for cid in claim_ids if cid and cid not in present]
    if missing:
        errors.append(f"brief/evidence-matrix.csv missing rows for claim_id(s): {', '.join(missing)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate paper-from-zero handoff artifacts.")
    parser.add_argument("--project-dir", default=".", help="Project directory containing brief/ and plan/ artifacts.")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.exists():
        return fail(f"project dir not found: {project_dir}")

    required = {
        "brief/topic-brief.md": project_dir / "brief" / "topic-brief.md",
        "brief/contribution-map.yaml": project_dir / "brief" / "contribution-map.yaml",
        "brief/evidence-matrix.csv": project_dir / "brief" / "evidence-matrix.csv",
        "plan/outline-contract.md": project_dir / "plan" / "outline-contract.md",
        "plan/router-decision.md": project_dir / "plan" / "router-decision.md",
    }

    errors: list[str] = []
    for rel, path in required.items():
        if not path.exists():
            errors.append(f"missing artifact: {rel}")

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    topic_text = read_text(required["brief/topic-brief.md"])
    contribution_text = read_text(required["brief/contribution-map.yaml"])
    outline_text = read_text(required["plan/outline-contract.md"])
    router_text = read_text(required["plan/router-decision.md"])

    errors.extend(validate_topic_brief(topic_text))

    statement = extract_primary_claim_statement(contribution_text)
    if not statement.strip():
        errors.append("brief/contribution-map.yaml primary_claim.statement is empty.")

    if not (has_any_list_items(contribution_text, "risk_factors") or has_any_list_items(contribution_text, "likely_reviewer_objections")):
        errors.append("brief/contribution-map.yaml must include at least one risk factor or reviewer objection.")

    primary_id, secondary_ids = extract_claim_ids(contribution_text)
    claim_ids = [cid for cid in [primary_id, *secondary_ids] if cid]
    if not claim_ids:
        errors.append("brief/contribution-map.yaml missing primary/secondary claim IDs.")
    else:
        errors.extend(validate_evidence_matrix(required["brief/evidence-matrix.csv"], claim_ids))

    errors.extend(validate_outline_contract(outline_text))
    errors.extend(validate_router_decision(router_text))

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print("paper-from-zero handoff validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

