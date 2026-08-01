# TRACE visualization v48 — implementation and verification

Status: **implemented on isolated branch; candidate UI, not merged to main**

Branch: `codex/v48-trace-visualization`

Data baseline: remote main transfer `592c765`

Implementation date: 2026-08-01

## Implemented surface

- `/trace` uses the existing `ArchiveShell`, type system and colour tokens.
- The initial view is an active-only region-by-decade atlas. It does not load
  the active catalogue or object neighbourhoods on first render.
- The object view lazily loads a compact active catalogue and then one of 576
  stable neighbourhood shards for the selected object.
- The 11 photo/print adjuncts use an explicit auxiliary layer with
  `countEligible=false` and no promotion into the active count.
- The 4,425 authority-review records use a separate, explicitly selected
  review layer. They are source-linked and do not enter active aggregates or
  graph edges.
- Evidence edges are grouped as source/provenance, time/place and
  medium/context. The actual relation label, direction, status and evidence
  URL remain visible.
- No historical influence edge or visual influence arrow is rendered. The
  interface states that the frozen data contains zero documented
  `influenced_by` edges.
- Every displayed root or evidence node returns to an existing archive object
  route or its recorded official source URL. Because the current frontend
  payload predates v48, 2,585 active roots have archive object routes and
  13,338 currently return to official source pages.

## Generated read models

`scripts/build_prefreeze_candidate_v48_trace_visualization.py` reads the
frozen SQLite database in read-only mode and requires these exact source
hashes before it can generate assets:

- candidate JSON:
  `b16bb0158c3ea27cee2909e96631ab84f3c8f6d0356476e45e641eb27edb4f48`
- SQLite:
  `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e`

It creates 580 declared JSON assets plus `manifest.json` under
`frontend/public/data/trace-v48/`. The frozen JSON and SQLite files are never
opened for writing.

The independent audit is
`scripts/audit_prefreeze_candidate_v48_trace_visualization.py`. It recalculates
source and asset hashes, counts all declared assets, checks layer policy and
rejects auxiliary influence or count eligibility.

## Data and performance gates

Generator: **PASS**

Independent audit: **24/24 PASS**

| Gate | Result | Budget |
| --- | ---: | ---: |
| Active objects | 15,923 | exactly 15,923 |
| Review objects | 4,425 | separate layer |
| Auxiliary objects | 11 | count-ineligible |
| Influence edges | 0 | exactly 0 |
| Atlas matrix total | 15,923 | exactly 15,923 |
| Atlas marks | 345 | at most 360 |
| `atlas.json` | 8,514 B / 3,128 B gzip | 180,000 / 45,000 B |
| `catalog.json` | 2,629,051 B / 553,405 B gzip | 4,500,000 / 1,100,000 B |
| Review catalogue | 875,591 B / 173,593 B gzip | 1,800,000 / 500,000 B |
| Auxiliary payload | 29,034 B | 100,000 B |
| Largest neighbourhood shard | 272,139 B | 600,000 B |
| Neighbourhood shard p95 | 230,870 B | 250,000 B |
| Runtime visualization packages added | 0 | 0 |

The full generated directory is about 100 MB uncompressed in the repository.
Network delivery relies on normal HTTP compression and progressive requests;
the browser never downloads the full directory as one payload.

## Frontend and route verification

Commands run from the visualization worktree:

```text
python3 scripts/build_prefreeze_candidate_v48_trace_visualization.py
python3 scripts/audit_prefreeze_candidate_v48_trace_visualization.py
cd frontend && npx tsc --noEmit
cd frontend && npm run build
cd frontend && npx next build --experimental-build-mode compile
cd frontend && npm run dev -- --hostname 127.0.0.1 --port 3047
```

- Python syntax checks: **PASS**.
- TypeScript: **PASS** with no diagnostics.
- Next production compilation and built-in type validation: **PASS**.
- Next production `compile` mode after the final component change: **PASS** in
  27.4 seconds; `/trace` is present in the route manifest and the shared first
  load JavaScript is 103 kB. Compile mode deliberately does not claim static
  generation completion.
- Full production static generation: **not completed**. The existing build
  expands 8,761 static routes and repeatedly exceeded Next's 60-second page
  generation timeout on pre-existing routes including `/about`, `/badges`,
  error pages and many `/surfaces/[id]` pages. The run was stopped at 1/8,761
  rather than reported as a successful build. No failure named `/trace`.
- Local development route: `GET /trace` returned **HTTP 200**. Cold
  compilation completed in 23.9 seconds; the first response completed in
  52.283 seconds. After the final component change, recompilation completed in
  798 ms and the verification response completed in 14.533 seconds.
- Served `atlas.json` and `neighborhoods/000.json` hashes matched their
  generated files byte-for-byte.
- In-app browser attachment timed out twice before a page was available for
  inspection. Therefore screenshots, console inspection and responsive visual
  acceptance remain **not passed**, not silently waived.

## Accessibility and responsive implementation

- Native buttons, links, search input, selects, table semantics and `details`
  disclosure are used.
- Relation direction, relation type, review status and evidence route are
  written in text; colour is not the sole signal.
- The local visual branches have a full text relation table fallback.
- The desktop atlas is an HTML table. Mobile replaces it with a selected-decade
  ranked list and progressively enters an object trace.
- Loading and error state are exposed through `aria-live`.
- The active catalogue search uses a deferred query so filtering 15,923 rows
  does not block urgent input updates.
- Reduced-motion preferences disable non-essential transitions.

Keyboard order, visible focus, screen-reader output and the mobile breakpoint
still require browser-level acceptance because the in-app browser could not
attach during this run.

## Boundary checks and remaining risks

- Frozen candidate JSON and SQLite SHA-256 values remain unchanged.
- The generator creates derivative read models only; it does not update v48.
- Active, auxiliary and review layers remain separate in data, controls and
  totals.
- Medium groups are display-only filters and do not rewrite frozen media.
- Region aggregation uses frozen normalized object geography. No institution
  location, search term or creator nationality is substituted.
- The current frontend object-route payload covers only 2,585 of 15,923 active
  roots. The other 13,338 deliberately return to official source pages until a
  separate, audited frontend data sync exists.
- A production deployment still needs a successful full static build or a
  separately approved change to the legacy static-generation strategy.
- Browser visual/console/mobile verification remains the final UI acceptance
  gate.

No visualization file should be promoted to main until the remaining browser
acceptance and full-build/deployment gate are resolved or explicitly accepted
as a documented release exception.
