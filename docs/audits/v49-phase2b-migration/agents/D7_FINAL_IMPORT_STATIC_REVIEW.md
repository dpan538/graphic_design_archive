# D7 — Final import-path static review

## Scope and boundary

This is an independent read-only review of the current Phase 2B implementation
directory and its Phase 2A physical-model interfaces.  It did not parse the
Candidate JSON, open SQLite, start/connect to PostgreSQL, run a migration,
start a network client, modify any Phase 2A migration/role/function, or touch
the protected main worktree.

The only file written by this agent is this record.  The active Candidate
extractor was not read, stopped, or modified.

## Static snapshot

Repository HEAD at review start:

```text
86ba95cae9ecf12e58fcabb8170c9020e151b386
```

Reviewed implementation hashes at the initial snapshot:

```text
README.md                         1fe6461a980fa479c55df5dab581fc624d99a127a6d7b291b597dce39ff4ffd2
expected-baseline.json            5c1b4a6509657b5e4f9a40d9d010f789a82caa7df2efa7a8bbe33d440e74cbfe
mapping-v1.json                   6ca7b8658a12b680c2b9d6253c77be018ed98ecfd93174416eeb766f75465c70
extract.py                        7bffa7d110dfcbabbcfb06bc971a72c27ede014e03571297e502950b642d4783
prepare-staging.sql               a1302069ff258b7775614427c9fb0f2028527cc83978c51866c93b4d6bde6a73
prepare-runtime.sql               58445c7e39949823ea3136dd98840b932dff269f8e6ea053a02f9be08a849620
load.sql                          dc62699880d1db43eccbbee44282d95d2e53512446728f6f253b4d3196c8f4d0
import.py                         5a2cb29cc910811bc5a15ac166d3e4accc9132a44efdee99394bb98f16906c35
verify.py                         b483c1c1db3dfbac287155ac02a9adf1515ff96abc6c62979d05058ec176644a
reconcile.py                      8a7f78ab6f7c7b96c73bec1d78c4cb6047cbec8ccda150ac06b18db7381c893c
run-rehearsal.sh                  58e3fdf39dab4ed1a1b0857e76946b5aecb447a11c72c8ed3d668845e290bb41
tests/run_failure_injections.py   502b9cd029bb02279204095a8ad848a141396e3fc3d5e55e931ace525bc6b2b8
tests/run_public_boundary_fixture.py
                                  781cd0a429e25a0a967b56badca81c26ff4c1231619368598c7a44fb6d87ac35
```

Static syntax checks passed:

```text
PYTHON_AST_PARSE=PASS
MAPPING_JSON_PARSE=PASS
EXPECTED_BASELINE_JSON_PARSE=PASS
RUNNER_SHELL_SYNTAX=PASS
```

## Confirmed controls

- The extractor is Candidate-only, strict UTF-8/duplicate-key/non-finite
  rejecting, UUIDv5-based, and preserves the full Candidate raw source asset
  plus per-surface raw records.
- Mapping has declared fallback raw-snapshot handling and the importer checks
  occurrence rule IDs, flags, field-literal identities, pointers, digest
  pairing, visible presence classes, and required staging-file hashes before
  opening PostgreSQL.
- The loader has no `ON CONFLICT`, no delimiter split, no random identity,
  no non-Candidate reader, and no insert into `research.semantic_relation`,
  `research.legacy_projection_fact`, or `release.trace_projection_edge`.
- Folder pairs are proposed typed assignments, not accepted assertions.
  TRACE roots remain root crosswalks; legacy graph arrays are retained only as
  raw/held material.
- Rights/policy/delivery are independently loaded as unknown/unknown/
  `citation_only`; no permissive rights assessment, `remote_image`, public
  pixel locator, current pointer, or release seal is staged.
- The one-transaction `psql` path has real failure checkpoints after staging,
  during a nonzero object subset, after corpus, after visual rows, and after
  parity.  The explicit object-to-surface-ledger FK is deferred by the Phase
  2A schema, so the reciprocal load ordering is valid.
- The verifier uses real `api_reader` connections for public-view access and
  raw-table/write denial probes.  A rollback-only Phase 2A fixture is correctly
  separated from the no-release population replay.

## Findings sent to the executor

### P0 — current extractor hash was recorded but not enforced

At this snapshot, `import.py` recomputed the staging manifest's self-binding
but did not compare `manifest.extractor.sha256` with the current
`extract.py` file hash.  An internally self-consistent bundle produced by a
different extractor could therefore reach PostgreSQL.  The importer should
reject this before its database-owner/schema checks, just as it already does
for the current mapping hash.

### P0 — same-batch/different-mapping verification was not an actual harness probe

`--test-batch-mapping-sha` queried an existing batch and deliberately raised
on an unequal supplied hash, but it bypassed `existing_batch()` and no
versioned test invoked it.  This is not yet an evidence-backed exercise of the
required same batch ID/different binding failure.  Add a post-commit
idempotency/collision harness that proves identical replay is a no-op, a
different binding is rejected, and row/count/content hashes remain unchanged.

### P0 — zero TRACE import needed direct populated-database proof

The loader is correctly free of forbidden TRACE writes, but `verify.py` at
this snapshot tested only accepted semantic relations and projection edges.
It did not query total semantic relations or `research.legacy_projection_fact`.
The final verifier/receipt must query these zero-only tables directly so
`TRACE_IMPORTED_CANONICAL_ROWS=0` and `LEGACY_GRAPH_EDGES_IMPORTED=0` are not
only code inspection or reconciliation declarations.

### P1 — staging-manifest parser should reject duplicate JSON keys

`require_stage()` used ordinary `json.loads` for `staging-manifest.json`.
Use the existing `strict_object` hook there as a defense-in-depth
fail-closed integrity check.

## Required final reread conditions

This static review must be reread after the above P0s are addressed and before
the final gate claims success.  The execution receipt still needs fresh
database evidence for replay equality, data counts, atomic rollback,
idempotency/collision, public boundary, and task-owned resource cleanup.

## Process exit

```text
D7_POSTGRES_STARTED=false
D7_POSTGRES_CONNECTED=false
D7_CANDIDATE_PARSED=false
D7_SQLITE_OPENED=false
D7_NETWORK_USED=false
D7_AGENT_OWNED_LONG_PROCESSES_REMAINING=0
D7_STATUS=STATIC_REVIEW_PENDING_P0_REMEDIATION
```

## Post-remediation static reread

The coordinator remediated the findings above without changing the active
`extract.py`, mapping registry, expected baseline, Phase 2A schema, roles, or
frozen inputs.  This reread again used repository reads and Python AST parsing
only; it did not access Candidate JSON, SQLite, or PostgreSQL.

Updated reviewed hashes:

```text
import.py                                      994dd0f9ee961362d3acdded0609affc666b7910aa1c2d74e4d9576dcf99a0f9
verify.py                                      3a536599dc5aa3c97ed24bcd1d01ba8283622b26b67e501b8f4e76af8b911603
tests/run_idempotency_and_batch_collision.py  58d1dab0d41d31f1048f88ff8e2583e1b323d36fee524ad0606200eba5d54ed4
```

```text
POST_PATCH_PYTHON_AST_PARSE=PASS
FORBIDDEN_TRACE_INSERTS=0
ON_CONFLICT_DO_NOTHING=0
```

### Resolution results

| Finding | Static evidence after remediation | Result |
| --- | --- | --- |
| Current extractor hash enforcement | `require_stage()` now strict-parses the manifest, validates extractor SHA syntax, and requires it to equal `sha256_file(MIGRATION_DIR / "extract.py")` before any database-owner/schema operation. | Cleared |
| Actual same-batch/different-mapping probe | `run_idempotency_and_batch_collision.py` first verifies the committed database, runs the production importer for its real no-op path, then invokes `existing_batch()` through an in-memory same-batch conflicting mapping/bundle binding. It requires `BATCH_ID_REUSE_HASH_MISMATCH` and identical before/after count, stable-key, and semantic-content hashes. | Cleared statically; execution remains required |
| Database-backed zero TRACE import proof | `verify.py` now requires zero total `research.semantic_relation`, `research.legacy_projection_fact`, working TRACE tree/branch/placement rows, and release projection node/edge/tree/branch/placement rows, while requiring exactly 15,923 root trace nodes. | Cleared statically; execution remains required |
| Duplicate staging-manifest keys | `require_stage()` now uses the existing duplicate-key-rejecting `strict_object` hook and fails before database access. | Cleared |

No further implementation P0 was found in this reread.  The actual execution
gate still needs to establish the generated bundle's current extractor hash,
fresh replay parity, real fault outcomes, live role checks, and cleanup.

```text
D7_FINAL_STATIC_P0_REMAINING=0
D7_STATUS=STATIC_REVIEW_PASS_PENDING_EXECUTION
D7_AGENT_OWNED_LONG_PROCESSES_REMAINING=0
```
