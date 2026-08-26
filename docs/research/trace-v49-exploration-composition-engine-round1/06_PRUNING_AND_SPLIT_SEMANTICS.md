# Pruning and split semantics

Finite V1 pruning reasons are:

- `BOUND_SATISFIED_BY_STRICTLY_STRONGER_EVIDENCE`: a strictly stronger ordinal group already satisfies the bounded topology;
- `TOPOLOGY_DEGREE_BOUND`: both endpoints have no remaining slot under the topology-derived degree budget;
- `EQUAL_EVIDENCE_CAPACITY_TIE`: admission would depend on identity order, so the candidate remains unresolved;
- `ROUND14_ASSOCIATION_NOT_QUALIFIED`: frozen control, structurally ineligible rather than pruned.

Pruning is a composition decision, not historical rejection. A pruned candidate remains a qualified Round 14 association, retains provenance, and can appear in another bounded seed context.

`NO_QUALIFIED_BRIDGE_IN_INPUT` creates a split boundary when admitted qualified inputs form multiple components. It states only that this input needs multiple bounded images. Missing, failed, or non-selected bridges never serialize as false, unrelated, disproved, or historically separate.

Every `ADMITTED`, `PRUNED`, `SPLIT_BOUNDARY`, `EVIDENCE_GAP`, and `UNRESOLVED` state has a reason code and bounded human-readable explanation.
