# Context Canvas Functional Decision

- **Decision date:** 2026-08-23
- **Source foundation:** TRACE v49 at `c5f4e794580607116206a9986ac6a549257f3bd2`
- **Status:** `DIRECTION_CONFIRMED / IMPLEMENT_NOW`

## Decision

Context Canvas is the first TRACE function. It is an ERD-like research composition workspace over an immutable `TraceContextDataset`, not a canonical data editor and not a relationship-authoring tool.

The functional prototype uses React, one SVG world-coordinate viewport, Pointer Events, and small pure TypeScript helpers. It adds no graph, canvas, layout, or export dependency. Semantic projection, composition state, deterministic layout, viewport transforms, rendering, persistence, and PNG export remain separate modules so a later visual redesign can replace presentation without changing meaning.

## Product boundary

| In scope | Out of scope |
|---|---|
| Four deterministic, non-empty templates | Empty-canvas authoring |
| Palette add/drag of dataset entities | Creating canonical entities |
| Automatic display of dataset-backed connections | Drawing, editing, accepting, or rejecting relations |
| Node reposition/hide, selection, inspector | Editing archival fields or predicates |
| Pan, zoom, fit, reset view, auto-arrange | Database or frozen-release writes |
| Bounded composition undo/redo and local persistence | Publishing proposed candidate context data |
| Canvas-only PNG export | SVG export or external export service |
| Synthetic, public-safe prototype fixture | Raw v49 candidate tables or v48 TRACE assets |

Removing a node means `HIDE_FROM_COMPOSITION`; it never means deleting source data. Position and visibility are local composition properties and carry no historical, chronological, causal, certainty, or similarity meaning.

## Semantic decision

The renderer preserves the foundation's separate types:

- `TraceControlledAssignment` renders as `controlled_assignment`;
- `TraceCuratedMembership` renders as `curated_membership`;
- accepted `TraceSemanticEdge` renders as `semantic_edge`;
- `TraceSourceAssociation` remains structurally distinct and is not given new public semantics;
- `TraceVisualGuide` remains `semantic:false` and is not promoted to a dataset connection.

A connection is visible only when it exists in the input dataset and both endpoint entities are visible. The production v49 semantic-edge population remains zero. Any semantic-edge exercise in this route is explicitly synthetic contract data with `historicalEvidence=false`.

## Evidence basis and readiness

This decision consumes, rather than repeats, the completed census and preprogram foundation:

- [`08_CONTEXT_DOMAIN_READINESS.md`](../trace-v49-round1/08_CONTEXT_DOMAIN_READINESS.md) records the candidate-data governance boundary and measured maximum of nine object-local context associations.
- [`13_TRACE_VISUALIZATION_CAPACITY_ENVELOPE.md`](../trace-v49-round1/13_TRACE_VISUALIZATION_CAPACITY_ENVELOPE.md) supports a small synchronous SVG implementation.
- [`14_TRACE_PUBLIC_READ_MODEL_REQUIREMENTS.md`](../trace-v49-round1/14_TRACE_PUBLIC_READ_MODEL_REQUIREMENTS.md) defines the future release-owned public projection.
- [`15_PREPROGRAMMING_VALIDATION.md`](../trace-v49-round1/15_PREPROGRAMMING_VALIDATION.md) records semantic type separation and immutable, accessible projections.

The route therefore runs in `synthetic-contract-only` mode. Functional readiness does not imply real-data readiness or final visual-design readiness.

## Functional completion condition

The round is functionally complete when the route can initialize from all four templates; add, hide, drag, select, inspect, arrange, pan, zoom, fit, reset, undo, redo, persist, and export; exposes an equivalent accessible-row representation; passes invariants `CTX-CANVAS-INV-001` through `018`; and does so without touching protected data, Search, current `/trace`, Spacetime, or Exploration Field surfaces.

## Explicit deferrals

`Spacetime` remains map-first parameter governance work and is not implemented here. `Exploration Field` remains open-ended factor/data-mining work and is not implemented here. Typography, color, spacing, motion, final component language, final node/edge appearance, and brand treatment are deferred to the later frontend redesign.
