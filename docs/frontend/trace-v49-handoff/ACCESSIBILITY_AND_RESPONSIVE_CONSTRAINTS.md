# TRACE accessibility and responsive constraints

These are testable functional constraints for a future frontend. They do not prescribe a visual style or begin frontend design.

## Baseline requirements

- Use native landmarks, headings, links, buttons, labels, lists, tables, and disclosure controls before custom interaction semantics.
- Preserve a logical document and focus order when content reflows. DOM order must carry meaning without reference to screen position.
- Every action must be keyboard operable. Pointer drag may supplement, but never replace, add/remove, move, focus, expand/collapse, period selection, geography selection, pagination, or export controls.
- Show keyboard focus. Do not make layer, selection, status, evidence state, mapping state, or validation state depend only on color.
- Announce asynchronous completion with a polite live region and errors with an alert. Avoid repeating the whole result on every state change.
- Associate every loading region with `aria-busy`; keep its stable heading or label available while data loads.
- Retain meaningful text at 200% browser zoom and under operating-system text enlargement without two-dimensional page scrolling for ordinary reading content.
- Respect reduced-motion preferences. No transition is required for comprehension.
- Touch targets and controls must remain independently operable at narrow widths; hover must not be the only way to reveal information.

## Function 1 — Context Canvas

The graph-like canvas requires an equivalent non-spatial representation. The governed Context dataset already supplies `accessibleRows`, and the current workspace builds rows for the selected record, visible nodes, and visible connections. The future frontend must keep that equivalent synchronized with the visible composition.

Required behavior:

- expose the selected root record and every visible contextual representation in text;
- expose connection labels, publication state, explanation wording, and provenance without requiring pointer inspection;
- identify node and connection selection programmatically;
- keep the root non-removable and explain a blocked removal through the status region;
- provide keyboard node movement as an alternative to drag;
- provide undo, redo, reset/layout, zoom, and export as labelled buttons with accurate disabled state;
- return focus predictably after add/remove, reset, or export;
- cancel an in-progress drag without committing an unintended position;
- never announce project-curated Context connections as historical relations.

At narrow widths, controls, canvas, inspector, palette, and accessible rows may become sequential regions. Reflow must not change the composition’s semantic membership. A clipped canvas may scroll or zoom independently, while the page-level text equivalent remains readable without canvas manipulation.

## Function 2 — Spacetime

The SVG map is an aggregate selector, not the sole data representation. Preserve:

- a programmatic title and description naming the selected period and explaining that marks are derived aggregate layout positions;
- the complete `accessibleRows` geography table as the numerical equivalent;
- row buttons that select the same geography as the map;
- mapping state, record count, denominator, temporal precision, and interpretation in text;
- a record list with a status while loading and a labelled load-more control;
- explicit text for mapped, aggregate-only, and unmapped states;
- a textual legend for aggregate, density, or texture mode.

Do not expose synthetic dot positions as object locations. Texture/pattern and map geometry must not be necessary to discover a count. When the map cannot render, retain the table and qualifications where the governed atlas itself remains valid.

On a narrow viewport, the selected-geography details and accessible table must follow the period controls in a coherent reading order. A horizontally constrained data table may use a labelled scroll container, but geography name and selection control must remain discoverable.

## Function 3 — Validated Exploration

The map and its plain-text tree are equivalent governed representations. The frontend must:

- make category and category-entry controls explicitly labelled;
- expose focused and expanded state programmatically;
- provide every currently available action without requiring spatial gestures;
- expose each association’s `association_accessible_description` and `explicit_non_claims`;
- keep node and association counts synchronized with the current state hash;
- render the server-provided Unicode tree and offer its ASCII equivalent;
- preserve tree whitespace in a semantic text container and support copying without mutation;
- announce stale-state and database-snapshot conflicts without discarding the user’s understanding of what changed;
- use the manifest’s `export_alt_text` for a validated PNG preview or download description.

At narrow widths, a graph may become independently pannable, but controls, current-state summary, plain-text tree, and nonclaims remain in normal reading flow. Do not hide the tree merely because a graph is available.

## Function 3 — Open Inquiry

Every list and detail view must carry a persistent accessible label equivalent to:

> Open Inquiry — unresolved, evidence incomplete; not a validated relation.

For every record, expose:

- stable inquiry ID and bounded scope;
- arity and participant labels/sense IDs;
- unresolved epistemic status;
- evidence disposition, qualifications, counterevidence, nonclaims, and provenance when present;
- pending external-human-review status;
- the statements that it does not count as validated, generate pair edges, enter validated composition, or modify validated topology.

Do not convey unresolved status only with a badge color. Do not show probability bars, confidence percentages, star ratings, or stochastic ordering. The detail route must have a useful heading even when its ID is long; allow the identifier to wrap rather than truncate the only copyable value.

Because there are exactly 11 records and the API has no pagination or filtering, a frontend may render one complete inventory. Any client-only rearrangement must be deterministic, clearly labelled, and must not suggest evidence ranking.

## v3 active/control distinction

If v3 inspection is exposed, `ACTIVE_PRODUCT_FACT` and `SYNTHETIC_CONTROL` must appear as text in the view’s persistent accessible name. A control-only `404 NOT_ACTIVE_PRODUCT_FACT` requires an explanatory error; it must not redirect automatically into the control catalog because that would erase the boundary.

## Error and empty-state wording

- A valid zero-result state says what was queried and that no governed records were returned.
- `404` says the governed identity was not found; it is not a generic empty state.
- `409` says the validated Exploration state or database snapshot is stale and requires reload/reset.
- `503` integrity failures say that the layer failed closed. Do not expose raw exception text or substitute another layer.
- Retryable export capacity errors preserve the state and provide an explicit retry control.
- Unsupported Open Inquiry query parameters explain that the endpoint is an unfiltered read-only inventory.

## Export accessibility

- A download control names the format and current governed subject.
- While preparing, expose progress as indeterminate rather than inventing a completion percentage.
- The validated Exploration manifest alt text remains available next to a downloaded PNG.
- Context PNG metadata and full-label SVG titles do not replace an on-page text equivalent.
- Spacetime functional export qualifications travel with the exported value.
- Open Inquiry has no export control in this contract.

## Verification checklist

Frontend acceptance must include, at minimum:

- complete keyboard traversal and activation at desktop and narrow widths;
- focus retention after asynchronous loads, errors, resets, and downloads;
- screen-reader reading-order review for each top-level function and both Function 3 layers;
- 200% zoom and text-enlargement checks;
- reduced-motion and forced-colors checks;
- non-color identification of selected, unresolved, mapped/unmapped, active/control, error, and disabled states;
- map/canvas-to-table/tree content-equivalence tests;
- long public ID, long inquiry ID, long label, and long nonclaim wrapping;
- automated assertions that Open Inquiry content never enters validated accessible trees, metrics, or export descriptions.
