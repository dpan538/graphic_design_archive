# Open Inquiry UX contract

## Contract status

Open Inquiry is the explicitly labelled, deterministic, read-only layer for 11
scoped higher-order association hypotheses that remain unresolved. It belongs
under TRACE Function 3 — Exploration, beside Validated Exploration. It is not a
validated-result option and it is not a source of pair edges.

```text
Exploration
├── Validated Exploration
└── Open Inquiry
```

`SCOPED_HIGHER_ORDER_HYPOTHESIS_COUNT=11`

`ACTIVE_PENDING_REVIEW_COUNT=0`

`EXTERNAL_HUMAN_REVIEW_STATUS=PENDING`

## Independent API boundary

| Purpose | Methods | Route | Query parameters | Result |
| --- | --- | --- | --- | --- |
| Inquiry inventory | `GET`, `HEAD`, `OPTIONS` | `/api/trace/v1/open-inquiry` | None; any query parameter is rejected. | One registry-bound response containing `count=11` and all records. |
| Inquiry detail | `GET`, `HEAD`, `OPTIONS` | `/api/trace/v1/open-inquiry/{inquiryId}` | None; any query parameter is rejected. | One registry-bound response containing the matching record. |

Do not add `include_unresolved`, `include-unresolved`, `open_inquiry`, or an
equivalent flag to a Validated Exploration request. Do not concatenate, union,
normalize, or cache Open Inquiry records as validated vocabulary,
associations, compositions, states, trees, exports, or metrics.

Success responses identify:

- `api_version="trace-open-inquiry/v1"`;
- `layer="OPEN_INQUIRY"`;
- the canonical `registry_sha256`;
- `evidence_bounded=true`;
- `validated_layer_contamination_allowed=false`;
- `implicit_pair_projection_allowed=false`;
- `validated_topology_mutation_allowed=false`;
- `stochastic_display=false`.

The frontend must reject or fail closed on a layer, boundary, count, or stable
identity that violates those values.

## Record-level invariants

Every displayed record must retain these exact machine-readable values:

```text
epistemic_status=UNRESOLVED_OPEN_INQUIRY
validated_relation=false
counts_as_validated=false
eligible_for_validated_graph=false
eligible_for_validated_composition=false
may_generate_pair_edges=false
may_modify_validated_topology=false
display_eligible=true
display_layer=OPEN_INQUIRY
default_in_validated_results=false
active=false
external_human_review_status=PENDING
product_eligible=false
product_path=null
participant_order_meaningful=false
relation_roles_asserted=false
pair_projection_policy=NONE
implicit_pair_projection_count=0
```

These fields are constraints, not optional badge metadata. A record that fails
one of them must not render as an Open Inquiry success state.

## Required inventory behavior

- Title the layer `Open Inquiry` and label its items `Unresolved open inquiry`.
- Preserve the canonical response order. Do not shuffle, randomly sample,
  rotate, weight, score, recommend, or stochastically reveal records.
- Display the inventory count as `11 scoped open inquiries`. Do not express it
  as a percentage or denominator-based coverage claim.
- A client-side text filter, if later approved, may only hide or reveal records
  already present in the confirmed response. It cannot rank them or change the
  canonical count. No such interaction is authorized by this handoff.
- Use `inquiry_id` for identity and navigation. `inquiry_key` is a stable
  readable key, not a replacement identity and not a truth claim.
- Show arity as the number of participants. Never project a multi-participant
  record into pair cards or pair links.
- Preserve participant presentation without implying sequence, direction, or
  semantic roles; the registry declares that order is not meaningful and
  relation roles are not asserted.

## Required detail behavior

An inquiry detail must expose, without interpretation:

- the `inquiry_key`, stable `inquiry_id`, arity, participant labels, and
  participant sense IDs;
- `bounded_scope` and `relation_form`;
- the evidence-incomplete state, support mode, disposition, available scoped
  status fields, qualifications, counterevidence, and explicit nonclaims;
- inquiry-only association identity when supplied, while retaining its
  non-product and non-validated status;
- provenance: authority base SHA, shard ID, source ledger path and hash, source
  row number and record hash, source IDs, rights record IDs when present,
  linked parent candidate, preserved parent disposition, source review status,
  and source activation status.

Governed `null` means the canonical registry does not supply that value. Render
it as `Not recorded for this inquiry`; do not infer a negative or positive
historical conclusion.

Place this disclosure in the detail's ordinary reading order, before any
provenance link:

> Evidence incomplete. This unresolved open inquiry is not a validated
> relation and does not change Validated Exploration.

The disclosure must remain available to assistive technology and in any
text-only rendering. It must not be reduced to a tooltip, color, icon, hover
state, or inaccessible abbreviation.

## Provenance access

Provenance is inspection access, not a public write or activation workflow.
The frontend may expose repository-relative source paths from the response as
copyable text or as links only when the deployment environment can safely
resolve them. It must always show the associated hash and source row so a human
reviewer can verify the exact record.

Do not turn `source_ids`, rights records, authority paths, or parent candidate
IDs into historical relation edges. Do not imply that an inquiry with more
locators, sources, or participants is more likely to be true.

## Validated-layer contamination barrier

Open Inquiry data must never:

- enter the 21 validated pairwise generic associations;
- create implicit pairs from any arity-2, arity-3, arity-4, or arity-5 record;
- add, remove, reorder, or relabel a validated composition node or association;
- change focus, expansion, selection, state hash, semantic hash, presentation
  hash, topology family, or available action in a validated map;
- appear in the validated plain-text tree;
- appear in a validated PNG, SVG, or export manifest;
- affect a validated count, reachability result, metric, ranking, or category;
- be submitted to a Validated Exploration action or export endpoint;
- be persisted under a Validated Exploration cache or state key.

Cross-navigation may carry only a return location and stable destination ID.
It cannot carry semantic state between layers.

## Prohibited probability and confidence UI

Do not create or derive:

```text
truth_probability
probability_true
likelihood_score
confidence_percentage
```

Do not replace these prohibited fields with stars, gauges, percentages,
traffic-light scores, progress bars, `likely/unlikely`, or an unlabeled
confidence ranking. Evidence fields describe bounded documentation status; they
do not estimate whether the hypothesis is true.

## Loading, empty, partial, and error behavior

- Loading: announce `Loading Open Inquiry records` or
  `Loading unresolved open inquiry`. Do not use validated records as skeleton
  content.
- Empty: the canonical inventory requires exactly 11 records. A different
  count is an integrity error, not a friendly empty state.
- Partial: the API is unpaginated and all-or-nothing. Do not show a truncated
  inventory as complete. Governed nullable detail fields do not make a record
  partial.
- Not found: show `The requested Open Inquiry record does not exist.` and a
  route back to the inventory. Do not substitute another record.
- Unsupported query: remove the unsupported parameter before retrying; do not
  silently ignore it.
- Registry integrity failure: remove unverified inquiry content, preserve no
  cached claim as current, and retry only when the response marks the failure
  retryable.

## No write path

The frontend must not expose approve, reject, activate, validate, publish,
score, edit, merge, split, promote, or create-pair actions. External human
review remains pending and occurs outside this read-only public contract.
