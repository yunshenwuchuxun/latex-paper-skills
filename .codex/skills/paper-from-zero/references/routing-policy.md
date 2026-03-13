# Routing Policy

## Route to `arxiv-paper-writer`
- Surveys, tutorials, taxonomies, benchmark syntheses
- Papers whose novelty is mainly synthesis or organization of prior work
- Deliverables that can be supported entirely by verified citations and visuals

## Route to `empirical-paper-writer`
- Novel methods, training recipes, evaluation settings, ablation claims
- Papers whose main contribution requires experiments, tables, or quantitative comparison
- Deliverables where at least one core claim needs an experiment contract

## Tie-Break Rule
If the topic spans both review and experiment, pick the mode that best matches the **main title claim** and record the alternative path in `plan/router-decision.md`.
