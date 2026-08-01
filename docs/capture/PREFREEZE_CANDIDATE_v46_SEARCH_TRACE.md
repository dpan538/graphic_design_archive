# Prefreeze candidate v46 synchronized search and TRACE

Local prefreeze validation artifact; not the production database.

## Layer counts

- active_objects: 15,921
- authority_uncertain_active: 0
- trace_accepted_objects: 15,921
- metadata_supported_objects: 2,971
- trace_unlinked_objects: 0
- review_documents: 12,515
- authority_review_objects: 4,425
- search_documents: 28,436
- active_search_documents: 15,921
- trace_nodes: 97,845
- trace_edges: 255,638
- object_trace_edges: 126,798

## Search benchmark

- Queries: 10
- Iterations per query: 100
- Worst p95: 1.717 ms

## Gates

- sqlite_integrity: ok — PASS
- active_object_count: 15921 — PASS
- authority_uncertain_active_leak: 0 — PASS
- authority_uncertain_review_objects: 4425 — PASS
- authority_uncertain_missing_search: 0 — PASS
- trace_coverage_pct: 100.00 — PASS
- accepted_trace_contract_incomplete: 0 — PASS
- accepted_trace_without_indexed_edges: 0 — PASS
- metadata_supported_unresolved_geography: 0 — PASS
- metadata_supported_core_edge_incomplete: 0 — PASS
- influence_edges: 0 — PASS
- qualified_spc_not_active: 0 — PASS
- filename_extension_titles: 0 — PASS
- active_objects_without_search_document: 0 — PASS
- review_documents_searchable: 12515 — PASS

## Boundaries

- Active objects and held capture context share a preprocessed FTS index but remain count-separated.
- TRACE tiers, core edges, auxiliary edges and evidence-return URLs remain queryable and no influence edge is generated from association.
- This completes verification of an existing local SQLite base snapshot; it does not rebuild a source capture or overwrite an official release.
