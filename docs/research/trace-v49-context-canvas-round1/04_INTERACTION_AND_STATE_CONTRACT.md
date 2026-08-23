# Interaction and State Contract

## State model

The required named states are represented by orthogonal, conflict-safe fields:

```ts
type Lifecycle = "INITIALIZING" | "READY";
type Interaction = "IDLE" | "PALETTE_DRAGGING" | "NODE_DRAGGING" | "PANNING";
type Selection =
  | { kind: "NODE_SELECTED"; id: string }
  | { kind: "CONNECTION_SELECTED"; id: string }
  | null;
type ExportState = "IDLE" | "EXPORTING" | "EXPORT_ERROR";
```

Only one `Interaction` may be active. `NODE_DRAGGING` and `PANNING` are mutually exclusive. Export uses an immutable composition snapshot; beginning export cancels no committed state but blocks template/reset actions until the snapshot is captured. Template switch and reset cancel any active drag/pan and release pointer capture.

## Composition state

The present snapshot contains `schemaVersion`, template ID/version, a de-duplicated visible stable-ID list, finite world positions by stable ID, and selection by stable canvas ID. The viewport is finite UI state but is excluded from composition undo history. Dataset entities and connections are referenced, not copied.

History stores `past`, `present`, and `future` composition snapshots with a maximum of 50 committed transitions. Adding after undo clears `future`. Initialization and persistence hydration do not create user history.

## Transition contract

| Event | Preconditions | State/result | History |
|---|---|---|---|
| Dataset/template initialize | `INITIALIZING`; validated dataset | deterministic composition, fitted view, `READY/IDLE` | none |
| Palette pointer down | eligible hidden entity; primary pointer | `PALETTE_DRAGGING`; drag preview identifies stable ID | none |
| Palette drop on canvas | valid finite world coordinate | entity visible at drop coordinate; incident known connections derive automatically; entity selected | one |
| Palette Add | eligible hidden entity | entity placed by deterministic add-position helper; entity selected | one |
| Duplicate add/drop | entity already visible | existing node selected/focused; no duplicate | none |
| Node pointer down/move | visible node; primary pointer | pointer capture; `NODE_DRAGGING`; preview world position updates geometry | none during move |
| Node pointer up | drag active | finite final position committed; `IDLE` | one if position changed |
| Node arrow key | focused visible node | move by 10 world units; Shift+Arrow moves by 1 | one per key activation |
| Background pointer drag | background or Space+drag | `PANNING`; viewport changes | none |
| Wheel / zoom control | `READY`; finite anchor | clamp zoom to `0.35..2.5`, preserve predictable anchor | none |
| Select node/connection | selectable stable ID exists | exactly one primary selection | none |
| Select background / Escape | no modal export capture | selection cleared; active non-export gesture cancelled | none |
| Hide from canvas | selected non-root visible node | node hidden; incident rendered connections disappear; selection clears | one |
| Hide root | root selected | rejected with status message | none |
| Auto Arrange | at least one visible node | deterministic typed-lane positions; selection retained | one if changed |
| Fit | at least one visible node | fit viewport from known bounds | none |
| Reset View | `READY` | restore the current template's default fitted viewport | none |
| Template change | target differs; not exporting | replace composition with deterministic target output | one |
| Reset Canvas | confirmation policy satisfied; not exporting | remove current storage entry, reapply current template, and clear composition history | clear past/future |
| Undo / Redo | matching stack non-empty | restore composition snapshot only | move snapshot between stacks |
| Export PNG | `READY`; content exists | `EXPORTING`, stable snapshot, then `IDLE` or `EXPORT_ERROR` | none |

All pointer conversions use `client → SVG viewport → world` coordinates. Invalid coordinates, missing IDs, stale pointer IDs, or non-finite viewport values fail closed and leave the last valid committed state intact.

## Selection and focus

Selection and DOM focus are related but not identical. Activating a node or connection selects it and moves focus to an appropriate accessible target. Selecting the background clears selection. Hiding a selected node or switching templates clears selection if its target no longer exists. Selection is programmatically exposed and never persisted as a mutable object copy.

## Persistence lifecycle

The storage identity combines release manifest SHA, selected stable record ID, Context Canvas schema version, template ID, and template version. Serialization stores stable IDs and finite numeric UI values only. Hydration validates identity, visibility eligibility, root presence, de-duplication, positions, and zoom bounds. Any parse, identity, or version failure discards the payload and initializes deterministically; it does not partially merge corrupt state. An explicit Reset Canvas also clears undo/redo history so stale pre-reset composition cannot restore persisted edits.

Storage quota or privacy-mode failure is non-fatal: the current in-memory composition continues, a concise status is announced, and future persistence attempts may retry. There is no account, server, API, canonical release, or PostgreSQL write.

## Status and error behavior

Add, hide, reset, undo/redo, auto-arrange, and export completion/failure produce concise `role=status` or live-region messages. Errors preserve the most recent valid canvas and return interaction state to `IDLE`. `EXPORT_ERROR` is recoverable by another export or composition action.
