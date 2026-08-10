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
- source commit `0404c7f96f9189f576c4c5b1368061e4082e436b` is an ancestor of final HEAD;
- source remote ref resolves to that exact commit at recovery time;
- dirty-main tracked/untracked baseline fingerprints are unchanged after work;
- final worktree is clean after one local architecture commit.

Any edit to the dirty main or wrong source commit is FAIL.

## G1 — v48 frozen byte integrity

PASS requires actual read-only recomputation, not receipt citation alone:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Candidate JSON | 190,067,852 | `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48` |
| SQLite snapshot | 421,801,984 | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` |
| Transfer manifest JSON | 21,752 | `865358db84c15d960b3535969a32521c0ffec177f7455d21db86cd131f787d5b` |
| Transfer manifest CSV | 12,861 | `694a60657077bcab8888c4a4ef1daf6059706e544606d4862e46c57dcf6ddc18` |

Also required: SQLite `integrity_check=ok`, no source modification, and LFS content present rather than pointer text. Citation-only verification is PARTIAL. Any mismatch or write is FAIL.

## G2 — Exact frozen counts and units

PASS requires independently named exact values:

| Unit | Expected |
|---|---:|
| Active objects | 15,923 |
| Remaining to 20,000 | 4,077 |
| TRACE nodes | 97,889 |
| Total graph edges | 255,695 |
| Active-object relation memberships | 126,822 |
| Medium/context memberships | 79,206 |
| Source/provenance memberships | 31,288 |
| Time/place memberships | 16,328 |
| Historical influence memberships | 0 |
| Active research trees | 30 |
| Published relation types | 20 |
| Source verified | 12,952 |
| Metadata supported | 2,971 |
| Review/authority hold | 4,425 |
| Auxiliary | 11 |
| Archive Search artifact items | 8,636 |
| Active TRACE catalog items | 15,923 |
| Saved audit sample | 200 / 200 pass |
| Freeze gates | 55 PASS / 0 HOLD |

TRACE manifest must have observed SHA-256 `1678e211023aa324078e0478f88670d2378b6dc5c398cc5c04722605038fee23` and declare 580 hashed assets, including 576 neighborhood shards, with zero declared hash failures. Total graph edges and memberships, or archive Search and TRACE objects, must not be conflated. Receipt/manifest evidence without future Postgres parity is PASS for recovery but PARTIAL for migration parity. Any unexplained mismatch or unit relabeling is FAIL.

## G3 — Architecture checkpoint scope

PASS requires exactly the requested architecture documents as the only checkpoint changes:

- `ARCHITECTURE.md`
- `docs/adr/0001-canonical-postgres-and-read-only-release.md`
- `docs/adr/0002-immutable-data-versioning.md`
- `docs/adr/0003-runtime-repository-and-fixture-mode.md`
- `DATA_MODEL_V49.md`
- `READ_API_V1.md`
- `MIGRATION_V48_TO_V49.md`
- `ACCEPTANCE_GATES.md`

They must consistently define all eight layers, read-only v48, PostgreSQL authority timing, immutable releases, repository/API boundary, fail-closed relations, migration mapping, CI split, and prototype restrictions. Missing hard invariants are PARTIAL; changes to v48 or visual code are FAIL.

## G4 — Canonical data model and normalization

Architecture PASS requires a complete logical mapping inventory, raw-literal preservation, provenance pointers, join cardinality/order/duplicate/null/unresolved policies, and JSONB limits.

Migration PASS later requires lossless raw round-trip, zero orphan joins, accepted joins backed by assertions/decisions, and an explicit quarantine/delta ledger. A reliable held queue with no release leakage is PARTIAL until resolved. Silent delimiter splitting, dropped values/order/duplicates, or opaque canonical JSONB relations are FAIL.

## G5 — Unknown relation fail-closed

Architecture PASS requires:

- one publishable `research.relation_type` registry;
- mandatory FK from canonical accepted edge;
- unmapped labels retained raw and routed to `workflow.relation_type_review_queue`;
- `held`, `count_eligible=false`, no assigned fallback family;
- release/API exclude unknown/non-approved relations;
- registry digest pinned in manifest;
- repository returns integrity error on corrupt release data.

Implementation PASS later requires zero accepted unregistered edges, zero coercions, zero non-approved release edges, and a passing `__unknown_relation__` negative fixture. Design without implementation is PARTIAL for the implementation gate. Any fallback to `medium_context/documented` or release leakage is FAIL.

## G6 — `ArchiveRepository` and Read API v1

Architecture PASS requires a release-bound async contract, three adapters (`Http`, immutable release, fixture), stable DTOs, keyset pagination, typed results/errors, exact release metadata, schema validation, cache/deduplication/cancellation responsibilities, and read-only release-pinned endpoints.

Implementation PASS later requires one shared conformance suite across all adapters and no UI storage knowledge. Interface-only work is PARTIAL for implementation. Direct PostgreSQL/browser credentials, direct full dump/SQLite imports, component shard decoders/paths, implicit mock fallback, or write endpoints are FAIL.

## G7 — Immutable manifest and shards

Architecture PASS requires canonical manifest rules, detached hash, exact file inventory, source/database/query/registry lineage, per-asset schema/bytes/records/hash/partition, self-identifying shard envelope, deterministic ordering, seal controls, and fail-closed validation.

Implementation PASS later requires repeat export byte equality, actual directory set equality (declared assets plus manifest/receipt only), all hashes/schema/release IDs verified, no cross-release references, and corruption tests. Format design without generated artifact is PARTIAL for implementation. Overwriting a version, mutable-only `current`, missing hashes, undeclared files, or fallback after corruption is FAIL.

## G8 — Data CI / frontend CI separation

Architecture PASS requires two independent workflows:

- data CI owns schema, imports, lineage, rights/research/workflow gates, reconciliation, release generation, and data receipt; it never runs Next;
- frontend CI consumes only a pinned contract/fixture/release, owns repository and focused UI contract tests, and never connects to canonical PostgreSQL or generates data;
- promotion later consumes both receipts without merging their dependency/cache/artifact boundaries.

Documented separation with no workflows yet is PARTIAL for CI implementation. A shared job that lets data mutate frontend output, or frontend access the live canonical database, is FAIL.

## G9 — Prototype process prohibition

PASS for architecture/prototype requires that none of these are run as acceptance steps:

- `npm install`;
- `next dev` or any server;
- `next build` or full static generation;
- full-project TypeScript/`tsc`;
- browser automation or manual browser launch;
- data export or regeneration.

Allowed work is documentation, read-only Git/file/hash/SQLite inspection, fixture/schema design, and later focused repository/unit/contract tests. Running a prohibited process during the prototype gate is FAIL. Full build/browser validation remains PARTIAL until a separately authorized promotion phase.

## G10 — Migration parity and promotion

PASS later requires M1–M8 receipts, exact or approved delta-ledger parity, rights non-widening, unknown-relation closure, deterministic sealed release, API/repository parity, independent CI receipts, full promotion-only TypeScript/build/browser/visual checks, and tested rollback.

Architecture-only completion is PARTIAL for this gate. Promotion with any held blocker, unexplained delta, missing receipt, or no rollback is FAIL.

## G11 — Residual process and local checkpoint receipt

PASS requires:

- no server, build, compiler, browser automation, data generator/export, or package installer process started by this work remains alive;
- final receipt reports worktree, branch, final HEAD, source ancestor, changed files, local commit, frozen hashes, main baseline comparison, and each gate result;
- no PR, merge, push, or deployment occurred.

Unknown residual state is PARTIAL. A prohibited residual process or unreported external mutation is FAIL.

## Promotion rule

Architecture completion may be accepted with G0–G3, architecture portions of G4–G8, G9, and G11 passing while implementation portions and G10 remain PARTIAL. No data/frontend promotion occurs until every implementation and promotion gate is PASS; any FAIL blocks promotion immediately.
