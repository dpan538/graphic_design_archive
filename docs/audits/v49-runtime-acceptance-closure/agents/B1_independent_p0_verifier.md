# B1 independent P0 verifier — sealed folder-membership stop

## Scope

This is an independent, read-only review of the closure P0 checkpoint.  It
does not run npm, Next, TypeScript, PostgreSQL, a browser, or a generator; it
does not edit implementation, stage, commit, or push.  The only file written
by this review is this report.

Reviewed worktree: `/private/tmp/graphic_design_archive_v49_runtime_acceptance_closure`

Reviewed source baseline: `64de7ab1ccc190b433266e3a793b9ff7d4c06016`

## Inspected paths

- `docs/audits/v49-runtime-acceptance-closure/00_EXECUTIVE_RECEIPT.md`
- `docs/audits/v49-runtime-acceptance-closure/01_FIXED_START_RECEIPT.md`
- `docs/audits/v49-runtime-acceptance-closure/02_SEALED_FOLDER_MEMBERSHIP_P0.md`
- `docs/audits/v49-runtime-acceptance-closure/03_SCOPE_AND_PROCESS_RECEIPT.txt`
- `docs/audits/v49-runtime-acceptance-closure/04_UNRUN_GATE_LEDGER.tsv`
- `docs/audits/v49-runtime-acceptance-closure/agents/A1_projection_adapter_audit.md`
- `database/migrations/002_raw_core_provenance.sql`
- `database/migrations/003_research_rights.sql`
- `database/migrations/004_release_audit.sql`
- `database/migrations/007_release_copy_integrity.sql`
- `database/migrations/009_read_api_core.sql`
- `database/functions/007_release_protocol_closure.sql`
- `database/functions/009_projection_inventory_builders.sql`
- `database/functions/014_release_copy_guards.sql`
- `database/roles/003_read_api_core_grants.sql`
- `frontend/src/lib/read-platform/server/postgres-repository.ts`
- `READ_API_V1.md` and `DATA_MODEL_V49.md`

## Commands actually run

```text
pwd; git worktree list --porcelain; git -C /private/tmp/graphic_design_archive_v49_parity_browser status --short --branch
rg --files docs/audits/v49-runtime-acceptance-closure database frontend | rg '(^docs/audits/v49-runtime-acceptance-closure/|010_read_api_exact_archive|fixture|release|seal|folder)' | head -240
sed -n ... docs/audits/v49-runtime-acceptance-closure/{00_EXECUTIVE_RECEIPT.md,01_FIXED_START_RECEIPT.md,02_SEALED_FOLDER_MEMBERSHIP_P0.md,03_SCOPE_AND_PROCESS_RECEIPT.txt,04_UNRUN_GATE_LEDGER.tsv,agents/A1_projection_adapter_audit.md}
rg -n -C 4 'research_folder_projection|copy_research_folder_to_draft|assignment_folder_membership|research_release_object|folder' database/migrations/007_release_copy_integrity.sql database/functions/009_projection_inventory_builders.sql database/functions/005_projection_builders.sql database/migrations/009_read_api_core.sql database/roles/003_read_api_core_grants.sql frontend/src/lib/read-platform/server/{postgres-repository.ts,provider.ts,open-read-repository.ts} database/scripts/replay.sh database/schema-manifest.json
rg -n -C 3 'folder_membership|folder.*member|member.*folder|research_folder_projection' database DATA_MODEL_V49.md READ_API_V1.md frontend/src/lib/read-platform
git status --short; git diff --name-only 64de7ab1ccc190b433266e3a793b9ff7d4c06016; git log --oneline --decorate -3; git ls-files docs/audits/v49-runtime-acceptance-closure
rg -n -C 6 'CREATE TABLE research\\.folder_membership|CREATE TABLE provenance\\.assignment_folder_membership|assignment_folder_membership|folder_membership' database/migrations database/functions
rg -n -C 5 'CREATE TABLE release\\.research_release_object|CREATE TABLE release\\.research_folder_projection|CREATE FUNCTION release\\.enforce_folder_copy_source|CREATE FUNCTION release\\.research_manifest_for' database/migrations database/functions
cat docs/audits/v49-runtime-acceptance-closure/03_SCOPE_AND_PROCESS_RECEIPT.txt; git status --short; git diff --name-only 64de7ab1ccc190b433266e3a793b9ff7d4c06016 -- database frontend .github
```

An attempted read-only `ps` listing was denied by the sandbox (`operation not
permitted`), so this reviewer makes no independent historical process-liveness
claim beyond the recorded receipt.

## Independent finding: confirmed P0

**The sealed folder-membership P0 is supported by the source.**

The required API resource is explicit in `READ_API_V1.md`: a release-pinned
folder-detail route and a separately paginated, rights-safe
`folders/{folderId}/surfaces` route.  The source membership relation exists
only as mutable canonical/provenance data:
`provenance.assignment_folder_membership` has `folder_id`,
`archive_object_id`, `membership_role`, and `member_ordinal` in
`002_raw_core_provenance.sql`, with the folder FK added in
`003_research_rights.sql`.

By contrast, `release.research_folder_projection` in
`007_release_copy_integrity.sql` has exactly four data fields after its release
key: `folder_id`, `folder_token`, and `label`; its primary key is only
`(research_release_id, folder_id)`.  It contains no object/member key, role,
or ordinal.  The sole official builder
`release.copy_research_folder_to_draft` copies exactly those three folder
fields from `research.folder`.  The candidate-fingerprint function includes
that folder projection but no folder-member projection.  The copied
`release.research_release_object` schema likewise has no folder reference.

There is no release-owned table, official builder, or `api_v1` view that joins
an exact research release to a folder member.  `009_read_api_core.sql` exposes
only a sealed descriptor and sealed surface view, while the reader grant file
grants only those two views.  The current PostgreSQL repository accurately
reflects this absence by returning empty folder lists/members and `NOT_FOUND`
for folder detail rather than claiming a mutable join is sealed.

Therefore a proposed `010` restricted to safe `api_v1` views/functions and
reader grants cannot implement the required exact-pair folder members without
joining `provenance.assignment_folder_membership` at read time.  That join
would let a sealed release change when canonical assignments change, violating
the release-pinned contract.  Adding a release-owned membership projection and
an authorized builder/seal-protocol extension is materially beyond the stated
forward-only migration scope.  Stopping before such an unsafe projection is
the correct P0 decision.

## Stop-scope review

The closure receipts and `git diff --name-only` against `64de7ab` support the
claim that no tracked implementation, migration, workflow, or package file was
changed: the only worktree change at review time is the new, untracked closure
audit package.  The unrun-gate ledger consistently marks database, API,
adapter, Next, browser, and public-boundary tasks `NOT_STARTED`, rather than
misreporting them as passes.  `03_SCOPE_AND_PROCESS_RECEIPT.txt` explicitly
records zero migrations, fixtures, releases, seal/CAS calls, browser work, and
prohibited production/full-rehearsal actions.

Those are honest *recorded scope* statements.  Their historical process
absence cannot be independently replay-proven by a later read-only review; the
present process listing was sandbox-denied.  This evidence limitation does not
weaken the schema P0, but it means this report does not upgrade the receipt to
a runtime verification result.

## Findings

| Severity | Count | Finding |
|---|---:|---|
| P0 | 1 | No release-owned folder-to-object membership projection/builder exists; a read-time mutable join would violate exact sealed-release semantics. |
| P1 | 0 | None newly identified within this narrow P0 review. |
| P2 | 1 | Historical zero-process evidence is a receipt assertion, not independently reconstructible after the fact because sandbox process inspection was denied. |

## Conclusion

`SEALED_FOLDER_MEMBERSHIP_P0_CONFIRMED=true`

`STOP_SCOPE_HONEST=true` for the recorded Git-visible scope, with the process
verification limitation stated above.

`RUNTIME_ACCEPTANCE_CLOSURE_APPROVED=false`

The correct status remains `PARTIAL_CHECKPOINTED`.  No migration, adapter,
runtime vector, or browser gate should be marked passed from this checkpoint.
