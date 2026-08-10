# 06 — Rights and Visual Federation Audit

- Audit package: **A6**
- Audit date: **2026-08-11** (Australia/Brisbane)
- Worktree: `/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform`
- Baseline branch: `refactor/v49-data-platform`
- Independent scope: external visual references, provider policy, IIIF endpoint semantics, rights observations and decisions, delivery safety, endpoint health, attribution, takedown, and independent visual-registry versioning
- Audit coverage: **COMPLETE**
- Package result: **FAIL**
- `RIGHTS_VISUAL_PRE_DDL_READY`: **false**
- `DATABASE_IMPLEMENTED`: **false**
- `DATABASE_FREEZE_READY`: **false**
- `FRONTEND_PROMOTION_READY`: **false**

`FAIL` is a readiness result, not a scan-coverage result. The repository contains substantial conservative rights research and useful v48 rights evidence, but the normative v49 model cannot yet represent the required independent research-release and visual-registry identities, endpoint roles, three orthogonal decision axes, or enforceable takedown behavior. These are P0 architecture gaps that must be closed before rights-aware physical DDL is written.

## 1. Scope

This audit examined:

- all nine current v49 architecture documents;
- the legacy SQL and manual-record schemas that describe sources, images, IIIF, terms and rights;
- provider-, rights-, IIIF- and image-related capture helpers and policy code;
- the v48 immutable SQLite representation fields using only `mode=ro&immutable=1`;
- the 68-row source registry, 38 manual/remediation records, all 447 CSV headers, rights-repair ledgers, and data-lineage evidence;
- current frontend representation types and remote-image rendering paths, without running the frontend;
- all 27 Deep Research DOCX files by local XML text extraction and the seven Markdown research reviews;
- A1, A2 and A3 audit evidence already present in `docs/audits/v49-pre-migration/`.

Affected paths include:

- `ARCHITECTURE.md`, `DATA_MODEL_V49.md`, `READ_API_V1.md`, `MIGRATION_V48_TO_V49.md`, `ACCEPTANCE_GATES.md`;
- `docs/adr/`, `docs/architecture/`, `docs/research-reviews/`, `docs/capture/`;
- `db/*.sql`, `db/manual_source_record.schema.json`;
- `data/source_registry.csv`, `data/rights_strategy.csv`, manual/remediation records, capture records, repair queues and raw-provider evidence;
- `scripts/rights_decision_engine.py`, `scripts/source_policy_registry.py`, `scripts/iiif_discovery.py` and related capture/audit scripts;
- `frontend/src/types/archive.ts`, `frontend/src/lib/layout.ts`, `frontend/src/components/archive/ImageZone.tsx`, and other current image renderers.

This audit does not decide whether any particular third-party image may legally be reused. It assesses whether the repository can store, review, freeze and deliver that decision without conflating technical access with authorization.

## 2. Explicit non-actions

The following were explicitly not performed:

- no third-party endpoint, API, page, redirect, IIIF service, manifest, viewer or image URL was requested;
- no image, thumbnail, manifest, canvas, screenshot or other third-party content was downloaded;
- no pHash, perceptual hash, blurhash, OCR, CV or image similarity operation ran;
- no proxy thumbnail, local derivative, replacement visual or QA asset was created;
- no browser, browser automation, npm, Next.js, TypeScript, Docker or PostgreSQL process ran;
- no SQLite write connection, sidecar, `VACUUM`, migration or export was created;
- no v48 artifact, shard, manifest, receipt, visual page, QA screenshot, package file, CI file or deployment file was modified;
- no provider terms or rights claim was reclassified, promoted or widened;
- no secret value was read or printed;
- no code, DDL, migration, API, adapter, fixture, commit, push, PR, merge or deployment was created by A6.

## 3. Evidence commands

Representative read-only commands are listed below. Large outputs were reduced to aggregate counts; provider URLs were never dereferenced.

```text
rg --files ...
rg -n -i '(rights|iiif|provider|takedown|attribution|...)' <bounded source paths>
sed -n '<range>p' <architecture/schema/policy/report file>
find data -type f \( -iname '*right*' -o -iname '*iiif*' -o ... \) -print
```

SQLite was opened only in this form:

```text
sqlite3 'file:/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform/data/prefreeze_candidate_v48.sqlite?mode=ro&immutable=1' '<aggregate SELECT>'
```

The aggregate queries inspected `objects.image_state`, `objects.image_url`, `objects.rights_state`, capture/source-record URL counts, and source-document counts. A read-only Python connection used the same immutable URI to aggregate URL schemes and host counts. It printed no payload body.

CSV and JSON shape checks used local standard-library readers:

```text
python3 -c '<read first CSV row; aggregate header presence only>'
python3 -c '<read 38 manual/remediation JSON records; aggregate key/value counts only>'
```

Deep Research reports were inspected locally without conversion or mutation:

```text
python3 -c '<zipfile: read word/document.xml; strip XML; count bounded policy terms>'
```

No command in this package writes data or contacts a network service.

## 4. Executive findings

### 4.1 The project has strong conservative intent

The historical rights work consistently says that public access, an API response, a visible image, an IIIF endpoint, a redirect, a source-hosted viewer, or an `og:image` signal is not a reuse grant. Useful evidence includes:

- `data/rights_strategy.csv` separates source categories and says item/provider terms remain controlling;
- `docs/capture/RIGHTS_FIRST_CRAWLER_DECISION_ENGINE_v0.md` prohibits treating IIIF, discovery signals, LLM terms summaries or visual similarity as open-image proof;
- `docs/capture/P0_RIGHTS_REPAIR_PREFLIGHT_ROLLUP_v1.md` records 511 P0 candidate rows across seven source families and **zero** automatic upgrades;
- `docs/capture/IMAGE_RIGHTS_REPAIR_QUEUE_v1.md` records 1,644 object-level rights/image repair candidates and explicitly requires item-level evidence;
- the Deep Research reports recommend structured rights, provider statements, source identifiers, attribution and human review.

These materials are valuable historical evidence. They do not, however, constitute the current normative v49 schema or a sealed visual registry.

### 4.2 The normative v49 model is not yet a visual-federation model

Current v49 documents define a generic sealed release pair, a `rights.digital_representation`, rights statements and a versioned display policy. They do not define:

- an independently versioned visual registry;
- a visual-registry manifest/hash and its own current-pointer CAS;
- a compatibility binding between a research release and a visual registry;
- typed external visual identity and provider object identity;
- distinct canonical-record, IIIF manifest, IIIF viewer, thumbnail and image-service endpoints;
- observed provider rights versus normalized rights assessment versus project delivery decision;
- endpoint health as a separate, non-authorizing observation;
- review-due/stale semantics, required-statement bundles, or enforceable takedown overrides.

The current single `release` manifest covers Archive, Search, TRACE and rights-safe representations. That is insufficient for a visual registry that must change independently for provider-policy review, endpoint health and emergency takedown while the scholarly research release remains citable and immutable.

### 4.3 Current runtime data makes this distinction operationally material

The frozen v48 SQLite snapshot contains:

| Measured unit | Count |
| --- | ---: |
| Objects | 15,923 |
| Nonblank external image URLs | 15,621 |
| Distinct external image URLs | 15,620 |
| URL schemes | 15,605 HTTPS; 16 HTTP |
| Distinct remote hosts | 49 |
| Blank image URLs | 302 |
| `IMG02` / `source_viewer_candidate` | 8,388 rows; 8,221 carry a URL |
| `IMG03` / `open_candidate` | 7,370 rows; all carry a URL |
| `IMG01` / `thumbnail_candidate` | 30 rows; all carry a URL |
| `IMG00` | 38 rows; no URL |
| `IMG04` | 97 rows; no URL |

The current frontend treats any nonblank `IMG01`, `IMG02` or `IMG03` URL as directly renderable. `frontend/src/components/archive/ImageZone.tsx`, `frontend/src/components/archive/main-sheets/MainSheetLab.tsx`, and `frontend/src/lib/layout.ts` place the remote URL in an HTML `<img>`. In particular, current `IMG02` is a source-hosted remote-pixel fetch, not merely a link to a provider viewer.

Therefore a stale or over-broad image-state label can disclose a provider pixel URL and cause a user browser to fetch it. A v49 API promise of “rights-safe” output is not enforceable until the rights assessment, delivery decision, endpoint health and visual-registry versions are explicit and pinned.

## 5. Required capability matrix

`PASS` means the current normative v49 documents can express and enforce the capability. Legacy SQL or prose alone does not make a v49 capability pass.

| Required capability | Current evidence | Result | Required decision before DDL |
| --- | --- | --- | --- |
| `researchReleaseId + researchManifestSha256` | Generic `releaseId + manifestSha256` exists, but it is not distinguished from visual-registry identity. | **PARTIAL** | Name the pair as the immutable research release identity and keep it independent of visual-delivery state. |
| Independent `visualRegistryVersion + registrySha256` | No normative object, manifest or envelope exists. | **FAIL** | Define immutable visual-registry versions and canonical registry-manifest bytes/SHA. |
| External visual reference identity | `rights.digital_representation` has a source URL/local asset reference, but no external-reference identity contract. | **PARTIAL** | Give every external visual reference a stable internal ID and provenance, separate from URL and delivered bytes. |
| Provider object ID | Provider keys can occur in raw/source records; no typed representation/provider-object binding exists. | **FAIL** | Store provider namespace plus exact provider object ID and source-record evidence; never use URL as identity. |
| Canonical record URL | `provenance.source_document` has a canonical URL; representation linkage and URL role are not specified. | **PARTIAL** | Make canonical record URL a typed endpoint role linked to provider object/source record. |
| IIIF manifest/viewer/thumbnail/image-service separation | Legacy schemas contain some manifest/canvas/thumbnail/info fields; v49 collapses them into one source URL. Viewer is not consistently modeled. | **FAIL** | Define typed endpoint/reference roles and forbid substituting one role for another. |
| Rights observation | Raw text/assertions can retain provider wording, but no normative time-bound observation entity is defined. | **PARTIAL** | Define immutable observation with source artifact/record, literal/URI, observed-at, locator, hash and observer/method. |
| Provider policy | Legacy `source_registry.csv` and SQL contain policy hints; current v49 only has project display policy. | **FAIL** | Define versioned provider-policy snapshots with terms source/hash, scope, effective dates, review due, restrictions and evidence. |
| Delivery mode | `display_policy` values mix rights assessment and delivery behavior. | **FAIL** | Define a separate delivery decision enum and its evidence/policy inputs. |
| Endpoint health | No normative table/axis; no CSV header among all 447 CSVs contains `endpoint_health`. | **FAIL** | Define time-bound health observations and a latest-health projection; health must never grant rights. |
| Attribution and IIIF required statement | v49 rights statement has generic credit/restrictions; ordered required-statement semantics are absent. | **PARTIAL** | Define versioned attribution/required-statement bundles with label/value/language/order and source evidence. |
| Review due and stale state | Effective dates exist conceptually; no explicit policy/rights review-due and stale transition exists. | **FAIL** | Define review due, supersession and deterministic stale evaluation. |
| Takedown override | Legacy SQL has a takedown contact and suppression flag; v49 has no override or emergency deny path. | **FAIL** | Define append-only, monotonic restrictive override, scope, evidence, actor, effective time, supersession and audit path. |
| Visual-registry `current` pointer/CAS | Only the generic research release pointer has CAS. | **FAIL** | Give visual registry a separate `(channel,generation,version,sha)` CAS and compatibility check. |
| Rights assessment, delivery mode and endpoint health are orthogonal | Current v49 rights decision includes `source_only`/`metadata_only`, and current IMG states also imply rendering. | **FAIL** | Store and gate the three axes independently; no axis may infer another. |
| Unknown/missing/conflict/stale fail closed | Current v49 prose says unresolved/conflict becomes metadata-only, but missing/stale are not modeled and LINK/CITATION behavior is not contractual. | **FAIL** | All four conditions must resolve to `LINK_ONLY` or `CITATION_ONLY`; no pixel URL is exposed. |
| API/IIIF/redirect cannot imply authorization | Historical prose says this, but current helper/runtime behavior can still promote/fetch based on viewer/IIIF state. | **FAIL** | Make it a schema, gate, projection and negative-test invariant. |

## 6. Evidence inventories

### 6.1 Source registry

`data/source_registry.csv` has 68 unique `source_id` rows and 68 unique source URLs. Field completeness is uneven:

| Field | Nonblank rows | Blank rows | Observed values relevant to readiness |
| --- | ---: | ---: | --- |
| `last_verified_date` | 68 | 0 | All are 2026-05-29 through 2026-05-31; no review-due rule exists. |
| `automation_status` | 33 | 35 | 31 `manual_review`, 2 `automated_probe`; no row uses the helper's accepted reviewed-status vocabulary. |
| `rights_basis` | 33 | 35 | Mixed free-text categories. |
| `record_level_rights_required` | 33 | 35 | 29 yes, 4 no. |
| `default_image_zone` | 33 | 35 | 24 IMG00, 6 IMG04, 3 IMG02. |
| `preview_allowed` | 33 | 35 | 31 no, 2 unknown. |
| `thumbnail_allowed` | 33 | 35 | 23 no, 6 review, 2 unknown, 2 yes. |
| `iiif_capable` | 33 | 35 | 16 unknown, 15 no, 2 yes. |
| `protocol_sensitive` | 33 | 35 | 31 false, 2 true. |

The registry is historical policy evidence, not a complete provider-policy registry. It lacks immutable policy-version identity, terms snapshot hash, effective interval, review due, supersession, jurisdiction/scope, endpoint roles, endpoint health, required statements, and current-pointer/CAS.

`scripts/source_policy_registry.py` correctly requires an explicit reviewed vocabulary for automatic thumbnail eligibility, but its `source_viewer_candidate` property can become true from preview, IIIF capability or IMG02 default without requiring a reviewed provider policy. That candidate must not become a delivery permission.

### 6.2 CSV evidence surface

All 447 data CSV headers were inspected without reading payload bodies. Header presence was:

| Header signal | Files containing at least one matching field |
| --- | ---: |
| rights | 125 |
| IIIF | 60 |
| viewer | 59 |
| image URL | 73 |
| thumbnail | 2 |
| canonical URL | 4 |
| endpoint | 5 |
| license | 3 |
| provider | 0 |
| endpoint health | 0 |
| takedown | 0 |
| attribution | 0 |
| required statement | 0 |
| review due | 0 |
| delivery | 0 |

There are 24 rights-named CSV files. They are fragmented capture, probe, repair, quality and summary evidence rather than one authoritative registry. They must not be silently unioned into canonical rights decisions.

### 6.3 Manual and remediation records

All 38 JSON records under `data/manual_source_records/` and `data/remediation_source_records/` contain a rights object. Only four contain an image object.

| Measure | Result |
| --- | --- |
| Rights states | 19 link-only; 10 metadata-open; 5 metadata-limited; 3 image-open; 1 image-embed-only |
| Image-use policies | 19 do-not-display; 15 metadata-only; 3 full-image-allowed; 1 source-viewer-only |
| Rights review required | 28 true; 10 false |
| Local copy permitted | 38 false |
| Image objects | 4 |
| Nonblank image rights URI among those four | 0 |
| Nonblank image rights label / credit | 4 / 4 |

The records preserve useful curator intent, but their combined rights/image-use labels conflate assessment and delivery. They have no independent endpoint-health or visual-registry identity. Per A3 they are authored evidence requiring a governed re-ingest decision, not v49 canonical decisions.

### 6.4 Research and policy documents

All 27 DOCX reports were locally inspected. Rights and IIIF are widely discussed, but no report uses the exact concepts `visual registry`, `endpoint health`, or `delivery mode`; only two reports mention `required statement`, and two contain a takedown discussion. This is evidence that the new federation contract is not merely missing from the v49 summary: it was not previously specified as a complete dual-version operational model.

The reports correctly support these retained principles:

- technical availability is not authorization;
- metadata rights, physical-object rights and digital-representation rights differ;
- IIIF roles and provider statements should travel with the representation;
- attribution and required statements must be machine-readable;
- community/protocol restrictions and takedown require human governance;
- unknown rights do not justify pixel display.

Research prose remains advisory until translated into normative schema, state vocabulary, gates and API contracts.

### 6.5 Repository/license boundary from A1–A3

Cross-audit evidence materially affects visual readiness:

- A1 found that root `LICENSE` covers source code, while `FRONTEND_DESIGN_LICENSE.md`, screenshots, reports and third-party provider content have different or unresolved boundaries. No artifact-level release license inventory exists.
- A1 found no repository-wide `NOTICE`, `THIRD_PARTY_LICENSES` or machine-readable SBOM and marks third-party/provider artifact inventory as a promotion P0.
- A2 found 60 `docs/qa/` files, 65 frontend QA/screenshot paths, exact duplicate QA blobs, and 253 PNG-extension/JPEG-signature paths. MIME or Git presence cannot prove reuse permission.
- A3 found 1,271 raw/probe JSON paths and 1,266 tracked raw files under 26 directories carrying a `do_not_commit_without_redaction_review` policy, without one comprehensive receipt.
- A3 classifies v48 JSON as the sole migration input; SQLite and visual products are reconciliation/evidence only. No visual URL, rights state, image state, raw provider file or QA image becomes authoritative merely by appearing in a derived product.

This audit therefore does not recommend deleting third-party evidence. It recommends withholding it from machine/public delivery until each artifact or reference has an explicit governed disposition.

## 7. Code-path findings

### 7.1 Rights decision helper is conservative about open reuse but not sufficient for delivery

`scripts/rights_decision_engine.py` correctly prevents discovery signals from upgrading an image and requires explicit open URI/text for IMG03. However:

- `has_iiif_manifest` or `has_source_viewer` alone returns IMG02;
- IMG02 selects `source_viewer_frame` without requiring a versioned provider-policy decision;
- attribution/required-statement completeness is not a precondition;
- policy review due, endpoint health, redirects and takedown overrides are not inputs;
- explicit open URI sets local copy permitted without a separate project delivery decision and obligation bundle.

This helper is historical capture logic, not a safe v49 policy engine.

### 7.2 IIIF discovery is correctly labeled but technically active when invoked

`scripts/iiif_discovery.py` states that a manifest is not a license. When invoked, it fetches a page, parses link/JSON-LD candidates, guesses manifest routes and requests them. A6 did not invoke it. It belongs in a quarantined capture toolchain with explicit authorization, rate/provider policy and immutable observations; it must not be used in runtime reads or pre-DDL validation.

### 7.3 Current frontend renders remote pixels from one coarse state

`frontend/src/types/archive.ts` exposes a single image URL plus state/credit/license label. It does not carry:

- visual-registry version/hash;
- endpoint role;
- provider-object/canonical-record identity;
- rights observation and assessment identity;
- delivery-decision identity;
- endpoint-health observation;
- required-statement bundle;
- takedown state.

`ImageZone.tsx`, main-sheet/sub-sheet renderers and `isRenderableImage()` directly fetch any URL for IMG01, IMG02 or IMG03. This is a legacy coupling finding only; A6 did not modify the frontend. v49 projections must not emit a rights-held pixel URL for `LINK_ONLY` or `CITATION_ONLY`, so the frontend cannot accidentally fetch it.

## 8. P0 findings

| ID | Finding | Affected paths | Risk | Required action | Blocks |
| --- | --- | --- | --- | --- | --- |
| A6-P0-01 | No independent visual-registry identity, manifest, lifecycle or CAS exists. | All nine v49 documents | A rights/provider/takedown change either mutates a scholarly release or cannot be safely published. | Define immutable `visualRegistryVersion + registrySha256`, its lifecycle/current CAS, compatibility with exact research release, and API dual-version envelope. | **DDL** |
| A6-P0-02 | External visual identity and endpoint roles are collapsed into a representation/source URL. | `DATA_MODEL_V49.md`; legacy schemas; frontend DTOs | Provider object identity is unstable; manifest/viewer/thumbnail/service URLs can be substituted and misinterpreted. | Define typed external reference/provider object and endpoint-role records with provenance and no URL-as-identity rule. | **DDL** |
| A6-P0-03 | Rights assessment, delivery mode and endpoint health are not three orthogonal axes. | `DATA_MODEL_V49.md`; `ARCHITECTURE.md`; `READ_API_V1.md` | Availability or a rights label can silently become pixel delivery. | Define separate state machines/tables and forbid implication between them. | **DDL** |
| A6-P0-04 | Unknown, missing, conflicting and stale decisions do not have one explicit fail-closed contract. | v49 rights model and acceptance gates | Stale/missing policy may expose remote pixels; `metadata_only` is ambiguous about URLs. | Require `LINK_ONLY` or `CITATION_ONLY`, suppress all pixel/service endpoints, and add negative cases for unknown/missing/conflict/stale/API/IIIF/redirect. | **DDL** |
| A6-P0-05 | Versioned provider policy, rights observation, required statement, review due and takedown override are incomplete or absent. | v49 model/API; `source_registry.csv`; legacy SQL | Decisions are not reproducible, obligations can be lost, and urgent suppression cannot override an old sealed visual record. | Define typed immutable observations, provider-policy versions, assessment evidence, attribution bundle, stale rules and monotonic restrictive takedown overlay. | **DDL** |
| A6-P0-06 | Current helper/runtime behavior can treat IIIF/viewer state as renderable and fetch a remote pixel. | `scripts/rights_decision_engine.py`; `scripts/source_policy_registry.py`; frontend image renderers | “IIIF exists” or “viewer candidate” can become network display without provider-policy authorization. | Mark legacy IMG logic non-authoritative for v49; derive delivery only from a sealed visual-registry decision. Do not modify frontend in this audit. | **frontend promotion**, and DDL must prevent leakage |
| A6-P0-07 | No artifact-level license/rights disposition covers third-party raw data, reports, QA and historical screenshots. | `data/**`; `reports/**`; `docs/qa/**`; frontend QA paths | Public/machine release may redistribute content outside the root MIT boundary. | Create release-scoped artifact/reference rights ledger; every unknown remains HOLD and citation/link-only. | **freeze/promotion**, not empty-schema creation |

All A6 P0s are open. P0-01 through P0-05 are architecture/DDL blockers. P0-06 and P0-07 may be implemented later, but the DDL and normative gates must be capable of enforcing them before physical schema work begins.

## 9. P1 and P2 findings

| ID | Priority | Finding | Risk | Recommended action |
| --- | --- | --- | --- | --- |
| A6-P1-01 | P1 | 35/68 source-registry rows lack the later policy fields; all dates are from May 2026 and there is no review-due rule. | Stale source policy appears current. | Preserve current CSV as historical evidence; migrate only through explicit provider-policy versions and stale evaluation. |
| A6-P1-02 | P1 | Rights evidence is fragmented across 125 CSV schemas/signals and 24 rights-named CSVs. | A union-by-column/name would manufacture authority. | Build a field-level evidence mapping ledger; ingest as observations/assertions with source artifact/hash/locator. |
| A6-P1-03 | P1 | 38 manual/remediation records combine rights state and image-use policy; four image blocks have labels/credits but no rights URI. | Human intent may be lost or over-promoted. | Preserve lexical values and import as observations; require new assessments/decisions rather than translating labels mechanically. |
| A6-P1-04 | P1 | Legacy `db/*.sql` contains richer fields but is `HOLD_UNKNOWN` and conflicts with accepted v49 identity/release decisions. | Old DDL may be mistaken for the v49 schema. | Mark legacy SQL non-executable for v49; use it only as requirements evidence. |
| A6-P1-05 | P1 | Metadata rights, object rights, representation rights, contractual provider terms and cultural/community protocol are not fully separated in v49. | One permissive axis can incorrectly override another restriction. | Model independently and compute effective delivery as the most restrictive applicable decision. |
| A6-P1-06 | P1 | No visual-registry/research-release compatibility gate or response-pair cursor/cache binding exists. | A client can mix a research release with an incompatible registry. | Bind cursors/cache/ETags to both exact pairs and reject incompatible composition. |
| A6-P2-01 | P2 | IMG00–IMG04 are presentation-era composite codes. | They encourage state-axis conflation. | Retain only as a derived legacy/UI projection; never use them as canonical rights, policy, health or delivery state. |
| A6-P2-02 | P2 | Redirect history and endpoint health have no measurement cadence/error vocabulary. | Broken endpoints may be mistaken for withdrawn rights, or successful redirects for permission. | Define observation time, status class, redirect chain hash, retry policy and stale threshold, without changing rights assessment. |
| A6-P2-03 | P2 | Attribution/required statements lack localization/order/rendering conformance rules. | Required provider language can be dropped or rearranged. | Define an ordered, language-tagged bundle and projection conformance test. |

## 10. Required pre-DDL semantic contract

This section is a decision requirement, not DDL or implementation.

### 10.1 Dual immutable identities

Every machine response that can expose visual metadata must identify both:

```text
researchReleaseId
researchManifestSha256
visualRegistryVersion
registrySha256
```

Rules:

1. The research pair identifies scholarly object/relation/claim data and remains immutable.
2. The visual pair identifies the exact rights/provider/delivery registry applied to those objects.
3. A visual registry declares the exact compatible research pair; no cross-pair fallback is permitted.
4. The research and visual `current` pointers are separate CAS-controlled routing records.
5. Runtime resolves both pointers once, validates compatibility, then uses exact pairs.
6. Cache keys, cursors, ETags, logs and receipts bind both pairs.
7. A visual policy/takedown change does not rewrite the research release; it creates a new registry version or a restrictive emergency override.

### 10.2 External visual reference and endpoint roles

The logical model must distinguish:

- internal external-visual-reference ID;
- provider ID and provider object ID;
- canonical provider record URL;
- IIIF manifest URL;
- IIIF viewer URL;
- IIIF canvas ID;
- thumbnail URL;
- IIIF Image API service URL/info document;
- direct source image URL;
- any governed local asset/derivative identity.

An endpoint is a locator, not identity or authorization. Endpoint aliases/redirects are observed history, not destructive updates. A provider object can have many endpoints; an endpoint can change without changing the provider object or archive object.

### 10.3 Three orthogonal axes

1. **Rights assessment** answers what the evidence supports. It includes `UNKNOWN`, `MISSING`, `CONFLICT`, `STALE`, restrictive states, and positively evidenced permission states.
2. **Delivery mode** answers what this project will return: at minimum `CITATION_ONLY`, `LINK_ONLY`, governed provider embed/viewer, controlled remote thumbnail, controlled remote image, governed local derivative and governed local original. The exact vocabulary must be closed before DDL.
3. **Endpoint health** answers what was technically observed at a time: unknown, healthy, redirected, degraded, missing, blocked, error, or stale observation. It never grants delivery permission.

No axis implies another. Effective delivery uses the most restrictive applicable rights, provider-policy, protocol, takedown and health rule.

### 10.4 Fail-closed rule

Any `UNKNOWN`, `MISSING`, `CONFLICT` or `STALE` rights/provider decision resolves to `LINK_ONLY` or `CITATION_ONLY`. The projection must omit direct pixel, thumbnail, image-service and embed endpoints. A canonical record link may remain only when it is itself allowed and not subject to takedown.

These facts never authorize display:

- API response success;
- public URL visibility;
- IIIF manifest/image service existence;
- viewer or thumbnail presence;
- HTTP 2xx/3xx or a redirect target;
- an open metadata license;
- source-family reputation;
- an LLM summary, discovery signal, pHash/similarity result or filename.

### 10.5 Observations, policies, decisions and obligations

The logical model must preserve separately:

- immutable provider/right observation with source artifact/record, literal/URI, locator, access time and hash;
- versioned provider-policy snapshot with terms/robots/policy source, snapshot hash, scope, effective interval, review due and supersession;
- curator/legal rights assessment with decision reasons and evidence joins;
- delivery decision with exact governing assessment/policy versions;
- endpoint-health observations and latest-health projection;
- ordered attribution/credit/IIIF required-statement bundle;
- cultural/community protocol and sensitivity restrictions;
- append-only takedown override.

An emergency takedown is a monotonic restrictive overlay: it may immediately suppress links/pixels for every affected registry version, never widen delivery, never mutate the archived registry bytes, and must be incorporated into the next sealed visual-registry version. Historical scholarly metadata can remain reproducible while delivery is safely revoked.

## 11. Authority and retention recommendations

| Asset family | Authority role | Classification | Source/owner | Recovery reference | Proposed action | Deletion risk |
| --- | --- | --- | --- | --- | --- | --- |
| v48 canonical JSON image/rights fields | lexical migration input only | `MIGRATE` | frozen v48 | checkpoint `0404c7f` plus freeze hash | Import literals/URLs as raw observations and reference candidates; never as current permission. | Critical |
| v48 SQLite image/rights rows | reconciliation only | `ARCHIVE_READ_ONLY` | v48 freeze | frozen SQLite hash | Preserve immutable; use only for aggregate/set reconciliation. | Critical |
| TRACE/Search visual products | derived display products | `ARCHIVE_READ_ONLY` / later reproducible | v48 builders | TRACE/Search manifests and Git | Keep behavior/evidence; do not seed rights decisions. | High |
| `data/source_registry.csv`, `data/rights_strategy.csv` | historical source-policy research | `ARCHIVE_READ_ONLY` | source/rights research | Git history | Preserve; supersede through versioned policy registry, not in-place authority. | High |
| Rights-repair CSVs/reports | curator/probe evidence fragments | `ARCHIVE_READ_ONLY` | capture audits | Git paths and summaries | Map selected rows to observations/evidence only after artifact disposition. | High |
| 1,266 tracked raw provider files | provider response evidence with missing global receipt | `HOLD_UNKNOWN` | capture runs/providers | A3 ledger and Git | Quarantine from migration/publication until terms/redaction/rights disposition. | High |
| Manual/remediation JSON | authored research evidence | `ARCHIVE_READ_ONLY` pending governed re-ingest | project curation | Git history | Preserve lexical content; require new rights assessment. | High |
| Legacy rights/IIIF Python helpers | historical capture logic | `ARCHIVE_READ_ONLY` for v49 runtime; selected concepts may be re-specified | project scripts | Git history | Do not delete here; do not reuse as v49 policy engine without contract tests. | Medium/high |
| Legacy `db/*.sql` rights tables | obsolete schema requirements evidence | `HOLD_UNKNOWN` | pre-v49 database work | Git history | Explicitly mark non-executable; supersede with approved DDL later. | Severe if executed |
| QA/screenshots and third-party visual evidence | mixed verification/third-party content | `HOLD_UNKNOWN` pending A9/artifact rights ledger | QA and providers | A1/A2/A9 ledgers | Do not publish, normalize or delete based on this audit. | High |

No A6 asset is a deletion candidate merely because its rights are unknown. Unknown content remains `HOLD_UNKNOWN` and fail-closed.

## 12. Acceptance and readiness matrix

| Gate | Result | Evidence |
| --- | --- | --- |
| A6 scope and command evidence | **PASS** | Required repository, data, policy, schema, runtime and cross-audit boundaries were inspected; commands and non-actions are recorded. |
| No network/image acquisition | **PASS** | No endpoint was contacted and no image/visual derivative was created. |
| Research release exact pair | **PARTIAL** | Generic release pair exists, but dual identity is absent. |
| Independent visual registry and CAS | **FAIL** | No normative model. |
| External visual/provider/IIIF role model | **FAIL** | v49 source URL is insufficient; legacy fields are non-normative and incomplete. |
| Orthogonal rights/delivery/health | **FAIL** | Current state vocabularies conflate them; health absent. |
| Unknown/missing/conflict/stale fail closed | **FAIL** | Only unresolved/conflict metadata-only prose exists; no complete state/gate/API suppression rule. |
| Attribution/required statement/review due | **FAIL** | Generic credit exists, but required structured obligations and stale semantics do not. |
| Takedown override | **FAIL** | Legacy contact/suppression hints do not provide a v49 append-only override. |
| API pixel-URL non-disclosure | **FAIL** | Contract says rights-safe, but DTO/gate and dual registry identity are unspecified; current runtime directly renders external URLs. |
| Artifact-level third-party disposition | **FAIL** | A1/A3 identify unclassified provider/QA/report/raw content. |
| `RIGHTS_VISUAL_PRE_DDL_READY` | **false** | P0-01 through P0-05 remain open. |

## 13. Recommended action sequence

1. **Close the normative rights/visual ADR.** Define dual versions, external visual/endpoint identity, the three axes, observations/policies/obligations, takedown overlay and CAS. Acceptance: every capability in section 5 is PASS and all nine v49 documents use one vocabulary.
2. **Convert the contract into physical-schema tests, without importing data.** Acceptance: negative cases prove API/IIIF/redirect/health cannot grant delivery; unknown/missing/conflict/stale expose no pixel endpoint; takedown wins over every sealed registry version.
3. **Build the artifact/provider disposition ledger before freeze.** Acceptance: every raw/QA/report/third-party reference has source, owner, policy/evidence, classification and permitted delivery; all unresolved items remain held/link/citation-only.

## 14. Residual process and completion receipt

- Every A6 shell execution cell completed and returned; A6 has no open shell session or task PID.
- A6 did not start Node, Next.js, TypeScript, PostgreSQL, Docker, browser automation, image processing, data generation or server processes.
- The final OS-wide prohibited/residual process scan is owned by the main auditor because A6 did not use or retain a privileged `ps` session.
- A6 modified exactly one file: `docs/audits/v49-pre-migration/06_RIGHTS_AND_VISUAL_FEDERATION.md`.
- No cleanup, deletion, migration, implementation, commit or push was performed.

## 15. Final A6 decision

The repository has credible rights-aware research history and multiple negative-upgrade safeguards, but it does not yet have a normative, machine-enforceable visual federation. The most important correction is not to delete visual complexity or collapse to metadata. It is to preserve research value while making scholarly identity, provider evidence, rights assessment, delivery behavior and endpoint health separately citable and separately governable.

**A6 audit coverage is COMPLETE. A6 package status is FAIL. `RIGHTS_VISUAL_PRE_DDL_READY=false`.**
