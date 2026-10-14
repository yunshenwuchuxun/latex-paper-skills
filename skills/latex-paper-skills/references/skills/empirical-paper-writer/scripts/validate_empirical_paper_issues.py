#!/usr/bin/env python3
"""Validate empirical paper issues CSV schema and required fields."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "ID",
    "Phase",
    "Title",
    "Section_Path",
    "Claim_ID",
    "Evidence_Type",
    "Experiment_ID",
    "Result_Status",
    "Description",
    "Source_Policy",
    "Target_Citations",
    "Visualization",
    "Acceptance",
    "Status",
    "Verified_Citations",
    "Depends_On",
    "Must_Verify",
    "Notes",
]
ALLOWED_PHASES = {"Research", "Experiment", "Writing", "Visual", "Refinement", "QA"}
ALLOWED_STATUS = {"TODO", "DOING", "DONE", "SKIP"}
PHASE_PREFIX = {"Research": "R", "Experiment": "E", "Writing": "W", "Visual": "V", "Refinement": "RF", "QA": "Q"}
ALLOWED_SOURCE_POLICIES = {"core", "standard", "frontier"}
ALLOWED_EVIDENCE_TYPES = {"n/a", "citation", "experiment", "figure", "table", "mixed"}
ALLOWED_RESULT_STATUS = {"n/a", "planned", "placeholder", "verified"}
ALLOWED_BOOL = {"yes", "no"}
PLACEHOLDER_RE = re.compile(r"\b(TBD|placeholder|<.+?>)\b", re.IGNORECASE)


def fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def parse_non_negative_int(value: str, *, row_idx: int, column: str, errors: list[str]) -> int:
    raw = value.strip()
    if not raw:
        errors.append(f"row {row_idx}: '{column}' is empty")
        return 0
    try:
        parsed = int(raw)
    except ValueError:
        errors.append(f"row {row_idx}: '{column}' must be an integer, got '{value}'")
        return 0
    if parsed < 0:
        errors.append(f"row {row_idx}: '{column}' must be >= 0")
        return 0
    return parsed


def looks_like_placeholder(value: str) -> bool:
    text = value.strip()
    return not text or bool(PLACEHOLDER_RE.search(text))


TEX_PLACEHOLDER_PATTERNS = [
    re.compile(r"\\fbox\{", re.IGNORECASE),
    re.compile(r"\(hypothesis\)", re.IGNORECASE),
    re.compile(r"\[Abstract placeholder", re.IGNORECASE),
    re.compile(r"placeholder\]", re.IGNORECASE),
    re.compile(r"\[Results pending\]", re.IGNORECASE),
    re.compile(r"\[Pending", re.IGNORECASE),
]


def _parse_tex_sections(tex_content: str) -> dict[str, str]:
    """Split tex content into sections keyed by section/subsection name."""
    section_re = re.compile(r"\\(?:section|subsection)\{([^}]+)\}")
    sections: dict[str, str] = {}
    matches = list(section_re.finditer(tex_content))
    for i, m in enumerate(matches):
        name = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(tex_content)
        sections[name] = tex_content[start:end]
    return sections


def audit_tex_placeholders(
    issues: list[dict[str, str]], tex_path: Path
) -> list[str]:
    """Check DONE Writing issues for residual placeholders in main.tex."""
    tex_content = tex_path.read_text(encoding="utf-8", errors="replace")
    sections = _parse_tex_sections(tex_content)
    warnings: list[str] = []

    for issue in issues:
        if issue["Status"].strip() != "DONE":
            continue
        if issue["Phase"].strip() != "Writing":
            continue
        section_path = issue["Section_Path"].strip()
        if not section_path or section_path.upper() == "N/A":
            continue

        # Match section path to tex sections (use last component for matching)
        leaf = section_path.split(">")[-1].strip()
        matched_content = None
        for sec_name, sec_text in sections.items():
            if leaf.lower() in sec_name.lower():
                matched_content = sec_text
                break

        if matched_content is None:
            # Try full content match for Abstract
            if leaf.lower() == "abstract":
                abstract_re = re.compile(
                    r"\\begin\{abstract\}(.*?)\\end\{abstract\}", re.DOTALL
                )
                abstract_match = abstract_re.search(tex_content)
                if abstract_match:
                    matched_content = abstract_match.group(1)

        if matched_content is None:
            continue

        result_status = issue.get("Result_Status", "").strip().lower()
        if result_status in {"planned", "placeholder"}:
            # Hypothesis-safe placeholder writing is allowed for these DONE sections.
            continue
        for pat in TEX_PLACEHOLDER_PATTERNS:
            if pat.search(matched_content):
                iid = issue["ID"].strip()
                tag = f" (result_status={result_status})" if result_status else ""
                warnings.append(
                    f"DONE issue '{iid}' section '{leaf}' still contains "
                    f"placeholder content matching /{pat.pattern}/{tag}"
                )

    return warnings


def main() -> int:
    if len(sys.argv) < 2:
        return fail("usage: validate_empirical_paper_issues.py <issues.csv>")

    path = Path(sys.argv[1])
    if not path.exists():
        return fail(f"file not found: {path}")

    rows: list[list[str]] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if any(cell.strip() for cell in row):
                rows.append(row)

    if not rows:
        return fail("csv is empty")

    header = rows[0]
    if header != REQUIRED_COLUMNS:
        return fail("invalid header. expected: " + ",".join(REQUIRED_COLUMNS) + " | got: " + ",".join(header))

    errors: list[str] = []
    seen_ids: set[str] = set()

    for idx, row in enumerate(rows[1:], start=2):
        if len(row) != len(REQUIRED_COLUMNS):
            errors.append(f"row {idx}: expected {len(REQUIRED_COLUMNS)} columns, got {len(row)}")
            continue

        data = dict(zip(REQUIRED_COLUMNS, row))
        for col in ["ID", "Phase", "Title", "Description", "Acceptance", "Status"]:
            if not data[col].strip():
                errors.append(f"row {idx}: '{col}' is empty")

        phase = data["Phase"].strip()
        if phase not in ALLOWED_PHASES:
            errors.append(f"row {idx}: 'Phase' must be one of {sorted(ALLOWED_PHASES)}, got '{phase}'")

        status = data["Status"].strip()
        if status not in ALLOWED_STATUS:
            errors.append(f"row {idx}: 'Status' must be one of {sorted(ALLOWED_STATUS)}, got '{status}'")

        issue_id = data["ID"].strip()
        if issue_id in seen_ids:
            errors.append(f"row {idx}: duplicate ID '{issue_id}'")
        seen_ids.add(issue_id)
        if phase in PHASE_PREFIX and not issue_id.startswith(PHASE_PREFIX[phase]):
            errors.append(f"row {idx}: ID '{issue_id}' does not match phase prefix '{PHASE_PREFIX[phase]}'")

        target = parse_non_negative_int(data["Target_Citations"], row_idx=idx, column="Target_Citations", errors=errors)
        verified = parse_non_negative_int(data["Verified_Citations"], row_idx=idx, column="Verified_Citations", errors=errors)

        if looks_like_placeholder(data["Acceptance"]):
            errors.append(f"row {idx}: 'Acceptance' still contains a placeholder or TBD value")

        evidence_type = data["Evidence_Type"].strip().lower() or "n/a"
        if evidence_type not in ALLOWED_EVIDENCE_TYPES:
            errors.append(f"row {idx}: invalid 'Evidence_Type' '{data['Evidence_Type']}'")

        result_status = data["Result_Status"].strip().lower() or "n/a"
        if result_status not in ALLOWED_RESULT_STATUS:
            errors.append(f"row {idx}: invalid 'Result_Status' '{data['Result_Status']}'")

        must_verify = data["Must_Verify"].strip().lower()
        if must_verify not in ALLOWED_BOOL:
            errors.append(f"row {idx}: 'Must_Verify' must be one of {sorted(ALLOWED_BOOL)}")

        section_path = data["Section_Path"].strip()
        claim_id = data["Claim_ID"].strip()
        experiment_id = data["Experiment_ID"].strip()
        source_policy = data["Source_Policy"].strip().lower()

        if phase == "Writing":
            if not section_path or section_path.upper() == "N/A":
                errors.append(f"row {idx}: Writing issues must define 'Section_Path'")
            if source_policy not in ALLOWED_SOURCE_POLICIES:
                errors.append(f"row {idx}: Writing issues must set 'Source_Policy' to one of {sorted(ALLOWED_SOURCE_POLICIES)}")
            if evidence_type != "n/a" and target <= 0:
                errors.append(f"row {idx}: Writing issues must set 'Target_Citations' > 0 unless Evidence_Type is n/a")
            if status == "DONE" and evidence_type != "n/a" and verified <= 0:
                errors.append(f"row {idx}: DONE writing issues must record Verified_Citations > 0 unless Evidence_Type is n/a")
            if not claim_id or claim_id.upper() == "N/A":
                errors.append(f"row {idx}: Writing issues must define 'Claim_ID'")
            if looks_like_placeholder(data["Visualization"]):
                errors.append(f"row {idx}: Writing issues must define a concrete 'Visualization' plan")
        elif phase == "Experiment":
            if not claim_id or claim_id.upper() == "N/A":
                errors.append(f"row {idx}: Experiment issues must define 'Claim_ID'")
            if not experiment_id or experiment_id.upper() == "N/A":
                errors.append(f"row {idx}: Experiment issues must define 'Experiment_ID'")
            if result_status == "n/a":
                errors.append(f"row {idx}: Experiment issues must define a concrete 'Result_Status'")
        elif phase == "Visual":
            if not section_path or section_path.upper() == "N/A":
                errors.append(f"row {idx}: Visual issues must define 'Section_Path'")
            if evidence_type not in {"figure", "table", "mixed"}:
                errors.append(f"row {idx}: Visual issues should set 'Evidence_Type' to figure/table/mixed")
            if not claim_id or claim_id.upper() == "N/A":
                errors.append(f"row {idx}: Visual issues must define 'Claim_ID'")
            if looks_like_placeholder(data["Visualization"]):
                errors.append(f"row {idx}: Visual issues must define a concrete 'Visualization' plan")
        else:
            if section_path and section_path.upper() != "N/A":
                errors.append(f"row {idx}: only Writing/Experiment/Visual issues may set 'Section_Path' (use N/A otherwise)")
            if source_policy and source_policy.upper() != "N/A":
                errors.append(f"row {idx}: only Writing issues may set 'Source_Policy' (use N/A otherwise)")

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    # --- Dependency consistency check ---
    parsed: list[tuple[int, dict[str, str]]] = []
    for idx, row in enumerate(rows[1:], start=2):
        if len(row) == len(REQUIRED_COLUMNS):
            parsed.append((idx, dict(zip(REQUIRED_COLUMNS, row))))

    done_or_skip = {
        data["ID"].strip()
        for _, data in parsed
        if data["Status"].strip() in {"DONE", "SKIP"}
    }
    dep_errors: list[str] = []
    for idx, data in parsed:
        if data["Status"].strip() == "DONE":
            deps_raw = data["Depends_On"].strip()
            deps = [
                d.strip()
                for d in deps_raw.split(";")
                if d.strip() and d.strip().upper() != "N/A"
            ]
            for dep in deps:
                if dep not in done_or_skip:
                    dep_errors.append(
                        f"row {idx}: issue '{data['ID'].strip()}' is DONE "
                        f"but dependency '{dep}' is not DONE/SKIP"
                    )
    if dep_errors:
        for err in dep_errors:
            print(err, file=sys.stderr)
        return 1

    print("Empirical issues CSV validation passed")
    print(f"  Total issues: {len(rows) - 1}")

    # --- Optional tex placeholder audit ---
    if len(sys.argv) >= 4 and sys.argv[2] == "--audit-tex":
        tex_path = Path(sys.argv[3])
        if tex_path.exists():
            issue_dicts = [
                dict(zip(REQUIRED_COLUMNS, r)) for r in rows[1:]
                if len(r) == len(REQUIRED_COLUMNS)
            ]
            tex_warnings = audit_tex_placeholders(issue_dicts, tex_path)
            for w in tex_warnings:
                print(f"warning: {w}", file=sys.stderr)
            if tex_warnings:
                print(f"  Tex audit: {len(tex_warnings)} warning(s)")
        else:
            print(f"warning: tex file not found: {tex_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
