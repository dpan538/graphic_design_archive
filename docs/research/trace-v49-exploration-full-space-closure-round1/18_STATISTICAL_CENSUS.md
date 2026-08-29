# Statistical Census

## Vocabulary

| Disposition | Count | Rate of candidates |
| --- | --- | --- |
| ACTIVE | 31 | 47.69% |
| MERGED_SUPERSEDED | 1 | 1.54% |
| REJECTED | 12 | 18.46% |
| RESEARCH_ONLY | 21 | 32.31% |

Active vocabulary is `31/65` (47.69%). Candidate-universe and active-vocabulary counts are not association counts.

| Vocabulary statistic | Distribution |
| --- | --- |
| Attestation-source IDs across active terms | `{"ATT-0007":1,"ATT-0008":1,"ATT-0040":1,"ATT-0041":1,"COMP-EVID-012":1,"COMP-EVID-013":1,"COMP-EVID-014":1,"COMP-EVID-015":1,"COMP-EVID-018":1,"COMP-EVID-019":1,"COMP-EVID-021":2,"COMP-EVID-022":1,"COMP-EVID-023":1,"GRAM-ATT-003":1,"GRAM-ATT-020":1,"R14-EVID-001-01":1,"R14-EVID-001-02":1,"R14-EVID-002-01":2,"R14-EVID-002-03":2,"R14-EVID-003-01":2,"R14-EVID-003-03":1,"R14-EVID-004-01":2,"R14-EVID-004-02":2,"R14-EVID-004-03":2,"R14-EVID-005-01":1,"R14-EVID-005-02":2,"R14-EVID-006-01":1,"R14-EVID-006-02":1,"R14-EVID-006-03":1,"R14-EVID-007-01":2,"R14-EVID-008-01":1,"R14-EVID-008-02":1,"R14-EVID-009-01":1,"R14-EVID-010-01":1,"R14-EVID-013-01":1,"R14-EVID-013-02":1,"R14-EVID-014-01":2,"R14-EVID-015-01":1,"R14-EVID-016-01":2,"R14-EVID-016-02":2,"R14-EVID-017-01":2,"R14-EVID-017-02":1,"R14-EVID-017-03":2,"R14-EVID-018-01":2,"R14-EVID-020-01":2,"R14-EVID-021-02":1,"R16-SRC-003:attestation:advertising":1,"R16-SRC-004:attestation:advertising":1,"R16-SRC-004:attestation:consumer-culture":1,"R16-SRC-005:attestation:design-education":1,"R16-SRC-006:attestation:design-education":1}` |
| Academic-source IDs across active terms | `{"COMP-SRC-001":3,"COMP-SRC-002":3,"COMP-SRC-004":2,"COMP-SRC-005":2,"COMP-SRC-006":2,"COMP-SRC-007":2,"COMP-SRC-008":2,"COMP-SRC-009":3,"COMP-SRC-010":3,"COMP-SRC-011":1,"COMP-SRC-012":1,"COMP-SRC-013":3,"COMP-SRC-014":2,"COMP-SRC-017":1,"COMP-SRC-018":1,"COMP-SRC-019":2,"COMP-SRC-020":3,"COMP-SRC-021":1,"COMP-SRC-022":1,"COMP-SRC-023":3,"COMP-SRC-024":3,"COMP-SRC-025":4,"GRAM-SRC-003":1,"GRAM-SRC-019":1,"R16-SRC-001":1,"R16-SRC-002":1,"R16-SRC-003":1,"R16-SRC-004":2,"R16-SRC-005":3,"R16-SRC-006":1,"SRC-0007":1,"SRC-0008":1,"SRC-0033":1,"SRC-0037":1}` |
| Category memberships across active terms | `{"medium":7,"movement":7,"region":12,"theme":11}` |
| Category memberships per active term | `{"1":26,"2":4,"3":1}` |
| Polysemy/ambiguity-flagged candidate dispositions | `{"ACTIVE":9,"RESEARCH_ONLY":5}` |

The polysemy/ambiguity subset is the deterministic set whose governed ambiguity note or decision reason contains `polysem*`, `ambigu*`, or `confus*`; it is a reporting filter, not a new eligibility rule.

## Associations

| Disposition | Count | Rate of all pairs |
| --- | --- | --- |
| ACTIVE_EXTERNALLY_SUPPORTED | 18 | 3.87% |
| ACTIVE_SOURCE_SUPPORTED | 3 | 0.65% |
| INACTIVE_CONFLICTING_SCOPE | 1 | 0.22% |
| INACTIVE_HARD_NEGATIVE | 9 | 1.94% |
| INACTIVE_INSUFFICIENT_EVIDENCE | 434 | 93.33% |

Active generic associations are `21/465` (4.52%). Strength, confidence, and D1/D5/D7 distributions follow.

| Dimension | Distribution |
| --- | --- |
| Strength | `{"MODERATE":4,"NONE":434,"STRONG":18,"WEAK":9}` |
| Confidence | `{"HIGH":11,"LOW":9,"MODERATE":11,"NONE":434}` |
| D1 | `{"0":443,"1":4,"2":18}` |
| D5 | `{"0":443,"1":4,"2":18}` |
| D7 | `{"0":443,"1":3,"2":19}` |

Co-occurrence-only and conflicting-scope rates are `0.00%` and `0.22%`. Within-category and cross-category edge rates are `100.00%` and `0.00%`.

## Graph

Graph density is `0.045161` over `31` nodes and `21` edges. Degree distribution is `{"0":5,"1":12,"2":12,"3":2}`; component-size distribution is `{"1":5,"2":5,"3":4,"4":1}`. Centrality is not historical importance.

## Compositions

| Measure | Value |
| --- | --- |
| Raw candidate node subsets | 11460917 |
| Connected node subsets | 30 |
| Raw edge subgraphs | 96 |
| Canonical association subgraphs | 58 |
| Valid topology compositions | 81 |
| Invalid topology candidates | 267 |
| Seed variants | 228 |
| Category-entry variants | 81 |
| Multi-category compositions | 0 |
| Pruning rate | 12.07% |
| Split rate | 12.07% |
| Gap rate | 0.00% |
| Unresolved rate | 0.00% |

Topology, composition-size, edge-count, and category-entry distributions are `{"BINARY_CONVERGENCE":18,"BINARY_FORK":18,"LINEAR_PATH":45}`, `{"2":21,"3":54,"4":6}`, `{"1":21,"2":54,"3":6}`, and `{"medium":2,"movement":6,"region":25,"theme":48}`.

## Interaction and export

States per production composition range `8–64`; transitions per state range `15–157`. There are `5760` canonical workflows with length distribution `{"0":228,"1":960,"2":1812,"3":1788,"4":840,"5":132}` and `11520` export variants, `2–2` per state.

## Runtime

Production latency, throughput, response-size, CPU, memory, event-loop-delay, PNG-cost, and concurrency-scaling results are reported without extrapolation in `17_PRODUCTION_LOAD_RESULTS.md`. Offline generation timings remain separate in `docs/audits/v49-exploration-full-space-closure-round1/raw/build-time-computation-results.json`.
