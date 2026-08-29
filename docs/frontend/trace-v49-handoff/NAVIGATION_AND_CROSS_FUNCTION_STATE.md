# TRACE navigation and cross-function state

This document defines functional navigation and state ownership. It does not specify a menu treatment, layout, typography, motion, or other visual design.

## Canonical navigation hierarchy

TRACE has exactly three top-level functions:

```text
TRACE
├── Context Canvas
├── Spacetime
└── Exploration
    ├── Validated Exploration
    └── Open Inquiry
```

Validated Exploration and Open Inquiry are sibling layers within Function 3. Open Inquiry must not be implemented as a toggle that augments a validated response. The user must be able to tell which layer they entered from the page title, route/state identity, and accessible context.

Existing functional pages include `/trace/context-canvas` and `/trace/spacetime`. The handoff does not authorize a new route scheme for Exploration or any frontend visual implementation. Route choices that do not already exist remain an open frontend decision.

## State ownership

| Owner | Canonical identity | Ephemeral state | Persistence/retrieval rule |
|---|---|---|---|
| Context Canvas | research manifest, Context projection hash, selected public record ID | composition, viewport, selection, interaction, undo/redo, export phase | local storage is namespaced by schema/template version, data mode, manifest, projection, and record; invalid persisted content fails back to the default template |
| Spacetime | research manifest, Spacetime projection hash, selected period | selected geography, renderer mode, viewport, record-page cursor/accumulator | current implementation keeps interaction state in the mounted client workspace; new period/geography requests invalidate older responses |
| Validated Exploration v2 | database snapshot, map ID, state ID/hash, composition ID | pending action and pending export only | server state is retrieved by map/state identity; every transition sends `expected_state_hash` |
| Exploration v3 | read-model SHA-256, data class, collection, item ID | selected catalog record | read-only; direct and control catalogs remain separate |
| Open Inquiry | registry SHA-256 and stable inquiry ID | list/detail selection | read-only list/detail retrieval; no mutation, randomization, validated-state inheritance, or query-driven filtering |

No function owns another function’s state. Leaving Context must not rewrite its saved composition. Selecting a Spacetime geography must not focus an Exploration node. Opening an inquiry must not change a validated composition.

## Deep-linkable identity

### Context Canvas

The existing page accepts `?record={publicStableId}`. Only a bounded `SURF-…` public stable ID is valid. On invalid input, the page mounts no dataset and reads or writes no local composition. The persisted canvas key includes the selected record and governed projection identity, so it must not be copied to another record or release.

### Spacetime

The API has stable period and geography identifiers, but the current page holds selection in component state. Do not claim that selected period, geography, renderer mode, or record-page position is currently deep-linkable. If URL serialization is later added, parsing must validate identities against the loaded governed projection before applying them.

### Validated Exploration

`map_id` identifies the governed category entry, while `state_id` and `state_hash` identify a precise state. A URL may carry opaque identifiers, but the server remains authoritative. On load, retrieve the state through `GET /api/trace/v2/exploration/maps/{mapId}?state_id={stateId}`; never synthesize state from URL fields.

If the database snapshot differs or the state no longer belongs to the map, show the service error and offer a governed reset. Do not silently select a “nearby” state.

### Open Inquiry

An inquiry detail can be addressed by its complete stable `R16B-HYPOTHESIS:…` or `R16B-SCOPED-HYPOTHESIS:…` ID. Preserve the full ID when generating a detail request. A missing or malformed ID is not an empty detail; it is `OPEN_INQUIRY_NOT_FOUND`.

## Cross-function links are navigational, not semantic

A cross-function link may carry only an identifier explicitly understood by the destination contract. It means “open this governed resource,” never “assert a relation between the source and destination.”

Permitted examples:

- a Spacetime record summary links to its public surface detail by `stableId`;
- a public record may open Context by that record’s governed public ID;
- a validated Exploration node or association may open its own v2 detail endpoint;
- an Open Inquiry list item may open its own inquiry detail.

Not permitted:

- using matching text labels to join Context representations to Exploration vocabulary;
- interpreting records in one period/geography as an association;
- projecting an Open Inquiry participant set into pairwise navigation links presented as validated edges;
- carrying a v3 control identifier into a direct active-product route;
- treating a browser breadcrumb or recent-history entry as evidence provenance.

Where no explicit destination identifier exists, present plain text rather than an invented link.

## Function-entry reset rules

- Entering Context initializes or restores only the composition keyed to the exact governed Context identity.
- Changing the Context record creates a different persistence namespace and clears active selection/history for the newly mounted record.
- Changing the Spacetime period clears geography selection, record pages, and map zoom before accepting the new atlas.
- Changing the Spacetime geography clears the old record accumulator; pagination resumes only from the cursor returned for the new period/geography pair.
- Creating a v2 map replaces any prior v2 state with the returned initial state.
- Applying a v2 action replaces the map atomically with the returned governed state. Never merge response fragments.
- Entering Open Inquiry starts in its own list/detail state and does not inherit validated focus, expansion, composition, metric, or export state.
- Moving between v3 direct and `/controls/` routes resets the selected data class. Do not keep an item visible under the wrong class.

## Back, forward, refresh, and concurrent requests

The implementation must define these behaviors before frontend completion:

- Browser back/forward restores only state represented in the URL. Local-only interaction state must not be claimed as history state.
- Refresh revalidates every server-owned identity. Context may restore a validated local composition; v2 must retrieve its state again; Open Inquiry must bind again to the registry hash.
- A new request cancels or supersedes the older request in the same state channel. Spacetime already uses separate request epochs for atlas and records.
- Loading in one function must not disable unrelated function navigation.
- An error in one layer must not fall through to another layer. In particular, Open Inquiry failure must not display validated records as a substitute.

## Required route-state labelling

Every Function 3 view must expose an accessible layer label:

- “Validated Exploration” for v2 validated vocabulary, associations, maps, trees, and PNG export;
- “Open Inquiry — unresolved, evidence incomplete” for the inquiry inventory and detail;
- “Exploration v3 active product facts” or “Exploration v3 synthetic controls” for v3 catalog inspection.

The label is part of the functional contract. It cannot rely only on color, iconography, position, or a transient announcement.

## Non-contamination invariant

Navigation must preserve this invariant across refreshes and transitions:

```text
validated associations before navigation
= validated associations after navigation
= 21

Open Inquiry implicit pair projections
= 0
```

Navigation may change what the user is reading. It must not change the governed graph, composition, export, or metrics.
