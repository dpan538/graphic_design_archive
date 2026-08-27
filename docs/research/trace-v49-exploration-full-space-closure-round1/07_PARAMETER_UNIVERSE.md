# Parameter Universe

The parameter universe is frozen at `e244d722378393618b40751c6173ef93bbd80a15bf3601ea9fd7c979745042e9`. Every parameter is assigned a finite legal domain, an authority, a default or explicit absence of default, and separate semantic/presentation identity effects.

`PARAMETER_COUNT=18`

`PARAMETER_UNIVERSE_FROZEN=true`

| Parameter | Class | Legal values | Default | Authority | Finite-domain proof | Semantic identity | Presentation identity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| node_set | semantic | all active-vocabulary subsets induced by connected edge subgraphs with 2–8 nodes | None | Round 15 MAX_NODE_COUNT=8 plus active graph | 31 active terms and fixed bounds | true | true |
| association_set | semantic | all connected subsets of the 21 active graph edges spanning the selected nodes | None | validated-association-graph-v2 | finite 21-edge power set with connectivity pruning | true | true |
| seed | interaction | each node admitted by a topology composition | lexicographically first node | Round 15 seed contract | at most 8 nodes per composition | false | true |
| focus | interaction | each composition node | seed node | v2 state contract | at most 8 nodes | false | true |
| category_entry | interaction | `["region","theme","medium","movement"]` | region | direct frozen database category census | exactly four governed category types | false | true |
| topology | semantic | `["LINEAR_PATH","BINARY_FORK","BINARY_CONVERGENCE","QUALIFIED_PATH","REFLEXIVE_RETURN","EVIDENCE_GAP_TREE"]` | LINEAR_PATH | Round 15 topology families plus strict adapter v2 | six enumerated families | true | true |
| qualification_gate | semantic | `[false]` | false | explicit governed inquiry record only | no active evidence-backed gate exists | true | true |
| navigation_return | interaction | `[false]` | false | explicit governed inquiry record only | no active evidence-backed return exists | false | true |
| evidence_gap_node_ids | semantic | `[[]]` | `[]` | explicit governed unresolved-evidence record only | no active evidence-gap composition exists | true | true |
| degree_bound | semantic | `[2]` | 2 | frozen Round 15 MAX_ADMITTED_DEGREE | constant | true | true |
| maximum_node_count | semantic | `[8]` | 8 | frozen Round 15 MAX_NODE_COUNT | constant | true | true |
| direct_proximity | semantic | `[1]` | 1 | Round 14 direct-neighbour threshold | constant graph distance | false | true |
| skip_one_proximity | semantic | `[2]` | 2 | Round 14 skip-one threshold | constant graph distance | false | true |
| pruning | semantic | `["ADMITTED","PRUNED"]` | ADMITTED | frozen Round 15 ordinal evidence arbitration | one decision per candidate association | true | true |
| split | semantic | `[false,true]` | false | frozen Round 15 component decision | Boolean outcome recorded, not arbitrarily combined | true | true |
| expanded_collapsed_state | interaction | power set of admitted composition nodes | `[]` | v2 state contract | at most 2^8 subsets | false | true |
| theme_token | presentation | `["neutral-v1","neutral-contrast-v1"]` | neutral-v1 | v2 export contract | two frozen token sets | false | true |
| export_preset | presentation | `["portrait_card"]` | portrait_card | v2 export contract | one fixed 1080×1620 preset | false | true |

Uninstantiated governed families remain in the universe with an explicit zero-valued legal gate; they are not silently deleted. Arbitrary combinations outside these domains are invalid.

Source: `docs/audits/v49-exploration-full-space-closure-round1/raw/exploration-parameter-universe-v2.json`.
