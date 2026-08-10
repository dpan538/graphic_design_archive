# ADR 0002: Immutable data versioning

- Status: Accepted for the v49 architecture baseline; implementation pending
- Date: 2026-08-10
- Scope: release identity, manifest, shards, and integrity behavior

## Context

v48 already has useful release evidence: frozen source hashes, a TRACE manifest, per-asset hashes, and isolated review/auxiliary catalogs. However, archive search is generated separately, individual TRACE assets do not carry a release identity, and the existing shard envelope contains only a version, shard number, and objects. A client can therefore fetch mutually inconsistent resources unless a stronger release boundary is imposed.

## Decision

Every v49 read dataset is an immutable release. A release has one globally unique, non-reusable `releaseId`, one canonical manifest, and one externally recorded manifest SHA-256. Archive, Search, TRACE, rights-safe representations, relation registry, and read projections are all members of that same release.

### Release identity and lifecycle

Allowed states are `draft`, `candidate`, `sealed`, and `superseded`.

- `draft` and `candidate` may be regenerated under a new candidate attempt ID.
- `sealed` bytes are immutable. Database privileges and a seal trigger reject mutation or deletion.
- `superseded` means a newer release is recommended; it does not permit modification or removal.
- A failed candidate is retained as workflow evidence but is never resolved by `current`.

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
- The `current` descriptor is a resolver with short caching or revalidation. A repository resolves it once, then switches to exact release URLs.
- Caches and request deduplication are keyed by release ID and manifest SHA, never path alone.

## Consequences

Archive, Search, and TRACE cannot drift independently. Reproducibility improves, but every exporter and repository implementation must implement the same integrity rules. Small manifest changes create a new release; that is intentional.

## Follow-up boundary

No v49 manifest or shard is generated in this architecture checkpoint. v48 manifest and shard files remain read-only. Format conformance, deterministic re-export, corruption tests, and seal enforcement are future acceptance gates.
