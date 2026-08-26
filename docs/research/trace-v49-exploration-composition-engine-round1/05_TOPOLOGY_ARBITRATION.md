# Topology arbitration

| Topology | Entry condition | Minimum | Invalid configuration | Semantic non-claim |
|---|---|---|---|---|
| `LINEAR_PATH` | one connected acyclic path, maximum degree two | 1 node / 0 edges; normally 2 nodes / 1 edge | cycle, branch degree above two, disconnected active core | sequence is inquiry order, not chronology |
| `BINARY_FORK` | three-node connected core with one degree-two junction plus explicit fork inquiry intent | 3 nodes / 2 associations | no junction, more than two branches | branches are alternatives, not historical descendants |
| `BINARY_CONVERGENCE` | same bounded undirected core plus explicit convergence inquiry intent | 3 nodes / 2 associations | no shared review junction | convergence is a review operation, not causal flow |
| `QUALIFIED_PATH` | linear path and mandatory qualification gate | 2 nodes / 1 association | continuation bypasses gate | the gate limits inquiry scope, not historical membership |
| `REFLEXIVE_RETURN` | at least one admitted association and explicit navigation return | 2 nodes / 1 association | semantic self-loop or return encoded as association | return is navigation only |
| `EVIDENCE_GAP_TREE` | at least one explicit unresolved-evidence node | 1 supported or qualified node plus gap state | gap encoded as failed association or negative fact | gap means unresolved evidence, not historical absence |

An explicit inquiry topology request is valid only if its entry condition holds. In `AUTO`, the engine enumerates valid structures. If several semantically non-equivalent topologies remain, it emits `topology_type=UNRESOLVED` and returns every candidate. Implementation order and visual seed cannot choose semantic topology.

The six canonical structural signatures are distinct. `TREE_STRATEGY_TOPOLOGY_DUPLICATE_COUNT=0` remains a freeze gate.
