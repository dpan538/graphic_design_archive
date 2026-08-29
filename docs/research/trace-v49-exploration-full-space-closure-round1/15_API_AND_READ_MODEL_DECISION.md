# API and Read-Model Decision

Round 16A selects versioned `trace-exploration/v2`. The legacy v1 route is specified to retire with HTTP 410 rather than silently change. V2 exposes categories, capabilities, map creation/retrieval, actions, vocabulary, generic associations, trees, export manifests, and PNGs. Its contract forbids Search DTOs, archive records, archive identifiers/titles, record links, Context records, Spacetime records, and census-only evidence fields; the measured counts below determine whether that contract passed.

The production read model is separate from the full audit census and is hash-addressed at `53eaf59c95446eeb3781a7153183c54b3ff59fd52f21744cc917053959dfdcc9`.

| Metric | Value |
| --- | --- |
| Production read-model bytes | 8802929 |
| Production model load ms | 37.79775 |
| RSS delta bytes | 43614208 |
| Heap delta bytes | 22232328 |
| Audit/production equivalence mismatches | 0 |
| Actual production HTTP tested | true |
| Functional API cases | 755855 |
| Functional API failures | 0 |
| Unexpected 5xx | 0 |
| Public archive object IDs | 0 |
| Public archive object titles | 0 |
| Public record links | 0 |
| Public Context references | 0 |
| Public Spacetime references | 0 |

OpenAPI, JSON schemas, TypeScript types, typed client, error catalog, real examples, and the capabilities response are versioned with v2. Runtime errors are allowlisted and sanitized; request size, stale-state, invalid-target, and snapshot mismatch behavior are tested through production HTTP.

Sources: `docs/audits/v49-exploration-full-space-closure-round1/raw/api-functional-validation-v2.json` and `docs/audits/v49-exploration-full-space-closure-round1/raw/production-read-model-metadata-v2.json`.
