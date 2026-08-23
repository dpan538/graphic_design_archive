# Layout and Connection Contract

## Coordinate and geometry model

Composition positions are finite world coordinates:

```ts
type ContextCanvasPosition = Readonly<{ x: number; y: number }>;
type ContextCanvasViewport = Readonly<{ x: number; y: number; zoom: number }>;
```

Viewport `x/y` are screen-space translation and `zoom` is clamped to `0.35..2.5`. The shared conversions are:

```text
screen = world * zoom + viewportTranslation
world = (screen - viewportTranslation) / zoom
```

Converters reject `NaN`, infinity, and zero/invalid zoom. Geometry, fit, and export use the same provisional known node box, `224 × 104` world units, rather than DOM measurement. Position is UI composition only and encodes no historical meaning.

## Deterministic typed-lane layout (`typed-lanes-v1`)

The pure layout function accepts visible entity IDs plus the immutable dataset and returns a complete position map. Lane precedence is:

1. selected/root object;
2. endpoints introduced by `controlled_assignment`;
3. endpoints introduced by `curated_membership`;
4. endpoints introduced only by `semantic_edge`.

An entity incident to multiple categories is assigned once to its earliest lane by this precedence. Within a lane, entities sort by normalized display label, then stable public ID. The root sorts first in the root lane. Coordinates are derived from shared node size and fixed functional horizontal/vertical gaps; no source-array order, random value, clock, current viewport, or DOM measurement participates.

The algorithm MUST return non-overlapping node boxes for the measured maximum workload, remain synchronous, and return deep-equal coordinates for equal inputs. `Auto Arrange` calls this helper; React components do not compute layout ad hoc.

## Connection derivation

The pure connection selector reads the dataset's typed collections separately. It emits renderer-neutral records keyed by category-qualified stable ID, for example `controlled_assignment:<id>`, preserving:

- actual `connectionKind`/category;
- stable source connection ID;
- source and target stable entity IDs;
- category-specific metadata used by the inspector and accessible name.

A record is returned only when both endpoint IDs are in the visible set. No geometry, shared label, co-occurrence, proximity, palette action, or previous composition may create a record. Hiding either endpoint removes only the derived rendered record. Re-adding the endpoint reveals the same source record again.

`controlled_assignment`, `curated_membership`, and `semantic_edge` remain distinct branches. The accepted semantic-edge source type is never populated from assignment or membership data. Visual guides, if later used, remain `semantic:false` and outside this connection result.

## Orthogonal routing

Connection geometry is a pure function of node boxes and the category-qualified connection ID.

1. Choose deterministic facing horizontal ports: right-to-left when target center is at or right of source center; left-to-right otherwise.
2. Compute a middle x coordinate between ports.
3. Route `M source → H middle → V targetY → H target`.
4. For connections sharing the same endpoint pair, stable-sort by category then ID and apply a small symmetric deterministic middle-lane offset.
5. Place any functional label at the stable middle segment; label text comes from source metadata, not inferred prose.

Paths recompute immediately from preview positions during node drag. There are no random control points, force simulation, global optimizer, or mutable SVG path objects. Equal visible IDs and positions MUST produce byte-equivalent path data.

## Fit to content

The pure fit helper unions all visible `224 × 104` node boxes and applies a shared world/screen padding. Given viewport width `W`, height `H`, content bounds `B`, and padding `p`:

```text
zoom = clamp(min((W - 2p) / B.width, (H - 2p) / B.height), 0.35, 2.5)
translation = viewportCenter - contentCenter * zoom
```

One node uses its known box and centers safely. An empty composition returns a documented finite default viewport without division by zero. Invalid container sizes preserve the last valid viewport. Connections do not expand fit bounds beyond their endpoint nodes; optional export metadata has its own export-only allowance.

## View operations

Background drag changes translation only. Wheel/trackpad zoom preserves the world point below the pointer; button zoom preserves the viewport center. `Fit` derives the current content viewport. `Reset View` derives the current template's default fitted viewport. View operations never enter composition history or persistence as semantic data.

## Capacity and performance

The v49 census reports a maximum of nine object-local context associations and a conservative maximum of ten items. Layout, connection recomputation, fit, and reducer operations therefore remain simple synchronous helpers with a provisional aggregate benchmark target of `P95 < 5 ms`. This contract does not justify graph, force-layout, canvas, WebGL, or worker dependencies.
