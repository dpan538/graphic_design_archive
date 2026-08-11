# A6 — Raw Source Evidence Receipt

- Task boundary: Phase 1C raw/provider/source-evidence disposition only.
- Source HEAD: `6b111a78818a9e9ef37e4909c1f288d3b844b77e`
- Package status: **PASS** for deterministic enumeration and classification; evidence-readiness remains **PARTIAL** because held rows require later governance.
- Modified files: only `docs/audits/v49-authority-research-delta/06_RAW_SOURCE_EVIDENCE_DISPOSITION.tsv`, `docs/audits/v49-authority-research-delta/07_RAW_SOURCE_EVIDENCE_SUMMARY.json`, and this receipt after handoff from the temporary builder.
- Frozen assets modified: **none**.
- Network access: **none**.

## Scope

The ledger includes all 1,561 tracked files under any `_raw/` or `/raw/` path plus all 38 tracked JSON records under `data/manual_source_records/` and `data/remediation_source_records/`. The previous audit's 1,271 raw/probe JSON paths were used only as a reconciliation expectation and were independently re-enumerated at this HEAD. The wider measured raw-directory boundary is 1,561 files because it also contains HTTP/XML/HTML/text response bodies.

Context/derived artifacts such as capture result CSVs, indexes, linkage tables, schemas, templates, scripts, and reports are not duplicated into the row ledger. They are referenced from `context_ref` where relevant. Visual rights, provider policy, endpoint health, and delivery mode are explicitly outside A6 and remain for Prompt B.

## Evidence commands

All commands were read-only except writing the three assigned audit outputs through a temporary deterministic builder and patch application:

- `git rev-parse HEAD`
- `git ls-files -z` with deterministic path filtering and lexical sort
- Node `fs.readFile`, `crypto.createHash('sha256')`, and JSON parse validation for every scoped asset
- parse `data/capture_runs/capture_run_manifest_v1.csv` for run-level context only
- parse `generated/prefreeze_candidate_v48_transfer_manifest.json` and independently compare bytes/SHA-256 for its 30 selected raw responses
- `@oai/artifact-tool` CSV import/inspection passed for 1,600 rows including the header and all 16 columns; the parent task will independently repeat final TSV acceptance after all packages land
- final repository JSON/TSV parse, row-width, uniqueness, path/size, byte-copy, `git diff --check`, and residual-process checks passed after patching

No secret value, provider payload content, URL body, credential, token, visual-rights conclusion, or image was printed.

## Measured results

| Measure | Result |
| --- | ---: |
| Scoped artifacts | 1,599 |
| Raw-directory artifacts | 1,561 |
| Prior-audit raw/probe JSON subset, remeasured | 1,271 |
| Authored manual/remediation source records | 38 |
| Capture-manifest-context artifacts | 1,266 |
| Outside capture manifest | 295 |
| Transfer-manifest-selected raw responses | 30 |
| Standalone source-probe response bodies | 265 |
| Total bytes | 96,019,917 |
| Valid JSON | 1,309 |
| Invalid JSON | 0 |
| Transfer selected byte/hash mismatches | 0 |
| `UNCLASSIFIED_RAW_SOURCE` | 0 |

All 1,599 rows have path, tracked state, byte count, full-file SHA-256, format classification, family, owner, context, capture policy, authority, provenance disposition, evidence eligibility, research-use disposition, reason, and immutable Git recovery reference.

## Findings and severity

### P0

- 1,266 capture-run payloads have run-level manifest context but no artifact-level source-terms, request/capture, redaction, and review receipt. They remain `HELD_UNSUPPORTED`; Git tracking is not authority.
- 265 standalone probe response bodies document reachability/protocol observations only and remain `HELD_UNSUPPORTED` for evidence and research use.
- 38 curator-authored source records remain `HELD_UNSUPPORTED` until locator validation and a governed re-ingest decision. They cannot create canonical rows by themselves.

### P1

- The 30 transfer-manifest-selected raw responses match declared bytes and SHA-256. They are eligible for legacy reconciliation/lineage verification only, never canonical migration or research-claim authority.

### P2

- The previous 1,271 count described only JSON. A complete raw-directory inventory is 1,561 because 290 tracked XML/HTML/text payloads were outside that JSON-only unit; future gates must name the unit.

## Unresolved items

- Artifact-level source/terms/redaction/capture receipts and review actors are absent for held provider payloads.
- Curator-authored source records require governed re-ingest and evidence-locator validation.
- Prompt B must decide visual rights, provider policy, endpoint health, delivery mode, and any machine exposure. A6 makes no judgment on those axes.

These are explicit held states, not unclassified rows. `UNCLASSIFIED_RAW_SOURCE=0`.

## Actions explicitly not performed

- no network request, download, HTTP probe, image handling, database access, data import, data rewrite, or frozen-asset mutation;
- no visual-rights, provider-policy, endpoint-health, or delivery-mode decision;
- no automatic deduplication, merge, delimiter split, or canonical assertion creation;
- no PostgreSQL, Docker, npm, Next, TypeScript, browser, PR, merge, deploy, commit, or push;
- no modification to dirty main.

## Residual process and exit

- Persistent process started by A6: **0**.
- Builder exit: **PASS**.
- Final repository validation: **PASS** — 1,599 rows, 16 columns, 1,599 unique paths, all paths present with declared byte sizes, summary gates consistent, and temporary-to-repository bytes equal.
- Repository TSV SHA-256: `7358cbfba94fc999317bf6a4a4d73ace444b250c909cde06aaa40a6fe9fb759d`.
- Repository summary JSON SHA-256: `df8b832a8ceb6db4aa2dac9e625a22c99ae2e6f2f2948b58d41d9fb56afddcf8`.
- Final A6 residual-process scan: **0 matching processes**. Sandbox-local `pgrep` could not read the process list, so the same narrow pattern was checked once through an approved read-only `ps` scan; it returned no row.
