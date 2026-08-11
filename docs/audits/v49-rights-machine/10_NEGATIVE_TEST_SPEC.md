# 10 — Rights, visual registry, machine contract negative-test specification

- Package: v49 Phase 1D B5
- Status: **LOCKED IMPLEMENTATION-NEUTRAL ORACLE; EXECUTABLE TESTS PENDING**
- Governing delivery rules: [04_RIGHTS_DELIVERY_TRUTH_TABLE.tsv](./04_RIGHTS_DELIVERY_TRUTH_TABLE.tsv)
- Governing entity and release model: [02_RIGHTS_VISUAL_MACHINE_DECISION_PACK_V49.md](./02_RIGHTS_VISUAL_MACHINE_DECISION_PACK_V49.md) and [07_DUAL_RELEASE_SEAL_CAS_SPEC.md](./07_DUAL_RELEASE_SEAL_CAS_SPEC.md)
- Governing serializer and identity policy: [08_MACHINE_VISUAL_EXPOSURE_CONTRACT_V1.md](./08_MACHINE_VISUAL_EXPOSURE_CONTRACT_V1.md) and [09_STABLE_ID_URI_POLICY.md](./09_STABLE_ID_URI_POLICY.md)

## 1. Purpose and boundary

This specification fixes deterministic negative-test inputs, expected states, structural serialization outcomes, error outcomes, and protected invariants before physical PostgreSQL DDL is written. It is deliberately implementation-neutral: a later database constraint suite, release verifier, repository conformance suite, and API serializer suite must all implement the same oracle.

This document does not claim that PostgreSQL, the Read API, OpenAPI, JSON Schema, JSON-LD, Linked Art/PROV-O, DCAT, CI, deployment, the frontend repository adapter, or production health probing exists. No network or provider endpoint is needed to execute these cases; endpoint observations are fixture values.

The frozen candidate JSON remains the only canonical migration input. SQLite is immutable reconciliation evidence; manifests are integrity evidence; Search and TRACE are derived products. No test may use a derived payload to repair or create canonical data.

## 2. Closed vocabulary and oracle notation

The only effective delivery modes are:

```text
BLOCKED
CITATION_ONLY
LINK_ONLY
SOURCE_VIEWER
REMOTE_IMAGE
```

The first matching numeric-precedence row in the rights truth table is authoritative. An unmatched or unregistered value reaches `RD-999` and yields `CITATION_ONLY`.

The cases below use these fixed fixture identities:

| Symbol | Meaning |
|---|---|
| `R-A` | Sealed, sidecar-verified research pair `(research-a, sha256:r-a)` containing object `O-A`. |
| `R-B` | Distinct sealed, sidecar-verified research pair `(research-b, sha256:r-b)`. |
| `V-A1` | Sealed, sidecar-verified visual pair compatible with exactly `R-A`. |
| `V-B1` | Sealed, sidecar-verified visual pair compatible with exactly `R-B`. |
| `E-A` | Registry entry for `O-A` and visual reference `VR-A`. |
| `L-RECORD` | Typed `CANONICAL_RECORD` locator. |
| `L-VIEWER` | Typed `SOURCE_VIEWER` locator. |
| `L-PIXEL` | Typed `DIRECT_IMAGE` remote-pixel locator. |
| `L-HELD` | Raw/internal locator classified `HELD`, never copied to a public projection. |

The symbolic `sha256:r-a`, `sha256:r-b`, and similar fixture labels below stand for distinct valid 64-character lowercase SHA-256 values; they are not literal wire values.

`HEALTHY_FRESH`, `UNREACHABLE`, `STALE`, `REDIRECTED`, and `UNKNOWN` are fixture endpoint-health observations, not live probes. `COMPLETE` is an independently validated attribution bundle. `ACTIVE_BLOCK_ALL` and `ACTIVE_CITATION_ONLY` are effective typed takedown overlays.

Oracle terms are exact:

- `ABSENT(path)` means the property does not exist anywhere in the public body, problem, public headers, HTML metadata, Search/TRACE payload, client-visible cursor, or public log projection. `null`, empty text, a redacted URL, CSS hiding, or a client-only flag does not satisfy absence.
- `REJECT_ATOMIC(code)` means the operation fails with the named stable code, commits no row/pointer/state/asset change, and leaves the before/after fingerprint equal.
- `UNCHANGED(domain)` means row count, stable-ID set hash, and relevant release/pointer generation are byte-for-byte or value-for-value equal before and after the attempt.
- A public response uses `visualRegistrySha256`. The B2 logical term `registrySha256` denotes the same digest and must not appear as a second public field.
- All version pairs are atomic. A successful research response always names `researchReleaseId + researchManifestSha256`; visual fields are both populated or both `null`.

## 3. Rights, policy, delivery, health, and takedown oracle

| Test ID | Deterministic input | Expected state / serialization | Protected invariant |
|---|---|---|---|
| `RM-N-001` | No takedown; rights `UNKNOWN`; policy `REMOTE_DISPLAY_ALLOWED`; attribution `COMPLETE`; only `L-PIXEL=HEALTHY_FRESH`. | First match `RD-021`; mode `CITATION_ONLY`; `ABSENT(remoteImageUrl)`, `ABSENT(thumbnailUrl)`, `ABSENT(imageServiceUrl)`, and no external locator. | Unknown rights plus a healthy pixel URL never authorizes or emits a pixel. |
| `RM-N-002` | Same as `RM-N-001`, plus independently allowlisted `L-RECORD=HEALTHY_FRESH`. | First match `RD-020`; mode `LINK_ONLY`; only `canonicalRecordUrl` may exist; all pixel/viewer/service fields absent. | Unknown rights may expose at most a qualified provider-record link. |
| `RM-N-003` | Rights `REMOTE_DISPLAY_PERMITTED`; policy `SOURCE_VIEWER_ONLY`; `L-VIEWER=HEALTHY_FRESH`; `L-PIXEL=HEALTHY_FRESH`. | First match `RD-050`; mode `SOURCE_VIEWER`; `sourceViewerUrl` may exist; `ABSENT(remoteImageUrl)` and every thumbnail/Image API/service field. | Viewer-only policy caps otherwise permitted rights; technical pixel availability cannot bypass policy. |
| `RM-N-004` | Rights `REMOTE_DISPLAY_PERMITTED`; policy `REMOTE_DISPLAY_ALLOWED`; attribution `COMPLETE`; `L-PIXEL=UNREACHABLE`; `L-RECORD=HEALTHY_FRESH`. | First match `RD-081`; mode `LINK_ONLY`; `canonicalRecordUrl` may exist; all pixel fields absent. | A dead pixel endpoint can only downgrade to a separately qualified link. |
| `RM-N-005` | Same as `RM-N-004`, but no qualified canonical-record locator. | First match `RD-082`; mode `CITATION_ONLY`; no external locator. | Positive rights and policy do not overcome unavailable delivery infrastructure. |
| `RM-N-006` | Rights and policy permit remote display; attribution complete; all locators healthy; takedown `ACTIVE_BLOCK_ALL`. | First match `RD-001`; mode `BLOCKED`; all locators structurally absent; overlay digest non-null. | An active block-all takedown has highest precedence. |
| `RM-N-007` | Same positive inputs; takedown `ACTIVE_CITATION_ONLY`. | First match `RD-002`; mode `CITATION_ONLY`; all external locators absent; citation-safe metadata only. | A scoped citation-only takedown wins over positive permission. |
| `RM-N-008` | Rights `UNKNOWN`; policy `REMOTE_DISPLAY_ALLOWED`; compare `L-PIXEL=UNKNOWN` with otherwise identical `L-PIXEL=HEALTHY_FRESH`. | Both evaluations remain `CITATION_ONLY` when no canonical link exists; rights and policy records are unchanged. | Endpoint health never elevates authorization or creates a more permissive rights/policy state. |
| `RM-N-009` | Rights `REMOTE_DISPLAY_PERMITTED`; policy state is unregistered text `ALLOW_EVERYTHING`; every locator healthy. | Terminal `RD-999`; mode `CITATION_ONLY`; no locator. | Unknown policy/relation-like labels fail closed rather than receive a permissive default. |
| `RM-N-010` | Rights `REMOTE_DISPLAY_PERMITTED`; policy `REMOTE_DISPLAY_ALLOWED`; attribution `INCOMPLETE`; pixel and record healthy. | First match `RD-070`; mode `LINK_ONLY`; record link only; pixel absent. | Required attribution is an independent positive-delivery prerequisite. |
| `RM-P-001` | No takedown; rights `REMOTE_DISPLAY_PERMITTED`; policy `REMOTE_DISPLAY_ALLOWED`; attribution `COMPLETE`; allowlisted `L-PIXEL=HEALTHY_FRESH`; compatible sealed pair. | First match `RD-080`; mode `REMOTE_IMAGE`; `remoteImageUrl` may exist. In v1, thumbnail, Image API/service/info, IIIF manifest/canvas, provider embed, and local-asset fields remain absent. | Exactly one positive control proves that denial is not caused by an oracle that can never permit delivery. |

`RM-P-001` is a necessary positive control, not evidence that any legacy v48 reference satisfies it. The measured Phase 1D legacy positive-rights coverage remains `0.0000%`.

## 4. Machine selection, redaction, and version oracle

| Test ID | Deterministic input | Expected result | Protected invariant |
|---|---|---|---|
| `MC-N-001` | Exact `R-A`; no visual selector. | `200` complete research response; visual pair both `null`; `visualRegistryState=NOT_SELECTED`; reason `VISUAL_REGISTRY_NOT_SELECTED`; no locator field. | Registry absence is not research-object absence. |
| `MC-N-002` | Exact `R-A`; visual `current` has no compatible registry. | `200` complete research response; visual pair both `null`; state `UNAVAILABLE`; reason `VISUAL_REGISTRY_UNAVAILABLE`; no locator. | Research remains citable while visual review lags; no prior registry fallback. |
| `MC-N-003` | Exact `R-A` plus explicit `V-B1`, which declares `R-B`. | `409 RELEASE_VERSION_MISMATCH`; problem names requested visual pair and requested/declared research pairs; no `data`; all locators absent. | Explicit research/visual mismatch is visible and never disguised as absence or fallback. |
| `MC-N-004` | Visual selector supplies only version or only SHA. | `400 INVALID_ARGUMENT`; no data/locator. | Visual pair atomicity is enforced. |
| `MC-N-005` | Exact compatible `R-A + V-A1`, but `V-A1` has no entry for `O-A`. | `200` normal research response with all four fields; `visualEntryState=NO_REGISTRY_ENTRY`; reason `VISUAL_REGISTRY_NO_ENTRY`; no locator. | Missing visual entry never blanks or errors the research object. |
| `MC-N-006` | `E-A` contains a governed `L-HELD` in internal storage; no public copied locator row. | Normal response according to allowed public fields; `ABSENT(L-HELD)` and `ABSENT(rawLocator)` everywhere. | Held/internal/raw locators never serialize. |
| `MC-N-007` | A corrupt copied visual projection unexpectedly contains `L-HELD` or an unknown visual field. | Visual composition is poisoned and withheld with reason `VISUAL_SERIALIZATION_HELD`; complete research-only DTO remains; offending value absent. | A positive allowlist catches upstream projection corruption before bytes reach a client. |
| `MC-N-008` | Effective mode is each of `BLOCKED`, `CITATION_ONLY`, `LINK_ONLY`, and `SOURCE_VIEWER`. | For every row, `ABSENT(remoteImageUrl)`, `ABSENT(thumbnailUrl)`, `ABSENT(imageServiceUrl)` and all IIIF pixel/service fields. | Non-`REMOTE_IMAGE` modes cannot leak pixels through alternate field names. |
| `MC-N-009` | Search and TRACE sealed projections contain `VR-A` with mode below `REMOTE_IMAGE`; internal source still has a pixel locator. | Search/TRACE public payloads contain stable IDs and allowed summaries only; every pixel/held locator absent. | Search/TRACE are not serializer escape hatches. |
| `MC-N-010` | Active takedown becomes effective after `V-A1` was sealed and an earlier response was cached. | Response is recomputed/revalidated before cache lookup; mode is reduced; former locator absent; non-null overlay SHA participates in ETag/cache/cursor key. | Takedown precedence bypasses stale locator caches without rewriting sealed bytes. |
| `MC-N-011` | Selected research or visual descriptor, manifest hash, schema, or sidecar is corrupt. | `503 INTEGRITY_FAILURE`; no fallback, partial composition, data repair, or locator. | Integrity failure cannot become availability fallback. |
| `MC-N-012` | Same object/claim/relation/source/visual reference is projected across a new research or visual version, or its locator changes. | Class UUID and canonical `urn:gdarchive:*` remain unchanged; occurrence URN changes only with its exact owning pair. | Stable identity is independent of release, locator, rights, and deployment host. |
| `MC-N-013` | Serializer receives a field absent from the closed `SAFE`/conditional `PUBLIC` classification. | Field is not emitted; release/serializer conformance fails closed. | Unknown fields default non-public. |
| `MC-N-014` | Client uses `POST`, `PUT`, `PATCH`, or `DELETE` under `/api/v1`. | `405 METHOD_NOT_ALLOWED`; advertised methods are `GET`, `HEAD`, `OPTIONS`; `UNCHANGED(raw/core/provenance/rights/research/release)`. | The public machine boundary is read-only. |

## 5. Seal, immutability, and CAS oracle

| Test ID | Deterministic input | Expected result | Protected invariant |
|---|---|---|---|
| `SC-N-001` | Direct `UPDATE` or `DELETE` against a sealed research projection, manifest, asset inventory, or release row. | `REJECT_ATOMIC(SEALED_RELEASE_IMMUTABLE)` and `UNCHANGED(research release)`. | A sealed projection cannot drift with canonical edits or privileged mistakes. |
| `SC-N-002` | Direct `UPDATE` or `DELETE` against a sealed visual projection, locator allowlist, manifest, asset inventory, or version row. | `REJECT_ATOMIC(SEALED_VISUAL_REGISTRY_IMMUTABLE)` and `UNCHANGED(visual registry)`. | Rights/locator state changes require a new registry version. |
| `SC-N-003` | Research-current CAS uses a stale generation or stale expected research pair. | `REJECT_ATOMIC(STALE_RESEARCH_CURRENT_CAS)`; research and visual pointer generations unchanged. | Lost updates cannot overwrite research current. |
| `SC-N-004` | Visual-current CAS uses a stale generation or stale expected visual pair. | `REJECT_ATOMIC(STALE_VISUAL_CURRENT_CAS)`; both pointer generations unchanged. | Lost updates cannot overwrite visual current. |
| `SC-N-005` | CAS target is sealed but its detached post-seal sidecar is absent or unverifiable. | Atomic rejection; pointer unchanged. | Seal alone is insufficient for pointer eligibility. |
| `SC-N-006` | Visual-current CAS targets `V-B1` while the guarded research current is `R-A`. | Atomic compatibility failure; neither pointer changes. | Visual CAS cannot publish a registry for another research pair. |
| `SC-N-007` | Research current advances from `R-A` to `R-B` while visual current still names `V-A1`. | Research CAS succeeds alone; visual composition becomes explicit unavailable/mismatch; no locator and no inheritance from `V-A1`. | Research updates never inherit unreviewed prior visual status. |
| `SC-N-008` | Seal or current-CAS function for one boundary attempts to write the other boundary's projection or pointer. | Atomic privilege/operation rejection; other boundary fingerprint unchanged. | Research and visual state machines are independent. |
| `SC-N-009` | Canonical rights, claim, relation, or object row changes after candidate closure. | Existing candidate/sealed copied projections remain unchanged; a new attempt/version is required. | Candidate/sealed data never joins mutable canonical tables at request time. |

## 6. Authority and derived-product anti-write oracle

| Test ID | Deterministic input | Expected result | Protected invariant |
|---|---|---|---|
| `AU-N-001` | A legacy Search item absent from the canonical candidate is submitted as an import/create source. | Rejected as derived authority; `UNCHANGED(raw source records/core archive objects/assertions)`. | Search cannot reverse-create canonical rows. |
| `AU-N-002` | A legacy TRACE node/edge/membership or shard value is submitted to create a canonical object, claim, semantic relation, or assertion. | Rejected/held as legacy projection only; all canonical set hashes and counts unchanged. | TRACE cannot reverse-create canonical research facts. |
| `AU-N-003` | A visual-registry public entry or machine response is submitted to create a provider object, external visual reference, rights observation, or archive object. | Rejected; no canonical or raw row created. | Release/API products are read products, never migration inputs. |
| `AU-N-004` | Derived asset contains `__unknown_relation__` or another unregistered relation label. | No canonical semantic relation, accepted claim, TRACE projection, publication row, or metric row; corrupt public asset returns `INTEGRITY_FAILURE`. | Unknown relation fail-closed remains intact across visual/machine work. |
| `AU-N-005` | Healthy IIIF/API/HTTP locator exists for a legacy reference with no adjudicated rights or provider policy. | Reference stays typed `RIGHTS_UNKNOWN` / `POLICY_UNKNOWN`; no assessment, provider mapping, or positive delivery is manufactured. | Technical access never fills an authority or rights gap. |

Every anti-write test compares pre/post counts and deterministic stable-ID set hashes for the affected schemas. An error response alone is insufficient if a side effect occurred.

## 7. Later executable suites and acceptance boundary

| Suite | Earliest phase | Must execute | Phase 1D status |
|---|---|---|---|
| Logical decision consistency | Pre-DDL | Document/registry vocabulary, truth-table coverage, identity/cardinality/state/version/serializer oracle | **Specified here; subject to joint verifier** |
| Physical DDL and privilege negatives | PostgreSQL foundation | `SC-N-001`–`SC-N-009`, typed-FK/exactly-one-subtype tests, reader/reviewer/releaser denial tests | **NOT RUN; database unimplemented** |
| Migration/authority verifier | Import and reconciliation | `AU-N-001`–`AU-N-005`, exact before/after counts and set hashes | **NOT RUN; migration prohibited** |
| Release/manifest verifier | Candidate/freeze | manifest/hash/sidecar/copy immutability, truth-table evaluation, compatibility, corruption and overlay tests | **NOT RUN; releases unimplemented** |
| Repository/API serializer conformance | Pre-freeze / frontend contract | `RM-*`, `MC-*`, exact envelope/problem shapes, structural absence across JSON/HTML/JSON-LD/Search/TRACE | **NOT RUN; API/schema/adapters unimplemented** |
| CI, crawlability, browser and deployment | Pre-promotion / pre-deployment | OpenAPI/JSON Schema, JSON-LD/DCAT, sitemap, accessibility/browser, production origin/health/deployment checks | **NOT RUN; deliberately not a pre-DDL blocker** |

Missing executable PostgreSQL, API, OpenAPI, JSON Schema, JSON-LD, CI, deployment, browser, and frontend Repository evidence keeps database/freeze/promotion/deployment readiness false where applicable. Their absence does not reopen the pre-DDL identity, cardinality, state, version, compatibility, or serialization decisions once the normative corpus and joint verifier agree.

## 8. Cross-package consistency findings

The Phase 1D B1–B4 packages agree on these invariants:

- delivery is one of the five closed modes and the first matching truth-table rule wins;
- rights assessment, provider-policy evaluation, delivery decision, endpoint health, attribution, and takedown are independent inputs/records;
- only `REMOTE_IMAGE` may expose `remoteImageUrl`, and v1 exposes neither thumbnail nor image-service URLs in any mode;
- visual registry absence produces a complete research-only response;
- an explicit incompatible visual selector is a typed `409 RELEASE_VERSION_MISMATCH`;
- research and visual releases are separately sealed and separately CAS-controlled;
- an active takedown is an external monotonic restrictive overlay and never rewrites sealed bytes;
- public serialization is a positive allowlist and held/raw/internal locators are structurally absent;
- Search, TRACE, registries, and machine responses cannot write back into canonical layers.

The following pre-existing normative terms require primary-task integration before the joint verifier can pass; B5 does not edit those files:

1. `DDL_DECISION_PACK_V49.md` still uses `PIXEL_ALLOWED` / `WITHHELD`; it must use or explicitly map to `REMOTE_IMAGE` / `BLOCKED` and the full five-mode vocabulary.
2. `READ_API_V1.md` currently makes the visual pair mandatory for every resource and rejects absence, which conflicts with the locked research-only success behavior.
3. Existing public examples use `registrySha256` and nested envelopes; the locked public field is `visualRegistrySha256`, while `registrySha256` is only the same internal/logical digest.
4. ADR 0004 and Read API problem/canonical templates use `.example` as if final; the stable-ID policy instead makes class URNs canonical and retains `.example` only for frozen UUID seed inputs.
5. Older text describes only three visual axes; the integrated model must preserve rights evidence/assessment, provider policy/evaluation, delivery decision, endpoint health, attribution obligations, and takedown as separately addressable records/inputs.

These are integration deltas, not contradictions among B1–B4 after B4's explicit narrowing. OpenAPI, JSON Schema, JSON-LD, DCAT, CI, deployment, actual API routes, production health checks, and browser tests remain later work and must not be promoted to physical-schema blockers.

## 9. Specification acceptance assertions

```text
NEGATIVE_ORACLE_REQUIRED_CASES_PRESENT=true
DELIVERY_MODE_VOCABULARY_CLOSED=true
UNKNOWN_RIGHTS_HEALTHY_URL_EMITS_PIXEL=false
VIEWER_ONLY_POLICY_EMBEDS_PIXEL=false
DEAD_PIXEL_ENDPOINT_CAN_WIDEN=false
ACTIVE_TAKEDOWN_HAS_PRECEDENCE=true
ENDPOINT_HEALTH_CAN_GRANT_RIGHTS=false
POST_SEAL_MUTATION_ALLOWED=false
STALE_RESEARCH_CAS_ALLOWED=false
STALE_VISUAL_CAS_ALLOWED=false
EXPLICIT_RESEARCH_VISUAL_MISMATCH=true
HELD_RAW_LOCATOR_PUBLIC_COUNT=0
REGISTRY_ABSENT_RESEARCH_RECORD_USABLE=true
DERIVED_SEARCH_TRACE_CAN_CREATE_CANONICAL_ROW=false
EXECUTABLE_IMPLEMENTATION_TESTS_RUN=false
```

## 10. Actions explicitly not performed

No database, DDL, migration, import, data export, network/HTTP/IIIF/image request, provider probe, npm, Next.js, TypeScript, browser, screenshot, Docker, API/schema/fixture implementation, frontend/package/CI/deployment edit, frozen-asset/QA edit, dirty-main mutation, commit, push, PR, merge, or deployment was performed by B5.
