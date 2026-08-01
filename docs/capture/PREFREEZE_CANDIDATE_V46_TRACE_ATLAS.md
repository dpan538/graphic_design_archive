# Prefreeze candidate v46 TRACE atlas

## Current evidence base

- active objects: 15,921
- accepted TRACE objects: 15,921
- active TRACE subgraph: 45,352 nodes / 126,798 edges
- full stored TRACE graph: 97,845 nodes / 255,638 edges
- object geography: 156 regions across 23 decade bins and 272 source families
- evidence-backed historical `influenced_by` edges: 0

## Product decision

A single browser force graph of every TRACE point is not an acceptable primary visualisation: it would be dense, slow, and would obscure the evidentiary difference between source lineage, metadata context, and historical relations.

Use three connected views instead:

1. **Object lineage explorer** — expand one selected object upward to its source root and downward to justified structural nodes. Cap an expansion at 200 nodes; always expose evidence URLs and edge labels.
2. **Geo–time atlas** — render the `region × decade` aggregate as a map, heatmap, or flowing timeline. It may indicate concentration, absence, co-location, or chronological sequence only.
3. **Source–geography matrix** — render source-family to object-geography counts to expose institutional concentration and counterweight gaps without assigning a source's location to the object.

## Semantic guardrails

- `documented_by`, object place, creator, year, collection, and series relations can be used in a lineage view only with their current evidence labels.
- Geographic proximity, shared collection, and decade co-occurrence must use neutral language such as `co-located`, `concurrent`, or `shared source context`; none may display as influence arrows.
- Historical arrows remain disabled because the active TRACE contains zero `influenced_by` evidence edges. Introducing arrows before direct evidence would manufacture history rather than reveal it.
- An uncertain authority or review-only object must remain outside all primary atlas aggregates until it passes the active-layer gate.

## Implementation boundary

The web client should receive small aggregate CSV/JSON payloads and retrieve selected-object adjacency from a query endpoint or pre-chunked object bundle. The 400 MB SQLite search database and full 97k-node graph are build/research artifacts, not browser payloads.

## Generated inputs

- `prefreeze_candidate_v46_trace_atlas_summary.csv`
- `prefreeze_candidate_v46_trace_atlas_edge_roles.csv`
- `prefreeze_candidate_v46_trace_atlas_geo_decades.csv`
- `prefreeze_candidate_v46_trace_atlas_source_geography.csv`
- `prefreeze_candidate_v46_trace_atlas_manifest.json`
