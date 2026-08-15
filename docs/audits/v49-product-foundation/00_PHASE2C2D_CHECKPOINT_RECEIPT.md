# Phase 2C/2D product foundation checkpoint

## Fixed input

- source remote ref: `origin/refactor/v49-data-platform`
- source SHA: `60329e8ec713221bbf42318a4f4c7477e6eb5a72`
- feature branch: `feat/v49-read-platform`
- worktree: `/private/tmp/graphic_design_archive_v49_read_platform`
- protected legacy main: observed only; not switched, modified, restored, or cleaned.

## Implemented core

- One `ArchiveRepository` contract and three adapters: server-only Postgres,
  compact 32-object fixture, and HTTP envelope client.
- Exact research release pair is carried through cursor, repository and API
  envelope.  There is no release-pair fallback.
- A forward-only migration adds exact sealed descriptor/surface views and
  reader grants.  It neither changes historical migrations nor current
  resolution semantics.
- Fixture is fixed at 32 objects, zero TRACE eligible objects and zero positive
  visual rights. Fixture selection throws in production.
- The fixture's held sentinel is test-only and no public DTO includes locator,
  pixel, thumbnail, image-service, proxy or raw payload fields.
- The disposable PostgreSQL 16 integration runner passed after fresh replay:
  R1/V1 seal, independent research/visual CAS, R2 promotion, V1 mismatch,
  stale CAS denial, sealed mutation denial and reader write denial.

## Frontend slices

- `/search`, `/folders/[type]`, `/folders/[type]/[slug]`, `/surfaces/[id]`,
  and `/trace` now use only the repository/API boundary, not legacy direct
  data imports. TRACE displays the honest zero-evidence state.
- The mobile Archive view has a focused-card touch/Next state, and the icon
  menu supports Escape close plus focus return. A generic error boundary says
  no fallback data was shown.

## Verification limitation / checkpoint

The required dev-server browser route capture could not be completed in the
managed execution sandbox: the single Next dev process did not retain its
localhost listener, and the in-app browser received `ERR_CONNECTION_REFUSED`.
No second server or full build was attempted. Consequently eight screenshot
receipt, DOM/network capture and computed-style accessibility evidence remain
**not verified**. This checkpoint must not authorize a release.

No full Next build, full population replay, extractor rerun, staging access,
production database access, stable/main push, PR, merge or deployment occurred.
