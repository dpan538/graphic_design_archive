# TRACE visualization decision — v48 frozen candidate

Status: implementation candidate; not a release layer
Data boundary: frozen v48 derivatives are read-only
Working branch: `codex/v48-trace-visualization`

## Outcome

TRACE uses three separate full-screen research views controlled by one mode button. The control changes its icon and explanatory question on hover/focus, but the views do not merge their meanings:

| View | Primary question | Visual grammar | Included relation family | Excluded claim |
|---|---|---|---|---|
| Medium / context | In which recorded media and contexts is this object situated? | Metro lines and stations | `medium_context` | No place, source lineage or influence |
| Time / geography | When and where are active design objects recorded? | Real world map or globe, region markers and time controller | Object `time_place` evidence plus a clearly separate aggregate distribution | No object coordinate, travel route, diffusion or influence |
| Sources | Which sources, creators, series and collections document the object? | Rooted evidence tree | `source_provenance` | No medium similarity, place proximity or influence |

This replaces the rejected “one graph carries every meaning” approach. Local readability is the primary layer; global scale is handled through aggregation.

## Full-screen shell and information drawer

- A selected object enters a viewport-filling visual workspace.
- A left-edge control wakes a collapsible evidence drawer on desktop and mobile.
- The drawer contains object identity, layer state, evidence return routes and the normalized node/edge ledger.
- Selecting a station, leaf or ledger row highlights the same local edge, opens the drawer and switches to the appropriate view family.
- Every evidence node retains an object or source return URL.
- Auxiliary media and review/authority-hold layers remain separate from the active layer and are never merged into active counts.

## Normalized TRACE vocabulary

`trace-taxonomy.ts` registers 21 display definitions:

- 20 relation types observed in the frozen v48 atlas;
- one reserved `influenced_by` type with a frozen count of zero.

Each definition provides:

- a stable display code such as `MC-MEDIUM`, `TG-PLACE` or `SP-DOC`;
- family and frozen v48 count;
- definition and evidence requirement;
- permitted assertion;
- prohibited inference.

Object-local marks are deterministic for the loaded graph:

- root: `OBJ`;
- peer nodes: `N01`, `N02`, …;
- edges: `MC-E01`, `TG-E01`, `SP-E01` or `HI-E01`.

These marks are display and audit identifiers. They do not rewrite frozen node/edge IDs or create new relations. Every normalized type has an independent `/trace/types/[type]` page.

## Geographic evidence policy

The map uses Natural Earth geometry distributed by `world-atlas/countries-50m.json`. It does not contain frozen object-level latitude/longitude, because v48 does not provide that evidence.

Displayed points follow this rule:

1. Resolve the audited object region to one or more named Natural Earth country features.
2. Calculate the centroid from those real features at runtime.
3. Aggregate active objects at that normalized region centroid.
4. Label the point and readout as a region aggregate, never an object production coordinate.

City-qualified labels such as `Paris, France` resolve through the documented country suffix. A small explicit alias table covers source vocabulary differences such as `United States` → `United States of America` and `Czech Republic` → `Czechia`.

Broad, historical or unresolved geometries are not guessed. They remain visible in the “Not mapped” count. Current static verification resolves 15,569 of 15,923 active objects; 354 remain deliberately unmapped:

| Region label | Objects | Reason |
|---|---:|---|
| Global / transnational | 223 | No single geography |
| Latin America | 126 | Broad multi-country category |
| Tuvalu | 2 | No feature in the selected 50m boundary set |
| Manchukuo | 1 | Historical geography not silently normalized |
| Tokelau | 1 | No feature in the selected 50m boundary set |
| Yugoslavia | 1 | Historical geography not silently normalized |

The map/globe switch uses Equal Earth and Orthographic projections. Selecting a mapped region recenters the globe. A future iteration may add direct pointer drag after runtime performance is measured.

## Time animation and regional context

- The active catalog is loaded only when the time/geography module opens.
- The user can select cumulative development from 1800 or a single decade.
- Play advances through the 23 frozen decade buckets at 850 ms per step.
- Playback never autostarts and stops under `prefers-reduced-motion`.
- The readout exposes visible, mapped, unmapped and selected-region counts.
- Dashed lines connect a selected region to three high-count regions in the same visible period. They are labelled “same-period co-presence, not influence” and are not TRACE edges.

## Search decision

`/search` is now a full workspace rather than a redirect or corner-card-only interaction. It searches three scopes:

- active TRACE object catalog, deep-linked to `/trace?object=…`;
- normalized TRACE relation definitions, linked to their independent pages;
- the existing published archive surface index.

Filters cover scope, region, decade, medium group and relation family. The shell search remains a quick entry point and links to the full workspace with its query preserved.

The active TRACE catalog is fetched in the browser. Result rendering is capped at 240 rows with a refinement notice. Published archive search now uses the generated `archive-search-v1.json` asset instead of importing the 87 MB mock into the shell client graph. The index contains 8,636 surfaces, is 22 MB raw / 2,079,960 bytes gzip, and has SHA-256 `3674aa608a555e37651d5f88359f1faa01b1255be4ae870aa5a529acbd9a9d76`.

`ArchiveShell` and quick search also avoid the large mock through a lightweight palette module. Assistant evidence retrieval stays behind the same-origin `/api/archive-assistant-evidence` route and therefore does not make the full archive payload part of the default TRACE client bundle.

## Accessibility and mobile

- Mode controls, projection controls, timeline and evidence marks are native buttons/inputs with labels and pressed states.
- SVGs include titles, descriptions and per-node accessible names.
- Modified clicks preserve normal new-tab behavior; plain clicks select and wake evidence detail.
- Mobile keeps the full-screen map, compact controls and bottom readout; complex metro/tree drawings fall back to the same normalized evidence index.
- Text tables provide a non-graphic path for all local edges.

## Performance budget

| Asset/operation | Loading rule | Current status |
|---|---|---|
| TRACE atlas | Initial TRACE page | Required summary only |
| Object catalog | On active object search or time/geography view | Lazy fetch; 15,923 records |
| 50m country geometry | On time/geography mode | Client-only dynamic chunk |
| Object neighborhood | On object selection | Existing shard cache |
| Diagram nodes | Selected object only | No global force simulation |
| Search table | Maximum 240 rendered TRACE rows | Implemented |
| Archive search index | On first non-empty archive query | Lazy fetch; 8,636 compact rows |

No force-directed global graph is introduced. No view attempts to render all nodes or edges at once.

## Acceptance status

Passed:

- targeted TypeScript check covering TRACE, map, search, ArchiveShell, relation pages and assistant API boundary;
- enhanced static verifier: active count, unresolved region, zero influence, taxonomy coverage/counts, real geometry, compact archive index integrity/uniqueness and absence of the large archive mock from the TRACE shell graph;
- formal HTTP routes: `/trace` and `/search` both returned `200` after cold development compilation;
- desktop browser interaction: global atlas, object selection, metro, world map, globe, source tree, drawer, normalized ledger selection, type page and unified search;
- time animation advanced from slider index 13 (`1800–1939`) to 22 (`1800–2029`) and stopped at the last decade;
- mobile browser interaction at 390 × 844: map, compact projection/time controls, left drawer and search workspace;
- React duplicate-key defect in the country layer fixed and rechecked with no new console error;
- complete screenshots stored under `docs/capture/trace-v48-visualization/`.

Open build risk:

- full-project `tsc --noEmit` produced no diagnostics but did not finish in five minutes; the targeted check is the passing code gate for this candidate;
- production build was not rerun after an earlier compile-only attempt exceeded approximately ten minutes;
- cold development compilation is abnormally slow on this workstation: the minimal page took 498.24 seconds on the first request, while warm responses were usable. This is an environment/build-pipeline risk, not a claim that production latency is acceptable.
