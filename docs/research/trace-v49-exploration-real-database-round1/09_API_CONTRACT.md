# API contract

The base path is `/api/trace/v1/exploration`. Eight capability routes cover categories, create/retrieve maps, actions, vocabulary, associations, export manifests, PNG bytes, and capabilities. Responses carry API/database/read-model headers. The OpenAPI document is `docs/api/trace-exploration-v1-openapi.yaml` and twelve JSON Schemas live in `schemas/trace/exploration`.

Database snapshot: `v49-api-contract-fresh-c:ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e`

Source commit: `aca7b9627ca42776d966f96ce4bd03db1f296ae3`

Read-model hash: `1abdeda493eed7871e0b1a5f1d7412be6bc6203068ac20e9547a32b6c5b473e9`

The product boundary is evidence-governed generic association. It does not emit typed, causal, directional, hierarchical, temporal, or quantitative historical relations. Fixtures are test inputs only and are never a production fallback.
