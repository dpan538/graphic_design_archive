# TRACE known limitations and open design questions

This document bounds the frontend handoff. It records unresolved product questions without beginning visual design, Search design, or deployment work.

## Governing status

TRACE Exploration is evidence-bounded. Its validated layer currently contains 21 evidence-qualified pairwise generic associations. Round 16B records 11 scoped higher-order hypotheses as unresolved Open Inquiry records; they are not validated relations, do not generate implicit pair edges, and do not enter validated results by default. External human review remains pending.

The following closure flags remain false:

```text
PAIR_ASSOCIATION_CLOSURE=false
HIGHER_ORDER_ASSOCIATION_CLOSURE=false
GLOBAL_COMPOSITION_COHERENCE_CLOSURE=false
PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE=false
COMPUTATIONAL_SPACE_CLOSURE=false
FUNCTION3_CLOSURE=false
```

The package is a functional frontend handoff, not evidence of research closure or frontend completion.

## Cross-cutting limitations

- Frontend visual design is not implemented by this package.
- The API contracts do not establish complete historical, pair, higher-order, global-composition, product-reachability, computational-space, or Function 3 closure.
- Authentication is not introduced by the documented TRACE routes; this package does not define an identity or authorization model.
- Responses are generally integrity-bound and fail closed. Offline fallback behavior is not specified and must not cross layer boundaries.
- The handoff does not authorize analytics, personalization, ranking, recommendations, or stochastic display.
- Search is outside this execution. No Search navigation, query model, visual treatment, ranking, or cross-function integration should be inferred from these documents.
- Deployment has not been performed and is outside this handoff.

## Function 1 — Context Canvas

Known limitations:

- Context represents governed project-curated medium, theme, and movement-context classifications. Region is deliberately deferred to Spacetime.
- Context connections are navigation context, not historical or Exploration associations.
- The existing page is marked as an unlinked governed-data workspace and is not a completed cross-site navigation experience.
- Workspace persistence is browser-local and bound to schema/template, data mode, release manifest, Context projection, and selected record. It is not an account-synced workspace.
- Browser PNG generation depends on image and 2D-canvas support and has explicit dimension/area limits.
- An invalid record parameter or projection integrity failure mounts no canvas dataset; no partial recovery UI is specified.

Open questions that preserve the evidence boundary:

- Which governed public-record entry points should link to Context Canvas?
- Should the accessible row equivalent be always expanded or user-collapsible while remaining immediately discoverable?
- What non-visual wording best explains the difference among medium, theme, and movement context without implying a historical relation?
- Should local saved-state presence be announced before restoration, and how should users explicitly discard it?

## Function 2 — Spacetime

Known limitations:

- Temporal values describe recorded context and use interval-overlap membership; they are not necessarily exact event dates.
- Geographic values describe recorded region context. Aggregate marks and synthetic density dots are not object coordinates.
- Mapped, aggregate-only, and unmapped geography are distinct governed states. A missing shape does not mean zero records.
- `realSemanticEdgeCount` is zero; geographic co-occurrence creates no semantic relation.
- The current client keeps selected period, geography, mode, viewport, and pagination state in memory rather than in a durable deep link.
- Record pagination is forward/cursor-based, at most 100 records per request; the current workspace requests 25.
- A functional export value exists in code, but no public Spacetime export endpoint or finished download control is defined.
- Geometry load failure and atlas load failure are separate states; a final fallback experience beyond the accessible data already loaded is not specified.

Open questions:

- Which subset of period/geography/mode state, if any, should become URL-addressable after validation against the projection hash?
- How should aggregate-only and unmapped geographies remain equally discoverable when no selectable geometry exists?
- Should a future Spacetime functional download expose canonical JSON only, or JSON plus a separately verified SVG artifact?
- How should the UI explain range-overlap membership beside a selected period without overwhelming the record list?

## Function 3 — Validated Exploration v2

Known limitations:

- The validated graph is limited to the current 31-word vocabulary and 21 evidence-qualified pairwise generic associations.
- “Generic association” is not a typed historical relation, direction, chronology, causality, hierarchy, influence, or exhaustive topology claim.
- The v2 state space is governed and bounded: four categories, 81 entries, 228 production compositions, 5,760 states, and at most eight visible nodes.
- English is the only supported locale.
- The only export preset is a 1080 × 1620 portrait card; the server offers two neutral token sets.
- Rendering has bounded concurrency and queue capacity.
- The interactive v2 frontend surface itself is not implemented by this handoff.
- v2 responses are private/no-store and tied to a database snapshot; durable client caching across snapshots is not supported.

Open questions:

- Which existing application route should host Validated Exploration without implying that the older `/trace` Evidence Atlas is a fourth TRACE function?
- How should category entry, focused node, composition, and state identity be represented in browser history while keeping the server authoritative?
- Should the Unicode or ASCII tree be the initial copy format, while keeping both immediately available?
- How should retryable render capacity and non-retryable stale-state errors be explained without losing the current readable map?

## Function 3 — Open Inquiry

Known limitations:

- The inventory is exactly the 11 scoped hypotheses derived from the canonical Round 16B machine-readable ledgers. It is not a claim about the size of a complete higher-order universe.
- All records are unresolved and pending external human review; none is active or product-eligible.
- The API is read-only and intentionally separate from Validated Exploration.
- The list and detail routes accept no query parameters and expose no pagination, filtering, sorting, mutation, or stochastic sampling.
- The API supplies no truth probability, probability-true field, likelihood score, or confidence percentage.
- Open Inquiry has no export route.
- Some records have inquiry-only governed association identities while others do not. That difference does not make either group validated.
- Nine further excluded higher-order structures are known, while the complete exclusion universe remains indeterminate; excluded structures are not added to the 11-record Open Inquiry registry by this contract.

Open questions:

- Should the inventory retain canonical registry order in every frontend view, or expose a deterministic client-only grouping by arity with an explicit non-ranking label?
- Which provenance details should be expanded initially, provided that evidence incompleteness and nonclaims remain visible without expansion?
- How should very long stable IDs remain copyable while participant labels remain the primary readable heading?
- What explicit transition text should appear when moving between Validated Exploration and Open Inquiry so users understand that the graph did not change?

Questions that are not open under this contract:

- There will be no “include unresolved” switch on the validated API.
- Open Inquiry records will not generate pair edges or modify validated topology.
- Inquiry display will not be stochastic.
- Inquiry evidence will not be converted into a probability or validation score.

## Exploration v3 runtime and controls

Known limitations:

- v3 is a read-only runtime/integrity catalog rather than the v2 interactive map contract.
- Its direct resources and synthetic controls use identical collection names but different explicit data classes.
- The current v3 headers state fail-closed product activation and no active product state graph.
- Synthetic controls are not Open Inquiry records and are not user-facing unresolved hypotheses.
- An `exports` collection record describes governed export traceability; it does not render an image.

Open questions:

- Does a frontend consumer need v3 inspection at all, or should it remain an engineering/audit surface?
- If exposed, what plain-language explanation prevents `SYNTHETIC_CONTROL` from being mistaken for live data or Open Inquiry?
- How should baseline-reconciliation failures be surfaced without redirecting to v2 or substituting controls?

## Decisions required before frontend implementation

The frontend owner should resolve and record:

1. routes and browser-history rules for Validated Exploration and Open Inquiry;
2. whether any currently in-memory Spacetime state becomes a governed deep link;
3. accessible labels and persistent evidence-boundary disclosure for every Function 3 layer;
4. deterministic, non-ranking Open Inquiry inventory order;
5. empty, stale, integrity-failure, and retryable-capacity copy;
6. which existing public-record surfaces may navigate into Context or Spacetime using explicit governed IDs;
7. whether v3 remains audit-only;
8. test coverage for zero leakage from Open Inquiry into validated maps, trees, exports, metrics, or navigation state.

None of these decisions permits changing the canonical data, adding implicit relations, expanding evidence claims, beginning Search work, or deploying the application.
