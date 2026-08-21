# Project log

This active log is a compact index of release-level decisions. The complete pre-hygiene implementation log remains immutable at tag `v49-data-api-closure-20260821` and can be read with:

```bash
git show v49-data-api-closure-20260821:PROJECT_LOG.md
```

## v49 release state — 2026-08-21

- Source closure commit: `d78f496bcdf2cd6941791986007cd7a885c4c532`.
- Source tree: `f0549c319d1e0b0cf5e0aab5a2b297361675b701`.
- Immutable annotated tag: `v49-data-api-closure-20260821`.
- Schema SHA-256: `df1e7741e59e5e6bf1ca80f2a33edfad1abb2fc6d95b57d4d6993b49917020dd`.
- Release projection digest: `11d92b70bd3a87113d4daabac2b5e4e38a3416cc55be894b42b0dd3d072ca640`.
- Canonical objects / assignments: 15,923 / 47,982.
- Eligible / held: 7,995 / 7,928.
- Accepted TRACE / positive visual rights: 0 / 0.
- Public Read API templates: 18; all tested with no 5xx/search 503.

## Current decisions

- `database/` is the only active database root; legacy `db/` is source-tag history only.
- v49 database implementation and canonical inputs are frozen byte-for-byte.
- `generated/public_surfaces_prefreeze_candidate_v48.json` is the sole canonical population input.
- SQLite/search/TRACE/manifests remain reconciliation-only and cannot repair canonical state.
- The browser never connects directly to PostgreSQL; `api_v1`/release-derived reads form the public boundary.
- Historical raw captures, backups, pre-v49 generated output, prompts, reports, and unrelated archive material are recoverable by immutable ref rather than duplicated in the active tip.
- Future database changes require v50+, a new forward-only migration, and an ADR.

## Current indexes

- Release: `docs/releases/v49/RELEASE_INDEX.md`
- Data retention: `docs/releases/v49/DATA_RETENTION.md`
- Audits: `docs/releases/v49/AUDIT_INDEX.md`
- Repository layout: `docs/maintenance/REPOSITORY_LAYOUT.md`
- Retention policy: `docs/maintenance/RETENTION_POLICY.md`
- Database freeze: `database/FROZEN_V49.md`
- Read API: `docs/api/v49-read-api-catalog.md`

