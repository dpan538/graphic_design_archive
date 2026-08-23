# Real-Data Validation Projection

## Purpose and interpretation

The projection converts frozen v49 source rows into one selected public object's `TraceContextDataset`. Its sole purpose is functional validation. Candidate data remains not published, ungoverned, and non-historical-evidence.

```text
audited surface-row ledger (eligibility authority)
                 +
immutable pre-freeze SQLite (selected title + typed folder rows)
                 +
FREEZE_V49 count receipt (count reconciliation)
                 ↓
public-ID intersection and held exclusion
                 ↓
typed validation mapping + proposed state
                 ↓
SHA-256 validation-only identities
                 ↓
one selected TraceContextDataset
```

## Reproducible source register

| Role | Frozen artifact | SHA-256 | Fields used |
| --- | --- | --- | --- |
| Eligibility authority | `docs/audits/v49-phase2b-migration/18_SURFACE_ROW_LEDGER.tsv` | `48f98f68ca2ec0cef96c82ecc9c01e4129eb9a3f91e08b07ad9a59644a9d4e01` | `surface_id_exact`, `research_disposition` |
| Count receipt | `database/FREEZE_V49.json` | `f0dda59dd515ba243eaf213bce9f42513727f1ab0a44685635921c3759a7d22e` | total/public/held counts and assignment total |
| Query-only candidate source | `data/prefreeze_candidate_v48.sqlite` | `ef190d00b9b265ecc49924aea4d82f389decd0a003d5aa7cf2d46971430c007e` | `objects.surface_id`, `objects.title`; `object_folder_refs.surface_id`, `folder_id`, `folder_type`, `title` |
| Public ID/title cross-check, never an eligibility source | `frontend/generated/search-v49/documents.json` | `35a6b7e1f8b749fca0ebfda9cf84f265de58d69fe6ef2bac0a4a2a9d263b1522` | public stable ID and public title parity only |

The release-data profile at `docs/statistics/v49-release-data-profile.json` has SHA-256 `091dba486c2096f99c332b03cf9586139f1bc26594bce4e1575d2b1ddc8fea0f`. It records zero sealed public folder memberships and zero semantic relations. Candidate validation therefore cannot be represented as a governed release.

## Eligibility and privacy boundary

Only rows marked eligible in the audited ledger enter the public index. The reconciled sets are:

```text
CANONICAL_OBJECT_COUNT=15923
PUBLIC_OBJECT_COUNT=7995
HELD_OBJECT_COUNT=7928
PUBLIC_HELD_OVERLAP_COUNT=0
UNCLASSIFIED_OBJECT_COUNT=0
```

SQLite fields named `count_eligible` and `trace_tier` are explicitly not eligibility authorities. Every one of the 15,923 SQLite objects has `count_eligible=1`; using that field would expose 7,928 held objects. Filtering `trace_tier=source_verified` would expose 4,957 held objects. The projection avoids both.

The externally observable lookup contract is:

| Input | Result |
| --- | --- |
| Gate disabled | `VALIDATION_DATA_NOT_GENERATED` |
| Missing record parameter with gate enabled | deterministic first eligible stable ID |
| Valid eligible public stable ID | selected-record dataset |
| Valid held stable ID | `RECORD_NOT_AVAILABLE` |
| Well-formed unknown stable ID | `RECORD_NOT_AVAILABLE` |
| Malformed value | `INVALID_RECORD_ID` |
| Source integrity failure | `DATA_INTEGRITY_ERROR` or `VALIDATION_PROJECTION_ERROR` |

The implementation never distinguishes held from unknown in the returned failure state.

## Server-only implementation

`frontend/src/features/trace-v49/context/realdata/source-index.server.ts`:

- imports `server-only`;
- requires the explicit `CONTEXT_CANVAS_REAL_VALIDATION` environment gate;
- parses the eligibility ledger and checks its 15,923 / 7,995 / 7,928 partition;
- SHA-256 verifies the freeze receipt, eligibility ledger, and SQLite against the registered frozen-input map before parsing;
- opens SQLite through `node:sqlite` in read-only, immutable, `PRAGMA query_only=ON` mode;
- selects only eligible stable IDs in deterministic 400-ID chunks;
- caches the completed source index at module scope;
- returns only the selected public record and a small deterministic sample picker.

The browser never reads SQLite, the ledger, Search, or the full 7,995-object candidate corpus. No generated full-corpus JSON is required or committed.

## Deterministic mapping

`frontend/src/features/trace-v49/context/realdata/project.server.ts` uses:

```text
MAPPING_VERSION=trace-context-realdata-v1
VALIDATION_RELEASE_ID=trace-v49-context-validation-round2-v1
VALIDATION_MANIFEST_SHA256=c07de2b6531f5f17cd31f705b6e42443277bf837ce9e13225ae684001da17363
```

The manifest hash is SHA-256 over newline-separated material consisting of `mapping:trace-context-realdata-v1` followed by the three `path:sha256` frozen-input entries sorted by path. Validation entity and connection identifiers use `ctxv49:<namespace>:<64-hex-sha256>`. Their identity hashes separately bind mapping version, namespace, source category, and stable source identity; display labels are never the sole identity. The namespace explicitly prevents these IDs from being mistaken for permanent public identifiers.

Ordering is independent of database row order: eligible stable IDs, typed folder rows, entities, and connections terminate in stable source identity or hashed validation identity. Two complete rebuild passes produced identical source-index, dataset, entity, connection, template, layout, accessibility, and export-preparation checksums.

## Mapping policy

- Root: public stable object ID and its public-safe title.
- Controlled candidates: medium, theme, and movement typed folder rows.
- Curated memberships: every typed medium, theme, movement, and region folder row.
- State: `proposed` for every real-data validation connection.
- Semantic edges: always `[]` for the frozen v49 release.
- Deferred: raw `objects.medium`, creator, object type, collection/source-adjacent fields, URLs, and other descriptive metadata.

The 16,106 controlled and 24,102 curated instances intentionally overlap at the source-row level for medium/theme/movement. They remain distinct semantic categories and use distinct hashed identities and connection IDs.

## Source integrity closure

The loader calculates and compares all three registered frozen-input SHA-256 values before projection. The full verifier independently recomputes the same sorted manifest and asserts it equals `c07de2b6531f5f17cd31f705b6e42443277bf837ce9e13225ae684001da17363`. A source-file mismatch fails closed as `DATA_INTEGRITY_ERROR`.
