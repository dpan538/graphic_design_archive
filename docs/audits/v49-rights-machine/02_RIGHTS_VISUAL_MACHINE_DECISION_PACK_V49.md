# v49 Phase 1D — Rights, visual registry, and machine-boundary decision pack

- Package: Phase 1D B2
- Decision status: **LOCKED FOR LOGICAL-TO-PHYSICAL MAPPING**
- Implementation status: **NOT IMPLEMENTED**
- Phase 1C dependency: `AUTHORITY_RESEARCH_DELTA_CLOSED=true`
- Frozen source ancestor: `0404c7f96f9189f576c4c5b1368061e4082e436b`

## 1. Scope and non-scope

This pack closes the identities, real-FK relationships, cardinalities, immutable boundaries, compatibility rule, state-transition authority, and current-pointer behavior needed before a physical PostgreSQL schema can be specified. It does not decide that any third-party image is reusable. It does not create DDL, import a row, fetch a URL, download an image, implement a serializer, generate a manifest, or change frontend behavior.

The frozen v48 candidate JSON remains the sole canonical migration input. Its visual/rights literals enter `raw` and `provenance` as observed source values, never as current permission. SQLite and TRACE products remain reconciliation/integrity evidence and cannot create a visual reference, provider object, rights assessment, delivery decision, or release entry.

## 2. Locked authority boundaries

| Boundary | Owns | Must never own or imply |
|---|---|---|
| PostgreSQL working database | Normalized, mutable-by-append/correction `raw`, `core`, `provenance`, `rights`, `research`, and `workflow` records before release closure. | A public mutable head, a sealed scholarly citation, or an implicit permission derived from URL availability. |
| Sealed research release | Immutable object, claim, semantic-relation, corpus, Search, TRACE and other research projections for one exact `(researchReleaseId,researchManifestSha256)` pair. | Third-party pixel/thumbnail/Image API/service/embed locators, provider-health state, or current visual permission. |
| Sealed visual registry | Immutable rights-safe visual-reference projections for one exact `(visualRegistryVersion,registrySha256)` pair and exactly one compatible research pair. | Canonical research truth, reverse writes to research/core, or automatic compatibility with a later research release. |
| Active takedown overlay | Append-only, monotonic restrictive emergency suppression outside sealed bytes; identified and auditable. | Widening delivery or rewriting a sealed research/visual manifest. |
| Machine composition | A read-only view of one exact research pair plus zero or one exact compatible visual pair, with any active restrictive overlay reported. | Cross-version fallback, guessing a registry from filenames, or exposing held/internal/raw locators. |

The research release may expose that an object has visual availability state or opaque registry join keys, but it contains no third-party pixel-bearing locator. The visual registry is the only public release boundary that may carry an allowlisted remote locator, and only when its effective delivery mode permits that locator role.

## 3. Closed visual identity model

### 3.1 Provider and provider object

`rights.provider` is the stable governed provider namespace. Its natural key is the immutable registered `provider_namespace_code`. Provider labels and websites are versioned attributes, not identity.

`rights.provider_object` identifies one provider record with natural key `(provider_id, exact_provider_object_id)`. The provider-defined identifier is case-preserving and is never replaced by a URL. A provider owns zero or many provider objects; each provider object belongs to exactly one provider.

An unknown provider does not produce a synthetic permissive provider. The external reference remains accounted with disposition `UNMAPPED_PROVIDER`, no provider-object FK, and a workflow hold.

### 3.2 External visual reference

`rights.external_visual_reference` is a stable provenance-bound assertion that a source occurrence refers to visual material. It is not an archive object, a URL, a downloaded file, a digital representation, a rights grant, a health result, or a delivery decision.

Its source-occurrence natural key is:

```text
(source_artifact_id, source_record_id, source_field_or_json_pointer,
 occurrence_ordinal)
```

For deterministic v48 replay, the internal UUIDv5 name is the exact UTF-8 string:

```text
urn:graphic-design-archive:v49:v48:visual-reference:
<surfaceId>:<RFC6901-json-pointer>:<zero-based-occurrence-ordinal>
```

using RFC 4122 URL namespace `6ba7b811-9dad-11d1-80b4-00c04fd430c8`, with no case or Unicode normalization. The UUID is merely a stable source-occurrence identity; it does not certify provider mapping, URL validity, byte identity, or permission.

Each reference has exactly one source occurrence and zero or one resolved provider object. One provider object may have many external references. A malformed nonblank literal can still receive a reference identity and a hold, but it creates no valid locator. `NO_VISUAL_REFERENCE` creates no external-reference row; it remains an explicit per-input disposition in the baseline ledger.

### 3.3 Object bridge

`rights.object_visual_reference` is the only canonical archive-object ↔ external-reference bridge. Its natural key is:

```text
(archive_object_id, external_visual_reference_id, reference_role)
```

The relationship is N:M: one archive object can have many visual references, and one visual reference can be relevant to many archive objects. Initial closed roles are `PRIMARY_DEPICTION`, `ALTERNATE_DEPICTION`, `DOCUMENTARY_CONTEXT`, `SOURCE_RECORD_VISUAL`, and `CITATION_VISUAL`. Role changes are new append-corrected assignments, not silent mutation of identity. Ordinal is presentation order and is not part of identity.

Every bridge has real FKs to `core.archive_object` and `rights.external_visual_reference`, plus provenance/acceptance support. An external reference cannot create an archive object; archive-object seeding remains solely the 15,923 candidate JSON surfaces established in Phase 1C.

### 3.4 Locators and representations

`rights.visual_locator` is an immutable, typed locator occurrence owned by exactly one external visual reference. It stores the exact lexical locator, its hash, source evidence, and one closed role:

```text
CANONICAL_RECORD
SOURCE_VIEWER
PROVIDER_EMBED
IIIF_MANIFEST
IIIF_CANVAS
IIIF_IMAGE_SERVICE
IIIF_INFO_DOCUMENT
THUMBNAIL_IMAGE
DIRECT_IMAGE
GOVERNED_LOCAL_ASSET
```

Roles are not interchangeable. In particular, a manifest is not a viewer, a viewer is not a thumbnail, an Image API service is not a direct image, and none is permission. Redirect targets are new observations/locator history; they never overwrite identity or widen delivery.

Locator natural identity is the exact source occurrence:

```text
(external_visual_reference_id, locator_role, source_artifact_id,
 source_record_id, source_field_or_json_pointer, occurrence_ordinal)
```

The same URL in two source occurrences remains two evidenced locators. URL normalization may support search diagnostics but never deduplicates identity.

`rights.digital_representation` denotes governed bytes or an independently evidenced file identity. A URL alone does not create it. `rights.external_visual_representation` is an N:M typed bridge between references and representations, keyed by `(external_visual_reference_id,representation_id,representation_role)`. This phase performs no download, hash, derivative, pHash, or representation creation.

## 4. Rights, policy, delivery, health, and takedown remain separate

The five decision axes are separate records and remain separate in copied release projections:

1. `rights.rights_observation`: immutable observed literal/URI/evidence with a closed typed subject bridge to exactly one provider object, external visual reference, digital representation, or visual locator. No arbitrary `target_type + target_id` exists.
2. `rights.rights_assessment`: evidence-based assessment over one closed typed subject. N:M `rights_assessment_observation` rows record supporting, contradicting, and qualifying observations.
3. `rights.provider_policy_version`: immutable provider policy/terms snapshot. `rights.provider_policy_evaluation` applies one or more exact policy versions to one object-visual-reference bridge and records the independent policy outcome.
4. `rights.delivery_decision`: project decision for exactly one object-visual-reference bridge. It links N:M to the governing rights assessments and provider-policy evaluations and separately allowlists locator roles. Its closed effective modes are `BLOCKED`, `CITATION_ONLY`, `LINK_ONLY`, `SOURCE_VIEWER`, and `REMOTE_IMAGE`.
5. `rights.endpoint_health_observation`: immutable, time-bound technical result for exactly one visual locator. It never changes rights or policy state and can only preserve or reduce effective delivery.

`rights.takedown_event` records evidence, actor, effective time, reason, and provenance. One event has one or more `rights.takedown_scope` rows. Each scope has exactly one row in a closed typed target subtype for provider, provider object, external visual reference, digital representation, visual locator, or object-visual-reference bridge. `rights.takedown_override` is an append-only restrictive result for one scope; it can force only `BLOCKED` or `CITATION_ONLY`.

An active override always wins. It does not update a sealed row. A rescission or scope correction is new evidence and cannot make an old sealed registry permissive again; positive delivery requires a newly assessed and sealed visual-registry version. The active override is incorporated into the next registry candidate.

The decision truth table is owned by `04_RIGHTS_DELIVERY_TRUTH_TABLE.tsv`. This identity model is compatible with its minimum rules: unknown/missing/conflict/stale rights or policy caps at link/citation; viewer-only policy cannot embed; a healthy endpoint never widens; `REMOTE_IMAGE` requires explicit rights and policy permission, complete attribution, acceptable health, and no active takedown.

## 5. No unconstrained polymorphic target

| Need | Closed real-FK structure |
|---|---|
| Rights-observation subject | One observation supertype plus exactly one of provider-object, visual-reference, representation, or locator subject subtypes. |
| Rights-assessment subject | One assessment supertype plus exactly one typed subject subtype using the same permitted target classes. |
| Takedown scope | One scope supertype plus exactly one provider, provider-object, visual-reference, representation, locator, or object-visual-reference scope subtype. |
| Object ↔ visual | `object_visual_reference` with two real FKs and registered role. |
| Reference ↔ representation | `external_visual_representation` with two real FKs and registered role. |
| Decision evidence | Explicit N:M assessment/observation/policy/evidence bridges. |
| Release visual join | Copied visual-registry entry with composite FK to the compatible research object projection and FK to the copied visual-reference projection. |

Every supertype/subtype family has a deferred exactly-one matching subtype invariant. Adding a target kind requires a reviewed schema migration, registry/version update, and negative tests. Free text, JSON IDs, or a generic `(target_type,target_id)` pair is prohibited in canonical, workflow, release, and API layers.

## 6. Independent release model

### Research release

A research release owns its exact research pair, copied research projections, canonical RFC 8785 manifest bytes/SHA, post-seal sidecar, and research-current CAS history. It never lists visual-registry assets or third-party pixel locators. A later canonical-table change cannot alter its sealed rows.

### Visual registry

A visual registry owns its exact visual pair and declares exactly one compatible research identity/hash pair. A research release may have zero or many compatible visual-registry versions; one visual registry is compatible with exactly one research pair. New compatibility is never inferred from matching archive-object IDs.

The registry contains copied, rights-safe projections:

- providers and provider objects needed by published entries;
- external visual references and object-reference bridges;
- typed public locators only when effective delivery allows the locator role;
- rights and provider-policy outcome identities/digests;
- delivery mode and reason codes;
- health state and observation freshness identity;
- attribution/required-statement bundle;
- effective takedown state;
- one exact compatible research pair.

Protected raw evidence and held/internal locators remain in governed storage and are represented in the public registry only by opaque evidence identifiers/digests and fail-closed reason codes. They are never copied into public manifest bytes or public assets.

`release.visual_registry_entry` has natural key:

```text
(visual_registry_version_id, archive_object_id,
 external_visual_reference_id, reference_role)
```

It carries the compatible research identity needed for a composite FK to that research release's object projection. `release.visual_registry_entry_locator` is keyed by `(visual_registry_entry_id,locator_role,ordinal)` and contains only allowlisted public locators. `BLOCKED` has no locator rows; all other modes obey the truth-table-specific allowlist. No serializer may recover an omitted locator from canonical tables at request time.

## 7. Compatibility and mismatch behavior

| Situation | Required behavior |
|---|---|
| Exact compatible research and visual pairs | Compose rights-safe entries and report both exact pairs. |
| Visual registry absent | Research record remains available; visual state is explicitly unavailable and contains no visual locator. |
| Visual pair declares another research pair | Return explicit `RELEASE_VERSION_MISMATCH` for visual composition or a research-only representation with mismatch reason, according to the endpoint contract; never fallback. |
| Research current advances before visual current | Research pointer changes independently. Until a compatible visual pointer is published, visual composition is unavailable/mismatched and no prior registry is inherited. |
| Visual registry advances for the same research pair | Research bytes and research manifest do not change. Consumers may select the new exact visual pair after its independent seal/CAS. |
| Active post-seal takedown | Suppress to `BLOCKED`/`CITATION_ONLY`, report the override identity/digest, bypass stale locator caches, and issue a replacement visual registry; never rewrite sealed bytes. |
| Hash/schema/sidecar failure | `INTEGRITY_FAILURE`; no fallback to `current`, v48, fixture, or another registry. |

## 8. Roles and privileged operation boundary

| Role | Visual/release responsibility | Explicit denial |
|---|---|---|
| `owner` | NOLOGIN owner; audited break-glass only. | Routine application use. |
| `migrator` | Reviewed schema changes via temporary `SET ROLE`. | Runtime observation, review, release, or reader use. |
| `ingestor` | Append source/locator/health observations through allowlisted functions. | Assessment, delivery, takedown outcome, release transition, CAS. |
| `reviewer` | Append policy versions/evaluations, assessments, delivery decisions, attribution bundles, takedown events/overrides through distinct allowlisted functions. | Direct canonical updates/deletes; release sealing or current CAS. |
| `releaser` | Build copied draft projections and call boundary-specific candidate, validate, seal, and current-CAS functions. | Change evidence/assessment/decisions; cross-mutate the other release boundary. |
| `reader` | Select only safe sealed `api_v1` projections/descriptors. | Canonical/held/raw locators, unsealed rows, DML/DDL. |
| `auditor` | Read invoker-rights audit views, receipts, grants, histories and protected evidence subject to audit policy. | DML/DDL, decisions, transitions, CAS, `BYPASSRLS`. |

Only append-observation, append-decision/takedown, boundary-specific transition/seal, and boundary-specific current-CAS operations may be `SECURITY DEFINER`. Functions are owned by `v49_owner`, schema-qualify every object, pin `search_path`, accept no dynamic identifier, record `session_user` and receipt hash, and have `PUBLIC EXECUTE` revoked. Ordinary reads and audits are invoker-rights. Research and visual transition functions cannot invoke one another.

## 9. Pre-DDL decisions versus later implementation

### Closed by this pack

- visual/provider/reference/locator identities and natural keys;
- archive-object ↔ visual-reference N:M bridge;
- closed real-FK target families;
- rights/policy/delivery/health/takedown separation;
- independent research and visual release identities;
- exact one-research-pair compatibility per visual version;
- copied release entry identity and locator omission boundary;
- independent state/seal/sidecar/current-CAS ownership;
- explicit missing/mismatch/takedown behavior;
- post-seal immutability and role/elevation boundary.

### Explicitly deferred and not a DDL-decision blocker

- PostgreSQL tables, migrations, triggers, grants and negative privilege tests;
- actual Read API/OpenAPI/JSON Schema/JSON-LD/Linked Art/PROV-O/DCAT;
- frontend Repository/API integration and image renderer changes;
- provider policy acquisition, HTTP/IIIF health probes, and positive-rights review;
- data/frontend CI, deployment, production monitoring and browser QA.

Those implementation items remain pre-freeze, pre-promotion, or pre-deployment gates. They do not reopen the identities/cardinalities locked here.

## 10. B2 gate result

```text
VISUAL_ENTITY_IDENTITIES_LOCKED=true
VISUAL_ENTITY_CARDINALITIES_LOCKED=true
ARBITRARY_POLYMORPHIC_TARGET_PROHIBITED=true
DUAL_RELEASE_MODEL_LOCKED=true
POST_SEAL_IMMUTABILITY_LOCKED=true
INDEPENDENT_CURRENT_CAS_LOCKED=true
RESEARCH_PIXEL_LOCATOR_EXCLUSION_LOCKED=true
B2_IMPLEMENTATION_PERFORMED=false
```

Global rights/machine readiness also depends on the B1 truth table, B3 100% legacy disposition, B4 machine contract, B5 negative oracle, normative-document integration, and independent joint verification.
