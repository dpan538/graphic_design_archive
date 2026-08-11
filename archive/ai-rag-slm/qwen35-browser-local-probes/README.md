# Qwen 3.5 browser-local probe archive

Status: **historical research only**.

This directory preserves the browser-local Qwen/LLM probe runners and their
recorded outputs exactly as they existed before v49 runtime retirement. The
contents are:

- non-authoritative research history;
- not imported by production code;
- not part of the v49 data platform;
- not a canonical, reconciliation, integrity-evidence, Search, or TRACE input;
- not an approved runtime, migration, release, or verification path.

The archived runners may contain original local output paths and experimental
assumptions. Do not execute them as a production or data-generation workflow.
If future historical analysis requires a new run, copy the runner into an
explicit experiment workspace and preserve the original archived bytes.

## Preserved files

| Original path | Archived path | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `frontend/scripts/probe-qwen35-runtime.mjs` | `runners/probe-qwen35-runtime.mjs` | 6,372 | `4c1cd1ca7e219d2a4ea4c0634474bda37bd1a3aa1985acf6cc9c18537300bda7` |
| `frontend/scripts/probe-qwen35-generation.mjs` | `runners/probe-qwen35-generation.mjs` | 14,078 | `6beeae595eff4e200cca082557443393d3794f2d6f62b6590f901535c5965616` |
| `frontend/scripts/probe-qwen35-rag-policy.js` | `runners/probe-qwen35-rag-policy.js` | 5,046 | `9951d67c86aab508ad378dbdde7c442f6d0ddefe89a070bbccffcd6e9e557f79` |
| `generated/qwen35_runtime_probe_v0.json` | `results/qwen35_runtime_probe_v0.json` | 3,572 | `dfeaaca5aa1509b8c0f50a1cc15e66004d10e15f748a0b68fd3aaed924c1cdb6` |
| `generated/qwen35_generation_probe_v0.json` | `results/qwen35_generation_probe_v0.json` | 3,141 | `1e11428a88e5c70445f6b0ee2733134d4f521eef36469a3c8a0bf05529853643` |
| `generated/qwen35_rag_policy_probe_v0.json` | `results/qwen35_rag_policy_probe_v0.json` | 25,321 | `2d163202c5a6c281d069da938393fff71a3d71e1b6348c7d857016e804eec682` |
| `generated/archive_assistant_primer_v0.json` | `results/archive_assistant_primer_v0.json` | 1,272 | `b189bca6593c83a674595665b415b0df749bd1364fee56c9850109552b564b06` |

The hashes above are both the pre-move and post-move values. A path move must
never be interpreted as a change in evidentiary authority.

## Preservation rule

Treat `runners/` and `results/` as read-only archival payload. Corrections or
new observations belong in a separately versioned experiment directory with a
new manifest; do not overwrite these files.
