# TRACE visualization v48 — feasibility and technical decision

Status: **accepted for implementation on a separate visualization branch**  
Data baseline: frozen candidate v48 (`d592566`), remote main transfer
`592c765`  
Decision date: 2026-08-01

## Decision

Implement a hybrid TRACE reader:

1. a rooted, evidence-labelled local tree after an object is selected; and
2. an aggregate time/geography atlas for the complete active layer.

Do not render the full TRACE database as one force-directed graph. The object
page and source-return route remain the primary evidence surfaces; TRACE is a
navigation and comparison layer, not a replacement for them.

## Evidence from the frozen data

- 15,923 active objects in 30 active TRACE trees.
- 97,889 TRACE nodes and 255,695 TRACE edges in the SQLite snapshot.
- The largest edge families contain 86,024, 57,111 and 41,971 edges.
- The largest active object trees contain 4,937, 3,587 and 2,920 objects.
- 12,952 active objects are `source_verified`; 2,971 are
  `metadata_supported`.
- 11 photography/printmaking adjuncts are searchable but
  `countEligible=false`.
- 4,425 authority-uncertain records remain in a separate review/search layer.
- Historical `influenced_by` edges: 0.

These sizes support precomputed aggregation and object-neighbourhood retrieval.
They do not support a readable or responsible all-node browser graph.

## Options considered

| Option | Strength | Failure mode at v48 scale | Decision |
| --- | --- | --- | --- |
| Tree / rooted genealogy | Best local edge reading; direction and evidence labels stay close to the selected object | A single global root would create thousands of siblings and falsely imply one genealogical hierarchy | Use only for an object-sized neighbourhood |
| Force-directed graph | Useful for a small, exploratory relation set | 97,889 nodes and 255,695 edges create an unstable density field; layout motion obscures evidence status and suggests proximity has historical meaning | Reject for global view; do not ship a decorative force simulation |
| Timeline + geographic aggregation | Scales well; reveals uneven temporal and regional coverage without inventing object-to-object relations | Aggregation cannot answer which source, creator or collection documents one object | Use for global view |
| Hybrid: local object tree + global time/geography atlas | Keeps local evidence legible and global patterns aggregate; supports separate active/review/auxiliary layers | Requires preprocessing and progressive asset loading | Adopt |

## Information architecture

### Object trace

The selected object is the root. Its directly indexed evidence edges are
grouped by role rather than spatially simulated:

- source/provenance: `documented_by`, `created_by`,
  `part_of_collection`, `captured_from_provider` and equivalent source edges;
- time/place: `associated_with_place`, `dated`, `dated_to`,
  `associated_with_year`;
- medium/context: `has_type`, `has_medium`,
  `has_material_or_technique`, and explicitly documented context relations.

Every edge shows its actual label, review state and evidence status. Incoming
and outgoing directions are visible in text. The root links to the existing
archive object route when that route is present in the current frontend
payload; otherwise it returns to the official source record. Evidence nodes
return to their recorded source URL.

The interface must never relabel adjacency, shared place, shared year,
co-occurrence or visual similarity as influence. Because v48 contains zero
`influenced_by` edges, the interface shows a plain “no documented influence
edge in this freeze” statement and renders no influence arrows.

### Time / geography atlas

The global view uses precomputed counts by decade and object geography, with
secondary source and medium filters. It shows distributions, not object-level
causal edges. Selecting a cell filters the compact object catalogue and can
then open one local object trace.

Desktop uses a bounded region-by-decade matrix and ranked distributions.
Mobile replaces the full matrix with one selected decade and collapsible region
rows; it never squeezes the desktop graph into a small viewport.

### Layer separation

- Active main objects are the default and the only contributors to active
  totals and the global atlas.
- The 11 photo/print adjuncts have a separately labelled auxiliary view and
  distinct line/shape treatment. They never change the active count.
- Authority-uncertain review records are loaded only after an explicit layer
  switch. They remain source-linked and do not enter active aggregates.
- No layer switch changes the frozen data; all filtering is presentational.

## Data architecture

Generate static read models from the frozen SQLite snapshot. Do not import the
190 MB candidate JSON or 422 MB SQLite database into the browser bundle.

Planned assets under `frontend/public/data/trace-v48/`:

- `atlas.json`: active counts, relation vocabulary, decade/region aggregates,
  source/medium summaries, layer totals and zero-influence policy.
- `catalog.json`: compact active object search/filter records. Loaded on demand,
  not on the initial page render.
- `review-catalog.json`: separate authority-review list, loaded only when the
  review layer is requested.
- `auxiliary.json`: the 11 count-ineligible adjunct records and their explicit
  evidence relations.
- `neighborhoods/000.json` … `neighborhoods/23f.json`: object-local nodes and
  edges partitioned into 576 stable hash buckets. The catalogue stores each object's
  shard key, so selecting one object fetches one shard rather than the graph.
- `manifest.json`: byte sizes, SHA-256 values, counts and performance gates for
  every generated asset.

The generator reads SQLite and existing source-route metadata only. Generated
assets are derivative visualization indexes; they cannot update the database or
candidate payload.

## Rendering and Next.js boundary

- `/trace` is a Server Component shell with a small Client Component for local
  selection and filters.
- Browser reads use versioned static assets. No client-to-database access and no
  internal API round trip are required.
- The initial render loads `atlas.json` only.
- Search loads `catalog.json` after input/focus; selecting an object loads one
  neighbourhood shard.
- Review and auxiliary files are separate lazy requests.
- No graph library is added. The local tree uses semantic HTML and restrained
  CSS connectors; the aggregate view uses a bounded HTML/SVG chart.

## Visual language

Reuse the existing archive/editorial system: Plex type, paper/canvas tokens,
thin rules, compact labels and restrained ephemera accents. The page does not
introduce a dark graph canvas, neon nodes, large coloured backgrounds,
decorative rings or black structural bars.

Colour is paired with text and line style and is limited to:

- relation family;
- verified / auxiliary / review status;
- medium branch; and
- current focus.

## Accessibility and no-graphic path

- Native search, select, button, link and `details` controls.
- Keyboard selection and visible focus styles.
- Edge direction and status are always written as text, never encoded only by
  position or colour.
- The local tree has a relation table containing the same nodes, labels,
  directions, statuses and source links.
- The atlas has a table fallback for decade/region counts.
- Live selection messages use an `aria-live` region.
- Reduced-motion preferences disable non-essential transitions.
- Every interactive graph node is a real object/source link.

## Performance gates

The generator fails when any budget is exceeded:

- initial `atlas.json`: at most 180 KB uncompressed and 45 KB gzip;
- active `catalog.json`: at most 4.5 MB uncompressed and 1.1 MB gzip;
- review catalogue: at most 1.8 MB uncompressed and 500 KB gzip;
- auxiliary file: at most 100 KB uncompressed;
- neighbourhood shard: at most 600 KB uncompressed, with p95 at most 250 KB;
- desktop atlas: at most 360 visible matrix marks;
- local view: direct evidence neighbourhood only, at most 80 rendered nodes
  before an explicit “show remaining” action;
- no new runtime visualization dependency.

## Non-goals and risks

- No full-network force layout.
- No inferred influence, similarity, chronology or geography edges.
- No merging active, review, authority-hold and auxiliary totals.
- No edits to v48 JSON, SQLite, gates or hashes.
- The current frontend object payload predates some v48 objects. Those roots
  return to their official source page until a separately audited frontend data
  sync adds an archive object route; the TRACE implementation must not silently
  create incomplete object pages.
- Aggregate geography uses the frozen normalized object geography labels. It is
  not a geocoded world map and must not substitute institution location.
