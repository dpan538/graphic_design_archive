# v49 acceptance gates

- Status: Normative gate specification for architecture, migration, release, and promotion
- Result vocabulary: `PASS`, `PARTIAL`, `FAIL` only

## Result semantics

- `PASS`: every required assertion for the stated gate and phase has current evidence.
- `PARTIAL`: design or safe isolation exists, but implementation/runtime evidence is intentionally pending. A `PARTIAL` gate never authorizes promotion.
- `FAIL`: an invariant was violated, evidence mismatched, or a prohibited action occurred. Work stops until a new, explicit recovery plan is approved.

Out-of-scope future implementation is reported as `PARTIAL`, not disguised as `PASS`. Conversely, intentionally not performing a prohibited action is `PASS` for the architecture/prototype gate.

## G0 — Worktree and source recovery

PASS requires:

- long-term worktree is not the dirty main worktree;
- branch is `refactor/v49-data-platform`;
- source commit `0404c7f96f9189f576c4c5b1368061e4082e436b` is an ancestor of final HEAD and its recovery ref resolves exactly;
- the phase-defined baseline commit matches local HEAD and the working-branch remote before edits;
- dirty-main tracked/untracked baseline fingerprints are unchanged after work;
- final worktree is clean after no more than the phase-authorized commit budget (two documentation commits in Phase 1B);
- when an ordinary push is required, the working-branch remote SHA is verified equal to final HEAD.

Any edit to the dirty main or wrong source commit is FAIL.

## G1 — v48 frozen byte integrity

PASS requires actual read-only recomputation, not receipt citation alone:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Candidate JSON | 190,067,852 | `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48` |
| SQLite snapshot | 421,801,984 | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` |
| Transfer manifest JSON | 21,752 | `865358db84c15d960b3535969a32521c0ffec177f7455d21db86cd131f787d5b` |
| Transfer manifest CSV | 12,861 | `694a60657077bcab8888c4a4ef1daf6059706e544606d4862e46c57dcf6ddc18` |
| TRACE manifest | 83,900 | `1678e211023aa324078e0478f88670d2378b6dc5c398cc5c04722605038fee23` |

All five must be recomputed from actual bytes. Also required: SQLite `integrity_check=ok`, no source modification, and LFS content present rather than pointer text. Candidate JSON is the only migration input; SQLite is reconciliation-only; manifests are integrity evidence. Citation-only verification is PARTIAL. Any mismatch or write is FAIL.

## G2 — Exact frozen counts and units

PASS requires independently named exact values in four non-interchangeable classes. Historical aspiration is recorded for context but is never parity.

### Canonical parity

| Unit | Expected |
|---|---:|
| Operational archive objects / canonical JSON rows | 15,923 |
| Source verified | 12,952 |
| Metadata supported, row-level | 2,971 |
| Metadata supported, manifest/meta declaration | 2,970 (known one-row conflict; blocking until explained) |

### Graph parity

| Unit | Expected |
|---|---:|
| TRACE projection nodes | 97,889 |
| TRACE projection edges | 255,695 |
| Active-object relation-membership projections | 126,822 |
| Medium/context memberships | 79,206 |
| Source/provenance memberships | 31,288 |
| Time/place memberships | 16,328 |
| Historical influence memberships | 0 |
| Active research trees | 30 |
| Observed relation labels/types | 20 |

### Derived reconciliation

| Unit | Expected |
|---|---:|
| Archive Search artifact items | 8,636 |
| Active TRACE catalog items | 15,923 |
| Search ∩ canonical/TRACE IDs | 2,585 |
| Search-only IDs | 6,051 |
| Canonical/TRACE-only IDs | 13,338 |
| Search ∪ canonical/TRACE IDs | 21,974 |
| Review/authority hold objects | 4,425 |
| Auxiliary objects | 11 |
| Saved audit sample | 200 / 200 pass |
| Freeze gates | 55 PASS / 0 HOLD |

TRACE manifest must declare 580 hashed assets, including 576 neighborhood shards, with zero declared hash failures. Search IDs must equal the legacy frontend mock set; canonical JSON IDs must equal the active TRACE catalog set. Search-only derived rows are not migration input. TRACE projection edges and memberships, or archive Search and TRACE populations, must not be conflated.

### Historical aspiration

The former 20,000 target and derived “remaining 4,077” value are collection/capacity history only. They are excluded from migration parity, release validation, freeze, and promotion. Making either value a gate is FAIL.

Receipt/manifest evidence without future PostgreSQL parity is PASS for recovery but PARTIAL for migration parity. The 2,970/2,971 evidence conflict must remain explicit in the delta ledger. Any other unexplained mismatch, silent normalization of that conflict, or unit relabeling is FAIL.

## G3 — Architecture checkpoint scope

PASS requires the normative architecture corpus and only authorized documentation changes:

- `ARCHITECTURE.md`
- `docs/adr/0001-canonical-postgres-and-read-only-release.md`
- `docs/adr/0002-immutable-data-versioning.md`
- `docs/adr/0003-runtime-repository-and-fixture-mode.md`
- `DATA_MODEL_V49.md`
- `READ_API_V1.md`
- `MIGRATION_V48_TO_V49.md`
- `ACCEPTANCE_GATES.md`
- `docs/architecture/DDL_DECISION_PACK_V49.md`
- `docs/adr/0004-research-claims-corpora-and-visual-registry.md`

They must consistently define all eight layers, artifact authority, operational archive-object semantics, entity/identity/cardinality, typed FKs, assertion/evidence/decision joins, semantic relation/claim/TRACE separation, epistemic classes, corpus/missingness, independent research-release and visual-registry identities, orthogonal states, immutable seal/CAS, role privileges, repository/API boundary, fail-closed relations and rights, migration mapping, CI split, and phase-scoped prototype restrictions. Missing P0 invariants are PARTIAL; changes to v48 or visual code are FAIL.

## G4 — Canonical data model and normalization

Architecture PASS requires a complete identity/cardinality and mapping inventory, operational archive-object semantics, raw-byte/literal authority, provenance pointers, real FKs, join cardinality/order/duplicate/null/unresolved policies, a closed assertion predicate registry and assignment subtype list, epistemic claim classes, corpus/missingness records, and JSONB limits. A v48 archive object denotes one catalogued design-object record in the governed cohort, not a proven unique intellectual work.

Migration PASS later requires lossless raw accounting, zero orphan joins, accepted joins backed by assertions/decisions, accepted semantic relations backed by qualifying claims/evidence, and an explicit quarantine/delta ledger. Unresolved literals/assertions may remain `proposed` in a fully accounted workflow queue and G4 can still PASS when no canonical assignment, semantic relation, TRACE projection, or release row exists for them. PARTIAL means accounting, provenance, or isolation is incomplete—not merely that the queue is non-empty. Silent delimiter splitting, dropped values/order/duplicates, unconstrained polymorphic IDs, treating TRACE projection identity as relation/claim identity, or opaque canonical JSONB relations are FAIL.

## G5 — Unknown relation fail-closed

Architecture PASS requires:

- one publishable `research.relation_type` registry;
- mandatory FK from an accepted semantic relation;
- unmapped labels retained as proposed raw assertions and routed to a queued `workflow.relation_type_review_queue` case;
- no semantic relation, claim acceptance, assigned fallback family, TRACE projection, publication-layer row, or metric-eligibility row;
- release/API exclude unknown/non-approved relations;
- registry digest pinned in manifest;
- repository returns integrity error on corrupt release data.

Implementation PASS later requires zero canonical unregistered relations, zero coercions, zero TRACE projections of non-approved relations/claims, and a passing `__unknown_relation__` negative fixture. A non-empty raw/workflow unknown queue is compatible with G5 PASS when isolation is complete; release completeness/promotion policy is evaluated in G10. Design without implementation is PARTIAL for the implementation gate. Any fallback to `medium_context/documented`, manufactured `documented_source_statement`, or release leakage is FAIL.

## G6 — `ArchiveRepository` and Read API v1

Architecture PASS requires an exact-pair-bound async contract, three adapters (`Http`, immutable release, fixture), stable DTOs, keyset pagination, typed results/errors, exact `(researchReleaseId,researchManifestSha256)` and `(visualRegistryVersion,registrySha256)` metadata, declared compatibility, schema validation, cache/deduplication/cancellation responsibilities, and GET-only pair-pinned endpoints.

Implementation PASS later requires one shared conformance suite across all adapters and no UI storage knowledge. Interface-only work is PARTIAL for implementation. Direct PostgreSQL/browser credentials, direct full dump/SQLite imports, component shard decoders/paths, implicit mock fallback, or write endpoints are FAIL.

## G7 — Immutable manifests, shards, and seal protocols

Architecture PASS requires canonical manifest rules for both the research release and visual registry, distinct detached hashes and `current` pointers, exact file inventories, source/database/query/registry lineage, explicit cross-version compatibility, per-asset schema/bytes/records/hash/partition, self-identifying shard envelopes, deterministic ordering, and this seal protocol independently for each boundary:

- only `draft → candidate → validated → sealed` forward transitions;
- candidate closure fixes snapshot/cohort/corpus/query/registry/claim/projection/asset fingerprints for research, or provider/endpoint/rights/policy/delivery/health/takedown/asset fingerprints for visual;
- validated requires immutable passing pre-seal receipts bound to that fingerprint;
- canonical manifest bytes and SHA are committed atomically with `validated → sealed`;
- detached post-seal sidecar records the manifest SHA and seal transaction without changing manifest inventory;
- a verified post-seal sidecar is required before pointer eligibility, and each `current` changes only by CAS to its own exact sealed identity/hash pair;
- candidate/sealed projections are copied rows and never drift through joins to mutable canonical tables.

Implementation PASS later requires repeat export byte equality, actual directory set equality (declared assets plus manifest/receipt only), all hashes/schema/identity pairs verified, no undeclared cross-version reference, sealed-projection drift checks, compatibility checks, and corruption tests. Format design without generated artifact is PARTIAL for implementation. Overwriting a version, coupling a visual takedown to research resealing, mutable-only `current`, missing hashes, undeclared files, or fallback after corruption is FAIL.

## G8 — Data CI / frontend CI separation

Architecture PASS requires two independent workflows:

- data CI owns schema, imports, lineage, rights/research/workflow gates, reconciliation, release generation, and data receipt; it never runs Next;
- frontend CI consumes only a pinned contract/fixture/release, owns repository and focused UI contract tests, and never connects to canonical PostgreSQL or generates data;
- promotion later consumes both receipts without merging their dependency/cache/artifact boundaries.

Documented separation with no workflows yet is PARTIAL for CI implementation. A shared job that lets data mutate frontend output, or frontend access the live canonical database, is FAIL.

## G9 — Prototype/checkpoint process prohibition

G9 applies only to an architecture, recovery, or prototype checkpoint whose task explicitly invokes it. It is not a permanent ban on authorized migration CI, release validation, or production promotion. For an in-scope checkpoint, PASS requires that none of these are run as acceptance steps:

- `npm install`;
- `next dev` or any server;
- `next build` or full static generation;
- full-project TypeScript/`tsc`;
- browser automation or manual browser launch;
- data export or regeneration.

Allowed work is the scope explicitly named by that checkpoint. Running a prohibited process during an in-scope G9 checkpoint is FAIL. A later phase does not become PARTIAL merely because it legitimately follows its own command matrix; production promotion may explicitly require full build/browser validation.

## G10 — Migration parity and promotion

PASS later requires M1–M8 receipts, exact or approved delta-ledger parity by canonical/graph/derived unit, rights non-widening, unknown-relation closure, deterministic sealed research release and compatible sealed visual registry, API/repository parity, independent CI receipts, full promotion-only TypeScript/build/browser/visual checks, and tested rollback.

Architecture-only completion is PARTIAL for this gate. Promotion with any item explicitly designated promotion-blocking, unexplained delta, missing receipt, or no rollback is FAIL. A fully isolated non-blocking raw/workflow queue does not fail G4/G5 by existence alone.

## G11 — Residual process and local checkpoint receipt

PASS requires:

- no server, build, compiler, browser automation, data generator/export, or package installer process started by this work remains alive;
- final receipt reports worktree, branch, final HEAD, source ancestor, changed files, local commit, frozen hashes, main baseline comparison, and each gate result;
- no PR, merge, force push, or deployment occurred; an ordinary push is allowed only when the checkpoint explicitly requires it and the remote SHA is then verified.

Unknown residual state is PARTIAL. A prohibited residual process or unreported external mutation is FAIL.

## G12 — Repository hygiene and cleanup authority

Architecture/audit PASS requires a repository-wide inventory with every tracked, ignored, and in-scope untracked path classified as `KEEP_ACTIVE`, `MIGRATE`, `ARCHIVE_READ_ONLY`, `GENERATED_REPRODUCIBLE`, `DELETE_CANDIDATE`, or `HOLD_UNKNOWN`; large/LFS/duplicate/generated evidence; owner/source/authority/recovery/action/risk fields; and proof that protected dirty main and frozen data were not changed.

Implementation PASS later requires approved cleanup receipts, license/third-party disposition, no unexplained generated artifact in Git, no unresolved public-repository secret exposure, and no deletion without a recovery reference. A delete-candidate ledger alone is PARTIAL for cleanup execution but PASS for Phase 1B classification. Unclassified assets, destructive cleanup, or cleanup of protected/frozen paths is FAIL.

## G13 — Research and data-quality freeze

PASS later requires:

- a versioned corpus with inclusion/exclusion policy, selection rationale, missingness categories, coverage metrics, and source-concentration receipt;
- claims separated into `documented_source_statement`, `scholarly_claim`, `computed_association`, and `causal_interpretation`;
- influence provenance with claimant, source, locator, and preserved wording;
- computed-association provenance with analysis run, method, parameters, exact input release/hash, and score;
- relation/claim identity separate from TRACE projection identity;
- exact canonical/graph/derived reconciliation and reviewed handling of the 2,970/2,971 conflict and graph-regeneration gap.

Design without implemented data/receipts is PARTIAL. Calling the full 15,923 Browse Index a strict research corpus without policy, presenting a computed edge as a documented fact, or using size/visual complexity as a deletion criterion is FAIL.

## G14 — Machine-readable publication contract

Architecture PASS requires stable object/relation/claim URIs; server-rendered crawlable HTML and canonical URLs; JSON Schema for manifests, shards, API DTOs, and errors; JSON-LD alternates with Linked Art/PROV-O mappings; a DCAT release catalog; GET-only version-pinned API; release diff/change feed; sitemap/robots policy; and explicit non-disclosure of rights-held or link-only pixel URLs.

Implementation PASS later requires contract/schema validation, content negotiation/link headers, URI persistence/redirect tests, crawlability tests, diff determinism, and rights-leakage negative tests against both exact version pairs. Documentation-only design is PARTIAL. A write endpoint in `/api/v1`, unstable relation/claim identity, client-only canonical content, or held-pixel leakage is FAIL.

## G15 — Rights-aware visual federation

Architecture PASS requires an independent sealed visual registry with `(visualRegistryVersion,registrySha256)`, its own manifest/sidecar/current-pointer CAS, declared compatibility with exact research releases, typed provider object and IIIF endpoint identities, and separate axes for rights assessment, delivery mode, and endpoint health. Rights observations, provider policies, attribution/required statement, review due, and takedown overrides are versioned evidence.

Implementation PASS later requires default `LINK_ONLY` or `CITATION_ONLY` for unknown/missing/conflicting/stale evidence, zero widening from endpoint accessibility or IIIF availability, no remote/proxied pixel URL in held machine/UI projections, verified attribution, takedown override precedence, and registry-current CAS tests. Design without registry data and tests is PARTIAL. Treating HTTP success, API access, IIIF, redirect, or provider ownership as image authorization is FAIL.

## Promotion rule

Architecture completion may be accepted with G0–G3, architecture portions of G4–G8 and G12–G15, G9, and G11 passing while implementation portions and G10 remain PARTIAL. Phase 1B audit completion does not imply pre-DDL readiness: `ENGINEERING_PRE_DDL_READY`, `RESEARCH_SEMANTICS_PRE_DDL_READY`, `RIGHTS_VISUAL_PRE_DDL_READY`, and `OVERALL_PRE_DDL_READY` are independently evaluated. No database, freeze, frontend promotion, or deployment occurs until its complete gate set is PASS; any applicable FAIL blocks immediately.
