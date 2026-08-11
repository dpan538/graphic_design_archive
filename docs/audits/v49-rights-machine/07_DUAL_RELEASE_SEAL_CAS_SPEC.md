# 07 — Independent research/visual release seal and CAS specification

- Package: Phase 1D B2
- Status: **NORMATIVE PRE-DDL SPEC; IMPLEMENTATION PENDING**
- Applies independently to: research release and visual registry

## 1. Two immutable boundaries, one normalized working database

PostgreSQL is the normalized working database. It owns reviewed mutable-by-append canonical state before release closure. It is not the public mutable head and is not itself a scholarly citation.

The release layer creates two independent copied boundaries:

```text
research release
  = exact research identity/hash
  + copied object/claim/relation/corpus/Search/TRACE projections
  + research manifest + post-seal sidecar + research current history

visual registry
  = exact visual identity/hash
  + copied provider/reference/rights/policy/delivery/health/takedown projections
  + one exact compatible research pair
  + visual manifest + post-seal sidecar + visual current history
```

Neither boundary owns or updates the other. A visual-policy, health, attribution, or takedown change creates a new visual version without resealing research. A research change creates a new research release and cannot inherit a previous visual decision merely because object IDs overlap.

Third-party pixel, thumbnail, Image API/service/info, embed, and governed-local-asset locators are absent from research-release projections and manifest bytes.

## 2. State machine

Both boundaries use only:

```text
draft → candidate → validated → sealed
```

| State | Permitted work | Forbidden behavior |
|---|---|---|
| `draft` | Build/rebuild copied projection rows under one attempt identity. | Public/current resolution; cross-boundary mutation. |
| `candidate` | Run boundary-specific receipts against the closed candidate fingerprint. | Changing cohort, copied rows, compatibility, query/policy inputs or asset inventory. |
| `validated` | Generate canonical manifest bytes from the fixed inventory and bound passing receipts. | New receipt scope, projection mutation, or public resolution. |
| `sealed` | Read immutable rows/assets; produce/verify detached sidecar; become pointer-eligible. | `UPDATE`, `DELETE`, live canonical joins, manifest overwrite, state rollback. |

Failures remain recorded on the attempt. Remediation creates a new release/version identity. `superseded` belongs to current-pointer/history metadata, not the release state machine.

## 3. Candidate fingerprints

### 3.1 Research fingerprint

The research candidate fingerprint closes at least:

- exact source/database snapshot and migration/query-pack identities;
- operational object cohort and surface/crosswalk projection;
- claim, semantic-relation and predicate/relation registry snapshots;
- corpus policy, membership, missingness and concentration receipts;
- Search and TRACE projection rows/assets;
- canonical/graph/derived count snapshots and authority/research receipts;
- research asset inventory and schema versions;
- role/grant receipt relevant to the boundary.

It excludes current visual permission, external pixel locators, provider health, and visual-current state.

### 3.2 Visual fingerprint

The visual candidate fingerprint closes at least:

- exact compatible `(researchReleaseId,researchManifestSha256)`;
- object ↔ visual-reference bridge snapshot for that research cohort;
- provider and provider-object identities;
- typed visual references and locator-role inventory;
- rights observations/assessments and evidence digests;
- provider-policy versions/evaluations;
- delivery decisions, reason codes and public locator allowlists;
- endpoint-health state and observation freshness identity;
- ordered attribution/required statements;
- active takedown state incorporated at closure;
- legacy disposition receipt and unclassified count zero;
- visual asset inventory, serializer/non-disclosure receipt and grants.

The fingerprint never treats endpoint availability as permission and never includes held raw locators in public assets.

## 4. Pre-seal receipts

Candidate → validated requires all mandatory receipts to be immutable, passing, and hash-bound to the exact candidate fingerprint.

Research receipts include Phase 1C authority/count/research evidence, source/frozen hashes, identity/FK/orphan checks, registry/corpus rules, projection counts, unknown-relation isolation, deterministic asset inventory, and privileges.

Visual receipts include:

- 100% legacy visual inventory and typed disposition, `UNCLASSIFIED_VISUAL_REFERENCE=0`;
- provider/reference/locator identity and typed-FK checks;
- rights/policy/delivery/health/takedown axis separation;
- truth-table evaluation and complete reason codes;
- positive-delivery attribution requirements;
- active-takedown precedence;
- public locator-role allowlist and held/internal/raw non-disclosure;
- exact research compatibility;
- deterministic visual asset inventory;
- role/default-privilege and negative privilege checks.

OpenAPI, JSON-LD, DCAT, CI, deployment, frontend Repository integration, production endpoint-health service, and browser QA are later implementation gates. Their absence does not prevent logical physical-schema specification once the decisions above are locked.

## 5. Manifest and seal transaction

Each boundary generates its own canonical UTF-8 RFC 8785 JSON manifest and computes SHA-256 over those exact bytes. The manifest cannot embed its own hash.

In one serializable transaction scoped to the owning boundary:

1. verify state is `validated` and lock the boundary row;
2. recompute/compare the closed candidate fingerprint;
3. verify every mandatory receipt hash and copied projection/asset inventory;
4. store the exact manifest bytes and manifest SHA-256;
5. transition `validated → sealed`;
6. commit or abort as one unit.

The research seal function cannot write visual tables or pointers. The visual seal function cannot write research projections or the research pointer.

After commit, a detached post-seal sidecar records:

- exact owning release/version ID;
- exact manifest SHA-256;
- seal transaction identity and timestamp;
- candidate fingerprint and seal-function version;
- optional signature/attestation.

The sidecar is outside the self-hashed manifest inventory. Sidecar failure leaves immutable sealed bytes but makes the version ineligible for `current`.

## 6. Post-seal immutability

Sealed release rows and assets are protected by all of:

- `v49_owner` NOLOGIN ownership;
- no direct DML grant to ingestor, reviewer, releaser, reader, or auditor;
- boundary-specific definer functions that reject sealed targets;
- a defense-in-depth mutation/delete trigger;
- candidate/sealed copied tables rather than views over canonical schemas;
- immutable asset paths/content hashes and manifest inventory equality;
- audit history for every transition and pointer operation.

No request-time join to mutable `core`, `rights`, `research`, or `workflow` may fill a sealed projection field. A canonical edit, new rights observation, or new health result creates a new candidate; it cannot make sealed bytes drift.

## 7. Independent current-pointer CAS

### 7.1 Research current

Research CAS compares:

```text
(channel,
 expected_generation,
 expected_research_release_id,
 expected_research_manifest_sha256)
```

and replaces it with one sealed, sidecar-verified research pair. The function updates only the research pointer and appends research-pointer history.

### 7.2 Visual current

Visual CAS compares:

```text
(channel,
 expected_generation,
 expected_visual_registry_version,
 expected_registry_sha256)
```

and replaces it with one sealed, sidecar-verified visual pair. It also takes a read guard over the expected research-current generation/pair and verifies that the target visual version declares that exact compatible research pair. The read guard prevents publishing an already-stale visual registry; it does not mutate or lockstep-advance the research pointer.

Any stale generation, old-pair mismatch, unsealed target, sidecar failure, or compatibility mismatch fails the CAS and writes no pointer row. Pointer histories are append-only.

### 7.3 Permitted transient mismatch

Research current may advance without a compatible visual current. This is deliberate: research publication cannot silently inherit unreviewed visual status. During the mismatch window:

- research records remain resolvable;
- visual composition reports `VISUAL_REGISTRY_UNAVAILABLE` or `RELEASE_VERSION_MISMATCH`;
- all visual locators are absent;
- no previous visual version is selected by fallback.

A later visual CAS publishes an independently reviewed compatible registry. A promotion orchestrator may coordinate the two CAS calls, but there is no function that mutates both boundaries as one state object.

## 8. Active takedown after seal

An emergency takedown cannot wait for a new registry and cannot rewrite an old registry.

1. Reviewer appends a typed takedown event/scope and restrictive override through a dedicated definer function.
2. Effective delivery is reduced to `BLOCKED` or `CITATION_ONLY` for every affected version/scope.
3. Public composition removes locators before serialization and reports override ID plus deterministic overlay digest; it never returns the formerly sealed pixel/link locator from cache.
4. Exact visual responses that can carry locators must revalidate the overlay; raw immutable visual assets are not directly public cache surfaces.
5. Releaser builds a new visual-registry candidate incorporating the override and advances visual current by CAS.
6. The original sealed registry remains immutable audit evidence.

An override can never widen delivery. A later rescission does not reactivate positive delivery in the old registry; it permits only a new evidence review and new sealed version. Reporting the applied overlay digest preserves reproducibility of the effective machine response in addition to the four release identity fields.

## 9. Pair resolution and error matrix

| Research pair | Visual pair | Compatibility | Result |
|---|---|---|---|
| sealed/verified | sealed/verified | exact | compose; include both exact pairs |
| sealed/verified | absent | n/a | research-only success; explicit unavailable visual state; no locator |
| sealed/verified | sealed/verified | mismatch | explicit mismatch; no locator; no fallback |
| sealed/verified | corrupt/unverified | any | `INTEGRITY_FAILURE`; no fallback |
| corrupt/unverified | any | any | `INTEGRITY_FAILURE`; no research or visual payload |
| current descriptor only | current descriptor only | not yet resolved | resolve once, verify, then switch to exact-pair requests; never cite `current` |

Cache, cursor, ETag, log and receipt keys for composed responses include both exact pairs and, when active, the takedown overlay digest. Research-only responses remain keyed solely by the research pair plus an explicit visual-unavailable/mismatch reason.

## 10. Security-definer separation

Allowed definer families are discrete:

```text
append_visual_observation          -> ingestor
append_rights_or_policy_decision   -> reviewer
append_takedown_override           -> reviewer
research_candidate_validate_seal   -> releaser
visual_candidate_validate_seal     -> releaser
research_current_cas               -> releaser
visual_current_cas                 -> releaser
```

No generic transition function accepts a boundary name. No function accepts an arbitrary table, schema, target kind, or SQL fragment. Each pins `search_path`, schema-qualifies every object, validates typed FKs and caller role, records `session_user`, and has `PUBLIC EXECUTE` revoked.

Negative privilege tests later must prove reviewer cannot seal/CAS, releaser cannot change rights evidence/decisions, reader cannot see held locators or unsealed rows, auditor cannot mutate, and neither boundary's functions can modify the other boundary.

## 11. Pre-DDL acceptance oracle

```text
RESEARCH_AND_VISUAL_STATE_MACHINES_INDEPENDENT=true
VISUAL_VERSION_EXACT_COMPATIBLE_RESEARCH_PAIRS=1
RESEARCH_CURRENT_MUTATES_VISUAL_CURRENT=false
VISUAL_CURRENT_MUTATES_RESEARCH_CURRENT=false
STALE_RESEARCH_CAS_FAILS=true
STALE_VISUAL_CAS_FAILS=true
SIDE_CAR_REQUIRED_FOR_POINTER=true
SEALED_UPDATE_DELETE_ALLOWED=false
SEALED_LIVE_CANONICAL_JOIN_COUNT=0
RESEARCH_RELEASE_THIRD_PARTY_PIXEL_LOCATOR_COUNT=0
MISMATCH_FALLBACK_ALLOWED=false
ACTIVE_TAKEDOWN_CAN_WIDEN=false
```

These are specification assertions. Physical tables, functions, triggers, tests, manifests, and pointers remain unimplemented.
