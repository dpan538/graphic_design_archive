# Composition Enumeration Method

Round 16A enumerates the complete finite active space rather than a fixture sample. The normative graph has 21 edges. Enumeration examines every bounded connected edge subgraph spanning 2–8 active nodes, records disconnected and over-bound candidates, evaluates all six topology families, and calls the frozen Round 15 engine for every canonical association subgraph through adapter `trace-round15-full-space-adapter-v2`.

The strict adapter does not modify Round 15. It requires a connected tree with maximum degree two for `LINEAR_PATH`, and exactly three nodes, two edges, and degree sequence `[1,1,2]` for each binary form. Qualification, return, and evidence-gap families require explicit governed records; their absence produces recorded invalid decisions rather than invented structures.

| Enumeration measure | Count |
| --- | --- |
| Raw node subsets | 11460917 |
| Connected node subsets | 30 |
| Raw edge subgraphs | 96 |
| Canonical association subgraphs | 58 |
| Topology candidate rows | 348 |
| Valid topology compositions | 81 |
| Invalid topology decisions | 267 |
| Duplicate canonicalisations | 0 |

`ALL_LEGAL_SUBGRAPHS_ENUMERATED=true`

`ALL_LEGAL_TOPOLOGIES_EVALUATED=true`

Sources: `docs/audits/v49-exploration-full-space-closure-round1/raw/composition-enumeration-v2.tsv`, `docs/audits/v49-exploration-full-space-closure-round1/raw/composition-rejection-ledger-v2.tsv`, and `docs/audits/v49-exploration-full-space-closure-round1/raw/canonical-composition-registry-v2.json`.
