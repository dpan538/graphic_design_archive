# Canonical Open Inquiry registry and isolated API

## Authority

The product registry is generated only from these two machine-readable Round
16B sources:

- `docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/scoped-association-hypothesis-ledger-shard-1-v1.tsv`
- `docs/audits/v49-exploration-higher-order-association-closure-round16b/raw/scoped-association-hypothesis-ledger-shard-2-v1.tsv`

The generator verifies the source bytes, headers, row-level record hashes, and
final line endings before normalizing any field. It preserves the complete
source hypothesis ID as the stable inquiry ID. It does not derive records from
conversation text or from the validated pair-association read model.

The canonical product artifact is:

`frontend/generated/trace-open-inquiry-v1/open-inquiry-registry.v1.json`

Its deterministic builder is:

`scripts/trace_round16b_integration/build_open_inquiry_registry.py`

## Inventory

`SCOPED_HIGHER_ORDER_HYPOTHESIS_COUNT=11`

`ARITY_2_COUNT=3`

`ARITY_3_COUNT=6`

`ARITY_4_COUNT=1`

`ARITY_5_COUNT=1`

`ACTIVE_PENDING_REVIEW_COUNT=0`

The three arity-2 records remain unresolved Open Inquiry records. They are not
validated pair associations. Four source records carry governed
inquiry-only association identities; that identity does not confer validation
or product activation.

## Epistemic and display contract

Every record carries the following invariant policy:

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
```

The registry contains no truth probability, likelihood score, confidence
percentage, or stochastic-display field. Open Inquiry ordering is
deterministic. Display eligibility means that an explicitly labelled Open
Inquiry surface may display the record; it does not make the record eligible
for validated results.

## Independent read-only API

The Open Inquiry API is independent from Validated Exploration:

```text
GET /api/trace/v1/open-inquiry
GET /api/trace/v1/open-inquiry/{inquiry_id}
```

Both resources also implement read-only `HEAD` and `OPTIONS` behavior. The list
returns the complete deterministic inventory. The detail resource accepts only
an exact stable source hypothesis ID. The list rejects every query parameter;
there is no filtering, pagination, sampling, randomization, or
`include-unresolved` switch.

The API responds with `Cache-Control: private, no-store`, an explicit
`OPEN_INQUIRY` layer header, a false validated-relation header, and the bound
registry digest. Registry-integrity failure returns no partial records.

## Isolation boundary

The implementation imports neither the Validated Exploration v2 module nor the
fail-closed v3 research runtime. Open Inquiry records are absent from validated
association responses and cannot change validated maps, compositions, states,
transitions, workflows, trees, PNG exports, or metrics. No mutation endpoint is
implemented.

This API makes the unresolved inventory inspectable. It does not establish
pair, higher-order, global-composition, product-reachability,
computational-space, or Function 3 closure.
