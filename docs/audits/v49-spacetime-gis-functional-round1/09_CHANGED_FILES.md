# Changed-file boundary

## Round 4 intended scope

The working change set is limited to:

- Context runtime engineering/rehearsal files, without Context semantic/governance changes;
- additive Spacetime domain role typing;
- generated `trace-spacetime-v1` server-only projection artifacts;
- pinned public Natural Earth geometry asset;
- pure Spacetime governance/GIS/dot/pattern/view-model functions;
- exact Spacetime read API integration and unlinked functional route;
- Round 4 generation, verification, benchmark, and rehearsal scripts;
- package scripts only when required to expose deterministic gates;
- this Round 4 research/audit package;
- compact Project Log status update.

## Protected boundaries

Expected final results:

| Boundary | Expected |
| --- | --- |
| Database files changed | 0 |
| Canonical release changed | false |
| Search implementation/files changed | 0 |
| Search algorithm/index identity changed | false |
| Context semantics changed | false |
| Context governance changed | false |
| Exploration implementation files added | 0 |
| Texture.js dependency retained | false |

No prior Round 3 audit package may be rewritten. No unsafe raw source dump belongs in this package.

## Exact final inventory

The final pre-commit inventory contains 81 paths: five modified and 76 new. `M` and `A` are the intended final diff states; the two seal ledgers are included.

```text
M	PROJECT_LOG.md
M	frontend/package.json
M	frontend/src/features/trace-v49/context/governed/reader.server.ts
M	frontend/src/features/trace-v49/spacetime/types.ts
M	frontend/src/lib/read-platform/server/read-api-controller.ts
A	docs/audits/v49-spacetime-gis-functional-round1/00_EXECUTIVE_RECEIPT.md
A	docs/audits/v49-spacetime-gis-functional-round1/01_CONTEXT_REHEARSAL_VALIDATION.md
A	docs/audits/v49-spacetime-gis-functional-round1/02_GEOGRAPHY_VALIDATION.md
A	docs/audits/v49-spacetime-gis-functional-round1/03_TEMPORAL_VALIDATION.md
A	docs/audits/v49-spacetime-gis-functional-round1/04_GEOMETRY_VALIDATION.md
A	docs/audits/v49-spacetime-gis-functional-round1/05_MAP_FUNCTION_VALIDATION.md
A	docs/audits/v49-spacetime-gis-functional-round1/06_TEXTURE_BENCHMARK.md
A	docs/audits/v49-spacetime-gis-functional-round1/07_PERFORMANCE.md
A	docs/audits/v49-spacetime-gis-functional-round1/08_SECURITY_BOUNDARY.md
A	docs/audits/v49-spacetime-gis-functional-round1/09_CHANGED_FILES.md
A	docs/audits/v49-spacetime-gis-functional-round1/MANIFEST.tsv
A	docs/audits/v49-spacetime-gis-functional-round1/SHA256SUMS.txt
A	docs/audits/v49-spacetime-gis-functional-round1/raw/context-runtime-rehearsal-summary.json
A	docs/audits/v49-spacetime-gis-functional-round1/raw/spacetime-functional-benchmark-summary.json
A	docs/audits/v49-spacetime-gis-functional-round1/raw/spacetime-geography-summary.json
A	docs/audits/v49-spacetime-gis-functional-round1/raw/spacetime-geometry-summary.json
A	docs/audits/v49-spacetime-gis-functional-round1/raw/spacetime-gis-benchmark-summary.json
A	docs/audits/v49-spacetime-gis-functional-round1/raw/spacetime-integration-gates.json
A	docs/audits/v49-spacetime-gis-functional-round1/raw/spacetime-projection-summary.json
A	docs/audits/v49-spacetime-gis-functional-round1/raw/spacetime-temporal-summary.json
A	docs/research/trace-v49-spacetime-gis-round1/00_EXECUTIVE_DECISION.md
A	docs/research/trace-v49-spacetime-gis-round1/01_CONTEXT_RUNTIME_REHEARSAL.md
A	docs/research/trace-v49-spacetime-gis-round1/02_SPACETIME_SOURCE_CENSUS.md
A	docs/research/trace-v49-spacetime-gis-round1/03_GEOGRAPHY_GOVERNANCE_POLICY.md
A	docs/research/trace-v49-spacetime-gis-round1/04_GEOGRAPHY_REGISTRY.tsv
A	docs/research/trace-v49-spacetime-gis-round1/05_GEOGRAPHY_EXCEPTION_REGISTER.tsv
A	docs/research/trace-v49-spacetime-gis-round1/06_TEMPORAL_GOVERNANCE_POLICY.md
A	docs/research/trace-v49-spacetime-gis-round1/07_TIME_BUCKET_REGISTRY.tsv
A	docs/research/trace-v49-spacetime-gis-round1/08_GIS_GEOMETRY_DECISION.md
A	docs/research/trace-v49-spacetime-gis-round1/09_PROJECTION_BENCHMARK.tsv
A	docs/research/trace-v49-spacetime-gis-round1/10_MAP_FUNCTION_CONTRACT.md
A	docs/research/trace-v49-spacetime-gis-round1/11_DOT_DENSITY_METHOD.md
A	docs/research/trace-v49-spacetime-gis-round1/12_TEXTURE_EXPERIMENT.md
A	docs/research/trace-v49-spacetime-gis-round1/13_SPACETIME_PUBLIC_PROJECTION_SPEC.md
A	docs/research/trace-v49-spacetime-gis-round1/14_SPACETIME_API_DECISION.md
A	docs/research/trace-v49-spacetime-gis-round1/15_ACCESSIBILITY_AND_SEMANTIC_BOUNDARY.md
A	docs/research/trace-v49-spacetime-gis-round1/16_PERFORMANCE_REPORT.md
A	docs/research/trace-v49-spacetime-gis-round1/17_PATHOLOGICAL_SAMPLE_REGISTER.tsv
A	docs/research/trace-v49-spacetime-gis-round1/18_EXPLORATION_FIELD_HANDOFF.md
A	docs/research/trace-v49-spacetime-gis-round1/19_ROUND_DECISION.md
A	docs/research/trace-v49-spacetime-gis-round1/20_EXTERNAL_REFERENCE_REGISTER.md
A	frontend/generated/trace-spacetime-v1/CHECKSUMS.sha256
A	frontend/generated/trace-spacetime-v1/geography-registry.json
A	frontend/generated/trace-spacetime-v1/geometry/geometry-manifest.json
A	frontend/generated/trace-spacetime-v1/governance-policy.json
A	frontend/generated/trace-spacetime-v1/manifest.json
A	frontend/generated/trace-spacetime-v1/period-region-aggregates.json
A	frontend/generated/trace-spacetime-v1/record-index.json
A	frontend/generated/trace-spacetime-v1/time-buckets.json
A	frontend/public/trace-spacetime-v1/natural-earth-50m-admin0-v5.1.1.geojson
A	frontend/scripts/benchmark-spacetime-functional-v1.mjs
A	frontend/scripts/benchmark-spacetime-gis.mjs
A	frontend/scripts/generate-spacetime-geometry.mjs
A	frontend/scripts/generate-trace-spacetime-v1.mjs
A	frontend/scripts/probe-context-api-lazy-boundary-v1.mjs
A	frontend/scripts/rehearse-context-runtime-v1.mjs
A	frontend/scripts/verify-spacetime-api-v1.mjs
A	frontend/scripts/verify-spacetime-gis.mjs
A	frontend/scripts/verify-spacetime-governance-v1.mjs
A	frontend/src/app/trace/spacetime/page.module.css
A	frontend/src/app/trace/spacetime/page.tsx
A	frontend/src/features/trace-v49/context/governed/read-api-runtime.server.ts
A	frontend/src/features/trace-v49/spacetime/gis/dot-density.ts
A	frontend/src/features/trace-v49/spacetime/gis/geometry.ts
A	frontend/src/features/trace-v49/spacetime/gis/index.ts
A	frontend/src/features/trace-v49/spacetime/gis/marks.ts
A	frontend/src/features/trace-v49/spacetime/gis/native-pattern.ts
A	frontend/src/features/trace-v49/spacetime/gis/projection.ts
A	frontend/src/features/trace-v49/spacetime/gis/types.ts
A	frontend/src/features/trace-v49/spacetime/governed/functions.ts
A	frontend/src/features/trace-v49/spacetime/governed/read-api-runtime.server.ts
A	frontend/src/features/trace-v49/spacetime/governed/reader.server.ts
A	frontend/src/features/trace-v49/spacetime/governed/types.ts
A	frontend/src/features/trace-v49/spacetime/map/SpacetimeWorkspace.module.css
A	frontend/src/features/trace-v49/spacetime/map/SpacetimeWorkspace.tsx
A	frontend/src/features/trace-v49/spacetime/map/index.ts
```

All paths are in Round 4 scope. Database and Search files are absent; canonical release content is unchanged; Texture.js is not a dependency; Exploration has no implementation path.
