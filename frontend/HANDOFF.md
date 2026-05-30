# Archive Box Frontend — Handoff (v0)

First complete **reading prototype** for the rights-aware graphic design history
archive index. Renders the archive **box → folder → sheet** metaphor from a
static mock. No ingestion, no crawling, no auth, no admin, no WebLLM, no
graph/timeline/map, no historical-node (HN) browse UI.

Stack: **Next.js 15 (App Router) · TypeScript · Tailwind CSS v3 · DaisyUI v4**.
Deploy target: **Vercel**.

---

## 1. Files created / changed

All new work lives in `/frontend`. Nothing in `db/`, ingest scripts, or Codex
pipelines was modified. The only data touch was copying the mock JSON.

### Config / scaffold
- `frontend/package.json` — deps + scripts
- `frontend/next.config.ts` — `reactStrictMode`, `outputFileTracingRoot` (pins
  the workspace root so an unrelated lockfile higher up is not selected)
- `frontend/tsconfig.json` — strict TS, `@/*` path alias
- `frontend/postcss.config.mjs` — tailwind + autoprefixer
- `frontend/tailwind.config.ts` — custom DaisyUI **`archive`** theme (1-bit /
  paper / minimal radius / high contrast), monospace-leaning fonts
- `frontend/.gitignore`

### Data + types + data layer
- `frontend/src/data/public_surface_mock_v0.json` — copy of the root mock (the
  bundled, imported source of truth)
- `frontend/public/data/public_surface_mock_v0.json` — second copy for
  static/public access (kept in sync; the app imports the `src/data` copy)
- `frontend/src/types/archive.ts` — full types matching the mock shape
  (`meta`, `folderTypes`, `folders`, `surfaces`)
- `frontend/src/lib/archive-data.ts` — data layer: `getFolders`, `getFolder`,
  `getSurface`, `getSurfacesForFolder`, `searchSurfaces`, chronology grouping
  (`groupByDecade`, `sortChronologically`), aggregation (`surfaceMix`,
  `imageDistribution`, `sourceCount`, `getGlobalCounts`,
  `getFolderTypeSummaries`), `folderHref`, `getFolderColor`, and
  `generateStaticParams` helpers

### Components — `frontend/src/components/archive/`
`ArchiveBoxFrame`, `FolderTypeRail`, `FolderTypeIndex`, `FolderCover`,
`FolderIndex`, `ChronologyDivider`, `SurfaceStrip`, `SurfacePage`, `ImageZone`,
`RightsStamp`, `SourceReturn`, `SurfaceTables`, `SparseCard`, `FallbackStub`,
`SearchPanel`, plus a small shared `primitives.tsx` (ImgBadge, StatusChip,
FolderTab, TypeLabel, CountCell).

### Routes — `frontend/src/app/`
- `layout.tsx` (sets `data-theme="archive"`, `lang="en"`)
- `globals.css` (archive CSS variables + binder margin, punch holes, empty
  image bay hatch, folder tab, stamp, stub hatch)
- `page.tsx` → `/`
- `folders/page.tsx` → `/folders`
- `folders/[type]/page.tsx` → `/folders/[type]`
- `folders/[type]/[slug]/page.tsx` → `/folders/[type]/[slug]`
- `surfaces/[id]/page.tsx` → `/surfaces/[id]`
- `search/page.tsx` → `/search`
- `not-found.tsx`

---

## 2. Run locally

```bash
cd frontend
npm install
npm run dev      # http://localhost:3000
```

Production build / preview:

```bash
npm run build
npm run start
```

`npm run build` succeeds and prerenders 22 pages (all folder types, all
folders, all surfaces). `/search` is server-rendered on demand because it reads
the `?q=` search param; the search itself is 100% client-side over bundled mock.

---

## 3. Vercel settings

- **Root Directory:** `frontend`
- **Framework preset:** Next.js (auto-detected)
- **Build command:** `next build` (default)
- **Output:** `.next` (default)
- **Install command:** `npm install` (default)
- No environment variables / server secrets are required for v0.

---

## 4. Behavior vs. binding rules (what was implemented)

- **Four folder types only** (Region, Theme, Medium, Movement). No HN rail, no
  `/folders/historical-node`, no spine/drawer.
- **Time is the in-folder sort axis**, never a top-level container. Folder index
  groups into decade dividers (`1890s`, `1910s`, …) with a trailing
  `Undated / date under review` bucket.
- **Folders are filter/aggregation views.** A surface can appear in several
  folders; the surface layout never changes by folder. Folder type color
  appears only on tab / edge / swatch, always paired with text — never on the
  record body.
- **`provisionalDisplayNumber` is displayed as-is** (legacy `HN*`/`STAGED-*`
  segments included). No HN navigation is derived from it.
- **IMG00–IMG04 driven by `image.state` from the payload**, never inferred from
  the URL:
  - `IMG00` → empty hatched frame + rights/source text, no remote image
    (verified: `SURF-ECAP001`).
  - `IMG01`/`IMG03` → render image **only if** `image.url` is present (no
    upscale for IMG01). `SURF-ECAP002` is IMG03 with `url: null`, so it shows
    the frame + license/credit label with no broken `<img>` (verified).
  - `IMG02` → empty frame + "View at source" viewer action.
  - `IMG04` → **no image frame at all** (verified: `SURF-NASA-INDEX`).
  - Unknown → defaults to IMG00.
- **Every surface page shows** the rights stamp, "View at source", access date,
  and the six table kinds (`SOURCE`, `NORMALIZED`, `RIGHTS`, `CLASSIFICATION`,
  `RELATIONS`, `CITATIONS`) when present.
- **Templates:** `sheet.main.v0`, `sheet.img00.v0`, `sheet.text.v0` render via
  the loose-leaf `SurfacePage` (binder margin + punch holes); `card.sparse.v0`
  via `SparseCard` (shows promotion/review status + completeness reason);
  `stub.fallback.v0` via `FallbackStub` (visibly "NOT INGESTED", required next
  action). `card.sparse.v0` has a mock example (`SURF-CARD-001`).
- **Search** (`/search`) is deterministic and local: substring match over
  title, creator, date, place, object type, medium, source name, folder titles,
  and every table row value. Shows a snippet + field + link to `/surfaces/[id]`,
  with a note that query expansion is reserved for a later local WebLLM version.
  No LLM / network calls.
- **Responsive**: information order is preserved on mobile; rights stamp and
  source action are never hidden behind menus (single-column stack with the
  rights/source aside moved above the body on small screens).

### Done-criteria check (all pass)
- `npm run build` succeeds in `/frontend`.
- All 6 routes render with real mock data.
- `SURF-ECAP001` (IMG00) → empty frame, no remote image.
- `SURF-NASA-INDEX` (IMG04) → no image frame.
- `SURF-ECAP002` (IMG03, url null) → frame + license/credit UI, no broken layout.
- `SURF-STUB-001` → fallback stub, visibly "not ingested".
- Folder index sorts chronologically (decade dividers + undated last).
- Search returns deterministic results from the mock.
- Works on desktop + mobile without overlapping text.

---

## 5. Known gaps vs. spec

- **Surface types not in the mock** are not rendered as dedicated pages:
  `sheet.continuation.v0`, `sheet.compound.v0`, `item.unassigned.v0`,
  `item.proposed-cell.v0`, the appendix templates, and `registry.card.v0`. The
  spec lists them; the v0 mock has no examples, so they were not built. The data
  layer/types are extensible (`TemplateId` is an open union).
- **Multi-page sheets / appendix markers (p02/p03)** are not implemented — the
  mock has single-page surfaces only (one surface even carries a `…/p02` display
  number, but there is no second physical page in the payload).
- **Folder type-index sort options** (alphabetical / most records / earliest /
  recently updated) are not interactive; type-index defaults to alphabetical and
  in-folder defaults to chronological, per spec.
- **No real images load anywhere** — every mock `image.url` is `null`, so IMG01
  and IMG03 currently always show the empty frame. The render path for an actual
  image exists and is exercised once a URL + license evidence is present.
- The two copies of the mock JSON (`src/data` and `public/data`) must be kept in
  sync manually; the app only imports the `src/data` copy.

---

## 6. What Composer should polish next

- **Visual detail:** refine the binder/punch-hole spacing on very small screens;
  consider a subtle paper texture toggle; tune folder-tab color contrast for the
  yellow Movement token (`#E2C044`) against the paper base for AA contrast.
- **Missing mock cases:** add example payloads for continuation/appendix pages,
  compound sheets, unassigned items, and proposed cells so those templates can
  be built and reviewed; add an IMG01 and an IMG03 example **with** a real
  permitted `image.url` to exercise the image render path.
- **Accessibility:** audit color-contrast of all badges/tabs; add visible skip
  link; verify table semantics with a screen reader; confirm focus order through
  the binder-margin layout; the search input uses `autoFocus` (lint-suppressed) —
  reconsider for screen-reader UX.
- **Search UX:** debounce / highlight matched substring within snippets; allow
  filtering results by folder type or IMG state; wire the `?q=` URL param to stay
  in sync as the user types (currently it only seeds the initial value).
- **Folder index:** add the optional per-row "View at source" already present on
  `SurfaceStrip`, plus a sort toggle once more surfaces exist.

---

## 7. TypeScript / build warnings left intentionally

- **No TypeScript errors**; the build's type-check and lint pass clean
  (`ReadLints` reports none).
- **`@next/next/no-img-element`** is intentionally disabled at the one `<img>`
  in `ImageZone.tsx`. `next/image` adds remote-domain config and optimization
  that is inappropriate for a rights-restricted archive where remote images are
  the exception and must not be silently fetched/optimized. A plain `<img>` only
  renders when the payload explicitly supplies a permitted URL.
- **`jsx-a11y/no-autofocus`** is disabled on the search input in
  `SearchPanel.tsx` (intentional focus for a search-first page; flagged for the
  a11y polish pass above).
- **npm advisories:** `npm install` may report 2 moderate advisories from the
  transitive dependency tree. Next.js was pinned to a patched 15.x
  (`^15.5.4`, resolved to 15.5.18) to clear the critical CVE flagged on the
  initial `15.1.6` pin. Remaining moderates are transitive and not addressed via
  a forced/breaking `audit fix` in v0.
- A first `next build` prints a **multiple-lockfile** warning if an unrelated
  `package-lock.json` exists in a parent directory; this is silenced by
  `outputFileTracingRoot` in `next.config.ts`.
