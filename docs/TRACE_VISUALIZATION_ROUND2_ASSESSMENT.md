# TRACE visualization — next-round assessment

Assessment date: 2026-08-04
Scope: visualization candidate on `codex/v48-trace-visualization`; not a release layer

## Priority 0 — application acceptance outcome

Completed:

1. `/trace` and `/search` now return `HTTP 200` and were exercised in the in-app browser.
2. Desktop and 390 × 844 mobile screenshots cover the metro, world map, globe, rooted source tree, drawer, selected ledger edge, type page and full search workspace.
3. The country-feature duplicate key found during visual acceptance was fixed.
4. The hidden 87 MB client dependency path through shared primitives was removed; a full reload contains no `public_surface_mock` script.

Still open:

- measure the verified low-concurrency production build again in CI before promotion beyond this visualization branch;
- reduce the approximately 6.29 MB legacy Reader first-load bundle without reintroducing the full archive mock into TRACE or search.

## Priority 1 — search and load performance

- Compact generated archive search asset: completed (8,636 rows; lazy client fetch).
- Independent archive and TRACE result loading: completed.
- Add result virtualization when the display cap is intentionally raised above 240.
- Add relation-aware object facets generated during TRACE preprocessing; the current object catalog does not enumerate each object’s local edge types.
- Add searchable node labels and evidence fields without loading every neighborhood shard in the browser.
- Add query-state URLs for all search filters, not only the initial text query.

## Priority 1 — geography quality

- Evaluate 10m geometry or a separately audited small-island point layer for Tuvalu and Tokelau; do not add hand-entered coordinates without a published geographic source.
- Create an explicit historical-geography authority table for Manchukuo and Yugoslavia if the project wants them mapped. Until then they remain unmapped.
- Decide whether broad labels such as Latin America should open a region aggregate panel rather than render one centroid.
- Add direct globe drag/keyboard rotation after measuring the 50m SVG path cost on mobile.
- Replace the current top-three same-period context with a documented analytical measure if “regional association” is meant to imply more than co-presence. Keep it outside TRACE edges.

## Priority 1 — TRACE analytical depth

- Add upstream/downstream direction toggles to the local ledger.
- Add a node-detail route if evidence nodes need stable citations independent of the object page.
- Add export for the selected local graph and filtered ledger in a provenance-preserving format.
- Add comparison mode for two objects without implying influence.
- Add review/authority-hold overlays that are visible on request but never mixed into active statistics.
- Add a documented promotion workflow for any future `influenced_by` edge; v48 remains at zero.

## Priority 2 — visual and interaction refinement

- Measure label collisions and introduce focus-driven labels rather than showing more labels globally.
- Add compact overview/minimap only if navigation testing proves it necessary.
- Mobile map, compact view switch, drawer spacing and search header were refined from real 390 × 844 screenshots; continue testing additional devices.
- Audit keyboard order across mode menu, map controls, timeline, drawer and evidence table.
- Test high contrast, zoom to 200%, reduced motion and screen-reader text mode.

## Frozen-data boundary

This round added application code, documentation and verification only. It must not rewrite frozen v48 JSON, SQLite, TRACE shards or counts. Later data changes require a new candidate version.
