# Migration plan: v48 to v49

- Status: Designed, not executed
- Source: immutable v48 candidate freeze
- Target: canonical PostgreSQL plus independent immutable research-release and visual-registry boundaries
- Rollback anchor: exact v48 release and hashes

## Scope boundary

This document is a plan, not a migration receipt. This architecture checkpoint creates no PostgreSQL database, runs no DDL, imports no records, exports no data, edits no v48 artifact, and rewires no visual page.

## Frozen source ledger

The migration begins only after actual bytes match this ledger:

| Artifact | Bytes | Required SHA-256 |
|---|---:|---|
| `generated/public_surfaces_prefreeze_candidate_v48.json` | 190,067,852 | `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48` |
| `data/prefreeze_candidate_v48.sqlite` | 421,801,984 | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` |
| `generated/prefreeze_candidate_v48_transfer_manifest.json` | 21,752 | `865358db84c15d960b3535969a32521c0ffec177f7455d21db86cd131f787d5b` |
| `data/prefreeze_candidate_v48_transfer_manifest.csv` | 12,861 | `694a60657077bcab8888c4a4ef1daf6059706e544606d4862e46c57dcf6ddc18` |
| `frontend/public/data/trace-v48/manifest.json` | 83,900 | `1678e211023aa324078e0478f88670d2378b6dc5c398cc5c04722605038fee23` |

Additional frozen evidence includes the transfer inventory (65 files, 613,077,245 bytes, two LFS objects, zero remote mismatch), SQLite `integrity_check=ok`, 55 PASS/0 HOLD, and the TRACE manifest/assets.

The JSON is the only v48 migration input. SQLite is a read-only reconciliation snapshot and must never be opened in writable mode or allowed to create sidecars. Transfer/TRACE manifests are integrity evidence. Archive Search, atlas/catalogs, and TRACE shards are derived products and may not contribute canonical rows or fill missing JSON fields.

The legacy `public_surface_shards_v1` sidecar is not a frozen release input: it was ignored/untracked while the monolith remained canonical. Migration must not discover or ingest it by directory convention.

## Migration phases

### M0 — Architecture and audit checkpoints

Deliver the normative design corpus and the comprehensive pre-migration audit in an isolated branch/worktree. Confirm source commit ancestry, no v48 or visual diffs, no forbidden processes, and documentation-only commits.

Exit: architecture terms, hard invariants, migration gates, and rollback are approved; every Phase 1B P0 has either been closed normatively or is carried as an explicit DDL-blocking item. No implementation is implied. At the Phase 1B checkpoint, `ENGINEERING_PRE_DDL_READY`, `RESEARCH_SEMANTICS_PRE_DDL_READY`, `RIGHTS_VISUAL_PRE_DDL_READY`, and `OVERALL_PRE_DDL_READY` remain false.

### M1 — Baseline seal

Use pure read-only verifiers to recompute all five hashes, file sizes, SQLite integrity, exact counts/population boundaries, transfer inventory, and all declared TRACE asset hashes. Store a new verification receipt outside frozen paths.

The existing freeze auditor is not a clean-room verifier for this purpose: it expects a v47 intermediate deliberately excluded from the transfer and writes reports into frozen paths. Its saved 55 PASS/0 HOLD receipt remains valid evidence, but cannot be presented as a fresh self-contained rerun from clean `0404c7f`.

Do not run legacy commands that write reports back into v48 or delete/rebuild TRACE output. A verifier may read the source and write only to a fresh temporary/checkpoint-specific receipt path.

Exit: all bytes/counts match or work stops. LFS pointer-only files, mismatch, missing files, or extra undeclared release files fail the phase.

### M2 — PostgreSQL foundation

Create physical migrations for `raw`, `core`, `provenance`, `rights`, `research`, `workflow`, `release`, and `api_v1`. Establish least-privilege roles, append-only/seal controls, migration replay, backup/restore plan, stable ID policy, and registry seeds.

M2 may not begin from the legacy `db/*.sql` chain or `scripts/run_db_migrations.py`: that chain is an 82-table/55-view public-schema prototype with unconstrained polymorphic targets and no v49 role, subtype, seal, or CAS guarantees. It is evidence to classify, not a v49 migration prefix. A future physical-schema task must start from an empty database only after the Phase 1C authority/research and Phase 1D rights/machine packages pass the independent joint pre-DDL verifier; this document itself does not authorize schema execution.

Exit: a fresh empty database replays deterministically and constraint/privilege tests pass. No v48 import yet.

### M3 — Raw staging

Register all five frozen artifacts by path/hash/authority role, but ingest records only from the canonical JSON. Preserve its raw artifact bytes/hash as lexical authority; parsed JSONB is a versioned convenience projection. Record order, JSON Pointer, literal, source locator, and import-run identity make replay idempotent.

Exit: every source item is accounted for, raw counts and aggregate hashes reconcile, and v48 files remain byte-identical. Parse failures are explicit quarantine rows, never dropped records.

### M4 — Canonical normalization

Build operational archive objects, agents, places, concepts, collections, temporal extents, rights representations, provenance assertions, research claims/relations/corpora, and typed joins from governed mapping versions. An archive object is one catalogued design-object record in the governed release cohort; it is not a claim of a unique intellectual work. Preserve raw text and produce a delta ledger for every unresolved or intentionally changed item.

Identity seeding is deterministic and non-deduplicating: each of the 15,923 canonical JSON `surfaceId` rows creates one UUIDv5 archive object plus one primary surface crosswalk. Each links to its unique `sourceRecordId` and unique TRACE root node. Source object keys and TRACE canonical keys are attributes, not unique identifiers.

Multi-value migration is provenance-led:

| Legacy shape | Required behavior |
|---|---|
| creator/medium/object type/subject/collection text | Preserve literal; create ordered typed joins only from a provider mapping or reviewed parse. |
| delimiter-packed branch IDs | Map registered branch tokens to `provenance.capture_branch`; quarantine unknown tokens. |
| folders, related folders, authority references | Build explicit memberships/relations with stable IDs and order. |
| historical nodes, movements, trace trees | Build typed research-node, corpus, classification, and tree memberships; never store queryable lists as canonical JSONB. |
| source statements, scholarly interpretations, computed associations | Build evidence-bearing claims with an epistemic class; semantic relations and TRACE projections are separate rows. |
| images and nested rights | Preserve each raw visual bundle and locator role. Build provenance-occurrence external visual references, the N:M object–visual bridge, provider/provider-object mappings, typed visual locators, rights observations/assessments, provider-policy versions/evaluations, delivery decisions, endpoint-health observations, attribution and typed takedown joins. Unknown, missing, conflicting or stale rights/policy fails closed to `LINK_ONLY` or `CITATION_ONLY`; unresolved provider mapping remains held. |
| review/publication gates | Build versioned workflow gate runs/results, not opaque mutable JSONB. |
| dossiers, page sequences, appendix reasons, registration members | Build ordered child/join tables. |
| compound children | Build typed parent–child object joins. |
| table citation arrays | Build assertion–citation joins with ordinal and role. |

The Phase 1D authoritative visual baseline accounts for all 15,923 candidate surface bundles: 15,788 are reference-bearing, 135 are `NO_VISUAL_REFERENCE`, and the reference-bearing population contains 15,790 typed locator occurrences across four legacy roles. All 15,788 are conservatively `RIGHTS_UNKNOWN`, `POLICY_UNKNOWN`, and `UNMAPPED_PROVIDER`; positive-rights coverage is 0.0000% because no versioned provider policy or governed visual assessment exists in v48. Those unknown states are migration work, not unclassified loss and not permission. Migration must reproduce the committed sequence/set hashes and `UNCLASSIFIED_VISUAL_REFERENCE=0` without URL deduplication or provider inference.

Semicolon incidence is a discovery signal, not a parser. Values such as names, place/date phrases, and physical dimensions can contain semicolons. Silent `split(';')`, loss of order/duplicates, trimming that changes meaning, or manufactured entities fail the phase.

Exit: each mapping has source pointer, cardinality, ordering, duplicate/null policy, normalization rule, provenance target, round-trip query, unresolved policy, and orphan checks. Unresolved values remain proposed assertions in a queued workflow case and create no canonical assignment or publication row.

### M5 — Governance and relation registry

Seed the reviewed relation/predicate registries and rights/provider policies. An accepted semantic relation requires a registered type FK and at least one accepted supporting claim or an evidence-bearing effective curator decision. A claim records exactly one epistemic class: `documented_source_statement`, `scholarly_claim`, `computed_association`, or `causal_interpretation`. Influence claims require claimant, source, locator, and preserved wording; computed associations require analysis run, method, parameters, exact input research release/hash, and score.

TRACE nodes/edges are release projections of accepted semantic relations and claims for one declared corpus; they are not the canonical relation or claim identity. Unknown source labels remain proposed raw assertions in a queued `workflow.relation_type_review_queue` case, without family, semantic relation, claim acceptance, TRACE projection, publication layer, or metric eligibility.

Inject a negative `__unknown_relation__` fixture in the later implementation phase. It must remain raw/queued, leave active/release counts unchanged, and cause any deliberately corrupt release asset to be rejected by the repository.

Exit: zero accepted unregistered relations, zero coercions, zero TRACE projections without an eligible accepted relation/claim, zero non-approved release projections, zero rights widening, and negative fixture isolation passes.

### M6 — v48 parity and delta ledger

Compare canonical/projection queries with frozen v48. Every metric is assigned to one of four non-interchangeable classes:

**Canonical parity**

- 15,923 canonical JSON rows / operational archive objects;
- 7,995 rows with explicit candidate `trace.tier=source_verified`;
- 4,957 rows with missing candidate `trace.tier`, preserved and fail-closed rather than silently normalized;
- 2,971 rows with explicit candidate `trace.tier=metadata_supported`. The candidate row set, immutable SQLite set and TRACE catalog set are identical; the candidate meta scalar 2,970 is retained as a stale aggregate with no competing member set.

**Graph parity**

- 97,889 TRACE projection nodes and 255,695 TRACE projection edges;
- 126,822 active-object relation-membership projections: 79,206 medium/context, 31,288 source/provenance, 16,328 time/place, zero historical influence;
- 30 active research trees and 20 observed relation labels/types in the v48 product.

**Derived reconciliation**

- 12,952 SQLite/TRACE rows normalized to `source_verified` by the legacy accepted-row fallback (= 7,995 explicit candidate rows + 4,957 missing-tier rows); this derived value cannot backfill the canonical tier or establish research eligibility;
- 8,636 archive Search artifact IDs and 15,923 canonical JSON/active TRACE IDs;
- exact population boundary: intersection 2,585, Search-only 6,051, TRACE-only 13,338, union 21,974;
- 4,425 review/authority-hold objects and 11 auxiliary objects, outside the active operational cohort;
- 18 forced LOC repair edges, 200/200 saved audit sample, 55 PASS/0 HOLD;
- 580 TRACE manifest assets, including 576 neighborhood shards, with their declared hashes.

**Historical aspiration**

- 20,000 is a prior capacity/collection aspiration only. Neither “remaining 4,077” nor any future approach to 20,000 is a migration, freeze, release, or promotion condition.

The 6,051 Search-only rows are reconciled as derived-product exclusions and are not imported. A v49 Search projection is generated from the sealed canonical cohort; 8,636 is not a canonical-row or future Search-result parity target.

Exit: exact canonical and graph parity or an explicit, reviewed delta ledger for every difference, plus exact derived-population set reconciliation. The 2,970/2,971 aggregate mismatch is resolved only when the three measured 2,971 member sets remain identical and the stale scalar is retained; it must never be presented as a fabricated one-row symmetric difference. Missing candidate tiers and the inability to regenerate the v48 graph solely from the current canonical JSON remain fail-closed until their explicit ledgers resolve them. Historical aspiration is recorded but never compared as parity. Any unexplained delta prevents promotion; it is not rounded away or relabeled.

### M7 — Immutable research release, visual registry, and read API

Copy research projections from one closed snapshot and advance the research release only through `draft → candidate → validated → sealed`. Candidate closure fixes cohort, corpus, query, relation/predicate registry, claim, projection, and asset fingerprints; validated requires all research pre-seal receipts. Generate canonical research-manifest bytes/SHA, commit them atomically with seal, emit the post-seal detached sidecar, and publish research `current` only by CAS.

Build the visual registry through its independent `draft → candidate → validated → sealed` lifecycle. Its manifest binds external visual references, object-reference bridges, provider objects, typed locators, rights observations/assessments, provider-policy versions/evaluations, delivery decisions, endpoint-health observations, attribution/review due, takedown overlays, and exactly one compatible research pair. It has a distinct manifest SHA, sidecar, and `current` CAS pointer. A visual registry may be superseded for takedown or rights changes without mutating or resealing a research release; a later research-current advance may temporarily leave no compatible visual current, in which case research remains available and every visual locator is omitted.

Exit: deterministic re-export hashes match, both exact identity pairs `(researchReleaseId,researchManifestSha256)` and `(visualRegistryVersion,visualRegistrySha256)` verify, compatibility is explicit, asset/schema IDs verify, API/repository DTO parity passes, performance budgets pass, and corruption/unknown-relation/rights-leakage tests fail closed. Sealed projections never join mutable canonical tables. The public serializer starts from an empty allowlist; a non-`REMOTE_IMAGE` entry contains no pixel, thumbnail or image-service field. v48 directories remain unchanged.

### M8 — Frontend adapter and promotion

Introduce the repository composition root without changing visual semantics. Dual-read comparison captures DTO/count/route parity. Production can pin either an accepted v49 research/visual pair or the untouched v48 rollback adapter; there is no data fallback hidden inside a request.

Only after data and frontend receipts pass may a later promotion lane run full TypeScript, production build, browser/accessibility, and visual regression. Prototype work must not use the full build as a progress gate.

Exit: explicit promotion decision, both exact identity/hash pins, production verification receipt, and tested rollback. No merge/deploy is part of the migration implementation itself unless separately authorized.

## Reconciliation method

Each metric has:

- stable name and human definition;
- unit and layer (`raw`, active, review, auxiliary, graph edge, membership, Search scope);
- source query and query-pack hash;
- v48 expected value;
- v49 actual value;
- expected intentional delta, owner, evidence, and approval;
- blocking severity.

Counts are never compared by similarly worded labels alone. In particular, total graph edges, active-object memberships, archive Search items, and active TRACE objects are different units.

Stable-ID reconciliation emits sets for missing, unexpected, duplicated, remapped, and quarantined IDs. Aggregate parity without ID-set parity is insufficient.

## Rollback and recovery

- v48 bytes remain the immutable rollback anchor for the whole migration.
- No migration deletes or overwrites v48 or a sealed v49 release.
- Before promotion, rollback means keep production pinned to v48.
- After promotion, rollback means atomically pin the previous exact research release and compatible visual-registry descriptor; never mutate either `current` pointer content in place.
- Database rollback restores a tested backup into a new recovery instance and revalidates release identity. It does not reverse-mutate a sealed release.
- A failed candidate stays recorded as workflow evidence and cannot be selected by `current`.

## Explicit stop conditions

Stop and mark the relevant gate `FAIL` for any source hash mismatch, write to frozen paths, missing LFS content, importing SQLite/Search/TRACE-derived rows, silent parse/drop or identity merge, treating an operational archive object as a proven unique intellectual work, collapsing claims/relations/TRACE projections, unknown relation coercion, rights widening, state-axis conflation, arbitrary visual target IDs, unexplained visual input, held-locator serialization, unexplained count/ID drift, use of 20,000 as parity/promotion, non-deterministic release, incomplete research or visual seal/CAS, stale CAS success, sealed projection drift, implicit cross-version fallback, API write path, frontend direct database access, or prototype-only prohibited process during a checkpoint governed by G9.

## Next authorized work packages

At most three independent work packages should follow this checkpoint:

1. Authority/research delta closure: classify every graph fact as regenerable, governed external evidence, or hold; resolve missing builder parents, 2,970/2,971, and raw artifact disposition. No DDL or derived-row ingestion.
2. Rights visual-registry decision completion: provider/object/endpoint crosswalk, policy/observation/attribution/review/takedown mapping, held-pixel rules, and dual-version seal/CAS test specification. No image download or frontend change.
3. Fresh physical-schema specification and privilege test plan: only after packages 1–2 pass, map typed FKs/natural keys/roles/dual seals from an empty namespace and execution-deny the legacy runner. Authorization to write DDL requires a new explicit gate receipt; this package itself does not import data.
