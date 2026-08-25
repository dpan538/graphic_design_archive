# TreeStrategy topology specification

All strategies retain one root inquiry, one primary inquiry flow, at most two semantic Nodes, at most two siblings, maximum depth four, and at most seven total items.

- `LINEAR_PATH`: one non-branching inquiry sequence with distinct start, evidence-check, continuation, and sequence-boundary roles.
- `BINARY_FORK`: a root with two explicit alternative question branches; no exclusivity of historical truth is implied.
- `BINARY_CONVERGENCE`: two branches carry separate bounded concepts and a convergence item contains structural references to both inputs.
- `QUALIFIED_PATH`: continuation is a descendant of a mandatory qualification gate and cannot bypass it.
- `REFLEXIVE_RETURN`: a navigation target returns to the root after an actor/self-positioning question; the parent tree remains acyclic and no semantic self-loop exists.
- `EVIDENCE_GAP_TREE`: supported and unresolved root branches are peers, and the missing-evidence branch owns a first-class evidence-gap item.

Canonical topology signatures omit labels, strategy names, and IDs while preserving item kinds, parent indexes, depth, branch status, convergence references, and navigation targets. The six neutral synthetic signatures are distinct.
