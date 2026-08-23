# Accessibility Contract

Accessibility is part of functional acceptance and is not deferred with visual styling.

## Semantic equivalent

`TraceContextDataset.accessibleRows` is the reference non-graphic representation. The route exposes a labeled list/table containing the selected record and typed dataset connections. Every currently visible connection has a matching row with the same stable category and category-specific facts; hiding a node may mark/filter its row as not currently on canvas but MUST NOT erase the underlying dataset representation.

The SVG has an accessible name and concise operating instructions that identify it as a local composition view. Nodes expose label, kind, stable public reference, canvas visibility/selection state, and an action to inspect. Connections expose category and endpoint labels. The accessible name MUST distinguish controlled assignment, curated membership, and accepted semantic edge; it MUST NOT call all lines relationships.

## Keyboard contract

| Target | Required operation |
|---|---|
| Template selector | Native select keyboard behavior; choosing a template is announced |
| Palette | Tab to named Drag/Add controls; Enter/Space on either reveals the entity without requiring pointer drag |
| Palette disclosure | Enter/Space toggles; `aria-expanded` and controlled region are accurate |
| Toolbar | Native buttons in logical order; Enter/Space activates; disabled state uses the native attribute |
| Canvas node | Tab focuses; Enter/Space selects; Arrow keys move 10 world units; Shift+Arrow moves 1; movement is announced |
| Canvas connection | Reachable SVG hit target or equivalent connection-list control; Enter/Space selects and opens inspector details |
| Canvas/background | Escape clears selection or cancels an active gesture; zoom, fit, and reset have button alternatives to gestures |
| Inspector | Logical heading/content order; Close and Collapse are buttons; Escape may close; focus returns to the invoking item/canvas |

Pointer drag is never the only method to add or move an entity. Wheel zoom and background pan are supplemented by Zoom In, Zoom Out, Fit, and Reset View controls. A user can understand all context data without manipulating the graphic.

## Focus and selection

Visible keyboard focus MUST remain distinct from selection and meet current focus-indicator requirements. Selecting an SVG item exposes programmatic state (for example `aria-pressed` or an equivalent selected state) and updates the inspector heading. Hiding a focused node moves focus to a predictable palette/add or canvas target. Template/reset actions restore focus to the invoking control unless that control is removed.

Connection paths may use a larger transparent hit target, but visual and accessible representations point to the same stable connection ID. Decorative route segments and export-only metadata are hidden from the accessibility tree.

## Status and errors

A polite status region announces entity added/already visible/hidden, root-hide rejection, auto-arrange, reset, undo/redo, template change, and successful export. Errors use an appropriate alert or assertive announcement without repeatedly interrupting normal pointer movement. Drag preview and every node `pointermove` are not announced; the committed end position is.

The Export button exposes `aria-busy` or equivalent state during `EXPORTING`; Undo and Redo expose true disabled states. Errors never strand focus or remove the accessible-row representation.

## Visual and touch fundamentals

Functional styling MUST provide readable text contrast, non-color-only selection/category cues, visible focus, usable zoom, and practical touch targets. Final colors, typography, and visual language remain deferred, but redesign may not regress contrast, focus, target size, reduced-motion preferences, or semantic labeling.

Pointer Events support mouse, trackpad-derived pointer, and touch. On narrow screens the palette and inspector may collapse or become sheets, but their disclosure buttons, Add actions, toolbar alternatives, status region, and accessible rows remain operable without horizontal page-level dependency.

## Acceptance checks

Automated/pure checks verify accessible-row coverage, stable accessible names, native disabled/busy attributes in rendered output where repository conventions allow, keyboard reducer actions, root protection, and focus-target decisions. The user performs final browser visual acceptance; this round deliberately does not start localhost or capture screenshots.
