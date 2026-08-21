# Repository layout

The active v49 repository has one database root, one API/runtime implementation, four frozen release-input artifacts, indexed documentation, and immutable historical recovery through Git refs.

| Path | Active responsibility |
|---|---|
| `database/` | Only database root; frozen v49 migrations, functions, roles, views, fixtures, tests, replay and schema contracts |
| `frontend/` | Next.js application and server-side read API boundary |
| `data/` | v48 SQLite reconciliation input and CSV transfer manifest only |
| `generated/` | canonical v48 Candidate JSON and JSON transfer manifest only |
| `scripts/repository/` | release inventory, hygiene, and database freeze verification |
| `docs/api/` | current Read API contract and examples |
| `docs/releases/v49/` | immutable source, input, audit, and release indexes |
| `docs/maintenance/` | layout, retention, ref/worktree ledgers, and inventories |
| `docs/audits/` | indexed formal evidence packages |
| `project-assets/` | rights/license documentation for project-owned design assets |

Historical `db/`, raw capture, backups, pre-v49 generated output, prompts, reports, unrelated archived probes, and the long-form project log are available only from `v49-data-api-closure-20260821`.

