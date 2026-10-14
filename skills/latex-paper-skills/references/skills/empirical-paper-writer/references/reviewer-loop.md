# Reviewer Loop

Run a self-review pass from four angles:
- **Novelty**: Is the gap real and visible against the closest baselines?
- **Completeness**: Does every main claim have an evidence path?
- **Credibility**: Are there any unverified claims written as facts?
- **Compilability**: Does the LaTeX project remain structurally valid?

For each pass, output a structured table:

| Claim / Section | Issue | Severity | Action Required |
|----------------|-------|----------|-----------------|
| <!-- claim or section path --> | <!-- challenged claim / missing evidence / weak wording / missing visual --> | HIGH / MEDIUM / LOW | <!-- specific fix: weaken wording / add citation / add experiment / add figure --> |

After each self-review pass, update the issues CSV:
- Insert new issue rows for any identified gaps (e.g., `Q5`, `W6a`).
- Re-run `validate_empirical_paper_issues.py` after edits.
- Do not mark the review pass complete until all HIGH-severity items have corresponding issues.
