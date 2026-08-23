# Context Canvas governed mode

## Shared core and data mode

The shared functional Canvas now supports `synthetic_contract`, `real_v49_validation`, and `governed_context_v1`. Governed mode consumes one `PublicContextDataset` through a thin adapter; it does not duplicate the Canvas implementation or load the full governed corpus in the browser.

The persistence schema is version 2. Version-1 validation compositions are intentionally rejected and reinitialized because validation IDs and membership-visible semantics cannot be migrated safely by label.

## Governed default

The default is the selected-record root plus all published or qualified controlled representations. Membership nodes and connections are zero; membership is provenance only. Semantic edges are zero. The palette exposes only controlled terms available in the selected dataset.

The sole governed template is a revised `context-overview` version 2 using `all-governed-representations`. The descriptive, curated, and full templates are removed from governed mode because they duplicate controlled content or could reintroduce provenance structures. All four version-1 templates remain test-only for synthetic and validation regression contracts.

## Meaning surfaces

The wrapper connection kind is `context_representation`, with governed labels `classified as`, `themed as`, and `curated within`. It is never a `TraceSemanticEdge`. Node, connection, inspector, palette, accessible table, and export preparation use registered explanation/provenance metadata rather than inferring meaning from labels.

The inspector exposes Context kind, full label, meaning, why shown, source basis, source state, publication state, permitted interpretation, prohibited interpretation, and policy version. Accessible rows carry equivalent type, label, state, basis, and interpretation. Export includes only controlled representations and release/projection traceability; it excludes memberships, validation IDs, internal IDs, and held fields.
