# A1 — Read-model projection coverage audit

## Scope and method

- Auditor: A1, read-only Queue A.
- Source reviewed: `3e666b5265ebe7b41ea0c98531b35761ff0d9485`.
- This report is an additive assessment only.  It did not start PostgreSQL,
  npm, Next, a browser, TypeScript, an importer, or any generator; it did not
  edit implementation files or make a commit.
- Classification describes the source tree before the authorized v3 migration.
  `SNAPSHOT_COMPLETE` means the required read identity is already derived from
  release-owned sealed rows, **not** that the API/provider implementation is
  complete.  It must not be used to conceal an absent DTO field or an empty
  placeholder.

## Inspected paths

- `READ_API_V1.md`
- `ARCHITECTURE.md` (read path, immutable-boundary sections)
- `DATA_MODEL_V49.md` (`research`, `release`, and `api_v1` sections)
- `frontend/src/lib/read-platform/repository.ts`
- `frontend/src/lib/read-platform/types.ts`
- `frontend/src/lib/read-platform/server/fixture.ts`
- `frontend/src/lib/read-platform/server/postgres-repository.ts`
- `frontend/src/lib/read-platform/http-repository.ts`
- `frontend/src/app/api/v1/[...path]/route.ts`
- `database/migrations/004_release_audit.sql`
- `database/migrations/005_normative_closure.sql`
- `database/migrations/007_release_copy_integrity.sql`
- `database/migrations/009_read_api_core.sql`
- `database/functions/009_projection_inventory_builders.sql`
- `database/functions/014_release_copy_guards.sql`

## Commands actually run

```text
rg --files -g 'READ_API_V1.md' -g 'ARCHITECTURE.md' -g 'DATA_MODEL_V49.md' \
  -g '*Repository*.ts' -g '*repository*.ts' -g 'route.ts' <source-worktree>
wc -l READ_API_V1.md DATA_MODEL_V49.md ARCHITECTURE.md \
  frontend/src/lib/read-platform/repository.ts \
  frontend/src/lib/read-platform/server/postgres-repository.ts \
  frontend/src/lib/read-platform/http-repository.ts \
  frontend/src/app/api/v1/[...path]/route.ts
sed -n / rg -n over the inspected Markdown, TypeScript, migration, and
function paths listed above
git status --porcelain; git rev-parse --abbrev-ref HEAD; git rev-parse HEAD
```

All commands were read-only.  No database connection or process launch was
attempted.

## Coverage matrix recommendation

| Read-model capability / contract resource | Source finding | Classification | Required disposition in this phase |
|---|---|---|---|
| `current` research descriptor | A current pointer is an allowed mutable alias, while the target descriptor is sealed and exact. It must be resolved once by a provider and must not be used for subsequent resource reads. | `SNAPSHOT_COMPLETE` | Preserve one-time resolver semantics; do not copy mutable pointer state into a sealed manifest. |
| Exact release descriptor / manifest identity | `release.research_release`, verification, manifest identity, and `api_v1.sealed_research_release_descriptor` already bind exact sealed rows. The existing descriptor does not carry the authorized v3 component inventory. | `SNAPSHOT_COMPLETE` | Extend the v3 manifest/component identity without replacing this exact-pair basis. |
| Archive overview | Current 009 descriptor has object and TRACE counts only; `PostgresArchiveRepository.getOverview()` currently substitutes `folderCount: 0` and `positiveVisualRightsCount: 0`. | `IMPLEMENT_IN_THIS_PHASE` | Copy release-owned counts/components; no hard-coded zeros or canonical count query at read time. |
| Folder types | No release-owned type registry projection exists. `research_folder_projection` has no type/slug metadata. | `IMPLEMENT_IN_THIS_PHASE` | Add canonical registry/working publication metadata and a release-owned type projection. |
| Folder list and detail | Current projection has only folder ID/token/label, and lacks type, slug, scope note, sort ordinal, named counts, or object membership. | `IMPLEMENT_IN_THIS_PHASE` | Snapshot all required public metadata using explicit working metadata, never parsing `folder_token`. |
| Folder members | No release-owned folder-object membership projection exists. Existing `release.research_folder_projection` cannot produce members, and mutable membership must not be consulted after build. | `IMPLEMENT_IN_THIS_PHASE` | Add object-level membership snapshot with same-release folder/object composite FKs, source/evidence decision binding, role, and ordinal. |
| Surface summary | 009 exposes only public ID, nullable title, layer, and object URN. The current Postgres adapter fabricates display/date/place/medium/type/source values. | `IMPLEMENT_IN_THIS_PHASE` | Add normalized release-owned presentation, credits, missingness, source label, and safe publication fields. |
| Surface detail | The current release object lacks description, ordered credits, safe citation and route, membership, and explicit missingness. | `IMPLEMENT_IN_THIS_PHASE` | Add the minimal positive-allowlist presentation family; raw payloads, workflow notes, locators, UUIDs, and pixel URLs stay excluded. |
| Archive Search | Current SQL searches 009 `sealed_surface` title only. It cannot produce the contracted summary/highlight/filter basis from an immutable presentation/search document. | `IMPLEMENT_IN_THIS_PHASE` | Build a release-owned search-document projection in the atomic builder with deterministic ordering/keyset fields. |
| TRACE atlas availability and counts | A fixture can honestly show zero, but the existing Postgres adapter returns a hard-coded empty atlas. Current zero state must be release-owned, not a UI/API constant. | `IMPLEMENT_IN_THIS_PHASE` | Snapshot trace availability/count components and provide honest zero rows/counts for this launch slice. |
| TRACE objects and neighborhood | Non-empty object/node/edge semantics need full relation, claim, corpus, and graph projections. The actual launch fixture/state is zero TRACE. | `DEFERRED_NOT_IN_LAUNCH_SCOPE` | Design and record only. This phase may expose release-owned honest zero availability; it must not read a v48 graph or manufacture nodes/edges. |
| Relation-type public registry | The working relation registry exists, but a complete public release registry/evidence-policy projection is absent. | `DEFERRED_NOT_IN_LAUNCH_SCOPE` | Design and record only; unknown/review labels remain fail-closed and unpublishable. |
| Semantic relation | Existing release relation rows are not sufficient for the complete public relation DTO/evidence summary required by the contract. | `DEFERRED_NOT_IN_LAUNCH_SCOPE` | Design and record only; no mutable `research` join during candidate/seal validation or reads. |
| Claim | Existing release claim/evidence structures do not form the complete public claimant/citation projection. | `DEFERRED_NOT_IN_LAUNCH_SCOPE` | Design and record only. |
| Corpus basic descriptor and count | Release corpus snapshot/member tables exist, but the provider returns `UNAVAILABLE` and there is no validated launch projection/manifest component for its public descriptor/count. | `IMPLEMENT_IN_THIS_PHASE` | Snapshot safe corpus descriptor/count and include it in the v3 component manifest. |
| Public source/citation minimum | `SurfaceDetail` requires an allowlisted citation. Current Postgres detail returns `citation: null`; no publication-safe citation projection exists. | `IMPLEMENT_IN_THIS_PHASE` | Copy only positive-allowlisted label/route data, never internal locator or raw provider payload. |
| Visual composition / registry | Research and visual boundaries are deliberately independent; no production visual builder is in scope. | `DEFERRED_NOT_IN_LAUNCH_SCOPE` | Leave the exact visual pair absent/unavailable. Do not derive pixels, remote image URLs, or visual composition from research snapshot data. |

## Material baseline findings

1. **P0 — folder membership is not snapshot-complete.**
   `database/migrations/007_release_copy_integrity.sql` defines
   `release.research_folder_projection` with only release ID, folder ID,
   token, and label. `release.copy_research_folder_to_draft()` in
   `database/functions/009_projection_inventory_builders.sql` only copies
   those fields. It cannot prove a sealed folder-to-object read model. A
   release-owned object-level membership table and atomic copy are therefore
   necessary, as authorized for this phase.

2. **P0 — the existing read surface substitutes facts rather than projecting
   them.** `frontend/src/lib/read-platform/server/postgres-repository.ts`
   returns empty folder lists/counts and synthesizes such values as
   `"Undated"`, `"Unspecified"`, and `"Archive surface"`. Those are not
   release-owned facts and cannot be a basis for sealed DTO parity. The new
   snapshot needs explicit field-level missingness rather than generated text.

3. **P1 — the existing copy guard checks live `research.folder` rows.**
   `release.enforce_folder_copy_source()` in
   `database/functions/014_release_copy_guards.sql` compares a copied row to
   mutable working data. This is acceptable only while constructing a fresh
   draft; it is not a candidate/seal validator. The v3 lifecycle must validate
   only release-owned rows, component hashes, and the single build receipt.

4. **P1 — corpus route/contract mismatch.** `READ_API_V1.md` lists both
   `/corpora` and `/corpora/{corpusVersionId}` and its mapping lists
   `listCorpora`, while `ArchiveRepository` declares only `getCorpus` and the
   current catch-all route implements only the detail form. This phase can
   close the authorized basic descriptor/count projection, but this discrepancy
   must remain recorded for the later API-contract window rather than silently
   broaden the current task.

5. **P2 — schema inventory is visibly stale.** Existing 009 views/grants are
   real migration content, whereas the earlier inventory issue described by
   the task means v3 must inventory 009 and every new migration/function/test
   explicitly. No historical receipt should be rewritten.

## Conclusion

`RELEASE_PROJECTION_COMPLETENESS_MATRIX_RECOMMENDATION=true`.

The authorized v3 work can close every launch-slice gap using one
serializable, set-based snapshot boundary. It must treat exact release
descriptor/current resolution as already release-bound, implement the
archive/folder/surface/search/corpus/zero-TRACE rows as new release-owned
components, and defer non-empty TRACE and visual composition without
pretending that either is complete. Candidate validation and sealing must
never rejoin the mutable canonical sources identified above.

P0=2, P1=2, P2=1 at the pre-v3 source baseline. These findings are the reason
for the authorized forward-only phase, not authorization to change frontend,
adapter, API-route, or migrations 001–009.
