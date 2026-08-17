# A3 — v5 digest design and snapshot-semantics audit

## Scope, source, and methods

Read-only audit of source 56d41d7bd55d90a7034bbcd017b0305b680e20b4. This report is the only file written by A3. No PostgreSQL server was started and no implementation or historical audit was changed.

Inspected paths:

- database/functions/017_release_projection_snapshot_closure.sql
- database/functions/016_release_projection_snapshot_v3.sql
- database/migrations/010_release_projection_snapshot.sql
- database/migrations/011_release_projection_snapshot_closure.sql
- database/migrations/002_raw_core_provenance.sql
- database/tests/005_release_projection_snapshot.sql
- database/tests/006_release_projection_negative_matrix.sql
- docs/audits/v49-release-projection-snapshot-closure/00_EXECUTIVE_PERFORMANCE_CHECKPOINT.md
- docs/audits/v49-release-projection-snapshot-closure/04_PERFORMANCE_STOP_RECEIPT.txt

Commands actually run:

    git -C /private/tmp/graphic_design_archive_v49_release_snapshot_closure status --short
    git -C /private/tmp/graphic_design_archive_v49_release_snapshot_closure rev-parse HEAD
    rg -n -C 3 component-hash/candidate-fingerprint/manifest/digest symbols ...
    sed -n 1,230p database/functions/017_release_projection_snapshot_closure.sql
    sed -n 230,455p database/functions/017_release_projection_snapshot_closure.sql
    sed -n 458,630p database/migrations/002_raw_core_provenance.sql
    rg canonical_jsonb_sha256 database/functions/*.sql

## Findings

### P0 — assignment current-leaf predicate has the wrong direction

release.research_launch_publishable_folder_assignments_v4 in 017 lines 7–49 uses a.supersedes_assignment_id IS NULL. With the established semantic new assignment supersedes old assignment, this selects a chain root, not the current leaf. The decision predicate correctly uses inverse NOT EXISTS newer, so assignment and decision semantics diverge. An old accepted assignment can be published while the newer accepted replacement is excluded.

V5 must materialize the inverse predicate once per build, then reuse it for folder type, folder, member, parity, disposition accounting, and source hashes:

    AND NOT EXISTS (
      SELECT 1 FROM provenance.canonical_assignment newer
      WHERE newer.supersedes_assignment_id = a.canonical_assignment_id
    )

Add a deterministic two-level chain fixture: both assignments accepted, newer supersedes older, and only newer with its current supported accept decision is published. Retain negatives for unreviewed/proposed/rejected/wrong-kind, held corpus, superseded decision, and missing supports evidence.

The inspected schema does not declare either supersession column unique; do not invent that constraint. Add and EXPLAIN reverse partial indexes:

    CREATE INDEX ... ON provenance.canonical_assignment (supersedes_assignment_id)
      WHERE supersedes_assignment_id IS NOT NULL;
    CREATE INDEX ... ON provenance.assignment_review_decision (supersedes_decision_id)
      WHERE supersedes_decision_id IS NOT NULL;

### P1 — v4 digest is unbounded, not Merkle

release.research_launch_component_hash_v4 (017 lines 51–71) constructs one ordered string_agg value in v_rows per component before hashing. It remains one O(component-byte-size) aggregate state and is consistent with the 8,000 builder failure. Do not substitute another complete aggregate, raise work_mem, or extend timeout. Use forward-only migration 012 and function/protocol 018 with release-snapshot-v5; leave v3/v4 history intact. Existing v3 release projection tables may remain physical storage, but no v5 receipt, fingerprint, validation, or seal may call v4 hashes.

### P1 — membership hash functions repeat canonical work

The membership insert at 017 lines 315–323 invokes assignment and decision hash functions per member, each with correlated canonical reads. Materialize the publishable set once, derive distinct assignment/decision/evidence digests using set-based join/group relations, join these values to memberships, and reuse the same expected set for parity. Do not evaluate the predicate for every projection and both EXCEPT sides.

### P1 — candidate and manifest must bind chunk topology

V4 projection_content_sha256 equals its component-manifest hash and validation recomputes full components. V5 must bind protocol version, component code, total row count, chunk size, ordered chunk ordinal, chunk row count, and the whole ordered chunk-digest sequence. Otherwise a chunk can move, duplicate, disappear, or be reinterpreted ambiguously.

## Exact v5 bounded-digest design

Add release-owned append-only v5 metadata with same-release FKs:

    release.research_launch_protocol_v5
      (research_release_id PK, protocol_version, chunk_size, created_at)
    release.research_launch_component_manifest_v5
      (research_release_id, component_code PK, row_count, chunk_size, chunk_count, content_sha256)
    release.research_launch_component_chunk_v5
      (research_release_id, component_code, chunk_ordinal PK,
       first_semantic_key_sha256, last_semantic_key_sha256, row_count, chunk_sha256)
    release.research_launch_build_receipt_v5 / validation_v5 / manifest_v5

For all ten components define an ordered, release-owned row relation. Order objects/presentation/search by archive_object_id (retain sort_key,archive_object_id in search payload); credits/citations by archive_object_id,ordinal; types by sort_ordinal,folder_type_code; folders by folder_type_code,sort_ordinal,folder_id; memberships by folder_id,membership_role,member_ordinal,archive_object_id; corpus by corpus_version_id; and TRACE by release ID.

Row digest is SHA-256 of canonical jsonb text whose envelope contains format gda-v49-research-component-row-v5, component code, semantic key array, and public release-owned row fields only.

Assign row_number() - 1 in this order and use chunk_ordinal=floor(row_number/1024). A chunk aggregates at most 1,024 fixed-size row-digest hex values. Its canonical payload binds format/component, ordinal, row count, and an ordered JSON array of row digests. First/last key digests are diagnostic only. The component digest binds protocol/component, total row count, chunk_size=1024, chunk count, and all ordered (chunk_ordinal,row_count,chunk_sha256) tuples. Thus no membership-scale string_agg or jsonb_agg remains.

The v5 manifest binds every component code/count/chunk parameters/hash. The v5 candidate fingerprint binds source identity, release ID, protocol version, v5 manifest, and ordered component entries. The sealed manifest embeds v5 manifest and candidate fingerprint. Persist builder version and chunk size. Validation/seal recompute only from release-owned projections and v5 metadata—never canonical mutable data, a caller hash, or v4 hashes.

## Required proof set

1. Component-by-component v4/v5 logical row-set equality at 32 objects; hash bytes are expected to differ.
2. Fresh A/B equality of v5 component manifest, candidate fingerprint, and sealed manifest digest.
3. Reorder/delete/duplicate/mutate row and chunk tuple cases change relevant v5 digests or are rejected by immutable guards.
4. Zero row plus newline, Unicode, and JSON-sensitive public values are deterministic.
5. Boundary cases 0, 1, 1023, 1024, 1025 prove no aggregate exceeds 1,024 rows.
6. EXPLAIN expected-set materialization, member projection, row/chunk hashing, and parity; membership-cardinality correlated subplans are a stop.

## P2

- release.canonical_jsonb_sha256 hashes PostgreSQL jsonb text while format labels say JCS. Preserve the established convention, but describe v5 precisely rather than claim portable external RFC JCS.
- Small source-disposition/manifest aggregates are not the recorded 8,000 bottleneck; every membership-level v5 aggregate still needs the 1,024 bound.

## Conclusion

P0=1, P1=3, P2=2. Correct the current-leaf predicate and implement the set-based v5 chunk protocol before another 8,000 performance attempt.
