# Conceptual primitive contract

The pure TypeScript authority is `frontend/src/lib/trace/exploration-domain.ts`. It imports no React, DOM, Search, Context, Spacetime, archive API, renderer, or external model code.

`ExplorationNode` binds a conceptual ID and reference, governed-or-unresolved concept kind, epistemic status, optional provenance reference, and optional visual role. Conceptual IDs use explicit conceptual prefixes and reject known archive identity prefixes.

`ExplorationFlow` sequences conceptual node IDs. `GENERATIVE_COMPOSITION` and `USER_COMPOSED` always require `historicalClaim=false`. `EVIDENCE_BACKED` requires a governed evidence reference.

`ExplorationCluster` groups node and flow IDs for grammar/user composition only. Its positive schema has no similarity or implied-relation field, and its grouping rule rejects similarity/object-clustering semantics.

`ExplorationTreeMap` stores nodes, flows, clusters, branches, inter-cluster flows, constraints, and visual-role bindings. Reference integrity is validated. `topologyIsVisualGeometry` must be `false`.

The reset policy accepts only unresolved structural placeholders. A future governed policy must provide a governance reference plus explicit vocabulary, flow-kind, and directionality sets.
