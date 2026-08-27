# Topology Census

Every canonical association subgraph was evaluated against all six governed topology families.

| Topology | Valid | Invalid | Total |
| --- | --- | --- | --- |
| LINEAR_PATH | 45 | 13 | 58 |
| BINARY_FORK | 18 | 40 | 58 |
| BINARY_CONVERGENCE | 18 | 40 | 58 |
| QUALIFIED_PATH | 0 | 58 | 58 |
| REFLEXIVE_RETURN | 0 | 58 | 58 |
| EVIDENCE_GAP_TREE | 0 | 58 | 58 |

## Rejection reasons

| Reason code | Count |
| --- | --- |
| BINARY_REQUIRES_EXACTLY_THREE_NODES_TWO_EDGES | 80 |
| EQUAL_EVIDENCE_CAPACITY_TIE | 2 |
| NOT_A_CONNECTED_LINEAR_TREE | 13 |
| NO_EXPLICIT_GOVERNED_EVIDENCE_GAP_NODE | 58 |
| NO_EXPLICIT_GOVERNED_NAVIGATION_RETURN | 58 |
| NO_EXPLICIT_GOVERNED_QUALIFICATION_GATE | 58 |
| TOPOLOGY_DEGREE_BOUND | 8 |

Pruned, split, gap, and unresolved composition counts are respectively `7`, `7`, `0`, and `0`. Zero-valued families were still evaluated and have explicit reasons.

The frozen Round 15 result is preserved as an input receipt. The adapter’s stricter binary rule prevents three-edge triangles from being mislabeled as two-branch structures. All 11 Round 16 legacy compositions are reconciled; unexplained count is `0`.

Sources: `docs/audits/v49-exploration-full-space-closure-round1/raw/composition-enumeration-v2.tsv`, `docs/audits/v49-exploration-full-space-closure-round1/raw/composition-rejection-ledger-v2.tsv`, and `docs/audits/v49-exploration-full-space-closure-round1/raw/composition-statistics-v2.json`.
