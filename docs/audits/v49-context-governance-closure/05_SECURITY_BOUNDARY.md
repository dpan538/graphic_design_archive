# Context security and protected-boundary validation

## Immutable inputs

The work was derived from source commit `b60ac6faf5f249e4c0d40697e9255770277cac03`. The frozen database, migrations, canonical release inputs, freeze receipt, and historical v49 API snapshots remain unmodified.

```text
DATABASE_FILES_CHANGED=0
CANONICAL_RELEASE_CHANGED=false
```

## Public projection exclusions

The governed projection and selected-record DTO exclude:

- held records and held-only terms;
- raw folder identifiers and internal UUIDs;
- validation-only `ctxv49:` identities;
- source URLs, private locators, and unsafe source rows;
- raw membership nodes or detail endpoints;
- region Context nodes;
- semantic edges, confidence, or historical claims;
- image, rights, and full source-description payloads.

Term IDs are kind-bound and representation IDs bind the public surface ID, kind, and governed term ID. Identity never depends on array position or label alone. The exhaustive check reports:

```text
PUBLIC_ID_COLLISION_COUNT=0
VALIDATION_ID_IN_GOVERNED_DTO_COUNT=0
INTERNAL_ID_EXPOSURE_COUNT=0
HELD_OBJECTS_EXPOSED=0
```

## Fail-closed read boundary

Malformed object IDs fail before repository lookup. Held and well-formed unknown IDs receive the same `404` code and detail. Release mismatch and projection-integrity failures do not fall back to a different release or source path. `HEAD` enforces the same lookup as `GET`; `OPTIONS` performs no record lookup; write methods return `405`.

## Server/client boundary

The generated projection and reader are server-only. The public route receives one selected dataset. Source-graph checks prohibit the exhaustive validation loader in the public runtime dependency graph, and production chunk checks prohibit the full corpus marker in client output.

```text
HEAVY_VALIDATION_SOURCE_INDEX_USED_BY_PUBLIC_RUNTIME=false
FULL_CONTEXT_CORPUS_IN_CLIENT_BUNDLE=false
```

The authoritative post-build guard scanned 51 production static files totaling 92,360,030 bytes and returned `PRODUCTION_STATIC_PASS`.

## Frozen neighboring domains

```text
SEARCH_FILES_CHANGED=0
SEARCH_ALGORITHM_VERSION_UNCHANGED=true
SEARCH_INDEX_DOCUMENT_COUNT=7995
SEARCH_INDEX_SHA_UNCHANGED=true
SPACETIME_IMPLEMENTATION_FILES_ADDED=0
EXPLORATION_IMPLEMENTATION_FILES_ADDED=0
CONTEXT_PUBLIC_NAVIGATION_ENABLED=false
```

Only a sanitized aggregate region handoff is authorized for future Spacetime governance. No normalization, coordinates, map, time selector, similarity model, scoring system, seed algorithm, renderer, or final visual redesign was introduced.

## Evidence safety

The audit package contains aggregate summaries and empty-or-sanitized failure registers. It contains no raw source dump, private folder ID, internal UUID, held object ID, or candidate-corpus enumeration.
