# Current-leaf validation

The final fixture covers: no successor, one successor, a multi-level chain, non-conflicting branches, rejected/withdrawn and failed-review candidates, validated/sealed lifecycle, review-decision supersession, equal-timestamp UUID tie-break, self-cycle rejection, orphan rejection, cross-object rejection, and exclusion of non-current assignments.

Required indexes are `canonical_assignment_current_leaf_v5_idx` and `assignment_review_decision_current_leaf_v5_idx`. Existence alone is insufficient; raw final EXPLAIN evidence records actual planner use or a cheaper measured plan.
