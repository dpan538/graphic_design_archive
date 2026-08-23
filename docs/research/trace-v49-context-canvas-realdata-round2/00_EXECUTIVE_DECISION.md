# TRACE v49 Context Canvas Round 2 — Executive Decision

## Decision

`DECISION=PROCEED_WITH_CONTROLLED_REAL_V49_VALIDATION`

The frozen sources reconcile to 15,923 canonical objects, 7,995 public objects, and 7,928 held objects. The current implementation has a defensible server-only projection for one selected public record and preserves all projected relationships as validation-only, proposed candidates. It does not establish a governed public Context release.

`REAL_CONTEXT_DATA_MODE=real_v49_validation`

`GOVERNED_PUBLIC_CONTEXT_RELEASE=false`

`REAL_SEMANTIC_EDGE_COUNT=0`

`PRODUCTION_REAL_CANDIDATE_EXPOSURE=false`

## Evidence status

| Gate | Status | Evidence |
| --- | --- | --- |
| Frozen count reconciliation | `PASS` | Ledger, freeze receipt, SQLite, and protected Search cross-check agree on 15,923 / 7,995 / 7,928. |
| Public/held authority | `PASS` | Eligibility is derived only from `18_SURFACE_ROW_LEDGER.tsv`; held and unknown lookups share `RECORD_NOT_AVAILABLE`. |
| Source mapping and state preservation | `PASS` | The selected-record projection uses typed folder rows, keeps every connection `proposed`, and leaves real semantic edges empty. |
| Source-file binding | `PASS` | The loader verifies the registered SHA-256 values for the freeze receipt, eligibility ledger, and immutable SQLite before parsing. |
| Server/client boundary | `PASS` | The loader imports `server-only`; source and build guards found zero forbidden client matches. |
| Full 7,995-object functional validation | `PASS` | 7,995 objects and 31,980 object/template cases; zero failed objects; all 18 real-data invariants pass. |
| Two-pass deterministic checksum | `PASS` | Both complete passes match; aggregate SHA-256 `499624075b99745c1eb95a8d6c2c1438eb7e74ca63222227b8bfb87fdaf38d76`. |
| Layout/export/persistence full-cohort gates | `PASS` | Zero layout collisions, export failures, persistence-key collisions, accessibility mismatches, or record-switch state leaks. |
| PNG browser conversion | `USER_REVIEW_PENDING` | Browser and localhost execution are excluded by request. |

`CONTEXT_CANVAS_REALDATA_VALIDATED=true`

The final isolated verifier evidence set contains 12 files and has SHA-256 `9d4a3d1f5a739269a7dc6abfb0711717d75d30dc81ced4b03aa6d2cb63f03ca0`.

## Reconciled projection workload

The mapping reproduces the prior census envelope without inventing semantic relations:

- controlled-assignment instances: 16,106;
- curated-membership instances: 24,102;
- combined Context associations: 40,208;
- public-object coverage: 7,995 / 7,995 for both groups;
- per-object association distribution: minimum 5, P50 5, P95 5, P99 7, maximum 9.

Medium, theme, and movement folder rows are deliberately represented twice: once as controlled candidates and once as their underlying proposed curated memberships. Region rows are curated memberships only. Raw `objects.medium`, creator, collection/source-adjacent fields, object type, URLs, and internal UUIDs are not promoted to connected Canvas entities.

## Boundaries

This package does not authorize publication, candidate acceptance, database mutation, Search changes, a full-corpus client bundle, or a new public API. It records a validation projection and the evidence still needed to close the round.

The functional and semantic contracts remain in:

- `docs/research/trace-v49-context-canvas-round1/`;
- `docs/research/trace-v49-round1/`.

Those packages are referenced rather than duplicated here.
