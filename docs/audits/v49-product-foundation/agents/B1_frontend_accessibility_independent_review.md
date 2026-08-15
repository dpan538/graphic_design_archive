# B1 independent frontend/accessibility review

Review date: 2026-08-15  
Reviewer scope: read-only static review of the three migrated slices. No npm,
Next, TypeScript compiler, PostgreSQL, browser automation, generator, commit,
or push was run by this reviewer.

## Scope and commands

Inspected paths:

- `frontend/src/app/search/page.tsx`
- `frontend/src/app/folders/[type]/page.tsx`
- `frontend/src/app/folders/[type]/[slug]/page.tsx`
- `frontend/src/app/surfaces/[id]/page.tsx`
- `frontend/src/app/trace/page.tsx`
- `frontend/src/components/archive/read-platform/ReadPlatformViews.tsx`
- `frontend/src/lib/read-platform/{types,repository,http-repository,pagination}.ts`
- `frontend/src/lib/read-platform/server/{fixture,open-read-repository,provider,postgres-repository}.ts`
- `frontend/src/lib/read-platform/test-fixtures.ts`
- `frontend/src/app/api/v1/[...path]/route.ts`
- `frontend/src/components/archive/shell/ArchiveShell.tsx`
- `frontend/src/components/archive/shell/ArchiveShell.module.css`
- `frontend/src/app/globals.css`
- `frontend/scripts/verify-read-platform-contract.mjs`

Commands actually run (all read-only):

```text
git -C /private/tmp/graphic_design_archive_v49_read_platform status --short
rg --files ...
sed -n ... <the paths above>
rg -n --glob '*.{ts,tsx,css}' '<legacy/data/public-boundary patterns>' ...
find frontend/src/app -type f -name page.tsx -print
git diff --name-only -- frontend/src/app frontend/src/components/archive/read-platform frontend/src/lib/read-platform frontend/src/app/globals.css
```

## Verified static evidence

- The migrated entry routes import `ReadPlatformViews` and/or the server-only
  `openCurrentReadRepository`; they do not import `archive-data`, the legacy
  archive-search client, TRACE v48 atlas/catalog/shards, or frozen JSON.
- The Search and TRACE client views use `HttpArchiveRepositoryProvider`; the
  Archive and surface routes resolve the server-only repository once. The
  provider rejects fixture selection in `NODE_ENV=production`.
- The real fixture declares 32 objects, zero TRACE-eligible objects, zero
  positive visual rights, citation-only delivery, and an unavailable visual
  pair. Test-only adversarial fixture data is isolated in
  `test-fixtures.ts` and is not imported by a route or provider.
- The public slice markup emits no image component, media URL, thumbnail,
  proxy, `srcset`, or held locator. TRACE renders the explicit, release-bound
  statement that no verified TRACE evidence exists and reports total zero;
  it does not draw a default graph.
- Search has a labelled native input, a disabled submit control while loading,
  an alert error path and a status empty path. TRACE has alert and status
  paths. The fixture's neighborhood requests fail as `NOT_FOUND` rather than
  creating an unknown relation.
- New read-platform controls have `min-height: 48px`; the compact menu column
  uses 3rem (48px) cells and icon-only items retain accessible names. Existing
  global `:focus-visible` styling is present. The 901px desktop rule follows
  the 900px mobile breakpoint, and the global stylesheet includes a
  reduced-motion rule.

## Findings

### P0 — static type failure in the read-platform path (1)

`frontend/src/lib/read-platform/server/postgres-repository.ts` calls
`requireFirst(input.first)`, while `requireFirst` accepts a `PageRequest`, not
a number. The returned value is consequently a `number | RepoResult` and is
then used as `first + 1`. This is a TypeScript incompatibility before the
Postgres adapter can be accepted. Correct the invocation to pass the complete
page request and branch on the typed error result, then rerun the affected
typecheck. This reviewer did not run TypeScript under the queue restriction.

### P1 — mobile menu cannot yet meet the specified Escape/focus-return proof (1)

`ArchiveShell.tsx` gives the menu trigger useful `aria-expanded` and labels,
but has no Escape key handler, no recorded trigger focus restoration, and no
menu focus management. The required keyboard transcript therefore cannot yet
prove Escape closes the menu and returns focus to the trigger. This is limited
to the shared shell but affects Search, Archive and TRACE at compact widths.

### P1 — Archive slice has no controllable failure state and no focus-changing swipe state (1)

`/folders/[type]` throws a raw error when repository access fails; there is no
route or app-level `error.tsx` reviewed to translate that into the required
user-facing Archive error state. Separately, the new `/folders/region` view is
a static folder list. It has no record-focused swipe interaction, so the
required pair of Archive mobile screenshots cannot demonstrate a before/after
swipe with different focus object and screenshot hash. This needs a small,
repository-backed interaction or an explicitly valid existing route-level
interaction before browser acceptance; it must not reintroduce legacy data.

### P2 — stale wording in preserved metadata and generic 404 (2)

- `frontend/src/app/trace/page.tsx` metadata still describes a frozen v48
  candidate despite the new v49 read entry point.
- `frontend/src/app/not-found.tsx` says “current staged pool,” which does not
  accurately describe the sealed-release terminology used by the migrated
  routes.

## Unresolved items and verification limit

This is a static review. It does not establish DOM geometry, network request
counts, bundle contents, actual keyboard focus movement, reduced-motion
computed styles, or the eight screenshot hashes. Those require the single
permitted browser context after the P0 is fixed. The search and TRACE error
messages, and the fixture's public-boundary structure, have only source-level
evidence here.

## Conclusion

Direct data coupling in the three migrated entry slices is statically zero,
and the rights-safe real TRACE empty state is correctly represented. The
independent acceptance gate is currently **not ready**: P0=1, P1=2, P2=2.
After the P0 correction and the two P1 interaction/error-state fixes, rerun
the affected typecheck and the bounded browser/accessibility acceptance before
claiming the frontend slices complete.

## Post-fix static addendum

Re-read after the implementation follow-up:

- `frontend/src/lib/read-platform/server/postgres-repository.ts`
- `frontend/src/components/archive/read-platform/ReadPlatformViews.tsx`
- `frontend/src/components/archive/shell/ArchiveShell.tsx`
- `frontend/src/app/error.tsx`

The previous P1 findings are remediated at source level:

- The mobile menu now registers an Escape handler while open, closes the menu,
  and returns focus to `menuButtonRef`.
- The Archive slice now has a controlled, repository-backed focus card. A
  swipe wider than 48px advances it, announces the active position, and the
  explicit “Next folder” control provides an equivalent keyboard path. Its
  `data-mobile-gesture-zone` keeps this gesture from being intercepted by the
  shared edge-back gesture.
- `frontend/src/app/error.tsx` supplies a rights-safe failure state that says
  no fallback data was shown and offers a retry control.

The earlier P0 is only **partially** remediated. The call now passes the full
page request, but `search()` uses `requireFirst<SearchHit>(input)` and returns
its non-number branch from a method declared as
`Promise<RepoResult<Page<SearchHit>>>`. That branch is
`RepoResult<SearchHit>`, not `RepoResult<Page<SearchHit>>`; static TypeScript
compatibility still requires the generic to be `Page<SearchHit>` (or an
equivalent typed error conversion). No compiler was run under this reviewer's
tool restriction.

Revised static conclusion: P0=1 (generic result mismatch pending), P1=0
(source-level remediation present), P2=2. The browser-runtime evidence limit
in the original review remains: focus movement, touch behavior, reduced
motion, geometry, network/bundle boundary, and required screenshot hashes
must still be proven in the single permitted browser run.

### Final post-fix check

The requested correction is now present exactly as
`requireFirst<Page<SearchHit>>(input)`. The error branch therefore matches the
declared `RepoResult<Page<SearchHit>>` return type at source level. B1's final
static status is **P0=0, P1=0, P2=2**. This is not a substitute for the
remaining bounded typecheck and browser-runtime evidence listed above.
