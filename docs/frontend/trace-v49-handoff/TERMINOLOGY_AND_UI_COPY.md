# TRACE terminology and UI copy

## Canonical public statement

Use this statement verbatim wherever the full public evidence boundary is
required:

“TRACE Exploration is an evidence-bounded system rather than a claim of
complete historical closure. Its validated mode currently uses 21
evidence-qualified pairwise generic associations. Round 16B additionally
records 11 scoped higher-order association hypotheses as unresolved open
inquiries. These hypotheses are not counted as validated relations, do not
generate implicit pairwise edges, and may appear only in explicitly labelled
inquiry contexts. Nine further excluded higher-order structures are currently
known, while the complete exclusion universe remains indeterminate.”

Do not shorten this statement in a way that changes a count, drops the
unresolved status, omits the pair-projection prohibition, or implies closure.

## Canonical product names

| Meaning | Required UI label | Notes |
| --- | --- | --- |
| TRACE Function 1 | `Context Canvas` | `Context` may describe the dataset, but it is not the canonical function name. |
| TRACE Function 2 | `Spacetime` | One word, capitalized. Do not rename it `Timeline`, `Map`, or `GIS`. |
| TRACE Function 3 | `Exploration` | Parent of two distinct layers. |
| Function 3 validated layer | `Validated Exploration` | Use on navigation, headings, and any cross-layer destination. |
| Function 3 unresolved layer | `Open Inquiry` | Singular as the layer name. Use `Open inquiries` only as ordinary plural copy. |
| One unresolved record | `Unresolved open inquiry` | Never `validated relation`, `candidate edge`, or `suggested association`. |
| Validated relationship unit | `Evidence-qualified pairwise generic association` | It is generic and non-directional; it is not a typed historical TRACE relation. |
| Open Inquiry evidence state | `Evidence incomplete` | This does not mean false, rejected, or probably true. |
| Source inspection area | `Provenance` | Show stable source identity and hashes. It is not a confidence panel. |
| No supplied nullable value | `Not recorded for this inquiry` | Do not convert `null` into a historical claim. |

Use the canonical hierarchy exactly:

```text
TRACE Exploration
├── Validated Exploration
└── Open Inquiry
```

## Required Open Inquiry disclosure

Use this complete disclosure on inquiry details:

> Evidence incomplete. This unresolved open inquiry is not a validated
> relation and does not change Validated Exploration.

An inventory-level summary may use:

> 11 scoped open inquiries. These unresolved hypotheses are separate from
> Validated Exploration and generate no pair edges.

When linking between layers, use explicit destinations:

- `Go to Validated Exploration`
- `Go to Open Inquiry`
- `Return to Open Inquiry inventory`
- `View inquiry provenance`

Do not use `Show more relations`, `Include unresolved`, or `Expand the graph`
for Open Inquiry navigation.

## Validated Exploration copy

Use `association` rather than `relation` when referring to the 21 current
validated generic associations. When space permits, pair it with the boundary:

> Generic association only; no causal, directional, hierarchical, temporal,
> identity, equivalence, or quantitative relation is asserted.

Use server-supplied accessible descriptions for individual associations. Do
not generate stronger labels from endpoint order, screen position, path
direction, line direction, focus, expansion, or topology.

An interactive map state may use:

- `Loading validated map`
- `Validated map unavailable`
- `State changed elsewhere. Reload the validated state.`
- `Validated export is being prepared`
- `Validated export unavailable`

Do not describe a successful bounded map as a complete map of historical
design relations.

## Context Canvas copy

Use `Project-curated context` for governed medium, theme, and movement-context
representations. Preserve server-supplied explanation and accessibility text.

For a valid empty dataset, use:

> No governed Context representations are available for this record.

Do not use `No context exists`, and do not infer a representation from Search,
Spacetime, object metadata, or Exploration.

## Spacetime copy

Use `Recorded regional context` for geography aggregation. Preserve mapping
state and temporal-precision language supplied by the governed dataset.

Where a non-map outcome needs explanation, distinguish:

- `Mapped`
- `Aggregate only`
- `Display unmapped`

Do not say that a record was physically present at a map coordinate, moved
between locations, influenced another record, or belongs to an Exploration
association unless an independent, governed product contract explicitly says
so. None is authorized by this handoff.

## Count language

These current counts may be stated exactly:

```text
VALIDATED_PAIR_ASSOCIATION_COUNT=21
SCOPED_HIGHER_ORDER_HYPOTHESIS_COUNT=11
ARITY_2_COUNT=3
ARITY_3_COUNT=6
ARITY_4_COUNT=1
ARITY_5_COUNT=1
ACTIVE_PENDING_REVIEW_COUNT=0
KNOWN_EXCLUDED_HIGHER_ORDER_STRUCTURE_COUNT=9
COMPLETE_EXCLUSION_UNIVERSE=INDETERMINATE
```

The 11 inquiries are an inventory of scoped hypotheses, not a percentage of
any pair-combination count, mathematical node-subset count, or an unknown
higher-order universe. `ACTIVE_PENDING_REVIEW_COUNT=0` means none of the
pending-review records is active; it does not mean human review is complete.

The repository also records zero accepted typed historical TRACE relations.
That is compatible with 21 validated pairwise generic associations because the
two counts refer to different governed concepts. Do not merge or relabel them.

## Closure language

Whenever closure status is shown, preserve all six values:

```text
PAIR_ASSOCIATION_CLOSURE=false
HIGHER_ORDER_ASSOCIATION_CLOSURE=false
GLOBAL_COMPOSITION_COHERENCE_CLOSURE=false
PRODUCT_ASSOCIATION_REACHABILITY_CLOSURE=false
COMPUTATIONAL_SPACE_CLOSURE=false
FUNCTION3_CLOSURE=false
```

Allowed summary:

> TRACE Exploration is an evidence-bounded functional baseline. Function 3
> research closure has not been established.

Do not use `complete`, `comprehensive`, `closed`, `fully mapped`, `all
relations`, `entire space`, `exhaustive`, or an equivalent phrase to describe
Function 3, its pair associations, its higher-order inquiries, global
composition coherence, product reachability, or computational space.

## Probability and ranking language

Do not create, request, display, or derive:

```text
truth_probability
probability_true
likelihood_score
confidence_percentage
```

Also prohibited for Open Inquiry are probability synonyms or visual proxies,
including `likely`, `unlikely`, `chance`, `odds`, star ratings, percentage
meters, confidence gauges, score-ranked lists, recommendation labels, and
traffic-light truth indicators.

Existing evidence fields such as `support_mode`, `disposition`, exact-group
support status, global-coherence status, sense-scope status, qualifications,
and counterevidence must retain their source meaning. They are not truth
scores.

## Status and implementation copy

Use these current release statements when relevant:

```text
EXTERNAL_HUMAN_REVIEW_STATUS=PENDING
FRONTEND_VISUAL_DESIGN_IMPLEMENTED=false
DEPLOYMENT_PERFORMED=false
```

Do not describe this handoff package as a finished frontend, visual-design
approval, deployment authorization, or completed human review.
