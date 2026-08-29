# Round 16B v3 semantic contract and synthetic controls

Parent checkpoint: `e5ddbc443c4a0a28004034cba439340ecdeb9a75`
Source authority: `5419770959bdb8998b693fb2275b47e29b92367c`
Contract: `trace-exploration-v3-semantic-contract-1.0.0`

This checkpoint establishes an additive `trace/exploration/v3` semantic boundary. It leaves every v2 file, generated v2 artifact, frozen v49 database artifact, main ref, and tag untouched. It does not implement a production runtime or activate a historical claim.

## Implemented boundary

The 11 Draft 2020-12 schemas distinguish governed scopes, vocabulary concepts, bounded concept senses, pair and higher-order association revisions, participant incidences, evidence and governed review, fact-derived activation, uncertainty, first-class composition-coherence review, association realizations, compositions, bipartite navigation, workflows, exports, the normative hash-binding contract, and the one-way v2-pair adapter. Higher-order projection is explicitly `NONE`.

Association semantic hashes and presentation hashes are independently bound. Composition and association counts are separate. The input manifest pins the v2 compatibility surface and the checkpoint-007 method and review evidence used to define this contract.

The embedded and standalone machine-readable hash-binding contract freezes UTF-8 canonical JSON rules, exact semantic and presentation field projections, the executable `/scope` to `scope_identity` projection, sorted scope set arrays, canonical unordered participant storage, ordered contiguous ordinals, field aliases, revision wrappers, ID prefixes, and digest truncation for concepts, senses, associations, revisions, incidences, composition-coherence reviews, realizations, compositions, states, workflows, exports, the adapter, and its synthetic v2 source fixture. Four identity-branch receipts commit both full materials and canonical incidence IDs so an independent verifier can recompute permutation, order, and role semantics.

## Synthetic control census

- synthetic pair revisions: 9
- synthetic active pair revisions: 9
- synthetic higher-order revisions: 5
- synthetic active higher-order revisions: 1
- governed synthetic scopes: 6
- governed synthetic concepts: 21
- governed synthetic bounded senses: 21
- governed active synthetic concepts: 11
- governed active synthetic bounded senses: 11
- synthetic incidences: 37
- synthetic association realizations: 10
- synthetic composition-coherence reviews: 2
- synthetic compositions: 2
- production active associations: 0
- production product-eligible compositions: 0
- implicit projected pairs: 0

The controls cover a valid arity-five hyperedge with a sparse, disconnected internal pair graph backed by two governed active pair revisions; a globally invalid four-node clique backed by all six governed active pair revisions; a bounded-sense conflict; a cross-case bundle; a genuinely governed isolated active synthetic term in a valid hyperedge; a renderable but globally invalid composition; forbidden hyperedge projection and subset realization; rejected activation under pending review; an active synthetic arity-five association whose projection policy remains `NONE`; and the one-way pair adapter. The 37 negative probes exercise fail-closed evidence, locator, conflict, scope, synthesis, support-provenance, authority, product, realization, navigation, workflow, and export boundaries.

## Evidence boundary and remaining work

`ACTIVE` in this fixture means only that the synthetic validator can exercise the valid state-machine branch. All fixture records live in `SYNTHETIC_CONTROL`; their production activation, product eligibility, and closure authority are false. No historical association is promoted.

The checkpoint gap ledger keeps production identity population, Round 16A global reconciliation, v3 runtime/database implementation, and the product arity bound open. Function 3 and every named closure dimension remain false.
