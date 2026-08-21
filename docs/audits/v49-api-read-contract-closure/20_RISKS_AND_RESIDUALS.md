# Risks and residuals

```text
P0_COUNT=0
P1_COUNT=0
P2_COUNT=1
```

P2: the repository declares `next lint`, but has no ESLint configuration or direct ESLint dependency; Next.js 15 prompts for setup. TypeScript checking and Next production build both pass. This is tooling debt, not an API contract or database integrity gap.

Deliberate fail-closed product state remains: zero accepted TRACE relations, zero public relation/claim/corpus detail records, zero folder projections, zero positive visual rights, and citation-only surface delivery. These are data/publication semantics, not missing API fallbacks. Future frontend design must render valid empty/404 states and must not infer relationships, rights, pixels, acceptance, or held records.

No staging/production/deployment residual exists. The sole task-owned PostgreSQL cluster was stopped cleanly; its postmaster PID no longer exists, no task-owned importer/builder/API harness process remains, and both exact scratch roots were removed after evidence was copied into this audit package. `TASK_OWNED_RESIDUAL_PROCESS_COUNT=0`.
