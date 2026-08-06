# TRACE visual analytics and mobile research interface — v48 decision

Status: implemented visualization candidate; not a release layer
Working branch: `codex/v48-visual-analytics`
Frozen-data boundary: v48 JSON, SQLite, neighborhood shards, node IDs, edge IDs, and counts remain read-only

## Decision

Desktop and mobile are separate interaction systems that share the same frozen evidence model. They are not responsive-size variants of one composition.

- Desktop preserves the archive/editorial skeleton and uses wide, full-screen analytical fields for comparison, hover inspection, precise filtering, and evidence return.
- Mobile acts as the first-contact research interface: a brighter ticket-and-stamp print palette, touch-sized controls, compact explanations, vertically staged charts, and short paths to About, search, TRACE, GitHub, and citations.
- Both surfaces keep the same scholarly boundary: association, co-presence, source linkage, medium context, and geographic aggregation are never rendered as historical influence.

## Chosen visualization system

| Mode | Research question | Geometry | Scale strategy | Evidence boundary |
|---|---|---|---|---|
| Medium / context | In which recorded media and contexts does an object sit? | Metro line and station grammar | Selected object only | Context is not influence |
| Sources | Which sources, creators, collections, and records document an object? | Rooted evidence tree | Selected object only | Provenance branches do not imply descent |
| Time / geography | When and where are active objects recorded? | Equal Earth map, orthographic globe, time controller, regional aggregates | 15,569 mapped objects, progressively filtered | Region centroids are aggregates, not object coordinates |
| Evidence constellation | How are 30 research trees and 20 observed relation types distributed? | Deterministic concentric ranks, radial membership guides, annular edge-volume spans | Aggregated global overview | Spokes and spans are counts, never causal links |
| Evolution field | How does corpus density change over time? | Decade field, exact totals, regional and medium channels | Aggregated desktop overview | Distribution is descriptive, not a diffusion claim |
| Chronogeographic routes | Which regions appear in which decades? | Region-by-decade route table | Aggregated desktop overview | Co-presence stays outside TRACE edges |

The hybrid system remains the preferred architecture: locally readable object evidence plus globally aggregated analytical views. A global force-directed graph is rejected because it obscures relation semantics, performs poorly at this scale, and encourages unsupported causal reading.

## Frozen quantitative contract

| Field | v48 value |
|---|---:|
| Active objects | 15,923 |
| TRACE nodes | 97,889 |
| Documented relations | 255,695 |
| Active research trees | 30 |
| Observed relation types | 20 |
| Reserved `influenced_by` type | 0 edges |
| Source-verified objects | 12,952 |
| Metadata-supported objects | 2,971 |
| Review / hold objects | 4,425, isolated |
| Auxiliary non-counting objects | 11, isolated |

No visualization component may recompute these totals from mixed active, review, hold, or auxiliary layers.

## Mobile information architecture

### Entry and navigation

- Mobile uses one large menu button; the five desktop navigation controls remain independent on desktop.
- The opening folder interface is a touch wheel, not an archive-box simulation. The active card and one complete previous and next candidate remain visible; distant candidates become geometry-preserving placeholders and are rendered only when they approach the focus window.
- Region and period filters sit at the bottom of the folder route. `Unresolved` remains outside the active regional stack and is reported as an isolated review route.

### Research dashboard

The mobile About entry begins with a compact dashboard rather than a long source register. It exposes:

- active objects, evidence relations, and research-tree counts;
- decade density across all 23 buckets;
- the four largest documented relation types;
- source-verification share;
- the explicit zero-inferred-influence boundary.

Long source, design-reference, research-ledger, and license material is available through collapsed disclosure sections. The project description is shortened on mobile without removing the frozen-version statement.

### Citation and return routes

- GitHub is linked directly.
- APA, MLA, and IEEE project citations are visible and copyable.
- Clipboard failure retains selectable text and announces a non-visual fallback.
- Every TRACE node that has a destination retains an object or source return path.

## Visual language

The palette is a controlled spot-color system on paper white, not a multicolour theme.

- Paper remains cool-warm neutral and brighter on mobile.
- Blue denotes interaction, selection, and mapped research focus.
- Orange marks current emphasis or a critical non-inference boundary.
- Yellow is limited to timeline and ticket-like indexing events.
- Red, green, and violet appear only where relation family, evidence state, or medium branch requires them.
- Fine rules, serial marks, perforation rhythms, and restrained print texture borrow the information logic of rail tickets, postal stamps, civic ephemera, and modular modernist structures. They are not decorative replicas.

Desktop hover lowers surrounding saturation while keeping focused labels and exact values legible. Mobile does not depend on hover; focus is established through scroll position, tap state, disclosure, and staged vertical motion.

## Accessibility contract

- Touch targets and the mobile menu meet the large-control intent of the interface.
- Graph marks expose roles, keyboard activation, pressed/focus state, labels, SVG titles, and descriptions.
- Exact tables provide a non-graphic route for every constellation count and every object-local edge.
- Reduced-motion users never receive autoplay.
- The map, timeline, drawer, filters, citation controls, and search remain keyboard reachable.
- Colour is never the only carrier of relation family or evidence status.

## Performance budget

- Atlas summary loads first; active catalog, geographic geometry, and neighborhood shards remain lazy.
- Object diagrams render one selected neighborhood, never the entire corpus.
- Mobile folder cards keep only the focus window interactive while spacers preserve scroll geometry.
- Search caps rendered TRACE rows and loads the archive index only after a non-empty archive query.
- The 8,636 stable `/surfaces/[id]` reading routes and data-heavy `/folders/[type]/[slug]` readers render on demand instead of being rebuilt in full for every interface-only release. Route identity, reader pagination, and folder context are unchanged; the four folder indexes remain static.
- The real map uses 50m Natural Earth geometry. 15,569 objects map to audited region aggregates; 354 broad, historic, or unsupported labels remain explicitly unmapped.

## Acceptance evidence

The candidate must pass all of the following before promotion:

1. home/archive, About/mobile, and TRACE static verifiers;
2. full TypeScript validation and production build;
3. SQLite integrity plus frozen JSON and SQLite SHA-256 recheck;
4. desktop screenshots for every global and object-local visualization;
5. mobile screenshots for the card wheel, filters, dashboard, citations, search, source view, and scroll-accessible map;
6. remote commit verification after a non-force push.

## Remaining risks

- The 354 deliberately unmapped aggregate or historical labels require authority-backed geometry before they can enter the map.
- A higher-density search result view will require virtualization rather than raising the current render cap.
- Direct globe drag and keyboard rotation should be added only after measuring the mobile SVG cost.
- Review/hold overlays need further usability testing so that visibility never becomes statistical mixing.
- The citation clipboard API can be unavailable in controlled browsers; manual text selection remains the fallback.
