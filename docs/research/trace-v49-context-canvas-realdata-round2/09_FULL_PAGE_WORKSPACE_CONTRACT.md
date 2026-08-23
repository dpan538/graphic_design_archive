# Full-Page Workspace Contract

## Route and page shell

The research workspace remains at `/trace/context-canvas` and accepts `?record=<PUBLIC_STABLE_ID>`. It is not added to global navigation and does not replace `/trace`.

The route is a server component with `robots.index=false` and `robots.follow=false`. It does not use `ArchiveShell`. `page.module.css` defines a `100dvh` shell with hidden outer overflow so the accessible reference cannot lengthen the document into an archive-style page.

## Functional regions

| Region | Responsibility | Scrolling |
| --- | --- | --- |
| Top | title, mode, selected public ID, record picker, template and toolbar context | fixed within workspace flow |
| Left | selected-record entity palette | independent overflow |
| Center | pan/zoom Canvas viewport and toolbar | consumes remaining primary space |
| Right | current node/connection inspector | independent overflow |
| Integrated reference | semantic non-graphic equivalent in expandable `details` | bounded internal overflow |

At narrow widths, the functional panels stack; the accessible reference remains capped at 38% of available height and 320 pixels. This is a usability fallback, not final responsive visual design.

## Data-mode states

When `CONTEXT_CANVAS_REAL_VALIDATION` is absent or disabled, the route remains in the shared synthetic-contract path. With the explicit gate enabled:

- no record parameter selects a deterministic public sample;
- an eligible public ID loads one real validation dataset;
- malformed, held, unknown, and projection-failure states render an explicit fail state;
- failed lookup never mounts an empty Canvas.

The active workspace identifies the data mode, selected public stable ID, validation release, and not-published/candidate status. It does not claim governed public availability.

## Accessibility contract

The integrated reference is the semantic authority for the current visible composition. It must contain the selected record and the same visible controlled assignments, curated memberships, and semantic edges as the graphic. For real v49, the semantic-edge section is empty.

Full original values remain in accessible rows even when Canvas display text is shortened. Node `aria-label` and SVG `<title>` also retain the full value. The all-object verifier established row identity, completeness, uniqueness, and parity for all 31,980 object/template cases, with zero accessible-row mismatches or duplicate rows.

## Deferred visual work

This contract establishes viewport occupation, independent scrolling, state visibility, and accessibility. Typography, color, density, panel styling, responsive composition refinement, and export aesthetics remain intentionally deferred to a later visual-design round.
