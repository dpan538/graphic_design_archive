# Cleanup action ledger

## Scope and status

Status: **PASS for Phase 1B classification; cleanup execution not authorized**.

The path-level ledger is `02_FILE_INVENTORY.tsv`. It records 14,359 paths with scope, path, tracked/ignored state, bytes, time, MIME/signature, owner/source, authority role, recovery reference, classification, reason, proposed action, duplicate identity, candidate hash, and deletion risk. This report adds the cross-package action decision and applies A9's stricter evidence ruling to the ten mechanically duplicate QA paths.

No protected-main path, frozen asset, tracked legacy source, QA frame, runtime dependency, frontend file, generated data, or delete candidate was removed, moved, rewritten, or re-encoded.

## Measured classification results

### A2 mechanical inventory snapshot

| Classification | Paths | Bytes |
|---|---:|---:|
| `KEEP_ACTIVE` | 201 | 6,689,919 |
| `MIGRATE` | 973 | 499,759,140 |
| `ARCHIVE_READ_ONLY` | 12,998 | 14,206,109,066 |
| `GENERATED_REPRODUCIBLE` | 0 | 0 |
| `DELETE_CANDIDATE` | 11 | 447,239 |
| `HOLD_UNKNOWN` | 176 | 7,967,299,304 |

### Consolidated conservative action state

A2 correctly identified ten exact redundant QA blobs as mechanical candidates. A9 then showed that their distinct scenario labels, capture intent, release/registry context, rights provenance, and test oracles are unrecoverable from the bytes alone. The consolidated action state therefore overlays those ten paths from `DELETE_CANDIDATE` to `HOLD_UNKNOWN`; the TSV remains the immutable A2 measurement snapshot and this report is the governing override.

| Classification | Effective paths | Effective bytes | Change from A2 |
|---|---:|---:|---|
| `KEEP_ACTIVE` | 201 | 6,689,919 | none |
| `MIGRATE` | 973 | 499,759,140 | none |
| `ARCHIVE_READ_ONLY` | 12,998 | 14,206,109,066 | none |
| `GENERATED_REPRODUCIBLE` | 0 | 0 | none; reproducibility was never inferred from a pathname |
| `DELETE_CANDIDATE` | 1 | 8,196 | only ignored `docs/.DS_Store` |
| `HOLD_UNKNOWN` | 186 | 7,967,738,347 | ten QA paths / 439,043 bytes moved here |

`DELETE_CANDIDATE` is not approval. The one remaining candidate may be removed only in a separately authorized cleanup with before/after status and recovery receipt.

## Action ledger

| Path or family | State | Tracked / authority | Source or owner | Recovery reference | Reason and risk | Proposed action / acceptance boundary |
|---|---|---|---|---|---|---|
| Five frozen v48 assets | `ARCHIVE_READ_ONLY` (JSON also migration source) | tracked LFS/content; exact roles in A3 | v48 freeze | checkpoint `0404c7f`, five hashes in report 13 | Critical rollback and integrity evidence | Never edit/dedupe. Migration reads only canonical JSON; SQLite is immutable reconciliation; manifests are evidence. |
| Other v48 JSON/SQLite/TRACE/shards/manifests/receipts | `ARCHIVE_READ_ONLY` | tracked; authoritative, reconciliation, or derived evidence by path | data/research owners | Git history plus A3 lineage ledger | Blind cleanup can erase lineage or disguise a non-self-contained build | Preserve; migrate only governed identities/projections after authority delta closure. |
| Four exact 90,895,254-byte `public_surface_mock_v0.json` placements | `MIGRATE` | tracked; derived runtime/Search projection, not canonical | data/frontend | Git `f076ca3`, A2 duplicate group | 272,685,762-byte duplication and direct full-payload coupling; deletion before adapter cutover breaks runtime | Replace all consumers/producers with sealed repository projection; verify route/search parity, then archive or remove redundant placements in a frontend task. |
| Nine frontend static-data producer/exporter scripts | `MIGRATE` | tracked; legacy producers | data/frontend | Git and A7 section 5.2 | Can overwrite frontend mirrors and bypass seal/CAS | Move generation ownership to data CI after release formats exist; require zero frontend-tree write side effects. |
| 26 runtime/compile data consumers | `MIGRATE` | tracked active runtime | frontend owner | Git and A7 consumer ledger | UI depends on legacy payload/path/decoder shapes | Cut over behind `ArchiveRepository`; acceptance is zero direct import/fetch/decoder outside adapters and passing pair-pinned contract tests. |
| `/contents`, unbounded folder Reader, dormant bulk params | `MIGRATE` | tracked active/dormant delivery code | frontend owner | Git and A7 | 26,041 membership links and up to 5,740-member request payload | Replace with bounded SSR/keyset windows; retire bulk params only after route/crawlability parity. |
| Six Puppeteer executables and four preview aliases | `ARCHIVE_READ_ONLY` or later isolated QA tooling | tracked; non-runtime tooling | QA/frontend | Git and A7 | Accidental browser/server invocation; no evidence manifest | Move behind explicit QA workflow/fixture and manifest. Do not invoke in prototype or product build. |
| `frontend/scripts/capture-file-page.js` | `HOLD_UNKNOWN` | tracked; unowned helper | unknown QA owner | Git | May have undocumented evidence consumer | Identify owner/caller. Archive or propose deletion only after dependency and scenario review. |
| Ten active AI/model runtime paths | `MIGRATE` (retire from runtime) | tracked; active product/runtime or package graph | frontend/AI | Git and A8 section 4 | Qwen remote model preparation undermines deterministic/right-safe runtime | Separately remove model UI/service/dependencies while preserving deterministic Search; focused contract/dependency/license checks required. |
| Seven v49 AI probe runners/outputs | `ARCHIVE_READ_ONLY` | tracked; historical experiment, non-authoritative | research/AI | Git and A8 | Executables can acquire models; outputs cover 1,417 historical surfaces and local paths | Move to non-runtime research archive; label non-authoritative; exclude from package/CI discovery. |
| 42 prompts/reports/system docs | `KEEP_ACTIVE` as documentation | tracked; historical methodology only | research/documentation | Git and A8 | Could be mistaken for executable or canonical evidence | Retain with retired/non-authoritative banner; no prompt authorizes model/crawl/ingest. |
| Protected-main `Archive/AI` and report artifacts | `ARCHIVE_READ_ONLY` | untracked protected-main recovery evidence | owner unknown | protected-main fingerprints and A8 | Four comparable files differ; not an authoritative retirement recipe | Do not copy wholesale or clean. Freeze only under separate protected-main authorization. |
| Protected-main clean hybrid RAG repo | `ARCHIVE_READ_ONLY` | nested clean repo; research history | research owner | nested HEAD in A8 | Independent experimental code/dependencies, not product input | Archive as independent repo; do not import into v49 runtime. |
| Protected-main dirty RAG lab | `HOLD_UNKNOWN` | nested repo with 9 modified tracked reports | owner decision required | nested HEAD/status in A8 | 6.9 GiB dependencies and uncommitted evidence; destructive cleanup could erase research | Owner first decides/fixes report provenance; only then classify dependencies as reproducible. |
| All 60 existing QA screenshots | `HOLD_UNKNOWN` | tracked historical QA; no rights/capture manifest | QA/research owner unassigned | Git `0404c7f`, A9 hashes | Pixel rights, scenario truth, viewport, release/registry identity, and accessibility oracle absent | Preserve byte-identically; create scenario/hash/rights manifest and owner decision before archive or deletion classification. |
| Ten QA duplicate non-keeper paths named below | `HOLD_UNKNOWN` override | tracked; exact bytes but distinct scenario labels | QA/research | Git plus duplicate keeper reference | Deleting can erase only evidence of intended scenario, including a failed swipe | No delete command until a scenario-to-hash manifest proves redundancy and a rights/owner decision exists. |
| `docs/.DS_Store` | `DELETE_CANDIDATE` | ignored/untracked, non-authoritative Finder metadata | OS | none required; byte count/status in TSV | Low deletion risk, but task did not authorize cleanup execution | Future exact-path removal only; verify it is still ignored, 8,196 bytes, and not replaced before action. |
| 1,266 raw tracked capture files / 26 observed directories | `ARCHIVE_READ_ONLY` pending disposition | tracked evidence; redaction/terms status unresolved | data/research/provider owners | Git, capture receipts, A3/A6 | Public-repository, terms, retention, rights, and declared 29-vs-26 directory conflict | Complete per-artifact disposition; do not migrate, publish, dedupe, or delete until approved. |
| Protected-main 10,937 untracked paths | `ARCHIVE_READ_ONLY` or `HOLD_UNKNOWN` per TSV | untracked protected work; not migration input | multiple/unknown | initial/final fingerprints and TSV | About 20.6 GB without proved Git recovery; includes databases/generated/active work | Exclude entirely. A separate owner-led archive/lineage task is prerequisite to any cleanup. |

## QA paths under the conservative override

All paths are under `docs/qa/screenshots/`:

1. `round10-mobile-region-stack-before-swipe.jpg`
2. `round11-mobile-trace-atlas-ready.png`
3. `round7-mobile-home-top-gap-fixed.png`
4. `round7-mobile-icon-menu.png`
5. `round8-mobile-menu-icon-only.jpg`
6. `round9-mobile-evidence-dots.jpg`
7. `round9-mobile-evidence-selected.jpg`
8. `round9-mobile-menu-icon-only.jpg`
9. `round9-mobile-object-current.jpg`
10. `round9-mobile-root-before-menu.jpg`

Their exact keepers, Git blob IDs, sizes, and risks remain in `02_FILE_INVENTORY.tsv`; seven content SHA groups and all 17 member paths are in report 09.

## AI/RAG/SLM retirement ledger

| Retirement class | Logical units | Action |
|---|---:|---|
| Remove from runtime | 10 | mandatory before frontend promotion; no removal this phase |
| Archive for history | 22 | preserve outside product runtime |
| Keep as documentation | 42 | retain, label non-authoritative |
| Unknown / needs review | 1 | owner/freeze decision before any dependency cleanup |
| Total | 75 | nested repo internals are not double-counted |

## A4/static-generation retirement ledger

| Class | Count or examples | Decision |
|---|---|---|
| Full production build entrance | 1 | later frontend CI only; prohibited in prototype/checkpoint |
| Active low-cardinality `generateStaticParams` routes | 2 | may remain only after repository decoupling and cardinality guard |
| Puppeteer screenshot/a11y executables | 6 | isolate as QA tooling; never build hooks |
| Static-data producer/exporter scripts | 9 | move to data CI/sealed release ownership; counted separately |
| Dormant bulk object/folder params and `/contents` bulk page | multiple code paths | retire/make unreachable before production build gate |
| Implemented print/PDF exporter | 0 | future on-demand, selected, bounded, rights-filtered design only |

## Recovery and deletion command drafts

These are review drafts, not executed commands.

For the only effective deletion candidate, a future authorized task must first re-run exact-path status/size checks, then may use this bounded command:

```text
rm -f -- docs/.DS_Store
```

Acceptance: target resolves exactly inside the v49 worktree, remains ignored/untracked and non-authoritative, before size is recorded, post-state is absent, dirty main/frozen hashes are unchanged, and the action is written to the process receipt.

No QA `git rm` draft is approved while A9 P0-01/P0-02 remain open. No command is drafted for protected-main dependency trees, tracked legacy files, frozen data, AI runtime paths, or producers because each requires a separate owner-approved implementation/recovery plan first.

## Evidence commands

Evidence comes from `git ls-files`, `git status --ignored`, full protected-main untracked enumeration, `stat`/`file` signatures, Git blob IDs, size-first candidate grouping, bounded SHA-256 confirmation, exact SQLite-candidate hashing, source/consumer searches, and package/process entrypoint inspection. Exact commands and performance controls are in reports 02, 07, 08, and 09.

## Priority, risk, and recommended action

- P0: protect frozen/dirty-main authority; remove runtime/model and direct data coupling only through later accepted implementations; disposition raw/third-party artifacts before publication.
- P1: assign owners/recovery for holds, isolate QA/model executables, prove producer recipes, and resolve MIME/evidence manifests.
- P2: remove OS metadata and proven redundant artifacts only after their higher-priority provenance gates close.

Blind deduplication has high risk: intentional release placement, capture provenance, or scenario meaning can differ even when bytes match. The safe order is authority → owner/recovery → consumer/producer parity → evidence manifest → explicit cleanup authorization.

## Actions explicitly not performed

No deletion candidate was deleted. No `git clean`, reset, checkout restoration, bulk delete, unparsed glob, history rewrite, package edit, dependency removal, frontend edit, QA re-encode, data regeneration, protected-main cleanup, or frozen-data mutation occurred. The only removed files were three task-created temporary scanners under `/tmp`, each exact-path and reconstructable; report 13 records them.
