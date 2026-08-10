# ADR 0002: Immutable data versioning

- Status: Accepted for the v49 architecture baseline; implementation pending
- Date: 2026-08-10
- Scope: release identity, manifest, shards, and integrity behavior

## Context

v48 already has useful release evidence: frozen source hashes, a TRACE manifest, per-asset hashes, and isolated review/auxiliary catalogs. However, archive search is generated separately, individual TRACE assets do not carry a release identity, and the existing shard envelope contains only a version, shard number, and objects. A client can therefore fetch mutually inconsistent resources unless a stronger release boundary is imposed.

## Decision

Every v49 read dataset is an immutable release. A release has one globally unique, non-reusable `releaseId`, one canonical manifest, and one externally recorded manifest SHA-256. Archive, Search, TRACE, rights-safe representations, relation registry, and read projections are all members of that same release.

### Release identity and lifecycle

The only forward states are `draft → candidate → validated → sealed`.

- `draft` projection rows/assets may be rebuilt under the draft attempt.
- `candidate` closes the source snapshot, cohort, query/registry digests, copied projection rows, and asset paths.
- `validated` means every required pre-seal receipt passes against one immutable candidate fingerprint.
- `sealed` commits canonical manifest bytes/hash with the state transition. Database privileges and a defense-in-depth trigger reject mutation or deletion.
- Supersession is pointer/history metadata on an already sealed release, not a mutable release state.
- A failed attempt remains with its failed receipts and is never resolved by `current`; remediation uses a new attempt/release ID.

The release ID is semantic but never content authority by itself. Consumers must bind the pair `(releaseId, manifestSha256)`.

### Canonical manifest

Manifest JSON uses one specified canonicalization algorithm (RFC 8785 JSON Canonicalization Scheme) and UTF-8. It contains at least:

```json
{
  "schemaVersion": "archive-release/v1",
  "apiContractVersion": "v1",
  "releaseId": "v49-YYYYMMDD.N",
  "createdAt": "RFC3339 timestamp",
  "status": "sealed",
  "sourceLineage": {
    "v48CandidateJsonSha256": "64 lowercase hex",
    "v48SqliteSha256": "64 lowercase hex",
    "v48TransferManifestSha256": "64 lowercase hex",
    "v48TransferManifestCsvSha256": "64 lowercase hex",
    "v48TraceManifestSha256": "64 lowercase hex",
    "sourceGitCommit": "full commit"
  },
  "database": {
    "migrationSetSha256": "64 lowercase hex",
    "projectionQueryPackSha256": "64 lowercase hex",
    "snapshotIdentity": "opaque immutable identifier"
  },
  "registries": {
    "relationTypesSha256": "64 lowercase hex",
    "rightsPolicySha256": "64 lowercase hex"
  },
  "counts": {},
  "assets": [],
  "gateReceipt": {
    "path": "receipts/acceptance.json",
    "sha256": "64 lowercase hex"
  }
}
```

Each `assets[]` entry contains:

- release-relative path, resource kind, media type, content encoding, schema ID;
- byte length, record count, SHA-256;
- deterministic sort key and partition/range description when sharded;
- uncompressed content hash when compression is present;
- dependencies by asset path plus expected hash.

The manifest must not contain `current`, mutable URLs, absolute local paths, credentials, or timestamps that make otherwise identical exports non-deterministic.

The manifest hash is stored in a small release descriptor outside the manifest and in the promotion receipt. The manifest cannot self-authenticate by embedding its own final hash.

### Seal protocol

1. Build copied release projections in a repeatable database snapshot while `draft`.
2. Transition to `candidate` with compare-and-swap on the draft state/version and close the candidate fingerprint.
3. Produce immutable pre-seal receipts for all five v48 artifacts, migration/query digests, exact counts and population boundaries, FK/orphan checks, relation registry, rights policy, unknown-relation isolation, grants, projection fingerprints, and deterministic asset inventory.
4. Transition to `validated` only when every required receipt is passing and hash-bound to the same candidate fingerprint.
5. Generate RFC 8785 manifest bytes from the validated inventory and receipt hashes, then compute SHA-256 over those exact bytes.
6. In one serializable transaction, recheck the fingerprint, store manifest bytes/hash, and transition `validated → sealed`. Any mismatch aborts.
7. Write a detached post-seal sidecar containing release ID, manifest SHA-256, seal transaction identity, timestamp, and optional signature/attestation. It is outside the self-hashed manifest and cannot change the asset inventory.
8. Update `current` only by CAS on the expected pointer generation, release ID, and manifest SHA. The target must be sealed; rollback uses the same CAS mechanism.

Candidate and sealed projections are copied/versioned rows. They are never views that join mutable canonical tables, so later canonical edits cannot make a sealed release drift.

### Shard envelope

Every shard uses a self-describing envelope:

```json
{
  "schemaVersion": "archive-shard/v1",
  "releaseId": "v49-YYYYMMDD.N",
  "resource": "trace-neighborhood",
  "shardId": "000",
  "partition": {
    "strategy": "stable-id-range",
    "startInclusive": "...",
    "endExclusive": "..."
  },
  "recordCount": 30,
  "recordsSha256": "64 lowercase hex",
  "records": {}
}
```

Records are sorted by stable ID with a documented tie-breaker. Partitioning is deterministic for a fixed export algorithm and query pack. Shards may reference only assets declared in the same manifest and release. The manifest lists every shard; unlisted files are not part of the release.

### Validation and fail-closed behavior

Before a repository exposes data it validates the descriptor, manifest schema, manifest hash, exact release ID, registry hashes, referenced asset hashes, and shard envelope. Validation may be lazy per asset, but a failed validation permanently poisons that repository instance.

Missing files, schema mismatches, release mismatches, hash mismatches, duplicate stable IDs, gaps/overlaps outside the declared partition policy, or unregistered relation types return `INTEGRITY_FAILURE`. They never fall back to another release, a mock, an `OTHER` relation, or stale in-memory data.

### Caching

- Exact sealed resources use strong ETags and `Cache-Control: public, max-age=31536000, immutable`.
- The `current` descriptor is mutable routing metadata with append-only history and CAS updates. It uses short caching or revalidation. A repository resolves it once, then switches to exact release URLs.
- Caches and request deduplication are keyed by release ID and manifest SHA, never path alone.

## Consequences

Archive, Search, and TRACE cannot drift independently. Reproducibility improves, but every exporter and repository implementation must implement the same integrity rules. Small manifest changes create a new release; that is intentional.

## Follow-up boundary

No v49 manifest or shard is generated in this architecture checkpoint. v48 manifest and shard files remain read-only. Format conformance, deterministic re-export, corruption tests, and seal enforcement are future acceptance gates.
