# TRACE function tree

## Canonical hierarchy

TRACE has exactly three top-level functions.

```text
TRACE
├── Context Canvas
├── Spacetime
└── Exploration
    ├── Validated Exploration
    │   ├── validated vocabulary and associations
    │   ├── composition and map state
    │   ├── plain-text tree
    │   └── validated PNG export
    └── Open Inquiry
        ├── inquiry inventory
        ├── inquiry detail
        ├── evidence-incomplete disclosure
        ├── provenance access
        └── no validated-layer contamination
```

`TRACE_TOP_LEVEL_FUNCTION_COUNT=3`

No route, version, renderer, export format, shared infrastructure component, or
legacy surface creates a fourth TRACE function.

## TRACE Function 1 — Context Canvas

Context Canvas presents a selected public record together with governed,
project-curated context representations for medium, theme, and movement
context. It uses the committed Context V1 projection through:

`GET /api/v1/releases/{release}/trace/objects/{id}/context`

The response supplies selected-record metadata, representations, explanations,
provenance, counts, and accessible rows. `availability="empty"` is a valid
governed state. Context Canvas must not infer missing representations or import
Search, geography, Spacetime, or Exploration semantics.

Context Canvas already has a functional, unlinked workspace. This handoff does
not redesign it or authorize public navigation.

## TRACE Function 2 — Spacetime

Spacetime presents recorded project context by governed period and geography.
Its read resources are:

- `GET /api/v1/releases/{release}/trace/spacetime/periods`
- `GET /api/v1/releases/{release}/trace/spacetime/atlas?period={periodId}`
- `GET /api/v1/releases/{release}/trace/spacetime/geographies/{geographyId}/records?period={periodId}&first={n}&after={cursor}`

The API distinguishes mapped, aggregate-only, and display-unmapped outcomes
and exposes temporal precision rather than inventing exactness. A region value
is recorded context; it is not an object coordinate, a claim of historical
presence, a movement path, an influence relation, or an Exploration
association.

Spacetime already has a functional, unlinked workspace. This handoff does not
redesign it or authorize public navigation.

## TRACE Function 3 — Exploration

Exploration has two and only two product layers.

### Validated Exploration

Validated Exploration is the deterministic product layer backed by 31
vocabulary records, 21 evidence-qualified pairwise generic associations,
governed compositions, immutable map states, server-built plain-text trees,
and validated export manifests and bytes.

The frontend-facing state API is `/api/trace/v2/exploration`. The server owns
category entry, composition selection, map state transitions, visible nodes
and associations, plain-text trees, semantic and presentation hashes, and
export manifests. The frontend renders these values; it does not requalify an
association or synthesize a topology.

The implemented `/api/trace/v3/exploration` baseline, reconciliation,
collection, and control resources remain part of Validated Exploration's
evidence and integrity infrastructure. They do not create another function or
an Open Inquiry layer. See the complete API catalog for their intended
frontend use and limitations.

Validated associations are generic and non-directional. Their presence does
not assert causality, influence, hierarchy, chronology, equivalence, identity,
or quantified historical strength.

### Open Inquiry

Open Inquiry is a separate, explicitly labelled, deterministic read layer for
11 unresolved scoped higher-order hypotheses:

- `GET /api/trace/v1/open-inquiry`
- `GET /api/trace/v1/open-inquiry/{inquiryId}`

The list and detail responses expose the inquiry's bounded scope,
participants, relation form, evidence-incomplete status, explicit nonclaims,
and provenance. Each record declares that it is not validated and cannot enter
the validated graph, composition, topology, export, or metrics.

Open Inquiry is not selected with `include_unresolved`, is never mixed into a
Validated Exploration response, and does not project an arity-2, arity-3,
arity-4, or arity-5 inquiry into implicit pair edges.

## Explicit non-members

- Search is outside TRACE and outside this handoff.
- The legacy `/trace` Evidence Atlas surface does not add a top-level function.
- HTTP methods, API versions, shared release identity, caches, and repository
  adapters are infrastructure, not functions.
- SVG is an implemented validated export transport, but the canonical product
  tree names the validated PNG export; neither format creates a function.
- Open Inquiry provenance links do not authorize mutation, adjudication, or
  activation from the public frontend.

## Closure status

```text
PAIR_ASSOCIATION_CLOSURE=false
HIGHER_ORDER_ASSOCIATION_CLOSURE=false
GLOBAL_COMPOSITION_COHERENCE_CLOSURE=false
PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE=false
COMPUTATIONAL_SPACE_CLOSURE=false
FUNCTION3_CLOSURE=false
```
