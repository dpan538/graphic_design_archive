# ADR 0002: Immutable data versioning

- Status: Accepted for the v49 architecture baseline; implementation pending
- Date: 2026-08-10
- Scope: release identity, manifest, shards, and integrity behavior

## Context

v48 already has useful release evidence: frozen source hashes, a TRACE manifest, per-asset hashes, and isolated review/auxiliary catalogs. However, archive search is generated separately, individual TRACE assets do not carry a release identity, and the existing shard envelope contains only a version, shard number, and objects. A client can therefore fetch mutually inconsistent resources unless a stronger release boundary is imposed.

## Decision

v49 has two independent immutable version boundaries:

1. A **research release** has one globally unique, non-reusable `researchReleaseId`, one canonical research manifest, and one externally recorded `researchManifestSha256`. Archive objects, Search, registered predicates/relation types, evidence-bearing claims, semantic relations, corpus/missingness, TRACE projections, and machine-readable research projections are members of that release.
2. A **visual registry** has one globally unique, non-reusable `visualRegistryVersion`, one canonical registry manifest, and one externally recorded public `visualRegistrySha256` (the same digest stored internally as `registry_sha256`). External visual references/object bridges, provider objects, typed locators, rights observations/assessments, provider-policy versions/evaluations, delivery decisions, endpoint-health observations, attribution/required statements, review due and takedown state are members of that registry.

The boundaries declare compatibility but do not share identity or `current`. A rights, endpoint-health, or takedown change creates a new visual registry without mutating or resealing the research release. A research claim/corpus change creates a new research release without silently carrying forward a visual authorization.

### Independent identity and lifecycle

The only forward states are `draft → candidate → validated → sealed`.

- `draft` projection rows/assets may be rebuilt under the draft attempt.
- `candidate` closes the source snapshot, cohort, query/registry digests, copied projection rows, and asset paths.
- `validated` means every required pre-seal receipt passes against one immutable candidate fingerprint.
- `sealed` commits canonical manifest bytes/hash with the state transition. Database privileges and a defense-in-depth trigger reject mutation or deletion.
- Supersession is pointer/history metadata on an already sealed release, not a mutable release state.
- A failed attempt remains with its failed receipts and is never resolved by `current`; remediation uses a new attempt/release ID.

The identity string is semantic but never content authority by itself. Consumers always bind `(researchReleaseId,researchManifestSha256)` and, when visual composition is selected, atomically bind `(visualRegistryVersion,visualRegistrySha256)`. The visual pair may be absent for a normal research-only response. Compatibility is an explicit manifest record, never inferred from simultaneous `current` resolution; an explicit mismatch fails without fallback.

### Canonical research manifest

Manifest JSON uses one specified canonicalization algorithm (RFC 8785 JSON Canonicalization Scheme) and UTF-8. It contains at least:

```json
{
  "schemaVersion": "archive-research-release/v1",
  "apiContractVersion": "v1",
  "researchReleaseId": "v49-research-YYYYMMDD.N",
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
    "predicateTypesSha256": "64 lowercase hex"
  },
  "corpus": {
    "corpusVersion": "opaque immutable identifier",
    "selectionPolicySha256": "64 lowercase hex",
    "missingnessReceiptSha256": "64 lowercase hex"
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

The manifest hash is stored in a small research-release descriptor outside the manifest and in the promotion receipt. The manifest cannot self-authenticate by embedding its own final hash.

### Canonical visual-registry manifest

The visual registry uses RFC 8785 and the same deterministic inventory rules, but a distinct schema and identity:

```json
{
  "schemaVersion": "archive-visual-registry/v1",
  "visualRegistryVersion": "v49-visual-YYYYMMDD.N",
  "status": "sealed",
  "compatibleResearchRelease": {
    "researchReleaseId": "v49-research-YYYYMMDD.N",
    "researchManifestSha256": "64 lowercase hex"
  },
  "providerRegistrySha256": "64 lowercase hex",
  "rightsPolicySha256": "64 lowercase hex",
  "assets": [],
  "gateReceipt": {
    "path": "receipts/visual-acceptance.json",
    "sha256": "64 lowercase hex"
  }
}
```

It records provenance-bound visual references, object-reference bridges and typed provider object IDs, and it separates canonical-record, viewer, embed, IIIF, thumbnail, image-service and direct-image locator roles. Rights observations/assessments, provider-policy versions/evaluations, delivery decisions, endpoint-health observations and takedown state are independent records. Unknown, missing, conflicting or stale rights/policy serializes no pixel URL and defaults to `LINK_ONLY` or `CITATION_ONLY`. Only `REMOTE_IMAGE` may expose the v1 allowlisted remote-pixel locator. Accessibility, redirect success, API availability or IIIF presence never implies authorization. An active takedown takes precedence and may force only `BLOCKED` or `CITATION_ONLY`.

### Seal protocols

The following protocol is executed independently for the research release and visual registry. A transaction cannot use one boundary's state transition to mutate the other.

1. Build copied release projections in a repeatable database snapshot while `draft`.
2. Transition to `candidate` with compare-and-swap on the draft state/version and close the candidate fingerprint.
3. Produce immutable pre-seal receipts. Research receipts cover all five v48 artifacts, migration/query digests, canonical/graph/derived counts, population boundaries, corpus/missingness, FK/orphan checks, predicate/relation registries, claim/projection eligibility, unknown-relation isolation, grants, projection fingerprints, and deterministic asset inventory. Visual receipts cover reference/bridge/provider/locator identity, rights observations/assessments, policy versions/evaluations, delivery/health/takedown separation, attribution, review due, held-pixel non-disclosure, compatibility, grants, and deterministic asset inventory.
4. Transition to `validated` only when every required receipt is passing and hash-bound to the same candidate fingerprint.
5. Generate RFC 8785 manifest bytes from the validated inventory and receipt hashes, then compute SHA-256 over those exact bytes.
6. In one serializable transaction, recheck the fingerprint, store manifest bytes/hash, and transition `validated → sealed`. Any mismatch aborts.
7. Write a detached post-seal sidecar containing release ID, manifest SHA-256, seal transaction identity, timestamp, and optional signature/attestation. It is outside the self-hashed manifest and cannot change the asset inventory.
8. Update that boundary's `current` only by CAS on the expected pointer generation, exact version ID, and manifest SHA. The target must be sealed and sidecar-verified; rollback uses the same CAS mechanism. Research-current and visual-current histories are separate.

Candidate and sealed projections are copied/versioned rows. They are never views that join mutable canonical tables, so later canonical edits cannot make a sealed release drift.

### Shard envelope

Every shard uses a self-describing envelope:

```json
{
  "schemaVersion": "archive-research-shard/v1",
  "researchReleaseId": "v49-research-YYYYMMDD.N",
  "researchManifestSha256": "64 lowercase hex",
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

Records are sorted by stable ID with a documented tie-breaker. Partitioning is deterministic for a fixed export algorithm and query pack. Research shards may reference only assets declared in the same research manifest. Visual-registry shards use their own envelope and may reference only assets declared in that registry. Cross-boundary references carry both exact identity/hash pairs and must satisfy declared compatibility. The owning manifest lists every shard; unlisted files are not part of either boundary.

### Validation and fail-closed behavior

Before a repository exposes research data it validates the research descriptor, manifest schema/hash, exact identity pair, referenced asset hashes and shard envelopes. If visual composition is selected it additionally validates the exact visual descriptor/manifest, declared compatibility and registry assets. Registry absence returns research-only data with no locator; an explicit invalid selector does not. Validation may be lazy per asset, but a failed selected boundary permanently poisons that repository instance.

Missing files, schema mismatches, version/compatibility mismatches, hash mismatches, duplicate stable IDs, gaps/overlaps outside the declared partition policy, unregistered relation types, or rights-held pixel leakage return `INTEGRITY_FAILURE`. They never fall back to another release/registry, a mock, an `OTHER` relation, a permissive delivery mode, or stale in-memory data.

### Caching

- Exact sealed research assets and non-public immutable visual evidence assets use strong ETags and immutable caching.
- Each `current` descriptor is mutable routing metadata with append-only history and CAS updates. It uses short caching or revalidation. A repository resolves each once, verifies compatibility, then switches to exact pair-pinned URLs.
- Research caches are keyed by research release ID/hash; visual caches are keyed by visual registry version/hash; combined DTO caches include all four values. Path alone is never a cache key. Locator-bearing public composition revalidates the active restrictive takedown overlay before cache lookup and includes `takedownOverlaySha256` in the cache/ETag/receipt identity when present.

## Consequences

Archive, Search, claims/relations, corpus, and TRACE cannot drift within a research release. Visual authorization and endpoint state cannot drift within a visual registry. The two boundaries may advance independently only through explicit compatible pairs. Reproducibility and takedown responsiveness improve, but every exporter and repository implementation must implement the same integrity rules. Small manifest changes create a new version in the owning boundary; that is intentional.

## Follow-up boundary

No v49 manifest or shard is generated in this architecture checkpoint. v48 manifest and shard files remain read-only. Research/visual format conformance, deterministic re-export, corruption and held-pixel tests, compatibility, and both seal/CAS implementations are future acceptance gates.
