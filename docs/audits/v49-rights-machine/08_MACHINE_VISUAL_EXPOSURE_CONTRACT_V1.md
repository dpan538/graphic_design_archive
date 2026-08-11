# 08 — Machine visual exposure contract v1

- Package: v49 Phase 1D B4
- Status: **LOCKED PRE-DDL CONTRACT; IMPLEMENTATION PENDING**
- Governing rights rule: [04_RIGHTS_DELIVERY_TRUTH_TABLE.tsv](./04_RIGHTS_DELIVERY_TRUTH_TABLE.tsv)
- Governing visual model: [02_RIGHTS_VISUAL_MACHINE_DECISION_PACK_V49.md](./02_RIGHTS_VISUAL_MACHINE_DECISION_PACK_V49.md)
- Governing identity policy: [09_STABLE_ID_URI_POLICY.md](./09_STABLE_ID_URI_POLICY.md)

## 1. Scope and authority

This contract fixes the public machine boundary that physical columns and release projections must be able to enforce. It covers exact research/visual version identity, registry-absent behavior, version mismatch, stable resource identifiers, a closed field-exposure matrix, fail-closed locator projection, reason codes, and the GET-only public surface.

It does not implement the Read API, OpenAPI, JSON Schema, JSON-LD, Linked Art, PROV-O, DCAT, CI, deployment, a frontend adapter, a provider-health service, or any PostgreSQL object. Those remain pre-freeze, pre-promotion, or pre-deployment implementation gates and are not empty-schema blockers.

The frozen v48 candidate JSON remains the sole canonical migration input. SQLite and legacy Search/TRACE/visual products are reconciliation or integrity evidence only. A machine request, derived product, URL, IIIF resource, redirect, or healthy endpoint can never create a canonical object, assertion, visual reference, or delivery permission.

## 2. Exact response identity

Every successful reproducible research-resource response uses these four flat fields at the top level:

```json
{
  "apiVersion": "v1",
  "researchReleaseId": "v49-research-YYYYMMDD.N",
  "researchManifestSha256": "64 lowercase hex",
  "visualRegistryVersion": null,
  "visualRegistrySha256": null,
  "visualRegistryState": "UNAVAILABLE",
  "visualReasonCodes": ["VISUAL_REGISTRY_UNAVAILABLE"],
  "takedownOverlaySha256": null,
  "data": {}
}
```

The public field is `visualRegistrySha256`. The logical/database term `registrySha256` in the Phase 1D B2 model denotes the same digest and must map to this one public field; it is not a fifth version value or a competing alias. A serializer must never emit both names.

### 2.1 Atomic pair rules

1. `researchReleaseId` and `researchManifestSha256` are non-null on every successful research-resource response.
2. `visualRegistryVersion` and `visualRegistrySha256` are atomic: both are non-null or both are `null`.
3. Non-null visual fields identify one sealed, sidecar-verified visual registry whose manifest declares the exact research pair in the same response.
4. `current` is a discovery alias only. A repository resolves it once, verifies the descriptor and compatibility, then issues exact-pair requests. No scholarly citation, cursor, cache entry, ETag, evidence record, or response identity uses `current` as a version.
5. The response body is authoritative. Diagnostic response headers must echo the same values and must not override them.
6. A generic `releaseId`, `version`, or `manifestSha256` field may not replace or collapse either pair.

An active post-seal takedown can change effective exposure without changing sealed registry bytes. When an override affects the response, `takedownOverlaySha256` is required and contains the deterministic digest of the applied restrictive overlay. It is `null` otherwise. Cursors, cache keys, ETags, logs, and receipts include that digest when present.

## 3. Selection and compatibility behavior

Exact resource requests bind the research release ID in the path and its manifest SHA-256 in the release selector. A visual selector, when supplied, contains both visual fields. Supplying only one field is `400 INVALID_ARGUMENT`.

| Situation | HTTP/result contract | Version fields | Locator behavior |
|---|---|---|---|
| Exact research pair; no visual selector | `200` research-only success | visual pair is `null`; state `NOT_SELECTED` | no visual locator field exists |
| Exact research pair; visual `current` has no compatible version | `200` research-only success | visual pair is `null`; state `UNAVAILABLE` | no fallback to an older registry; no locator field exists |
| Exact compatible research and visual pairs | `200` composed success | all four fields non-null; state `COMPATIBLE` | truth-table allowlist only |
| Compatible registry has no entry for the object/reference | `200` normal research success | all four fields non-null; state `COMPATIBLE` | `visualEntryState=NO_REGISTRY_ENTRY`; no locator field exists |
| Explicit visual pair declares a different research pair | `409 RELEASE_VERSION_MISMATCH` | error reports the requested visual pair and both actual/required research pairs | no data payload and no locator; no fallback |
| Explicit visual pair is not found | `404 VISUAL_REGISTRY_NOT_FOUND` | known request fields may be reported | no fallback and no locator |
| Either selected manifest/hash/sidecar is corrupt | `503 INTEGRITY_FAILURE` | only verified identities are authoritative | no fallback and no locator |
| Active takedown | normal response reduced to `BLOCKED` or `CITATION_ONLY`, unless the whole resource is legally suppressed | exact pairs remain; overlay digest is non-null | overlay wins before serialization and cache lookup |

Registry absence is not object absence. `getSurface`, object, claim, relation, source, corpus, and other research records remain valid research-only responses when the registry is not selected or no compatible registry exists. The UI/API must not turn that state into an error page, blank object, empty title, or invented image placeholder.

### 3.1 Explicit mismatch problem

A mismatch problem contains no research `data` object and no visual locator:

```json
{
  "apiVersion": "v1",
  "code": "RELEASE_VERSION_MISMATCH",
  "status": 409,
  "researchReleaseId": "requested research release",
  "researchManifestSha256": "requested research digest",
  "visualRegistryVersion": "requested visual version",
  "visualRegistrySha256": "requested visual digest",
  "compatibleResearchReleaseId": "research release declared by the registry",
  "compatibleResearchManifestSha256": "digest declared by the registry",
  "detail": "The selected visual registry is not compatible with the selected research release."
}
```

Problem `type` values use the domain-independent problem URNs in the stable-ID policy until a production canonical origin is approved. No `.example` URL is emitted as a supposedly final problem identifier.

## 4. Stable resource identifiers

The public read model exposes class-specific stable identifiers independently of route aliases and releases:

| Resource | Required fields | Identity rule |
|---|---|---|
| Archive object | `objectId`, `objectUrn`; optional legacy `surfaceId` alias | object UUID is stable; `surfaceId` is a resolver/crosswalk, never the object key |
| Semantic relation | `relationId`, `relationUrn` | independent of claims, TRACE edges, trees, layouts, and release placement |
| Research claim | `claimId`, `claimUrn` | independent of semantic relation and evidence item IDs |
| Citable source document | `sourceId`, `sourceUrn` | raw artifact/record keys stay internal unless a separately approved public source projection exists |
| External visual reference | `visualReferenceId`, `visualReferenceUrn` | provenance-bound reference identity; URL/provider key is not identity |

The canonical identity is version-independent. A release occurrence additionally carries `researchReleaseId + researchManifestSha256`; a visual decision additionally carries `visualRegistryVersion + visualRegistrySha256`. Stable IDs are never regenerated because a label, source locator, delivery mode, endpoint, provider mapping, merge, split, or takedown changes.

## 5. Closed field-classification matrix

Every projected field belongs to exactly one class. The public serializer uses a positive allowlist; a domain object, database row, raw JSON object, or provider payload is never spread into a DTO.

| Class | Meaning | Representative fields | Public serializer rule |
|---|---|---|---|
| `SAFE` | Release-validated research identity and non-sensitive descriptive projection. | four version fields; stable IDs/URNs; public labels; display dates; publication/corpus layer; registered relation/epistemic codes; public count units. | Explicitly copied after research-manifest/schema verification. |
| `PUBLIC` | Publishable only after a named release policy or evidence rule passes. | rights-safe citation metadata; publishable claimant/source summaries; ordered attribution/required statements; effective delivery mode/reason codes; allowlisted external locator for the exact mode. | Explicit conditional branch; condition and source projection identity are recorded. |
| `INTERNAL` | Governed operational material that public consumers do not need. | internal PostgreSQL keys other than approved stable IDs; raw-to-canonical crosswalk internals; complete assessment/policy/health history; workflow state/assignee; reviewer actor; request fingerprint; mutable provider configuration; unsealed rows. | Never selected by a public view or serializer. Available only through separately authorized invoker-rights audit/operations views. |
| `HELD` | Restricted, unresolved, private, raw, or unsafe material. | raw provider payload; raw locator literal not approved for release; signed/tokenized/private URL; held/internal locator; licensed excerpt; legal/reviewer notes; takedown requester/contact data; credentials; local filesystem path; quarantined malformed value. | Never present in any public response, log, problem detail, cursor, ETag input exposed to clients, HTML metadata, Search document, TRACE payload, or visual registry public asset. |

Unknown fields do not default to `SAFE` or `PUBLIC`. They fail the release serializer-conformance gate and remain `INTERNAL`/`HELD` until a reviewed contract version classifies them.

### 5.1 Resource allowlists

| Resource | `SAFE` allowlist | Conditional `PUBLIC` allowlist | Always excluded |
|---|---|---|---|
| Object/surface | version fields, object ID/URN, `surfaceId`, title/date, rights-safe typed labels, publication/corpus summary | rights-safe public source/citation summary; visual summary from a compatible registry | raw source record, provider payload, workflow notes, raw/local locator, unrestricted image fields |
| Claim | version fields, claim ID/URN, epistemic class, accepted wording only when publication-cleared, stance, public relation IDs | claimant/source/citation/locator summary only when separately publication-cleared | held quotation, raw evidence span, private reviewer note, internal confidence diagnostics |
| Semantic relation | version fields, relation ID/URN, registered predicate/type, typed endpoint IDs/URNs, public supporting/challenging claim IDs | rights-safe public explanatory label | TRACE layout as relation identity, unregistered predicate, held claim/evidence |
| Source | version fields, source ID/URN, public bibliographic citation and source type | public canonical source URL only under the source-publication rule; visual links still obey the visual truth table | raw capture URL/body, credentials, licensed content body, internal acquisition locator |
| Visual reference | version fields, visual-reference ID/URN, provider public ID/label if releasable, effective delivery mode, ordered reason codes, entry/override digest | attribution bundle and exactly the locator roles permitted by the first matching truth-table rule | raw locator history, held endpoints, observation bodies, internal policy/legal notes, health request fingerprint |

## 6. Visual locator projection

The serializer first evaluates the ordered truth table, applies any active takedown overlay, verifies the exact registry/research compatibility, and then constructs the visual DTO from an empty object. It never filters a prebuilt object after URLs have been attached.

| Effective mode | Permitted URL-bearing public field | Fields that must be structurally absent |
|---|---|---|
| `BLOCKED` | none | canonical record, source viewer, provider embed, remote pixel, thumbnail, IIIF manifest/canvas/Image API/info/service, local asset |
| `CITATION_ONLY` | none | every external locator URL |
| `LINK_ONLY` | `canonicalRecordUrl` only when the matching rule says `ALLOWLISTED_ONLY` and the typed locator is qualified | source viewer, provider embed, remote pixel, thumbnail, IIIF/service, local asset |
| `SOURCE_VIEWER` | `canonicalRecordUrl` and/or `sourceViewerUrl` only as allowed by the matching rule | provider embed unless explicitly represented as the approved viewer, remote pixel, thumbnail, IIIF Image API/service/info, local asset |
| `REMOTE_IMAGE` | `canonicalRecordUrl` and `remoteImageUrl` only as allowed by the matching v1 rule | `thumbnailUrl`, `imageServiceUrl`, IIIF manifest/canvas/info/service, provider embed, local asset remain absent in v1 |

For v1, only `REMOTE_IMAGE` may expose a remote-pixel locator. The current truth table does not expose thumbnail or image-service locators even in `REMOTE_IMAGE`; adding either requires a reviewed truth-table and machine-contract/schema version change. A locator field is omitted, not serialized as `null`, an empty string, a redacted URL, a CSS-hidden element, or a client-only boolean.

`SOURCE_VIEWER` exposes a viewer page, not pixels. `LINK_ONLY` exposes a canonical provider record page, not a viewer or image. `CITATION_ONLY` may expose bibliographic/source labels but no external URL. `BLOCKED` may retain a non-sensitive stable visual-reference ID and reason code only when the takedown scope permits that metadata.

An endpoint-health observation can only retain or lower a mode selected by rights and provider policy. Healthy HTTP/IIIF/API state, redirects, and URL presence can never create `PUBLIC` eligibility or upgrade the mode.

## 7. Positive serializer algorithm

The normative algorithm is:

1. Validate exact research descriptor, manifest hash, release state, resource projection, and stable IDs.
2. Initialize the envelope and `data` DTO from an empty schema-owned structure; copy only the research `SAFE` allowlist.
3. If no visual selector or compatible registry exists, set both visual fields to `null`, record the explicit state/reason, and return the complete research DTO.
4. If an explicit visual selector mismatches or fails integrity, return the typed problem; do not compose or fallback.
5. For a compatible registry, locate copied registry entries only. Do not join mutable `rights`, `core`, `raw`, or `workflow` tables at request time.
6. Apply the active restrictive takedown overlay before cache lookup and before any locator field is constructed.
7. Evaluate the first matching rights truth-table rule. Copy stable visual identity, effective mode, ordered reason codes, and only `SAFE`/approved `PUBLIC` fields.
8. Add only locator roles allowlisted by that rule and v1 field matrix. Never read omitted locators back from canonical/internal storage.
9. Validate the constructed public DTO against the closed serializer contract. An unexpected research field is `INTEGRITY_FAILURE`. An unexpected visual field/locator poisons visual composition and returns a research-only DTO with `VISUAL_SERIALIZATION_HELD`; it never leaks the value.
10. Compute cache/ETag/cursor identity from the exact research pair, optional exact visual pair, resource selector, and optional overlay digest.

Search and TRACE serializers follow the same allowlist and may only consume sealed research/visual projections. Their payloads cannot write back to or manufacture `raw`, `core`, `provenance`, `rights`, or `research` rows.

## 8. Visual state and reason-code registries

### 8.1 Composition state

The closed success-state vocabulary is:

```text
NOT_SELECTED
UNAVAILABLE
COMPATIBLE
```

Entry-level state is separately one of:

```text
NOT_EVALUATED
NO_VISUAL_REFERENCE
NO_REGISTRY_ENTRY
RESTRICTED
DELIVERABLE
```

Version mismatch, not-found, and integrity failure are typed problems, not empty success. They never reuse `UNAVAILABLE` to conceal an explicit bad selector.

### 8.2 Composition reason codes

```text
VISUAL_REGISTRY_NOT_SELECTED
VISUAL_REGISTRY_UNAVAILABLE
VISUAL_REFERENCE_ABSENT
VISUAL_REGISTRY_NO_ENTRY
VISUAL_REGISTRY_VERSION_MISMATCH
VISUAL_REGISTRY_NOT_FOUND
VISUAL_REGISTRY_INTEGRITY_FAILURE
VISUAL_SERIALIZATION_HELD
```

Delivery reason codes are exactly the `reason_code` values in `04_RIGHTS_DELIVERY_TRUTH_TABLE.tsv`. Codes are stable machine values. Human-readable details are optional, non-authoritative, and cannot contain held evidence or locator values.

## 9. GET-only public boundary

The public `/api/v1` boundary permits only `GET`, `HEAD`, and `OPTIONS`:

- `GET` returns immutable pair-pinned resources or short-lived discovery descriptors;
- `HEAD` returns the same status, ETag, and exact version diagnostics without a body;
- `OPTIONS` advertises the allowlisted read methods and CORS policy without performing work that reads provider endpoints;
- no ingest, scrape, review, health probe, rights assessment, delivery decision, takedown command, release transition, seal, CAS, export generation, assistant/chat, or other mutation endpoint exists under `/api/v1`.

Unsupported methods return `405 METHOD_NOT_ALLOWED` with an allowlist. Public requests never trigger a network fetch to a provider, on-demand image proxy, mutable-database enrichment, or derived-to-canonical write.

## 10. Cache, cursor, log, and non-disclosure rules

- A composed cache/cursor/ETag key contains all four exact version values plus resource/filter/sort identity and the active overlay digest when present.
- A research-only key contains the exact research pair and the explicit visual state/reason; it cannot collide with a composed response.
- A cursor presented with another pair or overlay fails; it is never silently rebound.
- Logs record request ID, API version, stable resource kind/ID, exact pair IDs/digests, state/reason code, and overlay digest only. They never record a raw/held locator, provider body, quote, legal note, contact, token, or query text outside an independently approved telemetry policy.
- Public errors disclose stable codes and safe version diagnostics, not internal paths, SQL, table names, raw values, signed URLs, or evidence bodies.
- HTML, JSON, JSON-LD, Search, TRACE, sitemap, change-feed, and alternate serializers must share the same exposure classifier. A non-JSON route is not an escape hatch.

## 11. Acceptance oracle

```text
MACHINE_RESPONSE_HAS_EXACT_RESEARCH_PAIR=true
VISUAL_PAIR_ATOMIC_NULLABILITY=true
PUBLIC_VISUAL_SHA_FIELD=visualRegistrySha256
REGISTRY_ABSENT_RESEARCH_RECORD_USABLE=true
EXPLICIT_MISMATCH_IS_ERROR=true
PUBLIC_SERIALIZER_IS_POSITIVE_ALLOWLIST=true
UNKNOWN_FIELD_DEFAULT_PUBLIC=false
HELD_RAW_LOCATOR_PUBLIC_COUNT=0
NON_REMOTE_IMAGE_PIXEL_URL_FIELD_COUNT=0
NON_REMOTE_IMAGE_THUMBNAIL_URL_FIELD_COUNT=0
NON_REMOTE_IMAGE_IMAGE_SERVICE_URL_FIELD_COUNT=0
ENDPOINT_HEALTH_CAN_WIDEN=false
PUBLIC_API_MUTATION_METHOD_COUNT=0
DERIVED_PAYLOAD_CAN_CREATE_CANONICAL_ROW=false
```

These are pre-DDL decisions and negative-test targets. No executable API/schema/serializer/test is claimed in this phase.

## 12. Explicitly deferred

The following remain implementation work and do not reopen this contract's identity/cardinality/state/version/serialization decisions: PostgreSQL DDL; API routes; OpenAPI; JSON Schema; JSON-LD; Linked Art/PROV-O; DCAT; canonical HTML; sitemap/robots; release diff/change feed; CI; deployment; production endpoint-health checks; frontend Repository adoption; browser QA; and positive provider-rights acquisition.
