# Migration plan: v48 to v49

- Status: Designed, not executed
- Source: immutable v48 candidate freeze
- Target: canonical PostgreSQL plus immutable release/API boundary
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

Additional frozen evidence includes the transfer inventory (65 files, 613,077,245 bytes, two LFS objects, zero remote mismatch), SQLite `integrity_check=ok`, 55 PASS/0 HOLD, and the TRACE manifest/assets.

The JSON remains canonical for v48. SQLite is a read-only query snapshot used for reconciliation and must never be opened in writable mode or allowed to create sidecars.

The legacy `public_surface_shards_v1` sidecar is not a frozen release input: it was ignored/untracked while the monolith remained canonical. Migration must not discover or ingest it by directory convention.

## Migration phases

### M0 — Architecture checkpoint

Deliver the eight design documents in an isolated branch/worktree. Confirm source commit ancestry, no v48 or visual diffs, no forbidden processes, and one local documentation commit.

Exit: architecture terms, hard invariants, migration gates, and rollback are approved. No implementation is implied.

### M1 — Baseline seal

Use pure read-only verifiers to recompute the four official hashes, file sizes, SQLite integrity, exact counts, transfer inventory, and all declared TRACE asset hashes. Store a new verification receipt outside frozen paths.

The existing freeze auditor is not a clean-room verifier for this purpose: it expects a v47 intermediate deliberately excluded from the transfer and writes reports into frozen paths. Its saved 55 PASS/0 HOLD receipt remains valid evidence, but cannot be presented as a fresh self-contained rerun from clean `0404c7f`.

Do not run legacy commands that write reports back into v48 or delete/rebuild TRACE output. A verifier may read the source and write only to a fresh temporary/checkpoint-specific receipt path.

Exit: all bytes/counts match or work stops. LFS pointer-only files, mismatch, missing files, or extra undeclared release files fail the phase.

### M2 — PostgreSQL foundation

Create physical migrations for `raw`, `core`, `provenance`, `rights`, `research`, `workflow`, `release`, and `api_v1`. Establish least-privilege roles, append-only/seal controls, migration replay, backup/restore plan, stable ID policy, and registry seeds.

Exit: a fresh empty database replays deterministically and constraint/privilege tests pass. No v48 import yet.

### M3 — Raw staging

Register frozen artifacts by path/hash and ingest their records into append-only raw tables with record order, JSON pointer/column, literal, source locator, and import-run identity. Re-running the same import is idempotent.

Exit: every source item is accounted for, raw counts and aggregate hashes reconcile, and v48 files remain byte-identical. Parse failures are explicit quarantine rows, never dropped records.

### M4 — Canonical normalization

Build objects, agents, places, concepts, collections, temporal extents, rights representations, provenance assertions, and research joins from governed mapping versions. Preserve raw text and produce a delta ledger for every unresolved or intentionally changed item.

Multi-value migration is provenance-led:

| Legacy shape | Required behavior |
|---|---|
| creator/medium/object type/subject/collection text | Preserve literal; create ordered typed joins only from a provider mapping or reviewed parse. |
| delimiter-packed branch IDs | Map registered branch tokens to `provenance.capture_branch`; quarantine unknown tokens. |
| folders, related folders, authority references | Build explicit memberships/relations with stable IDs and order. |
| historical nodes, movements, trace trees | Build typed classification/tree memberships; never store queryable lists as canonical JSONB. |
| images and nested rights | Build representation and rights-policy joins; unknown permission fails closed. |
| review/publication gates | Build versioned workflow gate runs/results, not opaque mutable JSONB. |
| dossiers, page sequences, appendix reasons, registration members | Build ordered child/join tables. |
| compound children | Build typed parent–child object joins. |
| table citation arrays | Build assertion–citation joins with ordinal and role. |

Semicolon incidence is a discovery signal, not a parser. Values such as names, place/date phrases, and physical dimensions can contain semicolons. Silent `split(';')`, loss of order/duplicates, trimming that changes meaning, or manufactured entities fail the phase.

Exit: each mapping has source pointer, cardinality, ordering, duplicate/null policy, normalization rule, provenance target, round-trip query, unresolved policy, and orphan checks. Unresolved rows remain held and cannot publish.

### M5 — Governance and relation registry

Seed the reviewed relation registry and rights policy. Canonical edges require a registered type FK and accepted evidence. Unknown source labels go only to `workflow.relation_type_review_queue` as `held`, without family and with `count_eligible=false`.

Inject a negative `__unknown_relation__` fixture. It must remain raw/held, leave active/release counts unchanged, and cause any deliberately corrupt release asset to be rejected by the repository.

Exit: zero accepted unregistered edges, zero coercions, zero non-approved release edges, zero rights widening, and negative fixture isolation passes.

### M6 — v48 parity and delta ledger

Compare canonical/projection queries with frozen v48. Exact baseline units include:

- 15,923 active objects; 4,077 remaining to the 20,000 capacity target;
- 97,889 TRACE nodes and 255,695 total graph edges;
- 126,822 active-object relation memberships: 79,206 medium/context, 31,288 source/provenance, 16,328 time/place, zero historical influence;
- 30 active trees;
- 12,952 source verified and 2,971 metadata supported;
- 4,425 review/authority hold and 11 auxiliary objects, excluded from active counts;
- 8,636 archive Search artifact items and 15,923 active TRACE catalog items, recorded as different scopes;
- 18 forced LOC repair edges, 200/200 saved audit sample, 55 PASS/0 HOLD.

Exit: exact parity or an explicit, reviewed delta ledger for every difference. Any unresolved delta prevents promotion; it is not rounded away or relabeled.

### M7 — Immutable candidate release and read API

Materialize `api_v1`, generate a new release-scoped manifest and deterministic shards in a fresh destination, verify exact declared file set plus detached manifest hash, and run the same repository contract suite against API, immutable release, and fixture adapters.

Exit: deterministic re-export hashes match, asset/schema/release IDs verify, API/repository DTO parity passes, performance budgets pass, and corruption/unknown-relation tests fail closed. v48 directories remain unchanged.

### M8 — Frontend adapter and promotion

Introduce the repository composition root without changing visual semantics. Dual-read comparison captures DTO/count/route parity. Production can pin either the accepted v49 release or the untouched v48 rollback adapter; there is no data fallback hidden inside a request.

Only after data and frontend receipts pass may a later promotion lane run full TypeScript, production build, browser/accessibility, and visual regression. Prototype work must not use the full build as a progress gate.

Exit: explicit promotion decision, release/manifest pin, production verification receipt, and tested rollback. No merge/deploy is part of the migration implementation itself unless separately authorized.

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
- After promotion, rollback means atomically pin the previous exact release descriptor/adapter; never mutate `current` content in place.
- Database rollback restores a tested backup into a new recovery instance and revalidates release identity. It does not reverse-mutate a sealed release.
- A failed candidate stays recorded as workflow evidence and cannot be selected by `current`.

## Explicit stop conditions

Stop and mark the relevant gate `FAIL` for any source hash mismatch, write to frozen paths, missing LFS content, silent parse/drop, unknown relation coercion, rights widening, active/review/auxiliary leakage, unexplained count/ID drift, non-deterministic release, cross-release asset reference, API write path, frontend direct database access, or prototype full build.

## Next implementation work packages

At most three independent work packages should follow this checkpoint:

1. Physical schema and pure baseline verifier: migrations/roles/constraints plus a read-only v48 receipt, with no record import.
2. Mapping specification and fixture: field-level mapping ledger, relation registry, small contract fixture, and negative fail-closed cases, with no production data cutover.
3. Repository/API contract skeleton and CI split: interfaces, DTO schemas, adapter contract tests, and separate workflow definitions, with no visual-page rewrite or full prototype build.
