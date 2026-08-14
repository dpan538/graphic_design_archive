# D8 — Phase 2B audit-package final review

## Scope and isolation

This is a read-only final-package review performed while the single Candidate
extractor was running. It did not parse or hash Candidate JSON, open SQLite,
start or connect to PostgreSQL, create a database, or modify a Phase 2A
migration, role, function, frozen input, historical receipt, or protected main
worktree. The only write by this task is this record.

Reviewed snapshot:

```text
generate_audit.py SHA-256=040608eada3196e0516e3632911712c2833d814f54557d02aa7b2342176766d5
mapping-v1.json SHA-256=6ca7b8658a12b680c2b9d6253c77be018ed98ecfd93174416eeb766f75465c70
field-occurrence-ledger.schema.json SHA-256=7b4c166ef14570aa6099d576b599acfc8481ee505f13a606560d27710a88905f
AUDIT_RUNTIME_EVIDENCE_AVAILABLE=false
```

Read-only commands were limited to `rg --files`, `find`, `sed`, `nl`, `wc`, and
`shasum` over the Phase 2B implementation and audit paths.

## Required-package coverage

The generator is structured to produce all required receipts `00` through
`17`, the required artifact/mapping TSVs, copied small ledgers, an occurrence
ledger provenance record, agent register, `MANIFEST.json`, and
`CHECKSUMS.sha256`. The two required TSV schemas are complete on their face:

- `02_ARTIFACT_AUTHORITY_LEDGER.tsv` has `path`, `bytes`, `sha256`, authority
  role, and the three population/reconciliation/integrity flags.
- `03_FIELD_MAPPING_MATRIX.tsv` exposes all required mapping-contract fields:
  source/pattern/type/cardinality, target, transform, null/missing/order/
  duplicate/delimiter policies, vocabulary/unknown disposition, exposure,
  provenance, round trip, and raw-snapshot flag.

The checksum self-loop design is sound: `MANIFEST.json` inventories all audit
files except itself and `CHECKSUMS.sha256`; `CHECKSUMS.sha256` then hashes the
manifest and every other audit file while excluding only itself. A final
`shasum -a 256 -c CHECKSUMS.sha256` remains required after generation.

## P0 findings sent to the controller

### D8-P0-01 — Gate status is not fail-closed against report contents

`require_runtime_reports()` (lines 107–121 in the reviewed snapshot) checks
only report names, each top-level `status=PASS`, replay hash equality, and
schema pins. `render_receipts()` then emits all Phase 2B gate booleans and
zero counters as fixed literals. A malformed or partial report marked PASS
could therefore produce `PHASE_STATUS=MIGRATION_REHEARSAL_VERIFIED` without
proving the required failure probes, idempotency/collision, public boundary,
cleanup, or exact runtime metrics.

The generator must validate the required schema and exact values from every
runtime report before emitting the final status, including the full failure
probe set/zero residue, idempotency flags, public fixture fields, process
cleanup/deletion fields, reconciliation authority boundary, and baseline count
vector/metrics.

### D8-P0-02 — Copied ledger files are not individually manifest-pinned

`stage_provenance()` validates every file *listed* in `staging-manifest.json`,
then copies six required small ledgers (lines 69–78) without requiring that
each source name is listed in that manifest or checking its own descriptor at
copy time. A required ledger omitted from a manifest could be copied into the
audit package without a staging integrity pin.

For each copied ledger, require a manifest descriptor and independently verify
its byte size and SHA-256 before copying. Missing descriptors must stop the
gate.

### D8-P0-03 — Full temporary occurrence-ledger deletion is not evidenced

The planned provenance record correctly contains the temporary full ledger's
path-at-generation, row count, byte size, SHA-256, schema, and deterministic
regeneration command (lines 85–99). It does not record a deletion state, and
the generator only embeds an opaque process JSON receipt. Phase 2B explicitly
requires a deletion status for the full temporary ledger.

Require process evidence bound to the same ledger descriptors and state, after
normal cluster stop, that the task-owned staging directory and full occurrence
ledger are absent. Render that state explicitly in the occurrence provenance
receipt; do not claim verification until it is present.

### D8-P0-04 — Agent task register omits the D8 record

`agent_register()` hard-codes D1–D7 and ROOT. This D8 independent review is
required by the controller and has its own detailed record, but would be
absent from `AGENT_TASK_REGISTER.md`. Add D8 with this exact path before audit
generation so the final manifest/checksum covers it and every subagent is
registered.

## Exit state

```text
D8_CANDIDATE_PARSED=false
D8_SQLITE_OPENED=false
D8_POSTGRES_STARTED=false
D8_POSTGRES_CONNECTED=false
D8_IMPLEMENTATION_MODIFIED=false
D8_HISTORICAL_RECEIPT_MODIFIED=false
D8_P0_REMAINING=4
D8_STATUS=BLOCKED_PENDING_AUDIT_GENERATOR_REMEDIATION_AND_RUNTIME_EVIDENCE
```

## 2026-08-12 remediation reread

This focused reread inspected only the patched
`database/data-migrations/v48-to-v49/generate_audit.py` (SHA-256
`b89765a087a38b2d78e4c6d8a88af15f542e21f4ea43b493b01988138543ad74`).
It again did not access staging, Candidate JSON, SQLite, or PostgreSQL.
`ast.parse` completed successfully.

### Original findings

| Finding | Patched static evidence | Result |
| --- | --- | --- |
| D8-P0-01 report-content gate | `require_runtime_reports()` now validates exact replay metrics and hashes, reconciliation/boundary values, the complete failure-probe set and zero-residue outcomes, idempotency/collision evidence, public fixture facts, and cleanup/process evidence before rendering a pass gate. | Cleared, subject to live execution. |
| D8-P0-02 unpinned copied ledgers | `descriptor_for()` and `validate_file_descriptor()` require a manifest descriptor and verify source and copied target bytes/SHA-256 for all six ledgers. | Cleared. |
| D8-P0-03 occurrence ledger deletion proof | Freeze-stage-provenance mode persists pinned provenance before cleanup; final rendering requires a process cleanup descriptor matching the occurrence rows/bytes/SHA and `verifiedAbsent=true`, then renders it in receipt 24. | Cleared, subject to live cleanup evidence. |
| D8-P0-04 D8 task registration | `agent_register()` now includes D8 and its exact record mapping. | Cleared. |

The manifest/checksum self-loop remains correct, and the freeze-stage-provenance
mode appropriately separates staging capture from later task-owned staging
deletion.

### D8-P0-05 — Field mapping/coverage gate values remain hard-coded

The final gate still writes `FIELD_OCCURRENCES_ACCOUNTED=100.0000%` and all
six mapping/delta claims (`UNMAPPED_SOURCE_FIELDS`,
`SILENTLY_DROPPED_FIELDS`, `SILENT_DELIMITER_SPLITS`,
`CROSS_ARRAY_POSITIONAL_ZIPS`, `AUTOMATIC_DEDUPLICATION`, and
`UNEXPLAINED_MAPPING_DELTAS`) as literals. The patched
`validate_frozen_provenance()` checks Candidate SHA, surface count, and full
occurrence ledger row count/SHA, but does not require the corresponding
staging-manifest coverage/delta metrics to be the exact claimed values.

This leaves a fail-open path for the final mapping-accountability assertions:
a provenance manifest with a nonzero mapping delta could still be rendered as
a verified all-zero gate. Require the exact staging manifest values for these
claims before final receipt generation.

```text
D8_REMEDIATION_REREAD_AST_PARSE=true
D8_ORIGINAL_P0_CLEARED_STATICALLY=4
D8_REMAINING_P0=1
D8_STATUS=BLOCKED_PENDING_MAPPING_COVERAGE_GATE_AND_RUNTIME_EVIDENCE
```

## 2026-08-12 final mapping-coverage reread

The latest focused reread inspected only
`database/data-migrations/v48-to-v49/generate_audit.py` (SHA-256
`e943cd3b006dfb9f3d095c1cf21af40a6b8f70602d9fa789d4e4c54e91b46a1e`).
It did not access staging, Candidate JSON, SQLite, or PostgreSQL.
`ast.parse` passed.

`validate_frozen_provenance()` now fail-closes before final rendering unless
the staging manifest proves all of the previously unbound assertions:

- exact `fieldLiteralCount=3559820`;
- zero `unmappedSourceFields`, `silentlyDroppedFields`,
  `silentDelimiterSplits`, `crossArrayPositionalZips`,
  `automaticDeduplication`, and `unexplainedMappingDeltas`;
- a nonempty, nonnegative `mappingRuleUse` whose sum is exactly the full field
  occurrence count; and
- all seven exact Phase 1D visual parity hashes.

This closes D8-P0-05 at static-review level. The audit generator now has no
remaining D8 P0 findings; the final gate still depends on the controller
supplying successful live staging, replay, failure, permission, and cleanup
evidence.

```text
D8_FINAL_AST_PARSE=true
D8_P0_REMAINING=0
D8_STATUS=STATIC_AUDIT_PACKAGE_REVIEW_PASS_PENDING_LIVE_EVIDENCE
```
