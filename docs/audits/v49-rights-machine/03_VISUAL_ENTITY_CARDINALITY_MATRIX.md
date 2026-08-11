# 03 — Visual entity identity and cardinality matrix

- Package: Phase 1D B2
- Status: **LOCKED LOGICAL MODEL; PHYSICAL DDL PENDING**
- Governing summary: [02_RIGHTS_VISUAL_MACHINE_DECISION_PACK_V49.md](./02_RIGHTS_VISUAL_MACHINE_DECISION_PACK_V49.md)

## 1. Identity ledger

| Logical record | Stable identity / natural key | Required parent(s) | Cardinality | Mutable before release? | Release behavior |
|---|---|---|---|---|---|
| `rights.provider` | UUID plus unique immutable `provider_namespace_code` | none | 1 provider → 0..N provider objects and 0..N policy versions | append-corrected labels/metadata | copied only when referenced by a registry entry |
| `rights.provider_object` | `(provider_id,exact_provider_object_id)` | exactly 1 provider | 1 provider object → 0..N external references | append-corrected; ID immutable | copied provider-scoped identity; URL is not key |
| `rights.external_visual_reference` | `(source_artifact_id,source_record_id,source_field_or_json_pointer,occurrence_ordinal)` | exactly 1 source occurrence; 0..1 resolved provider object | one ref → 0..N object bridges, locators and representation bridges | append-only identity; mapping corrections are decisions | copied as visual-reference projection, never research fact/pixel |
| `rights.object_visual_reference` | `(archive_object_id,external_visual_reference_id,reference_role)` | exactly 1 archive object and 1 external reference | object ↔ reference is N:M | append-corrected assignment | copied into registry entry; cannot create object |
| `rights.visual_locator` | `(external_visual_reference_id,locator_role,source_artifact_id,source_record_id,source_field_or_json_pointer,occurrence_ordinal)` | exactly 1 external reference and evidence occurrence | one ref → 0..N locators; one locator → 0..N health observations | immutable occurrence; redirects/new values append | public copy only if role is allowed by effective delivery |
| `rights.digital_representation` | UUID; byte/content identity only when independently evidenced | governed byte/evidence record | representation ↔ external reference N:M through bridge | append-only identity | visual projection may cite opaque identity/digest; no download implied |
| `rights.external_visual_representation` | `(external_visual_reference_id,representation_id,representation_role)` | exactly 1 reference + 1 representation | N:M | append-corrected | copied only if relevant and publishable |
| `rights.rights_observation` | UUID plus source/evidence occurrence digest | exactly one typed subject subtype | subject → 0..N observations; observation may support 0..N assessments | immutable | registry copies assessment/evidence identity/digest, not held raw locator |
| `rights.rights_assessment` | UUID/version over exactly one typed subject | exactly one typed subject; 0..N evidence bridges while proposed, 1..N for effective assessment including explicit absence evidence | subject → 0..N assessment history | append-only/superseding | one or more exact effective assessment identities feed an entry |
| `rights.provider_policy_version` | `(provider_id,policy_scope_id,effective_from,snapshot_sha256)` | exactly 1 provider and source artifact | provider → 0..N versions; a version may govern N references | immutable snapshot | exact version IDs/digests copied |
| `rights.provider_policy_evaluation` | UUID/version for one object-reference bridge | exactly 1 object-reference bridge; 1..N policy-version bridges when known; explicit unknown/missing state otherwise | bridge → 0..N evaluation history | append-only/superseding | exact effective evaluation copied |
| `rights.delivery_decision` | `(object_visual_reference_id,decision_version)` | exactly 1 object-reference bridge; N:M assessment and policy-evaluation support | bridge → 0..N decision history; at most one effective per registry candidate | append-only/superseding | copied effective mode/reason and locator allowlist |
| `rights.endpoint_health_observation` | `(visual_locator_id,observed_at,method_version,request_fingerprint_sha256)` | exactly 1 visual locator | locator → 0..N observations | immutable | copied state/freshness identity; cannot widen delivery |
| `rights.attribution_bundle` | UUID/version plus deterministic ordered-item digest | evidence and language-tagged ordered items | bundle may serve N decisions; decision uses 0..1 unless mode requires 1 | immutable version | required for `REMOTE_IMAGE`; copied rights-safe |
| `rights.takedown_event` | UUID plus evidence/actor/effective time | evidence + reviewer authority | event → 1..N scopes | append-only | referenced by override digest and next registry |
| `rights.takedown_scope` | UUID plus `(event_id,scope_ordinal)` | exactly 1 event + exactly 1 typed target subtype | event → 1..N; target → 0..N events | immutable | effective restrictive result copied/reported |
| `rights.takedown_override` | UUID plus `(takedown_scope_id,override_version)` | exactly 1 scope | scope → 1..N append-only results | monotonic restrictive only | immediately overlays old registries; next registry incorporates |
| `release.research_release` | exact `(researchReleaseId,researchManifestSha256)` | sealed copied research snapshot | one research release → 0..N compatible visual versions | immutable after seal | contains no third-party pixel-bearing locator |
| `release.visual_registry_version` | exact `(visualRegistryVersion,registrySha256)` | exactly 1 compatible research pair | research release → 0..N visual versions; visual version → exactly 1 research pair | immutable after seal | owns copied visual projections/manifest/sidecar |
| `release.visual_registry_entry` | `(visual_registry_version_id,archive_object_id,external_visual_reference_id,reference_role)` | registry, compatible research object projection, copied visual reference | registry → 0..N entries | copied candidate; immutable at candidate closure | one effective delivery/rights/policy/health/takedown state |
| `release.visual_registry_entry_locator` | `(visual_registry_entry_id,locator_role,ordinal)` | exactly 1 registry entry | entry → 0..N public locator rows | copied candidate; immutable at candidate closure | omitted unless truth-table mode explicitly permits role |
| `release.research_current_pointer` | `(channel)` plus generation and exact research pair | sealed, sidecar-verified research release | one current row/channel; append-only history | CAS only | never updates visual pointer |
| `release.visual_current_pointer` | `(channel)` plus generation and exact visual pair | sealed, sidecar-verified visual registry | one current row/channel; append-only history | CAS only | never updates research pointer |

## 2. Closed subject/target subtype families

### Rights-observation and rights-assessment subject

Exactly one subtype row is required:

| Subtype | Real FK target | Purpose |
|---|---|---|
| `provider_object_subject` | `rights.provider_object` | Provider/item-level observed statement. |
| `external_visual_reference_subject` | `rights.external_visual_reference` | Reference-specific rights evidence. |
| `digital_representation_subject` | `rights.digital_representation` | Byte/file/surrogate-specific evidence. |
| `visual_locator_subject` | `rights.visual_locator` | Endpoint/locator-specific observed statement without treating the URL as identity. |

### Takedown scope target

Exactly one subtype row is required:

| Subtype | Real FK target | Scope semantics |
|---|---|---|
| `provider_scope` | `rights.provider` | All governed content from the provider, only when evidence supports that breadth. |
| `provider_object_scope` | `rights.provider_object` | One provider record/object. |
| `external_visual_reference_scope` | `rights.external_visual_reference` | One provenance-bound visual reference. |
| `digital_representation_scope` | `rights.digital_representation` | One evidenced byte/file identity. |
| `visual_locator_scope` | `rights.visual_locator` | One endpoint/locator occurrence. |
| `object_visual_reference_scope` | `rights.object_visual_reference` | One archive-object use of a visual reference. |

There is no generic target row. A future target class requires a migration and an updated exactly-one-subtype constraint before any row can use it.

## 3. Locator-role cardinality and delivery boundary

| Locator role | Cardinal parent | May appear for delivery mode | Prohibited inference |
|---|---|---|---|
| `CANONICAL_RECORD` | external visual reference | truth table may allow for `LINK_ONLY`/`SOURCE_VIEWER`/`REMOTE_IMAGE`; takedown can suppress | A record page does not grant pixels. |
| `SOURCE_VIEWER` | external visual reference | `SOURCE_VIEWER` or `REMOTE_IMAGE` only when provider policy permits; never as a pixel locator | Viewer availability is not remote-display permission. |
| `PROVIDER_EMBED` | external visual reference | only an explicitly policy-permitted viewer/embed path; otherwise omitted | An iframe/embed endpoint is not inherently authorized. |
| `IIIF_MANIFEST` | external visual reference | never copied as a deliverable pixel by itself; exposure is contract/policy controlled | IIIF presence is not authorization. |
| `IIIF_CANVAS` | external visual reference | not public unless explicitly needed and safe under the contract | Canvas identity is not image permission. |
| `IIIF_IMAGE_SERVICE` | external visual reference | only under `REMOTE_IMAGE`, if explicitly permitted | Healthy service cannot widen rights. |
| `IIIF_INFO_DOCUMENT` | external visual reference | only under `REMOTE_IMAGE`, if required and permitted | Technical metadata is not a license. |
| `THUMBNAIL_IMAGE` | external visual reference | only under `REMOTE_IMAGE` and explicit thumbnail scope | “Thumbnail” is not fair-use permission. |
| `DIRECT_IMAGE` | external visual reference | only under `REMOTE_IMAGE` | HTTP success or redirect is never enough. |
| `GOVERNED_LOCAL_ASSET` | external visual reference | only under a later explicit local-delivery policy; no such asset is created here | Git/local presence does not grant rights. |

`BLOCKED` produces zero public locator rows. `CITATION_ONLY`, `LINK_ONLY`, and `SOURCE_VIEWER` never carry direct pixel, thumbnail, IIIF Image API/service/info, or governed-local-asset locators. Exact public allowlists are fixed by the B1 truth table and B4 serializer contract; omission is structural, not a CSS choice.

## 4. Release projection FKs and non-drift

The copied visual registry is self-contained. It does not resolve mutable canonical rows when serving a sealed version.

Required logical references are:

1. `visual_registry_version.compatible_research_release_id/hash` → one sealed research descriptor.
2. `visual_registry_entry.(compatible_research_release_id,archive_object_id)` → one copied object row in that exact research release.
3. `visual_registry_entry.(visual_registry_version_id,external_visual_reference_id)` → one copied visual-reference projection in that registry.
4. Each entry's provider/policy/assessment/delivery/health/attribution/takedown identifiers → copied registry-local projections or immutable registry snapshots.
5. Each entry locator → a copied registry-local locator row, never a live canonical URL lookup.

Candidate closure prevents adding/removing entries, changing copied outcomes, changing compatible research identity, or changing locator allowlists. Seal protection prevents all `UPDATE`/`DELETE`. Canonical corrections or new observations can only feed a new visual-registry version.

## 5. Baseline-measurement boundary

The pre-migration A6 reconciliation measured 15,923 SQLite objects, 15,621 nonblank external image URLs, 15,620 distinct URLs, and 302 blank URLs. Those figures demonstrate why URL and object identity cannot be conflated; they are not the Phase 1D typed baseline and do not determine positive rights coverage.

The authoritative Phase 1D inventory and typed percentages belong to `05_LEGACY_VISUAL_DISPOSITION_BASELINE.tsv` and `06_LEGACY_VISUAL_DISPOSITION_SUMMARY.json`. This B2 model imposes these invariants on that work:

- every canonical input surface has one disposition row;
- `NO_VISUAL_REFERENCE` has no external-reference entity;
- every nonblank/malformed occurrence is accounted without URL deduplication;
- `UNKNOWN`/`UNMAPPED_PROVIDER`/`MALFORMED` are legal typed holds;
- `UNCLASSIFIED_VISUAL_REFERENCE=0` is required;
- no baseline row creates a positive rights, policy, delivery, or health assertion by inference.

## 6. Acceptance assertions for later DDL tests

```text
NO_UNCONSTRAINED_TARGET_TYPE_ID=true
EXACTLY_ONE_TYPED_OBSERVATION_SUBJECT=true
EXACTLY_ONE_TYPED_ASSESSMENT_SUBJECT=true
EXACTLY_ONE_TYPED_TAKEDOWN_SCOPE=true
OBJECT_VISUAL_REFERENCE_IS_N_TO_M=true
URL_IS_IDENTITY=false
URL_ACCESS_IS_PERMISSION=false
RESEARCH_RELEASE_HAS_PIXEL_LOCATOR=false
VISUAL_VERSION_COMPATIBLE_RESEARCH_PAIRS=1
SEALED_PROJECTION_LIVE_CANONICAL_JOINS=0
```

These are logical acceptance oracles. Physical constraint names and SQL are deliberately deferred.
