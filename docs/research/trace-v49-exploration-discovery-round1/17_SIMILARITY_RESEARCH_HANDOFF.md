# Similarity research handoff

## Readiness decision

`EXPLORATION_SIMILARITY_RESEARCH_READY=true`

The signal space is mapped well enough to begin a separate research round, but no similarity function, feature weights, distance metric, ranking rule, clustering model, probability model, template registry, renderer, public API, or public route is selected here.

## Recommended future architecture

Use a hybrid architecture:

1. precompute governed direct-feature indexes and bounded frequency/intersection/concentration tables;
2. retain a compact public-only inverted curatorial index server-side;
3. derive object-local candidate fanout on demand rather than materializing 28,008,976 pair rows;
4. return explainable contributing signals and denominators with every future candidate result;
5. keep held data, raw source rows, internal identifiers, and full source corpus out of the client;
6. govern any public Exploration-derived release independently from Context and Spacetime.

## Inputs available to the next round

- 64-signal registry with levels, costs, fanout, materialization risk, and known failures;
- 3,364 one-dimensional frequencies;
- 6,146 observed pair cells and 2,399 bounded triple cells;
- 4,251 rare observed candidates;
- 10-class missingness/uncertainty taxonomy and 19 observed state intersections;
- four concentration diagnostics;
- exact aggregate curatorial fanout and rarity receipts;
- 15 reproducible public pathological cases;
- a 20-row structure registry that separates membership, graph-reference, scalar-row, governed, candidate, legacy, empty, and unsafe semantics.

## Required next questions

The next research round should compare candidate retrieval strategies, normalization choices, missing-feature handling, broad-container attenuation, and explanation stability. It must define evaluation questions before choosing weights. It should test whether source concentration and broad curatorial containers overwhelm governed Context/Spacetime signals, and it must retain the red-team distinction between archive structure and historical relation.

Probability terminology remains prohibited without a calibrated model and evaluation set. Even a future affinity score must be presented as an exploratory archive-derived candidate, not a scholarly claim.

## Explicit non-decisions

```text
SIMILARITY_MODEL_SELECTED=false
SIMILARITY_WEIGHTS_SELECTED=false
DISTANCE_METRIC_SELECTED=false
RANKING_POLICY_SELECTED=false
CLUSTERING_MODEL_SELECTED=false
PROBABILITY_MODEL_SELECTED=false
EXPLORATION_TEMPLATE_REGISTRY_FROZEN=false
EXPLORATION_RENDERER_IMPLEMENTED=false
PUBLIC_EXPLORATION_API_IMPLEMENTED=false
PUBLIC_EXPLORATION_ROUTE_IMPLEMENTED=false
```
