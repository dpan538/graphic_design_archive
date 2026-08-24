# Domain contract validation

Six structural checks pass:

1. Neutral Node, Flow, Cluster, and TreeMap fixtures validate.
2. Identical Image content produces identical canonical serialization/build hash.
3. Identical Image, seed, and generation policy produces identical Instance receipt.
4. Container state mutates without changing Image hash.
5. RenderedPng accepts only the safe closed metadata contract.
6. The active repository guard passes.

All fixtures use neutral structural IDs: `NODE-TEST-A`, `NODE-TEST-B`, and `FLOW-TEST-A`. No historical relation vocabulary is present.

## Required invariant result

All `EXP-RESET-INV-001` through `EXP-RESET-INV-030` pass: zero objects; no archive identity; no similarity/recommendation/Context/Spacetime/model/vector layer; both historical branches superseded; no invented vocabulary; all primitives retain their epistemic and mutability boundaries; sealed evidence remains recoverable; and Search, Context, Spacetime, and v49 database remain unchanged.
