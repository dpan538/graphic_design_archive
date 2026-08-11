# A2 — Count Parity and Parser Audit Receipt

**Exit status: PASS**

## Task boundary

A2 measured canonical candidate input accounting, identity, field/cardinality hazards, TRACE row projections, and the metadata_supported conflict. A2 did not define research eligibility, graph epistemic classes, rights, visual delivery, or database implementation.

Exclusive committed outputs:

- docs/audits/v49-authority-research-delta/05_METADATA_SUPPORTED_RECONCILIATION.md
- docs/audits/v49-authority-research-delta/05_METADATA_SUPPORTED_SYMMETRIC_DIFF.tsv
- docs/audits/v49-authority-research-delta/agents/A2_COUNT_PARSER_RECEIPT.md

No other repository file was modified by A2.

## Assets read

| Path | Authority/use |
|---|---|
| generated/public_surfaces_prefreeze_candidate_v48.json | sole canonical migration input; parsed once |
| data/prefreeze_candidate_v48.sqlite | immutable reconciliation, mode=ro&immutable=1 |
| frontend/public/data/trace-v48/catalog.json | derived reconciliation |
| frontend/public/data/trace-v48/manifest.json | derived count/schema context |
| generated/prefreeze_candidate_v48_transfer_manifest.json | integrity/role context only |
| scripts/audit_prefreeze_candidate_v48_freeze.py | historical audit semantics |
| scripts/build_prefreeze_candidate_v9_search_sqlite.py | legacy tier-fallback lineage |
| scripts/build_prefreeze_candidate_v47_search_sqlite.py | later projection behavior |
| scripts/build_prefreeze_candidate_v48_loc_geo_repair.py | v48 construction context |
| existing v49 architecture and pre-migration audit references located by bounded rg | terminology comparison only |

## Commands and process behavior

- read the Spreadsheets skill, its style guide, API quick start, and scientific-research guidance before TSV authoring;
- workspace dependency loading in this subtask produced no output twice and was terminated under the health rule; the root task supplied the approved bundled Node/Python paths, and no package was installed;
- syntax-checked the temporary Node scanner;
- executed one candidate JSON parse with the bundled Node runtime and 4 GiB heap ceiling;
- queried SQLite only through file:...?...mode=ro&immutable=1;
- read the 2.2 MB shared TSV for post-reconciliation instead of re-reading the 190 MB candidate;
- ran Python TSV UTF-8/header/column validation, bounded jq projections, shasum for temporary/A2 outputs, git diff --check, and an A2-specific residual-process scan;
- referenced the root-owned verifier command python3 scripts/verify_v49_authority_research_delta.py --json; A2 did not create a second verifier.

Candidate scanner receipt:

| Item | Value |
|---|---|
| exit | 0 |
| elapsed | 123.00633325 seconds |
| max RSS | 1,238,592 KiB |
| candidate parses | exactly 1 |
| candidate SHA re-runs | 0 |
| SQLite integrity checks | 0 |
| frozen writes | 0 |

## Evidence and measured results

| Metric | Value |
|---|---:|
| LEGACY_INPUT_SURFACES | 15,923 |
| ACCOUNTED_INPUT_SURFACES | 15,923 |
| UNACCOUNTED_INPUT_SURFACES | 0 |
| BASELINE_ARCHIVE_OBJECTS | 15,923 |
| unique nonblank surfaceId | 15,923 |
| unique nonblank sourceRecordId | 15,923 |
| unique trace.objectNodeId | 15,923 |
| candidate explicit source_verified | 7,995 |
| candidate missing trace.tier | 4,957 |
| candidate explicit metadata_supported | 2,971 |
| candidate meta scalar metadata_supported | 2,970 |
| SQLite metadata_supported | 2,971 |
| TRACE catalog metadata_supported | 2,971 |
| candidate/SQLite/TRACE metadata set symmetric difference | 0 / 0 |
| trace edge ID references | 126,822 |
| unique trace edge IDs | 126,822 |
| trace edgeCount mismatches | 0 |
| edgeIds/edgeLabels length-mismatch surfaces | 9,393 |

Deterministic evidence hashes:

| Evidence | SHA-256 |
|---|---|
| surfaceId set | 7bae71cb2915a6ea6a9c9c43024a0a84bab5200edffad96298f398a7b8053d46 |
| sourceRecordId set | 16795db4223fd1e00ef362ba0a29b7a521a38ccf56638e9928d70a3343112f2e |
| metadata_supported surface set | 9985c0f29e006e0ca30a707fce2d85711689c3a40b1efe634301f5f33e2fe9c8 |
| 4,957 missing-tier surface set | fbabc473e5ca7c7435a13d3c6c28a05198a97d15331f1f0b0b01b7464d81cceb |
| shared candidate ledger | 4d5f15cda8e1267426fd91ea76da92573ab2851ee033468ebb0ef206ff0c4c46 |
| compact JSONL surface/source pairs | 8abf8de0518b7ca1a92cd3df69e82ce2be3710b18bf59de8fd289c0149bca9bf |
| compact JSONL surface/object-node pairs | 3c9c48f7322a5f4fe3a7e1083d33554cf32502b3f39a31a75284426acd4ce08b |
| compact JSONL surface/tree/object-node triples | 6cc14666f72d4c53b43a76748fd514fb471551fa119d780e3861a68e8458258d |
| compact JSONL active TRACE tuples | 28d964437073bf92bdc2ad3b827620687237f3eefd1199e5d9167011d125de92 |

Temporary shared ledger:

| Path | Shape | Bytes | SHA-256 |
|---|---|---:|---|
| /private/tmp/v49_phase1c_candidate_rows.tsv | one header + 15,923 rows × 11 columns | 2,238,838 | 4d5f15cda8e1267426fd91ea76da92573ab2851ee033468ebb0ef206ff0c4c46 |

The ledger was sent to A3 and A4 with schema and hashes. It is temporary, derived, and not a canonical database.

## Findings

| ID | Priority | Result |
|---|---|---|
| A2-P0-01 | P0 | metadata 2,970/2,971 is an aggregate-unit mismatch. Candidate, SQLite, and TRACE catalog have the same 2,971-member set; no mismatch row/object can be honestly named because the meta scalar has no member set. |
| A2-P0-02 | P0 | candidate has 4,957 missing trace.tier keys. Legacy SQLite promoted exactly those IDs to source_verified through an explicit accepted-state fallback. The set is locked and must fail closed for research use. |
| A2-P1-01 | P1 | delimiter-packed/prose strings are common and cannot be split generically. |
| A2-P1-02 | P1 | edgeLabels cannot be positionally zipped to edgeIds for 9,393 surfaces. |
| A2-P1-03 | P1 | optional sourceObjectKey/sourceLocator and missing/null/blank distinctions require lossless parsing. |

## TSV and document validation

The symmetric-difference TSV is UTF-8, contains one header, four deterministic comparison rows, 20 unique columns, zero CR bytes, and no empty data row. The first static pass exposed one unnamed empty column; A2 named it row_identity and reran validation successfully. git diff --check passed for both A2 primary outputs before this receipt was added.

At that validation point:

| File | SHA-256 |
|---|---|
| 05_METADATA_SUPPORTED_RECONCILIATION.md | bcd8b6cba3e8065e11ff1efa4dba6dc6149a7850c33793117f1ce84d385437b9 |
| 05_METADATA_SUPPORTED_SYMMETRIC_DIFF.tsv | 704dec6d351ccb248002724e6d1b03c6c761bc5bd27c50c4b00d38ef72c3842c |

The root task will run the artifact-tool TSV inspection, global verifier, manifest, and package checksums after all agents finish.

## Unresolved and out-of-scope

No A2 measurement is unresolved. A2 deliberately does not convert 4,957 missing tiers into research-held object counts; A4 owns corpus eligibility. A3 owns relation classification. Prompt B owns rights and machine exposure.

## Modifications and prohibited actions

Modified only the three files listed under Task boundary. No candidate, SQLite, manifest, shard, frontend, QA, package, CI, deployment, or protected-main file was changed.

Not performed: PostgreSQL, DDL, Docker, npm, Next, TypeScript, browser, data import/export, image/network access, deduplication, merge, delimiter split, frozen hash repetition, SQLite write/integrity/vacuum, PR, merge, or deploy.

## Exit and residual processes

- A2 exit: PASS.
- Candidate scanner PID 97949 exited 0.
- Post-check process exited.
- Final A2-specific process scan returned no matching Node or Python process.
- Temporary evidence remains in /private/tmp for root/A3/A4 reuse; no long-running process owns it.
