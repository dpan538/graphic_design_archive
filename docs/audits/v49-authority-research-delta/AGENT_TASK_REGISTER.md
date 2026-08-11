# Phase 1C agent task register

- Concurrency cap: three subagents
- Cumulative packages: seven
- Shared-worktree rule: exclusive output paths per package
- Frozen-input rule: read-only; SQLite only by immutable URI

| Package | Independent scope | Exclusive outputs | Status | Mutation boundary |
|---|---|---|---|---|
| A1 | authority, lineage, missing v47 parents, clean-checkpoint builder boundary | `01_SCOPED_AUTHORITY_MATRIX.md`; `02_PARENT_ASSET_DEPENDENCY_LEDGER.tsv`; `agents/A1_AUTHORITY_LINEAGE_RECEIPT.md` | PASS | reports only; no parent recovery or builder run |
| A2 | deterministic 15,923-row parse, ID/presence/cardinality, metadata conflict | `05_METADATA_SUPPORTED_RECONCILIATION.md`; `05_METADATA_SUPPORTED_SYMMETRIC_DIFF.tsv`; `agents/A2_COUNT_PARSER_RECEIPT.md` | PASS | reports only; one candidate parse, immutable reconciliation |
| A3 | graph-unit measurement and closed classification | `03_GRAPH_FACT_CLASSIFICATION_RULES.json`; `04_GRAPH_FACT_RECONCILIATION.json`; `agents/A3_GRAPH_CLASSIFICATION_RECEIPT.md` | PASS_WITH_EXPLICIT_HOLDS | reports only; no graph promotion or regeneration |
| A4 | versioned research corpus, TRACE eligibility, missingness | `09_RESEARCH_CORPUS_POLICY.md`; `10_CORPUS_MEMBERSHIP_BASELINE.tsv`; `11_MISSINGNESS_BASELINE.json`; `agents/A4_CORPUS_MISSINGNESS_RECEIPT.md` | PASS | reports only; consumed A2 shared ledger, did not rescan candidate |
| A6 | raw/source evidence enumeration and provenance/research-use disposition | `06_RAW_SOURCE_EVIDENCE_DISPOSITION.tsv`; `07_RAW_SOURCE_EVIDENCE_SUMMARY.json`; `agents/A6_RAW_SOURCE_EVIDENCE_RECEIPT.md` | PASS; EVIDENCE_READINESS_PARTIAL | reports only; Prompt B axes excluded |
| A7 | epistemic relation registry and TRACE projection delta | `08_EPISTEMIC_RELATION_REGISTRY.json`; `12_TRACE_PROJECTION_DELTA.md`; `agents/A7_EPISTEMIC_TRACE_RECEIPT.md` | PASS_WITH_EXPLICIT_HOLDS | reports only; no candidate/SQLite rescan |
| A5 | detached whole-package verifier | `agents/A5_INDEPENDENT_VERIFIER_RECEIPT.md` | PASS; 134/134 machine checks, zero errors | validation receipt only; did not edit package conclusions |

## Shared evidence discipline

- A2 performed the only subagent full candidate parse and published `/private/tmp/v49_phase1c_candidate_rows.tsv` (15,923 rows, 2,238,838 bytes, SHA-256 `4d5f15cda8e1267426fd91ea76da92573ab2851ee033468ebb0ef206ff0c4c46`) for A3/A4. The temporary ledger is not a committed authority artifact.
- A3 and A4 consumed the shared aggregates/ledger rather than repeating the 190 MB parse.
- The primary task performed one five-asset hash pass and one SQLite immutable `integrity_check` before package verification.
- A6 enumerated and hashed its bounded 1,599-artifact source-evidence scope once.
- A5 is intentionally independent of A1–A4/A6/A7 design decisions and cannot repair their outputs.

## Health and forbidden-process boundary

Each completed agent receipt records its commands, measured results, explicitly unperformed actions, and zero agent-owned residual process. No package launched PostgreSQL, Docker, npm, Next.js, TypeScript, browser automation, data export, image download, frontend server, migration, or frozen-asset writer.

## Final register result

A5 returned PASS with no conflict. The primary task must now regenerate package manifest/checksums, rerun the whole-package verifier, and perform final Git/main/process verification. A later mismatch cannot be masked by A5's earlier PASS; it must leave the package `PARTIAL_WITH_EVIDENCE` unless corrected and reverified.
