# TRACE Visualization Capacity Envelope

This document defines data-volume budgets, not visual grammar. No renderer, layout, map, animation, canvas, SVG, CSS, or visualization dependency is selected.

## Measured v49 object-local envelope

| Domain/workload | Minimal | P50 | P90 | P95 | P99 | Maximum | Interpretation |
|---|---:|---:|---:|---:|---:|---:|---|
| context controlled assignments | 2 | 2 | 2 | 2 | 3 | 4 | proposed/raw candidates |
| context folder memberships | 3 | 3 | 3 | 3 | 4 | 5 | proposed curated memberships |
| combined context associations | 5 | 5 | 5 | 5 | 7 | 9 | not semantic edges |
| context item upper bound incl. selected | 6 | 6 | 6 | 6 | 8 | 10 | assumes one distinct item/association |
| spacetime observations | 2 | 2 | 2 | 2 | 2 | 2 | one raw time + one raw region candidate |
| coordinate-mapped place observations | 0 | 0 | 0 | 0 | 0 | 0 | all public candidates unmapped |
| raw source associations | 1 | 1 | 1 | 1 | 1 | 1 | restricted source-record bridge |
| evidence/claim/relation nodes | 0 | 0 | 0 | 0 | 0 | 0 | governed layers empty |
| accepted one-hop nodes | 1 | 1 | 1 | 1 | 1 | 1 | selected object only |
| accepted one-hop edges | 0 | 0 | 0 | 0 | 0 | 0 | no semantic graph |

Recommended handling at current measured scale:

- context: `INLINE` through P95; `SCROLLABLE` for P99/max;
- spacetime: `INLINE` accessible rows; map rendering is not meaningful until governed coordinate mappings exist;
- sources: `INLINE` empty/source-association state; future evidence fanout must be remeasured after population;
- semantic graph: explicit empty/not-published state.

## Legacy stress envelope

Retained v48 graph data is used only as `LAYOUT/PERFORMANCE DIAGNOSTIC ONLY; NOT HISTORICAL INTERPRETATION`.

| Legacy public workload | P50 | P90 | P95 | P99 | Maximum |
|---|---:|---:|---:|---:|---:|
| 1-hop nodes | 12 | 16 | 17 | 20 | 32 |
| 1-hop edges | 11 | 15 | 16 | 19 | 31 |
| 2-hop nodes | 3,637 | 5,671 | 5,682 | 5,759 | 6,363 |
| 2-hop edges | 21,099 | 26,415 | 27,614 | 27,739 | 28,566 |

The legacy global graph has 97,889 nodes and 255,695 edges; its maximum undirected degree is 6,539. This prohibits an unbounded generic depth-2 public endpoint. A future graph service should default to depth 1, require typed/directed relation filters, paginate relations, enforce explicit node/edge budgets, and return deterministic cursor plus `truncated=true`. Depth 2 requires `PROGRESSIVE_DISCLOSURE` and likely `VIRTUALIZED` result handling.

## Pure projection benchmark

Public-safe synthetic structures were sized exactly to the measured v49 minimal/P50/P95/P99/max counts. On Node `v22.21.0` arm64:

| Workload/domain | Projection P95 | Accessible-row P95 | Serialized bytes | Retained heap for 250 outputs |
|---|---:|---:|---:|---:|
| median context | 0.018333 ms | 0.007541 ms | 4,252 | 1,012,000 B |
| P95 context | 0.017875 ms | 0.007500 ms | 4,177 | 992,112 B |
| maximum context | 0.035545 ms | 0.013916 ms | 6,954 | 1,495,864 B |
| P95 spacetime | 0.005542 ms | 0.003125 ms | 1,873 | 552,032 B |
| P95 sources | 0.005000 ms | 0.002500 ms | 1,604 | 491,120 B |

The provisional pure-projection target of P95 <20 ms passed by a wide margin. The computation can remain synchronous for these structures. Measurements exclude network, parsing, endpoint authorization, and rendering. Source/evidence and relation performance must be re-benchmarked when nonzero governed populations exist.
