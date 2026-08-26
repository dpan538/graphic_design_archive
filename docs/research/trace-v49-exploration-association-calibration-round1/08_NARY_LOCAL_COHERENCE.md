# N-ary local coherence

V1 validates every semantic-node pair at shortest graph distance 1 and 2. Pairs beyond distance 2 are not hard-gated unless the future layout places them in a meaningful visual-neighbourhood band. All-to-all association is explicitly unnecessary.

Topology rules:

- `LINEAR_PATH` and `QUALIFIED_PATH`: adjacent path pairs are direct; nodes two steps apart are skip-one.
- `BINARY_FORK`: root/branch pairs are direct; sibling concepts are skip-one.
- `BINARY_CONVERGENCE`: inputs/convergence concept pairs are direct; distinct inputs are skip-one.
- `REFLEXIVE_RETURN`: the semantic path is validated normally; navigational return is not a semantic self-loop.
- `EVIDENCE_GAP_TREE`: supported semantic edges are validated; an unresolved gap branch cannot survive as active proximity.

The inspectability budget is pair=2, small composition=3–5, field=6–8, with 8 active concepts as the V1 maximum. Larger proposals require prior hierarchical decomposition. Six fixtures cover all strategies: 4 pass unchanged, 1 prune, and 1 split.
