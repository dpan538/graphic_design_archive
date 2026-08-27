# Canonical Workflow Census

There is one deterministic shortest workflow from the applicable production root to every reachable exportable state. Breadth-first search uses a stable action/target order. Every workflow was replayed twice and checked against both target state and semantic hashes.

| Metric | Value |
| --- | --- |
| Canonical workflows | 5760 |
| Workflow targets | 5760 |
| Replayed workflows | 5760 |
| Replay failures | 0 |
| State replay mismatches | 0 |
| Semantic replay mismatches | 0 |
| Length minimum | 0 |
| Length maximum | 5 |
| Length mean | 2.425 |
| Length median | 2 |

## Workflow-length distribution

| Length | Count |
| --- | --- |
| 0 | 228 |
| 1 | 960 |
| 2 | 1812 |
| 3 | 1788 |
| 4 | 840 |
| 5 | 132 |

Sources: `docs/audits/v49-exploration-full-space-closure-round1/raw/workflow-census-v2.tsv` and `docs/audits/v49-exploration-full-space-closure-round1/raw/transition-census-v2.tsv`.
