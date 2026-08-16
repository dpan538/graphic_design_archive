# A2 — Atomic Snapshot, Lifecycle, Permission, and Manifest Audit

## Scope and result

This was a read-only source audit of `3e666b5265ebe7b41ea0c98531b35761ff0d9485`. It covered release schema, projection builders, lifecycle/guard functions, grants, replay/inventory, and existing database tests. No database, npm, browser, TypeScript compiler, or generator was started; no implementation file was edited.

**Conclusion:** the requested v3 design is feasible as an additive, forward-only database phase, but it must be a new v3 construction and lifecycle path. Reusing either the existing piecemeal builders or the current candidate/validate/seal functions would violate the new sealed-snapshot rules. There is no unresolvable P0 after the explicit authorization; the material requirements below are P1 implementation risks that must be closed by tests before the phase can pass.

## Inspected paths

| Area | Paths inspected |
|---|---|
| Release tables and Phase 2C view | `database/migrations/004_release_audit.sql`, `database/migrations/007_release_copy_integrity.sql`, `database/migrations/008_final_integrity_closure.sql`, `database/migrations/009_read_api_core.sql` |
| Canonical folder/evidence model | `database/migrations/002_raw_core_provenance.sql`, `database/migrations/003_research_rights.sql`, `database/functions/001_deferred_constraints.sql`, `database/functions/004_controlled_writes.sql`, `database/functions/006_normative_closure.sql` |
| Builders, guards, lifecycle and digests | `database/functions/002_mutation_guards.sql`, `database/functions/003_release_and_cas.sql`, `database/functions/005_projection_builders.sql`, `database/functions/007_release_protocol_closure.sql`, `database/functions/008_projection_builders_v2.sql`, `database/functions/009_projection_inventory_builders.sql`, `database/functions/014_release_copy_guards.sql` |
| Roles, replay, inventory and tests | `database/roles/002_database_grants.sql`, `database/roles/003_read_api_core_grants.sql`, `database/scripts/replay.sh`, `database/scripts/run_tests.sh`, `database/schema-manifest.json`, `database/tests/002_release_seal_cas.sql`, `database/tests/003_roles.sql`, `database/fixtures/phase2c_32_base.sql` |
| Read contract | `READ_API_V1.md`, `ARCHITECTURE.md`, `DATA_MODEL_V49.md` |

## Actual commands

```text
pwd; git worktree list --porcelain; git branch --show-current; git status --porcelain=v1
rg --files -g 'AGENTS.md' -g 'READ_API_V1.md' -g 'ARCHITECTURE.md' -g 'DATA_MODEL_V49.md' -g 'ACCEPTANCE_GATES.md' -g '0*.sql' -g '*release*' -g '*manifest*' -g '*seal*' -g '*role*'
sed -n ... database/migrations/007_release_copy_integrity.sql database/migrations/009_read_api_core.sql database/functions/009_projection_inventory_builders.sql database/functions/014_release_copy_guards.sql database/functions/015_final_integrity_closure.sql database/roles/003_read_api_core_grants.sql
rg -n -C 4 'CREATE TABLE release\\.research_release|CREATE TABLE release\\.research_release_object|CREATE FUNCTION release\\.(seal|validate|require_research_draft|guard_research_projection_mutation|copy_research_release_object|create_research)' database/migrations database/functions database/roles database/tests
sed -n ... database/migrations/004_release_audit.sql database/functions/008_projection_builders_v2.sql database/functions/002_mutation_guards.sql database/functions/007_release_protocol_closure.sql database/functions/003_release_and_cas.sql database/tests/002_release_seal_cas.sql database/tests/003_roles.sql
rg -n -C 3 'CREATE TABLE research\\.folder|CREATE TABLE provenance\\.assignment_folder|folder_membership|assignment_folder|canonical_assignment|assignment_decision' database/migrations database/functions database/fixtures
rg -n -C 3 'CREATE TABLE (raw|core|research|provenance)\\..*(surface|citation|credit|place|medium|description)|legacy_surface_ledger|surface_id' database/migrations database/fixtures
sed -n ... database/migrations/002_raw_core_provenance.sql database/migrations/003_research_rights.sql READ_API_V1.md DATA_MODEL_V49.md ARCHITECTURE.md database/roles/002_database_grants.sql database/roles/003_read_api_core_grants.sql database/scripts/replay.sh database/scripts/run_tests.sh database/schema-manifest.json
```

All commands above were read-only. Ellipses mean bounded `sed` line ranges; no whole-disk or staging search was performed.

## Current-state findings

### 1. Current folder projection is metadata-only

`release.research_folder_projection` in `007_release_copy_integrity.sql` contains only release ID, folder ID, token, and label. It has neither type/slug/scope/sort metadata nor a release-owned object membership relation. `release.copy_research_folder_to_draft()` in `009_projection_inventory_builders.sql` only copies that metadata.

The canonical object-level source is correctly shaped in `provenance.assignment_folder_membership` (`folder_id`, `archive_object_id`, `membership_role`, `member_ordinal`). The parent `provenance.canonical_assignment` has an accepted/proposed/rejected/superseded state and evidence-bound review history. A v3 builder can select accepted effective assignments with a matching folder subtype and effective evidence-bound accept decision. It must not derive public membership from a folder token or directly consult this mutable table after build.

### 2. Existing release guards are insufficient for a single-use build

`release.guard_research_projection_mutation()` in `002_mutation_guards.sql` only requires `release_state = draft`. A caller can therefore continue writing old projection tables until the candidate transition. The requested rule is stricter: all v3 projection writes must require `draft` **and** absence of a v3 build receipt.

The forward-only implementation needs a new receipt-aware trigger function and triggers on every new v3 table. Because the v3 builder also needs `release.research_release_object` for the required same-release FK, a receipt-aware guard must additionally protect writes to that existing table for releases carrying a v3 receipt. This is additive: it does not replace historical trigger functions and has no effect on pre-v3 releases without a receipt.

### 3. Existing lifecycle validation reads mutable canonical state

`release.validate_research_projection()` in `007_release_protocol_closure.sql` compares copied rows to live `raw`, `core`, `provenance`, and `research` rows. `release.seal_research_release()` in `003_release_and_cas.sql` calls that validator, and `release.verify_sealed_research_integrity()` recomputes the legacy candidate fingerprint. Therefore the current v1/v2 lifecycle fails the requirement that validation/seal of a built candidate or sealed v3 release read release-owned state only and survive post-build canonical drift.

Use new versioned functions, for example `build_research_launch_snapshot_v3`, `compute_research_candidate_fingerprint_v3`, `validate_research_release_v3`, `build_research_manifest_bytes_v3`, `seal_research_release_v3`, and `verify_sealed_research_integrity_v3`. They must not invoke the old validator, old manifest builder, or old integrity verifier for v3 releases.

### 4. Existing fingerprints and manifests omit launch components

The v2 candidate fingerprint includes `research_folder_projection` but no folder membership, surface presentation, credits, citations, search documents, corpus summary, or honest TRACE availability component. `build_research_manifest_bytes()` is a v1 manifest with object/relation/trace counts only. Neither satisfies the required component manifest/digest contract.

The v3 digest must use explicit ordered release-owned rows, not timestamps, `txid`, audit IDs, or a mutable source read. At minimum it must include component hashes/counts for `releaseObjects`, `surfacePresentation`, `surfaceCredits`, `surfaceCitations`, `folderTypes`, `folders`, `folderMemberships`, `searchDocuments`, `corpusSummary`, and `traceAvailability`. The folder-membership hash order must include folder, role, ordinal, and object so any requested change affects the candidate fingerprint and sealed manifest.

### 5. Permission closure must be additive and explicit

`002_database_grants.sql` gives the publisher positive `EXECUTE` on the piecemeal `add_*_to_draft` and `copy_*_to_draft` functions. The user-authorized v3 path requires a new roles file applied after existing grants to revoke these publisher capabilities and grant only the official v3 build/lifecycle calls. `api_reader` remains a SELECT-only consumer of explicit `api_v1` projections; it must not receive base-table access. Any new read views/grants belong in a new forward-only roles/view file, never in `003_read_api_core_grants.sql`.

### 6. Replay and inventory need one coherent forward update

`database/scripts/replay.sh` already replays `009_read_api_core.sql` and `003_read_api_core_grants.sql`, but `database/schema-manifest.json` stops at migration `008` and its stable file inventory predates `009`. The v3 change must update the replay order and the normalized schema inventory together to include `009`, the new migration(s), v3 functions, guards, roles, and v3 tests. It must publish a new schema hash rather than overwrite Phase 2A/2B receipts.

## Allowed forward-only implementation plan

1. Add `database/migrations/010_release_projection_snapshot_v3.sql` only. Define closed `research.folder_type_registry` and `research.folder_publication_metadata`; release folder type/folder/object-membership snapshot tables; relational surface presentation, credit, citation, search, corpus-summary and TRACE-availability snapshot families; release component-manifest and single-use build receipt tables; same-release composite FKs and required indexes.
2. Add v3 builder/lifecycle functions in new numbered function files. The builder must require `SERIALIZABLE`, take a transaction advisory lock, reject non-empty/non-new drafts, use set-based `INSERT … SELECT`, compute source/copy `EXCEPT` parity before receipt insertion, create candidate fingerprint, then make only the allowed `draft → candidate` transition. Fault injection must be opt-in, test-only, and transaction-aborting.
3. Add a receipt-aware v3 mutation guard in a new function file; attach it additively to new snapshot tables and to legacy release-object/corpus tables where v3 uses them. Then add a new role-grant file that removes publisher access to piecemeal builder functions and grants only the v3 entrypoints. Preserve historical functions and grants files byte-for-byte.
4. Add v3 validation/seal/verify functions that query only the release-owned snapshot/component/receipt/manifest data after build. Canonical drift may be reported in an append-only non-gating sidecar but must not be queried by a v3 gate.
5. Add replay/inventory updates plus dedicated v3 database tests for constraints, atomic failures, concurrent serializable build, privileges, canonical drift, and deterministic component/manifest hashes. Run only the permitted disposable PostgreSQL tests.

## P0/P1/P2 assessment

| Severity | Count | Finding / required disposition |
|---|---:|---|
| P0 | 0 | No immutable-design impossibility remains after the explicit authorization. Do not proceed if an implementation proposes a mutable canonical read after builder receipt. |
| P1 | 4 | Existing lifecycle reads canonical post-build; existing mutation guard is draft-only; old publisher grants enable piecemeal writes; schema inventory omits replayed 009. All require forward-only closure. |
| P2 | 1 | The launch contract allows optional detail fields, but source/citation positive allowlist and explicit missingness codes must be recorded before surface presentation DTO scope is declared complete. |

## Unresolved items / guardrails

- Public source/citation text must come from an explicit safe positive allowlist in v3 rows. Do not derive it from `raw_value`, `field_literal`, provider payload, workflow notes, or internal locators.
- An accepted folder membership must retain the selected assignment and effective decision snapshot hash. If the current source has an accepted assertion path without a review decision, the builder must reject it for this launch snapshot rather than synthesize a decision ID.
- The new v3 lifecycle must be selected explicitly by v3 releases; compatibility with historical releases remains historical and must not be retrofitted.
- Nonempty TRACE relation/claim and visual composition remain documented/deferred, not marked complete by zero rows. Honest zero availability must itself be copied and hashed as a release component.

