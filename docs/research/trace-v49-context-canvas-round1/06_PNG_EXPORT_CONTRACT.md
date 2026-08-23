# PNG Export Contract

## Required result

`Export PNG` downloads a deterministic 2× rasterization of the full visible Context Canvas composition. It includes nodes, dataset-backed connections, labels, a solid default background, and an optional isolated public-safe footer. It excludes the palette, toolbar, inspector, browser chrome, selection outline, hover/focus treatment, drag preview, status messages, and other application UI.

## Native-browser pipeline

No export dependency or external service is permitted. Export uses:

```text
immutable composition snapshot
→ derive visible typed connections and shared SVG geometry
→ compute full node bounds plus export padding/footer allowance
→ build export-only SVG with explicit presentation attributes
→ XML serialize
→ SVG Blob + temporary object URL
→ decode into Image
→ draw on HTMLCanvasElement at scale=2
→ canvas.toBlob("image/png")
→ temporary download URL
→ revoke both URLs and release temporary objects
```

Export snapshots committed state at activation. Later pointer or viewport changes cannot alter that export. The current screen viewport does not crop output; bounds come from all visible node boxes. The export renderer reuses layout/connection geometry helpers but not interactive SVG DOM cloning, preventing application chrome from leaking into the file.

## Dimensions and rendering

- Default scale is `2`; the internal API accepts a finite future scale parameter within a guarded implementation limit.
- CSS output dimensions derive from full content bounds plus padding; bitmap dimensions are the rounded CSS dimensions multiplied by scale.
- The implementation rejects empty, non-finite, zero, or unsafe browser-size bounds before canvas allocation.
- Presentation attributes and a solid background are serialized explicitly; export does not depend on external stylesheets, web fonts, images, authentication, or network fetches.
- Selected/focused/hovered state is ignored so equal committed layout and export options produce equal SVG geometry/content.

PNG encoder bytes and timestamps need not be byte-identical across browsers. The export-only SVG snapshot MUST be deterministic for the same public dataset, visible IDs, positions, template version, and export options.

## Public-safe metadata and filename

The optional footer is an isolated export concern and may contain only:

```text
Context Canvas · <selected public record ID> · <public release ID>
```

It MUST NOT contain an internal UUID, held/private state, source URL, raw payload, local-storage key, evidence locator, or private release path. The footer can be removed or redesigned without changing composition geometry.

The filename contract is:

```text
context-canvas-<safe-public-record-id>-<YYYYMMDD-HHmmss>.png
```

Sanitization accepts only a known public selected-record ID, replaces runs outside `[A-Za-z0-9_-]` with `-`, trims separators, applies a reasonable length bound, and falls back to `record` if empty. A value shaped like an internal UUID or not equal to the dataset's public selected-record ID is never used.

## State, accessibility, and failure

Activation moves export state from `IDLE` to `EXPORTING`; the button exposes a busy state and duplicate activation is disabled. Completion returns to `IDLE` and announces the filename. SVG serialization, image decode, canvas allocation, `toBlob`, or download failure moves to recoverable `EXPORT_ERROR`, announces a concise error, revokes allocated URLs, creates no partial download, and leaves composition/persistence unchanged.

## Verification hooks

Pure tests cover export bounds, default scale, deterministic export SVG, inclusion of visible nodes/connections, omission of selection and application chrome markers, safe footer fields, filename sanitization, and rejection of private/internal identifiers. Browser visual acceptance is intentionally left to user review; no localhost or screenshot workflow is part of this round.
