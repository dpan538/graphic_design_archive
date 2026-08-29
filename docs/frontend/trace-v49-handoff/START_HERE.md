# TRACE v49 bounded frontend handoff — start here

“Do not scan the entire repository. Begin with this bounded handoff package.
Expand to implementation source only through the paths listed in
SOURCE_MANIFEST.json.”

## Purpose and status

This directory is the bounded implementation handoff for the three TRACE
functions: Context Canvas, Spacetime, and Exploration. It records the product
tree, API-facing state semantics, data and export contracts, navigation rules,
accessibility constraints, approved language, and the exact source paths needed
to verify those contracts.

This is not a visual design, a deployment instruction, a Search specification,
or a claim that TRACE research is closed.

`TRACE_TOP_LEVEL_FUNCTION_COUNT=3`

`FRONTEND_VISUAL_DESIGN_IMPLEMENTED=false`

`DEPLOYMENT_PERFORMED=false`

`EXTERNAL_HUMAN_REVIEW_STATUS=PENDING`

## Read in this order

1. `TRACE_FUNCTION_TREE.md` and `trace-function-tree.v1.json` establish the
   canonical three-function hierarchy.
2. `TRACE_API_CATALOG.md` and `trace-api-catalog.v1.json` in
   `../../api/trace/` enumerate the implemented HTTP surface. The catalog is
   authoritative for methods, schemas, source files, and tests.
3. `FRONTEND_STATE_MATRIX.md` defines loading, empty, partial, and error
   behavior without prescribing visual styling.
4. `OPEN_INQUIRY_UX_CONTRACT.md` defines the hard separation between
   Validated Exploration and Open Inquiry.
5. `DATA_CONTRACTS_AND_EXAMPLES.md` and `EXPORT_CONTRACT.md` describe payload
   handling and deterministic exports.
6. `NAVIGATION_AND_CROSS_FUNCTION_STATE.md` records navigation and state
   isolation across the three functions.
7. `ACCESSIBILITY_AND_RESPONSIVE_CONSTRAINTS.md` and
   `TERMINOLOGY_AND_UI_COPY.md` define non-negotiable access and language
   requirements.
8. `KNOWN_LIMITATIONS_AND_OPEN_DESIGN_QUESTIONS.md` identifies what this
   package intentionally does not decide.
9. `SOURCE_MANIFEST.json` is the only approved expansion path into
   implementation source. `HANDOFF_INTEGRITY_REPORT.md` records its integrity
   verification.

## Product boundary in one view

```text
TRACE
├── Context Canvas
├── Spacetime
└── Exploration
    ├── Validated Exploration
    └── Open Inquiry
```

Search is not a TRACE function. Open Inquiry is not a mode, flag, query
parameter, or extension of a Validated Exploration response.

Validated Exploration currently exposes 21 evidence-qualified pairwise generic
associations. Open Inquiry exposes 11 scoped higher-order hypotheses in a
separate, explicitly labelled, read-only API. Those 11 records remain
unresolved and cannot add pair edges, composition membership, map topology,
validated exports, or validated metrics.

## API orientation

Use the complete catalog for request and response schemas. These are the
frontend-facing entry boundaries:

- Context Canvas: governed object-context data at
  `GET /api/v1/releases/{release}/trace/objects/{id}/context`.
- Spacetime: governed periods, atlas, and paginated geography records at
  `GET /api/v1/releases/{release}/trace/spacetime/periods`,
  `GET /api/v1/releases/{release}/trace/spacetime/atlas?period={periodId}`,
  and
  `GET /api/v1/releases/{release}/trace/spacetime/geographies/{geographyId}/records?period={periodId}`.
- Validated Exploration: the stateful map, vocabulary, association, and export
  resources under `/api/trace/v2/exploration`.
- Open Inquiry: the independent inventory and detail resources at
  `GET /api/trace/v1/open-inquiry` and
  `GET /api/trace/v1/open-inquiry/{inquiryId}`.

All four boundaries are fail-closed. The frontend must consume the server's
semantic decisions and stable identifiers; it must not infer associations,
project higher-order records into pairs, rebuild validated compositions, or
silently substitute stale data after an integrity failure.

## Non-negotiable evidence boundary

```text
PAIR_ASSOCIATION_CLOSURE=false
HIGHER_ORDER_ASSOCIATION_CLOSURE=false
GLOBAL_COMPOSITION_COHERENCE_CLOSURE=false
PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE=false
COMPUTATIONAL_SPACE_CLOSURE=false
FUNCTION3_CLOSURE=false
```

The number 11 is an inventory count, not a percentage. Do not compare it with
any pair-combination count, mathematical node-subset count, or an unknown
higher-order universe.

## Implementation rule

Implement only behavior grounded in this handoff and its source manifest. When
a necessary interaction, layout choice, or copy variant is not specified,
record it as an open design question. Do not resolve it by adding semantics,
research claims, stochastic ranking, or cross-layer data joins.
