# Paper Stack Architecture

## Layers
- **Router**: `paper-from-zero`
- **Review executor**: `../arxiv-paper-writer`
- **Empirical executor**: `../empirical-paper-writer`
- **Shared paper core**: reused assets/scripts/references from `../arxiv-paper-writer`

## Data Flow
1. Topic in
2. Literature mapping
3. Contribution framing
4. Evidence matrix
5. Outline contract
6. Route to review or empirical writer
7. Writer produces project scaffold, issues contract, draft, and QA artifacts

## Shared Core Reuse
- Assets: IEEEtran base, bibliography template, plan/issues templates as patterns
- Scripts: arXiv registry, citation audit, source ranking, compile, style profile
- References: BibTeX rules, citation workflow, template usage, writing style, visual guidance, QA

## Decision Boundary
- `paper-from-zero` decides **what kind of paper this is**.
- The downstream writer decides **how to turn the contract into a draft**.
