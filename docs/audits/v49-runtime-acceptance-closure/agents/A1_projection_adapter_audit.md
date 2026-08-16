# A1 — projection and PostgreSQL-adapter audit

**Audit scope:** read-only inspection of source commit `64de7ab1ccc190b433266e3a793b9ff7d4c06016` (`docs: checkpoint v49 runtime acceptance evidence`). This report does not assert a database replay, TypeScript check, runtime vector, browser run, fixture generation, or production connection.

## Conclusion

**Closure is not ready for a sealed-release runtime claim.** The source has useful independent research/visual lifecycles, copied release tables, fingerprinting, serializable seal functions, mutation guards, and a narrow exact-pair read view. Those controls are not yet an end-to-end, snapshot-consistent release-projection builder or a complete PostgreSQL `ArchiveRepository`.

Most importantly, a sealed projection cannot currently be *built without mutable canonical reads*. Draft-copy functions read `core`, `research`, `rights`, `raw`, and `provenance`; draft construction has no enforced single immutable input snapshot; and candidate/validation logic re-reads those live source tables. After a release is sealed, the implemented `api_v1` views read release tables rather than canonical tables, but that is only a narrow read-path property, not proof of a reproducible construction boundary.

## Inspected evidence and commands

Commands were inspection-only, run against `/Users/jarlgiovanni/Desktop/modern_GD_history` unless noted:

```text
git show -s --format='%H%n%s%n%ci' 64de7ab
git ls-tree -r --name-only 64de7ab database
git ls-tree -r --name-only 64de7ab db
git show 64de7ab:DATA_MODEL_V49.md
git show 64de7ab:MIGRATION_V48_TO_V49.md
git show 64de7ab:ACCEPTANCE_GATES.md
git show 64de7ab:READ_API_V1.md
git show 64de7ab:docs/adr/0001-canonical-postgres-and-read-only-release.md
git show 64de7ab:docs/architecture/DDL_DECISION_PACK_V49.md
git show 64de7ab:database/migrations/004_release_audit.sql
git show 64de7ab:database/migrations/007_release_copy_integrity.sql
git show 64de7ab:database/migrations/008_final_integrity_closure.sql
git show 64de7ab:database/migrations/009_read_api_core.sql
git show 64de7ab:database/functions/005_projection_builders.sql
git show 64de7ab:database/functions/007_release_protocol_closure.sql
git show 64de7ab:database/functions/008_projection_builders_v2.sql
git show 64de7ab:database/functions/009_projection_inventory_builders.sql
git show 64de7ab:database/functions/010_visual_inventory_builders.sql
git show 64de7ab:database/functions/014_release_copy_guards.sql
git show 64de7ab:database/scripts/replay.sh
git show 64de7ab:database/schema-manifest.json
git show 64de7ab:database/roles/003_read_api_core_grants.sql
git show 64de7ab:frontend/src/lib/read-platform/server/postgres-repository.ts
git show 64de7ab:frontend/src/lib/read-platform/server/provider.ts
git show 64de7ab:frontend/src/lib/read-platform/server/open-read-repository.ts
git show 64de7ab:frontend/src/lib/read-platform/server/fixture.ts
git show 64de7ab:frontend/src/lib/read-platform/http-repository.ts
git show '64de7ab:frontend/src/app/api/v1/[...path]/route.ts'
git show 64de7ab:frontend/scripts/run-runtime-acceptance-vectors.mjs
git show 64de7ab:docs/audits/v49-runtime-acceptance/00_EXECUTIVE_RECEIPT.md
git show 64de7ab:docs/audits/v49-runtime-acceptance/04_ADAPTER_VECTOR_RECEIPT.md
git worktree list --porcelain
```

No `npm`, Next, `tsc`, PostgreSQL, browser, or generator command was run.

## Existing capabilities confirmed

- `release.research_release` and `release.visual_registry_release` have distinct `draft → candidate → validated → sealed` state shapes in [004_release_audit.sql](../../../../database/migrations/004_release_audit.sql); both have separate manifests, verification rows, and current pointers.
- [007_release_protocol_closure.sql](../../../../database/functions/007_release_protocol_closure.sql) requires serializable transactions for the actual seal operations and builds each manifest from the corresponding release inventory. [002_mutation_guards.sql](../../../../database/functions/002_mutation_guards.sql) guards sealed parents and children.
- Research/visual rows are copied into `release.*` inventory tables, including release objects, claims, relations, trace projections, folders, visual entries, public locators, and takedown snapshots. [009_read_api_core.sql](../../../../database/migrations/009_read_api_core.sql) reads only `release.*` for its two implemented `api_v1` views.
- The visual copy path checks accepted bridge and delivery data and limits copied locators by delivery mode; it is a sound starting point for rights-safe projection construction. See [010_visual_inventory_builders.sql](../../../../database/functions/010_visual_inventory_builders.sql).

## Findings

### P0 — Release construction is not snapshot-sealed from immutable inputs

`release.add_research_object_to_draft`, claim/relation/node builders, and visual-entry builders in [005_projection_builders.sql](../../../../database/functions/005_projection_builders.sql), [008_projection_builders_v2.sql](../../../../database/functions/008_projection_builders_v2.sql), [009_projection_inventory_builders.sql](../../../../database/functions/009_projection_inventory_builders.sql), and [010_visual_inventory_builders.sql](../../../../database/functions/010_visual_inventory_builders.sql) select their source values from mutable `core`, `research`, `rights`, `raw`, and `provenance` tables while a release remains `draft`.

The source offers a caller-supplied `p_database_snapshot_identity` in `release.set_research_projection_set_to_draft`, but does not bind it to an exported database snapshot, a source-version fence, or a single projection-build transaction. `release.close_research_candidate` locks the release row and `release.validate_research_projection` compares copies with then-current canonical rows; it does not lock or freeze all source inputs used while the draft was assembled. Equivalent visual validation is also live-source based.

This can reject a changed draft, which is useful, but it cannot establish that a multi-call draft was assembled from one immutable canonical state. The source therefore does **not** meet the requested “build sealed projections without mutable canonical reads” property. The model and `MIGRATION_V48_TO_V49.md` require a closed snapshot; this implementation needs a controlled, repeatable-read/serializable builder boundary with a verified source snapshot identity (or a complete immutable staging/projection input) before candidate close.

### P0 — The PostgreSQL adapter and `api_v1` surface are intentionally partial

[postgres-repository.ts](../../../../frontend/src/lib/read-platform/server/postgres-repository.ts) implements only descriptor/overview, minimal surface lookup, and title search. Folder, TRACE, relation, claim, corpus, and visual methods return empty data, `NOT_FOUND`, or `UNAVAILABLE`; `open()` rejects every visual selector. It synthesizes several public DTO fields instead of reading sealed DTO projections.

[009_read_api_core.sql](../../../../database/migrations/009_read_api_core.sql) exposes only `api_v1.sealed_research_release_descriptor` and `api_v1.sealed_surface`; [003_read_api_core_grants.sql](../../../../database/roles/003_read_api_core_grants.sql) grants only those two views. This cannot satisfy the public surface declared in [READ_API_V1.md](../../../../READ_API_V1.md) or the repository contract across adapters. A runtime-closure result must remain partial until exact-pair, rights-safe release projections and adapter mapping exist for every required resource.

### P1 — No production composition root or current-resolution path reaches the PostgreSQL adapter

[provider.ts](../../../../frontend/src/lib/read-platform/server/provider.ts) only constructs `FixtureArchiveRepositoryProvider` when explicitly selected and otherwise throws. It never creates `PostgresArchiveRepositoryProvider`. [open-read-repository.ts](../../../../frontend/src/lib/read-platform/server/open-read-repository.ts) opens `research: { alias: "current" }`, whereas the PostgreSQL provider explicitly accepts exact research pairs only. Consequently the application has no production path from server composition to the narrow PostgreSQL adapter.

The source runtime receipt also records `POSTGRES_ADAPTER_RUNTIME_PASS=false`, no completed Fixture/HTTP vector, and a known exact-pair error-semantic discrepancy; see [04_ADAPTER_VECTOR_RECEIPT.md](../../../../docs/audits/v49-runtime-acceptance/04_ADAPTER_VECTOR_RECEIPT.md). This is independent corroboration, not a test rerun.

### P1 — A permitted migration 010 must repair the executable schema inventory as well as add projections

[replay.sh](../../../../database/scripts/replay.sh) already applies migrations `001` through `009`, including [009_read_api_core.sql](../../../../database/migrations/009_read_api_core.sql). A new runtime-closure migration must therefore be forward-only `010_*`; it must not revise prior migrations or rely on an unlisted replacement sequence.

However, [schema-manifest.json](../../../../database/schema-manifest.json) stops its `migrationOrder` and `stableFiles` at `008`, while the replay script applies `009` and the Phase 2C grant file. This makes the recorded schema-package inventory incomplete before adding any 010 work. The closure must update the replay/manifest/hash inventory and reader grants coherently, then verify them in the designated database lane. Otherwise the declared release/migration query-pack identity cannot describe the executable schema that the adapter expects.

### P2 — Existing sealed reads are a narrow, positive result, not full projection coverage

The two current views use an explicit sealed research pair and read copied release rows, so their runtime queries do not join mutable canonical entities. That is the correct direction. Their object projection contains only surface ID, title, publication layer, and URN, though; the adapter fills remaining values with placeholders. The system should retain this positive copied-row rule when adding all other public DTOs, rather than introducing `api_v1` joins back to `core`, `research`, `rights`, `raw`, or `provenance`.

## Permitted 010 migration shape

The safe shape is a single forward-only `database/migrations/010_*` (with its necessary replay/manifest/grant bookkeeping), using the existing owner role and `ON_ERROR_STOP` convention. It should:

1. Add only release-scoped copied DTO/projection tables, exact-pair `api_v1` views, constraints/indexes, and reader grants needed by the production adapter. Every public row must be keyed by the exact research pair and, where selected, an exact compatible visual pair.
2. Build public values from copied release rows under a declared, enforced source snapshot. Do not make `api_v1` read live canonical schemas, and do not accept a free-text “snapshot identity” as the only proof of input closure.
3. Keep visual composition optional and fail closed: an absent registry produces research-only data with no locator; an explicit incompatible pair returns `RELEASE_VERSION_MISMATCH`; only copied/allowlisted `REMOTE_IMAGE` fields expose pixel locators.
4. Leave migrations `001`–`009` immutable, incorporate `010` into the deterministic replay/package manifest, and extend reader grants only to positive-allowlist views. A view-only 010 cannot close the P0 snapshot-construction gap; it needs a corresponding controlled builder and later dedicated verification.

## Final severity assessment

| Severity | Count | Blocking interpretation |
|---|---:|---|
| P0 | 2 | No immutable construction boundary; no complete release-backed PostgreSQL/API surface. |
| P1 | 2 | No production wiring/current resolution; package inventory is inconsistent with replay. |
| P2 | 1 | Current release-only views are correct but much too narrow. |

**Final result: `PARTIAL` / not ready to claim runtime acceptance closure.** The existing sealing model can be extended, but the next implementation must create snapshot-consistent copied projections and a complete exact-pair adapter; it cannot achieve closure merely by exposing more views over mutable canonical tables.
