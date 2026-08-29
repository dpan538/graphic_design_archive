# State and Transition Census

The product state space is fully materialized from category entry, production composition, seed, focus node, and expansion subset. Visible nodes and associations are deterministic projections of that state. States are immutable; actions return a hash-bound next state.

| Metric | Value |
| --- | --- |
| States enumerated | 5760 |
| States validated | 5760 |
| Unreachable production states | 0 |
| Duplicate state hashes | 0 |
| Transitions enumerated | 749944 |
| Transitions executed | 749944 |
| Transitions passed | 749944 |
| Transitions failed | 0 |
| State mutation count | 0 |
| Stale-state accepted count | 0 |
| Invalid-target accepted count | 0 |

## Action distribution

| Action | Count |
| --- | --- |
| COLLAPSE_NODE | 9240 |
| EXPAND_NODE | 8112 |
| EXPORT_CURRENT_STATE | 5760 |
| FOCUS_NODE | 18480 |
| MOVE_FOCUS | 7824 |
| RESET_CATEGORY | 5760 |
| SELECT_CATEGORY | 23040 |
| SELECT_COMPOSITION | 671728 |

States per production composition range from `8` to `64`. Transitions per state range from `15` to `157`.

`ALL_REACHABLE_STATES_ENUMERATED=true`

Sources: `docs/audits/v49-exploration-full-space-closure-round1/raw/state-census-v2.tsv`, `docs/audits/v49-exploration-full-space-closure-round1/raw/transition-census-v2.tsv`, and `docs/audits/v49-exploration-full-space-closure-round1/raw/space-generation-summary-v2.json`.
