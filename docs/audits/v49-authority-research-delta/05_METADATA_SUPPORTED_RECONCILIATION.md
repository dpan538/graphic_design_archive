# v49 Phase 1C — Count Parity and Parser Audit

**A2 status: PASS**

This report closes the A2 evidence scope. It proves input accounting and identity parity, locates the 2,970/2,971 conflict at its real aggregate unit, and identifies a separate legacy projection normalization affecting 4,957 missing candidate trace.tier values. It does not decide research-corpus membership.

## Scope

- deterministically enumerate every /surfaces/<index> row in the frozen v48 candidate JSON;
- measure surfaceId, sourceRecordId, source-fingerprint inputs, field presence/type/null/blank state, nested arrays, and delimiter risks;
- reconcile metadata_supported membership against immutable SQLite and the derived TRACE catalog;
- distinguish candidate-explicit TRACE tiers from legacy derived normalization;
- produce a reusable per-surface temporary ledger without expanding nested arrays into archive objects.

Excluded: visual rights, provider policy, delivery mode, PostgreSQL, migration, deduplication, delimiter splitting, frontend work, data export, and any mutation of frozen assets.

## Assets and authority

| Asset | Access | Role in this audit |
|---|---|---|
| generated/public_surfaces_prefreeze_candidate_v48.json | one controlled JSON.parse; read-only | sole canonical migration input |
| data/prefreeze_candidate_v48.sqlite | URI mode=ro&immutable=1; no integrity re-run | immutable reconciliation only |
| frontend/public/data/trace-v48/catalog.json | read-only | derived set reconciliation only |
| scripts/build_prefreeze_candidate_v9_search_sqlite.py | read-only | lineage evidence for the legacy tier fallback |

Neither SQLite nor TRACE catalog created, filled, removed, or reclassified a canonical row.

## Evidence commands

~~~text
/Users/jarlgiovanni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --check /private/tmp/v49_phase1c_a2_scan.mjs
/Users/jarlgiovanni/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --max-old-space-size=4096 /private/tmp/v49_phase1c_a2_scan.mjs
/Users/jarlgiovanni/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -c '<immutable SQLite tier/set reconciliation>'
/Users/jarlgiovanni/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 /private/tmp/v49_phase1c_a2_post.py
jq '<bounded field/array projections>' /private/tmp/v49_phase1c_a2_summary.json
python3 scripts/verify_v49_authority_research_delta.py --json
~~~

The candidate process exited 0 after 123.00633325 seconds with maximum RSS 1,238,592 KiB. It parsed the candidate exactly once and did not recompute the five-asset freeze hashes. The SQLite check did not execute integrity_check. The global verifier is owned and run by the root task; A2 did not implement a competing verifier.

## Input accounting

| Metric | Measured |
|---|---:|
| LEGACY_INPUT_SURFACES | 15,923 |
| ACCOUNTED_INPUT_SURFACES | 15,923 |
| UNACCOUNTED_INPUT_SURFACES | 0 |
| BASELINE_ARCHIVE_OBJECTS | 15,923 |
| HELD_OBJECTS — input-accounting meaning only | 0 |
| REJECTED_OBJECTS — input-accounting meaning only | 0 |

Every array element under top-level /surfaces is one object. Each is retained as one baseline archive object. HELD_OBJECTS=0 and REJECTED_OBJECTS=0 here mean only that no input surface failed structural accounting; they do not assert research or TRACE eligibility.

No nested array, delimiter, TRACE node, edge, folder, source record, compound child, or table row was counted as an additional archive object.

## Identity and deterministic hashes

| Check | Result |
|---|---|
| nonblank surfaceId | 15,923 |
| unique surfaceId | 15,923 |
| duplicate surfaceId | 0 |
| nonblank sourceRecordId | 15,923 |
| unique sourceRecordId | 15,923 |
| duplicate sourceRecordId | 0 |
| unique nonblank trace.objectNodeId | 15,923 |
| identity/type accounting errors | 0 |

| Projection | SHA-256 |
|---|---|
| sorted exact surfaceId lines | 7bae71cb2915a6ea6a9c9c43024a0a84bab5200edffad96298f398a7b8053d46 |
| sorted exact sourceRecordId lines | 16795db4223fd1e00ef362ba0a29b7a521a38ccf56638e9928d70a3343112f2e |
| source-order ordinal<TAB>surfaceId<TAB>sourceRecordId | 4cec7a95aa752efb5dd4536fcb7a771bc097d515c366dfb16a0771a45944236f |
| sorted source-evidence tuples | ebb9668ca8a28f6994b9697d3166b593e356865d413b200bfc87c740144f066e |
| sorted surface/row semantic fingerprints | 448efb9f2f0eca459619dccdde4df8fd8054e8fb51c1642fc1f5b272d97a188c |
| compact JSONL [surfaceId,sourceRecordId] | 8abf8de0518b7ca1a92cd3df69e82ce2be3710b18bf59de8fd289c0149bca9bf |

The first two recipes sort exact UTF-8 values bytewise, append one LF per value, and hash the complete byte stream. The ordered identity recipe uses one-based, five-digit ordinals and one final LF. A source-evidence tuple is sourceRecordId, sourceObjectKey, sourceUrl, and sourceName joined with U+0000; absent optional values remain empty. A row semantic fingerprint is SHA-256 over JSON.stringify(row) in parsed property order; it is a deterministic parsed projection, not lexical authority over raw bytes.

## Field presence, type, null and blank audit

| JSON path | Present rows | Type / condition | Missing, null or blank |
|---|---:|---|---:|
| surface.surfaceId | 15,923 | string | 0 |
| surface.sourceRecordId | 15,923 | string | 0 |
| surface.sourceUrl | 15,923 | string | 0 |
| surface.sourceObjectKey | 7,711 | string | 8,212 missing |
| surface.sourceLocator | 4,747 | string | 11,176 missing |
| surface.title | 15,923 | string | 0 |
| surface.creator | 15,923 | string | 0 blank |
| surface.medium | 15,923 | string | 0 blank |
| surface.objectType | 15,923 | string | 0 blank |
| surface.sourceSubjects | 15,923 | string | 458 blank |
| surface.dateEnd | 15,923 | 15,847 numbers + 76 nulls | 76 null |
| surface.collectionEvidence | 15,918 | object | 5 missing |
| surface.publicationRole | 15,921 | string | 2 missing |
| surface.publicationGate | 15,921 | object | 2 missing |
| surface.trace | 15,923 | object | 0 |
| surface.trace.tier | 10,966 | string | 4,957 missing |
| surface.trace.state | 15,923 | string; all accepted | 0 |
| surface.trace.reviewState | 15,923 | string | 0 |
| surface.trace.influenceState | 15,923 | string; all not_inferred | 0 |
| surface.trace.treeId | 15,923 | string; 30 unique | 0 |
| surface.trace.objectNodeId | 15,923 | string; 15,923 unique | 0 |

Missing, explicit null, and blank string are separate states. A parser must preserve all three.

## Nested arrays and expansion hazards

| Path | Parent rows | Total elements | Min–max |
|---|---:|---:|---:|
| surface.compoundChildren | 15 | 132 | 3–64 |
| surface.folders | 15,923 | 47,982 | 3–5 |
| surface.tables | 15,923 | 95,538 | exactly 6 |
| surface.tables[].rows | 15,923 | 808,809 | 2–18 per table |
| surface.trace.branchIds | 15,923 | 80,093 | 1–8 |
| surface.trace.edgeIds | 15,923 | 126,822 | 2–31 |
| surface.trace.edgeLabels | 15,923 | 79,683 | 2–8 |

trace.edgeCount equals edgeIds.length for all 15,923 surfaces. Edge IDs are 126,822 occurrences and 126,822 unique values; no edge ID is shared between two candidate surfaces.

edgeIds.length differs from edgeLabels.length for 9,393 surfaces. edgeLabels is therefore a per-surface vocabulary summary, not a positionally zipped label for each edgeId. Any parser that zips these arrays silently assigns false relation labels.

## Delimiter risks

Counts below are rows whose raw string contains the character, not inferred value counts:

| Field | semicolon | pipe | newline | spaced slash |
|---|---:|---:|---:|---:|
| creator | 3,849 | 4 | 45 | 17 |
| medium | 10,791 | 567 | 0 | 7,037 |
| objectType | 7,117 | 0 | 0 | 452 |
| sourceSubjects | 15,233 | 22 | 0 | 2,155 |
| placeText | 864 | 24 | 0 | 6,860 |
| dateText | 47 | 0 | 0 | 0 |

These fields remain lexical strings. Punctuation may be prose, dimensions, geographic wording, evidence notes, or a legacy multi-value encoding. No split, trim-and-drop, merge, deduplication, or nested-array expansion is permitted without a field-specific reviewed rule and a source-row-preserving disposition.

## metadata_supported: exact reconciliation

| Representation | Unit | Count | Set result |
|---|---|---:|---|
| candidate /meta/traceMetadataSupportedCount | aggregate scalar only | 2,970 | no membership set exists |
| candidate row trace.tier=metadata_supported | surfaceId membership | 2,971 | canonical row set |
| immutable SQLite row tier | surface_id membership | 2,971 | exact match to candidate |
| derived TRACE catalog tier | item ID membership | 2,971 | exact match to candidate |

The three measurable membership sets have SHA-256 9985c0f29e006e0ca30a707fce2d85711689c3a40b1efe634301f5f33e2fe9c8; both candidate↔SQLite and candidate↔TRACE symmetric differences are empty.

The remaining +1 is an **aggregate-unit mismatch** at /meta/traceMetadataSupportedCount, not an object-level symmetric difference. The scalar contains no IDs and declares no ordering or prefix rule. Consequently there is no evidence-honest “extra row” to name. Selecting the 2,971st row under an invented ordering would fabricate provenance.

A2 scoped decision:

- preserve 2,970 as stale historical summary metadata;
- use the 2,971 candidate row memberships for canonical parsing and parity;
- accept SQLite and TRACE catalog only as exact reconciliation of that row set;
- reject any future unexplained delta;
- METADATA_SUPPORTED_CONFLICT_RESOLVED=true within this scoped authority boundary.

The machine-readable comparison is in 05_METADATA_SUPPORTED_SYMMETRIC_DIFF.tsv.

## Separate P0: missing candidate tier normalized by a derived builder

| Candidate trace.tier state | Rows |
|---|---:|
| explicit source_verified | 7,995 |
| explicit metadata_supported | 2,971 |
| key missing | 4,957 |

Immutable SQLite instead reports source_verified=12,952 and metadata_supported=2,971. All 4,957 differences are exactly candidate trace.tier missing versus SQLite trace_tier=source_verified. There are no other tier differences.

The exact 4,957-ID delta set hash, using sorted raw surfaceId lines with LF, is:

fbabc473e5ca7c7435a13d3c6c28a05198a97d15331f1f0b0b01b7464d81cceb

The historical cause is explicit in scripts/build_prefreeze_candidate_v9_search_sqlite.py:299: when a trace satisfied an operational accepted check, the builder replaced a missing tier with source_verified. This is a derived normalization, not candidate JSON evidence.

Required authority disposition:

- candidate-explicit source_verified remains 7,995;
- the 4,957 missing values remain missing in canonical raw/parsed projections;
- SQLite must not backfill them;
- research and assertion eligibility must fail closed until a versioned evidence rule classifies them;
- operational input accounting still retains all 15,923 surfaces.

This boundary is now reflected in canonical parity terminology; A2 does not assign those 4,957 surfaces to a strict research corpus.

## Reusable temporary evidence

| Path | Rows / bytes | SHA-256 | Reproduction |
|---|---|---|---|
| /private/tmp/v49_phase1c_candidate_rows.tsv | 15,923 data rows + one header / 2,238,838 bytes | 4d5f15cda8e1267426fd91ea76da92573ab2851ee033468ebb0ef206ff0c4c46 | run the single-pass A2 Node scanner |
| /private/tmp/v49_phase1c_candidate_metadata_supported_ids.txt | 2,971 / 54,544 bytes | 9985c0f29e006e0ca30a707fce2d85711689c3a40b1efe634301f5f33e2fe9c8 | derived during the same parse |
| /private/tmp/v49_phase1c_a2_summary.json | 160,702 bytes | 1c51d7e9fe809003247a21defed543cd6f7c5ea0de35d0390b8461636935a468 | same scanner |
| /private/tmp/v49_phase1c_a2_post.json | 8,109 bytes | 26a56f82e1a21c20857c680fbc168fd7eb56c1c97ea45392f95caab2832783e4 | run the TSV/immutable-SQLite post-check |

The shared TSV schema is:

~~~text
surface_id
source_record_id
source_ordinal
json_pointer
trace_tier
trace_state
trace_review_state
trace_influence_state
trace_tree_id
trace_object_node_id
trace_edge_count
~~~

It is UTF-8, has one header, preserves source order, escapes control characters, and contains no nested expansion. It is temporary and must not be committed as a second canonical database.

## Findings and severity

| ID | Severity | Finding | Scoped status |
|---|---|---|---|
| A2-P0-01 | P0 | 4,957 missing candidate tiers were promoted to source_verified in derived SQLite | PASS: exact set and fail-closed authority boundary established |
| A2-P0-02 | P0 | meta scalar 2,970 conflicts with 2,971 measurable row memberships | PASS: aggregate-unit mismatch resolved; no false row attribution |
| A2-P1-01 | P1 | delimiter-bearing legacy strings cannot be split generically | PASS: measured and prohibited |
| A2-P1-02 | P1 | 9,393 edge-label arrays cannot be zipped to edge IDs | PASS: measured and handed to graph reconciliation |
| A2-P1-03 | P1 | optional source keys/locators and missing/null/blank states require lossless parsing | PASS: measured and preserved |

## Unresolved items and actions not performed

No A2 measurement is unresolved. Research eligibility, strict TRACE eligibility, epistemic graph classification, rights, and visual registry remain owned by their respective Phase 1C queues.

Explicitly not performed:

- no frozen JSON, SQLite, manifest, shard, QA, or frontend edit;
- no candidate hash re-run;
- no SQLite integrity check, write, sidecar, vacuum, migration, or export;
- no delimiter split, nested expansion, deduplication, merge, rejection, or row repair;
- no npm, Next, TypeScript, browser, Docker, PostgreSQL, network, or image operation.
