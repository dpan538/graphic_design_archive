# Asset Preview Capture Constraints

Date: 2026-06-01

These constraints govern all visual asset review work for cards, slips,
bookmarks, reading notes, appendices, sheets, and text pages.

## Canonical Preview Loop

Every asset design review must use a stable preview loop:

1. Implement or update the asset layout.
2. Run the relevant build or preview server.
3. Capture the asset through the project screenshot script.
4. Inspect the generated screenshot paths and manifest.
5. Only then report the design state to the user.

For text pages the current commands are:

```bash
npm run preview:text-pages
npm run capture:text-pages
```

The preview server uses `127.0.0.1:3037` so it does not collide with the
main project browsing session.

## Hard Rules

- Do not claim a visual fix is complete without a fresh screenshot generated
  after the latest code change.
- Do not reuse a stale `/private/tmp` screenshot path as evidence for a new
  design revision.
- Do not crop a full-page screenshot manually and present it as a layout
  proof.
- Do not switch between Quick Look, static HTML, browser tabs, and manual
  screenshots during the same review without recording the switch and the
  reason.
- Do not use the user's visible browser window as the verification surface.
- Do not accept a page if the capture manifest reports overflow, broken
  images, missing groups, empty groups, or incorrect page ratio.
- Do not keep designing when the capture path is broken. Stop and repair the
  preview/capture loop first.
- Treat deletion/filtering requests as membership-only changes. If the user
  asks to remove specific layout IDs or keep a named set, only update the
  layout membership array, selector, or preview grouping required to express
  that set. Do not alter the remaining layout components, CSS, surface
  bindings, proportions, scale, or screenshot framing unless the user
  explicitly asks for a redesign.
- Preserve the last accepted screenshot state as a baseline when filtering a
  group. Before reporting, verify the kept layout IDs, page classes, rendered
  dimensions, and manifest result against the accepted baseline.
- If a layout-ID instruction is ambiguous, stop and repeat the exact IDs that
  will be kept or removed. Do not silently remap the request into a new
  composition.

## Screenshot Evidence

Every screenshot run must produce:

- one full-page capture;
- one capture per review group;
- a `manifest.json` with capture paths, source URL, run id, page counts,
  ratio checks, image checks, and overflow checks.

For text pages, the expected groups are:

| Group | Selector | Expected role |
|---|---|---|
| image | `[data-text-group="image"]` | vertical image/text pages |
| text | `[data-text-group="text"]` | vertical spread-led pure text pages |
| horizontal | `[data-text-group="horizontal"]` | horizontal 2:3 pages |
| experimental | `[data-text-group="experimental"]` | experimental vertical text pages |

## Text Page Asset Rules

- Text pages are not bookmarks, cards, slips, tickets, or appendices. They may
  borrow typographic tension from print references, but not the functional
  border language of those other assets.
- Do not use a source image as a full-page or soft background on text pages.
  Images must remain explicit evidence plates with visible boundaries or
  captions.
- Do not use a multi-image wall unless the same surface carries at least three
  distinct renderable image URLs. If that condition is not met, fall back to a
  single evidence plate plus text/citation structure.
- Text pages must preserve reading hierarchy: title/entry page, body page,
  marginal note, image evidence, and citation roles should be visibly distinct.
- A layout is only reusable if it defines a content constraint, such as minimum
  text length, image count, image orientation tolerance, or source/citation
  density. Do not ship one-off compositions that only work for a single
  selected surface.

## Failure Response

If the screenshot tool fails, the next action must be one of:

- fix the screenshot tool;
- fix the preview route;
- document the blocker and stop.

The next action must not be another unverified layout change.
