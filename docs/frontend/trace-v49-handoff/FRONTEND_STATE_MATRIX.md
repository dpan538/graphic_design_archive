# TRACE frontend state matrix

## Scope

This matrix defines observable frontend states for implemented TRACE data
boundaries. It does not prescribe layout, color, typography, animation, or
other visual design.

Every state transition must preserve the active function, product layer,
release identity, and last server-confirmed state. A response from one function
or Exploration layer must never be used as fallback data for another.

## Shared state meanings

| State | Required meaning | Required behavior |
| --- | --- | --- |
| Initial | No request has been started for the current identity. | Do not imply that data is empty or unavailable. |
| Loading | A bounded request is pending. | Mark the affected region busy, retain its accessible name, and announce completion or failure. Do not randomize placeholders or alter semantic state. |
| Populated | The server returned a valid non-empty response. | Render only server-returned records and preserve stable IDs, labels, provenance, and ordering. |
| Empty | The server returned a valid response whose contract explicitly permits no items. | Say that no governed data is available for the selected scope. Do not infer, synthesize, or borrow records. |
| Partial | A contract-authorized subset is complete while another bounded request remains pending. | Identify what is complete and what remains. Partial does not mean malformed, integrity-failed, or silently truncated. |
| Error | The server rejected the request or failed closed. | Preserve the last confirmed state only when the matrix permits it, identify that it is stale, expose retry only for a repeatable request, and never convert an error into Empty. |

HTTP `HEAD` and `OPTIONS` are contract checks, not user-visible content states.

## Function and resource matrix

| Function / resource | Loading | Empty | Partial | Error and recovery |
| --- | --- | --- | --- | --- |
| Context Canvas — object context | Bind loading to the requested public stable record ID. Do not mount local canvas data while the governed lookup is pending. | `availability="empty"` is a successful record-specific state. Show the selected record and state that it has no published governed representations. | Not supported. The dataset, explanations, and accessible rows are one integrity-bound unit. | For invalid ID, not found, release mismatch, or integrity failure, mount no replacement dataset. Preserve the requested ID for correction; retry only the same governed request. |
| Spacetime — periods | Block period-dependent requests until the governed periods response succeeds. | An empty period inventory is not an accepted functional state; treat it as integrity failure rather than fabricating a default. | Not supported. | On invalid argument or integrity failure, do not request an atlas and do not select a local default period. |
| Spacetime — atlas for one period | Bind loading to release and period. Keep an already rendered atlas only if it is explicitly labelled as the prior period while the new request is pending. | A valid atlas may contain zero marks for a period; preserve its governed totals, mapping states, and precision disclosures. | Not supported within one atlas response. | On missing period, release mismatch, or integrity failure, do not render marks from another period under the failed selection. Retry the same release-period pair. |
| Spacetime — geography records, first page | Bind loading to release, period, and geography. | A valid zero-item page means no governed records for that selection. It does not mean the geography or period is absent. | Not applicable before the first page succeeds. | Invalid `period`, `first`, `after`, cursor, or identity is an error. Do not fall back to unpaginated local records. |
| Spacetime — geography records, later page | Keep already confirmed pages available and label the pending append. Disable duplicate requests for the same cursor. | A successful terminal page ends pagination; it does not erase earlier pages. | Allowed: confirmed earlier pages plus an explicitly pending later page. Apply a page only when its release, period, geography, and cursor chain still match the active request identity. | Preserve confirmed pages, announce that more records could not be loaded, and retry only the failed cursor. A stale response must be ignored. |
| Validated Exploration — categories and capabilities | Request these before enabling category or export choices that depend on them. | Zero categories or a count mismatch is not a supported product-empty state; fail closed. | Categories and capabilities may load independently, but a control remains unavailable until its own contract is present. Do not infer capabilities from categories. | Show the API error code and retryable state. Do not substitute the retired v1 API or Open Inquiry data. |
| Validated Exploration — create or retrieve map | Bind loading to category entry or map/state identity. | A valid map may have a bounded visible subset, but no successful empty map contract exists. Missing composition or state is an error. | Not supported within a map response: state, composition, nodes, associations, plain-text tree, and hashes form one server-confirmed unit. | Keep the last confirmed map only if it is labelled unchanged. Do not merge fields from the failed response. Correct invalid input or retry a retryable integrity failure. |
| Validated Exploration — state action | Keep the last confirmed map visible and mark only the submitted action pending. Send its `expected_state_hash`. | Not applicable. | The prior state is complete while the transition is pending; do not apply optimistic node, edge, focus, expansion, or composition changes. | On `STALE_EXPLORATION_STATE`, reload the authoritative state. On invalid or unavailable actions, leave the prior state unchanged. Never replay against a different database snapshot. |
| Validated Exploration — vocabulary or association detail | Bind loading to the stable vocabulary or association ID. | Not supported; an unknown identifier returns an error. | Not supported. | Preserve the originating validated map and report that the detail is unavailable. Do not fill from Open Inquiry participants or evidence. |
| Validated Exploration — plain-text tree | Treat the tree as part of the same map response, not as a separately inferred client state. | Not supported for a valid map response. | Not supported. | If the map/tree unit fails integrity, do not generate a replacement tree from visible nodes or associations. |
| Validated Exploration — export manifest | Bind loading to exact map ID, state hash, composition ID, preset, and theme token set. | No exportable composition is an error, not an empty file. | Not supported. | Keep the interactive map unchanged. Surface invalid, stale, version-mismatch, request-limit, or integrity failures without downloading a file. |
| Validated Exploration — PNG or SVG bytes | Announce that deterministic export rendering is in progress after the manifest input is fixed. | A zero-byte or wrong-content-type response is an error. | Do not offer a partial download. | `RENDER_CAPACITY_EXCEEDED` may be retried against the same state. Any other render or integrity failure must not produce or relabel bytes as a validated export. |
| Open Inquiry — inventory | Label the pending region `Open Inquiry` before requesting data. Do not show validated associations as placeholders. | The canonical registry currently requires exactly 11 items. A successful response with another count fails the handoff integrity contract; it is not a product-empty state. | Not supported. The API is unpaginated and returns one deterministic registry-bound inventory. | Show an Open Inquiry-specific error. Never fall back to Validated Exploration, a chat transcript, or locally copied hypotheses. Retry only when `retryable=true`. |
| Open Inquiry — detail | Bind loading to the stable `inquiry_id` and retain the Open Inquiry label. | Not supported; an unknown or malformed ID returns `OPEN_INQUIRY_NOT_FOUND`. | Not supported. Evidence fields may contain governed `null` values, but the record itself remains a complete response. Render null as not recorded, not as inferred absence of evidence. | Keep the inventory available if it is still current, but do not substitute a neighboring record. Integrity failure closes both list and detail access until a fresh validated response succeeds. |

## Layer-isolation rules for all states

1. A loading or error state in Open Inquiry cannot alter a validated map.
2. A validated action or export cannot carry an Open Inquiry ID, participant,
   relation form, evidence field, or provenance value.
3. Context and Spacetime selections may be preserved as navigation context, but
   they are not semantic inputs to Exploration.
4. Search results, rankings, and query state are outside this matrix and must
   not be introduced as TRACE fallback behavior.
5. Cached content must retain its source function, layer, release/database
   identity, and hash. A cache hit does not relax integrity validation.

## Accessible state communication

- Use `aria-busy="true"` on the bounded region whose request is pending, not on
  the entire application when other functions remain usable.
- Announce loading completion, zero governed results, pagination failure, and
  retryable errors through a non-disruptive live region. Use an alert for a
  fail-closed state that removes the requested content.
- Move focus only after an explicit navigation action; background refreshes
  must not steal focus.
- Never communicate unresolved/validated status, mapping state, error, or
  selection by color alone.
