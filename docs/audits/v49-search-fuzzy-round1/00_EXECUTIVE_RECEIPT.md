# v49 Fuzzy Search Round 1 — Executive Receipt

## Outcome

`PHASE_STATUS=COMPLETE`

`DECISION=GO_WITH_CONDITIONS`

`SEARCH_V1_READY=true`

The first-release search is a non-AI, deterministic, explainable lexical scorer over exactly 7,995 sealed public v49 stable-ID/title records. The 7,928 held records are absent from the artifact and runtime. No database, canonical release, production/staging environment, external search service, or AI/vector dependency changed.

## Source identity

| Field | Value |
|---|---|
| SOURCE_BRANCH | `chore/v49-repository-hygiene-database-freeze-20260821` |
| SOURCE_SHA | `c0ca9a1d4745cfd1054b924c648e57887830960d` |
| SOURCE_TREE_HASH | `f8ecd0046a4b8e3c1be657b2a31ac0b863f08ad0` |
| FEATURE_BRANCH | `feat/v49-fuzzy-search-round1-20260823` |
| WORKTREE | `/private/tmp/graphic_design_archive_v49_fuzzy_search_round1` |

The historical SHA was verified against local/remote source state before the isolated feature worktree was created; no newer valid descendant was present.

## Selected system

| Field | Value |
|---|---|
| Architecture | compact release-pinned server-only document set + bounded full-corpus lexical scorer |
| Algorithm | `v49-lexical-fuzzy-1` |
| Index format | `gda-search-documents-v1` |
| Documents | 7,995 |
| Raw bytes | 1,435,371 |
| Gzip bytes | 256,941 |
| Index SHA-256 | `35a6b7e1f8b749fca0ebfda9cf84f265de58d69fe6ef2bac0a4a2a9d263b1522` |
| Browser delivery | server-only; `/search` first-load JS 113 kB |
| New dependency | none |

## Quality and performance

| Metric | OLD | NEW |
|---|---:|---:|
| Held-out Top-1 | 31.79% | 100.00% |
| Held-out Top-5 | 32.37% | 100.00% |
| Held-out MRR@10 | 0.3191 | 1.0000 |
| Typo recovery | 0.00% | 100.00% |
| No-result precision | 100.00% | 100.00% |

NEW local compute: 41.90 ms P50, 56.73 ms P95, 189.31 ms maximum; cold typo query 88.83 ms. The benchmark is a 271-query real-record-derived known-item test with a 197-query held-out split, not a human topical-relevance claim.

## Key production corrections

- production composition now defaults to the validated derived-v49 provider;
- relevance cursor binds release, manifest, query hash, algorithm, format, index SHA, scope, and terminal tuple;
- every hit has a machine-readable explanation;
- stale 22 MB / 8,636-row legacy browser index and dead consumers are deleted;
- client `fetch` is wrapped to preserve the correct browser global binding;
- explicit Enter submission is verified;
- search UI is archive-only and displays no unsupported metadata.

## Boundaries

```text
DATABASE_FILES_CHANGED=0
CANONICAL_RELEASE_CHANGED=false
AI_DEPENDENCY_ADDED=false
VECTOR_DEPENDENCY_ADDED=false
EMBEDDING_ARTIFACT_COUNT=0
AI_API_CALL_COUNT=0
NEW_EXTERNAL_SEARCH_SERVICE=false
TRACE_RUNTIME_FILES_CHANGED=0
CLAUDE_REDESIGN_TOUCHED=false
```

One pre-existing TRACE verification script was updated only to read the replacement search artifact after the stale public asset was removed; TRACE runtime/data/UX semantics were not changed.

## Evidence map

- research decision: `docs/research/search-v49-round1/00_EXECUTIVE_DECISION.md`
- architecture: `docs/research/search-v49-round1/02_SEARCH_ARCHITECTURE_DECISION.md`
- raw query comparison: `docs/research/search-v49-round1/03_SEARCH_QUALITY_COMPARISON.tsv`
- aggregate benchmark: `benchmark-results.json`
- manual failure review: `docs/research/search-v49-round1/09_FAILURE_ANALYSIS.md`
- validation: `01_VALIDATION.md`
- release/security gates: `02_RELEASE_AND_SECURITY_GATES.md`
