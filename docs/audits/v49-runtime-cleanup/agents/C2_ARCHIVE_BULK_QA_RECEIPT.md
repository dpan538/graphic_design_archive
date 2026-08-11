# C2 — Historical probe archive, bulk-helper retirement, QA governance and safe-delete receipt

Status: **PASS**

Scope owner: Phase 1D cleanup C2

Commit authority: none; `git mv` updated the index and produced seven staged
R100 renames. C2 did not run an independent `git add`, did not stage any
additional path, and did not commit. The main controller owns the consolidated
index/allowlist review and final commit.

## 1. Task boundary

C2 performed only these actions:

1. moved three historical Qwen probe runners and four recorded probe/result
   files into a tracked read-only archive;
2. removed the two audited, unreferenced, high-cardinality static-parameter
   helpers `allFolderParams` and `allSurfaceParams`;
3. added a governance README and JSON Schema for the 60 existing QA images;
4. deleted the one explicitly approved ignored/untracked file
   `docs/.DS_Store` after an exact path, size, status, and hash check.

C2 did not touch `Reader`, `ArchiveShell`, deterministic Search, assistant CSS,
the assistant route or libraries, package manifests, package locks, frozen v48
assets, the dirty main worktree, or any QA image bytes or paths.

## 2. Historical probe disposition

Archive root:
`archive/ai-rag-slm/qwen35-browser-local-probes/`

The archive README declares the payload historical research only,
non-authoritative, not production-imported, and not part of the v49 data
platform. The following pre-move and post-move measurements are identical:

| Original path | Archived path | Bytes | Pre/post SHA-256 | Git result |
| --- | --- | ---: | --- | --- |
| `frontend/scripts/probe-qwen35-runtime.mjs` | `archive/ai-rag-slm/qwen35-browser-local-probes/runners/probe-qwen35-runtime.mjs` | 6,372 | `4c1cd1ca7e219d2a4ea4c0634474bda37bd1a3aa1985acf6cc9c18537300bda7` | R100 |
| `frontend/scripts/probe-qwen35-generation.mjs` | `archive/ai-rag-slm/qwen35-browser-local-probes/runners/probe-qwen35-generation.mjs` | 14,078 | `6beeae595eff4e200cca082557443393d3794f2d6f62b6590f901535c5965616` | R100 |
| `frontend/scripts/probe-qwen35-rag-policy.js` | `archive/ai-rag-slm/qwen35-browser-local-probes/runners/probe-qwen35-rag-policy.js` | 5,046 | `9951d67c86aab508ad378dbdde7c442f6d0ddefe89a070bbccffcd6e9e557f79` | R100 |
| `generated/qwen35_runtime_probe_v0.json` | `archive/ai-rag-slm/qwen35-browser-local-probes/results/qwen35_runtime_probe_v0.json` | 3,572 | `dfeaaca5aa1509b8c0f50a1cc15e66004d10e15f748a0b68fd3aaed924c1cdb6` | R100 |
| `generated/qwen35_generation_probe_v0.json` | `archive/ai-rag-slm/qwen35-browser-local-probes/results/qwen35_generation_probe_v0.json` | 3,141 | `1e11428a88e5c70445f6b0ee2733134d4f521eef36469a3c8a0bf05529853643` | R100 |
| `generated/qwen35_rag_policy_probe_v0.json` | `archive/ai-rag-slm/qwen35-browser-local-probes/results/qwen35_rag_policy_probe_v0.json` | 25,321 | `2d163202c5a6c281d069da938393fff71a3d71e1b6348c7d857016e804eec682` | R100 |
| `generated/archive_assistant_primer_v0.json` | `archive/ai-rag-slm/qwen35-browser-local-probes/results/archive_assistant_primer_v0.json` | 1,272 | `b189bca6593c83a674595665b415b0df749bd1364fee56c9850109552b564b06` | R100 |

All four archived JSON files parse successfully. Searches of `frontend/src`,
`frontend/package.json`, and `frontend/package-lock.json` found zero active
references to the archived runner/result names.

Historical prose in `PROJECT_LOG.md`, `prompts/`, and `docs/system/` retains the
original paths as provenance; it is not an executable production import.

## 3. Dormant bulk helper retirement

Changed file: `frontend/src/lib/archive-data.ts`

- removed `allFolderParams`, whose all-folder expansion was unreferenced;
- removed `allSurfaceParams`, whose all-surface expansion was unreferenced;
- retained `allFolderTypeParams`, which is still used by the low-cardinality
  route `frontend/src/app/folders/[type]/page.tsx`;
- retained all A4 visual components and pagination primitives.

Post-change reference scans:

```text
rg "allFolderParams|allSurfaceParams" frontend/src
matches = 0

rg "allFolderTypeParams" frontend/src
matches = 3 (definition, import, call)
```

The Next.js static-generation guidance was applied by distinguishing dormant
high-cardinality expansion helpers from the active low-cardinality
`generateStaticParams` input.

### A4 preservation proof

The following HEAD and worktree hashes are identical:

| Path | HEAD/worktree SHA-256 |
| --- | --- |
| `frontend/src/components/archive/layouts.tsx` | `033f631ba4b8dc5dbbb4f71eebae76fc5aa0616622d4f9cd67e90ac154269847` |
| `frontend/src/components/archive/blocks.tsx` | `85e6bd377541baf2e1762cbb2a84d3c68294203dc639dd7cecdbb22907fb4a46` |
| `frontend/src/components/archive/reader/LeafFrame.tsx` | `a7726ba872a556c121f8dff767f6e8eebfaf12f1cd1ccd9187183f9077f0cae9` |
| `frontend/src/lib/paginate.ts` | `94f3e4522440ce90cabee54e972043f45aa6131f081a35e5ae1dd1b2be2a77c6` |

## 4. QA evidence governance

Added:

- `docs/qa/README.md`;
- `docs/qa/SCREENSHOT_MANIFEST.schema.json`.

The schema requires research-release identity, an atomic optional
visual-registry identity pair, SHA-256, bytes, actual MIME, extension,
dimensions, rights provenance, oracle/version/observations, interaction
coverage, and accessibility coverage. Missing evidence uses `NOT_EVALUATED`;
the schema does not retroactively certify the legacy images.

Measured before and after:

```text
filesystem image count = 60
tracked image count = 60
path-plus-content fingerprint =
287289be2f58cae02f8746290c37ebec8880cd1bf461f112a64733b1cb499220
image diff versus HEAD = none
```

The 60 files remain `HOLD_UNKNOWN` pending provenance and rights review. The
known 26 filename-extension/MIME mismatches (all 60 signatures are JPEG; 26
paths end in `.png`) were intentionally preserved rather than renamed or
re-encoded.

## 5. Approved safe delete

Exact path:
`/Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform/docs/.DS_Store`

Before:

```text
Git status = !! docs/.DS_Store
bytes = 10244
SHA-256 = dcdc3b5be1090bb9a63ec44a879703de496bfdcb496e5bb1471095b138a51cd8
```

Command:

```text
rm -f /Users/jarlgiovanni/Desktop/modern_GD_history_v49_data_platform/docs/.DS_Store
```

After:

```text
path exists = false
Git status entry = none
```

Reason: ignored/untracked macOS metadata, explicitly approved as the only safe
delete in Phase 1D. It was not evidence or source data. It was never tracked,
so Git does not restore it; macOS can regenerate it. No other ignored,
untracked, generated, QA, or legacy file was deleted.

## 6. Evidence commands

Read-only or narrowly scoped commands used:

```text
git status --short
git ls-files <seven assigned probe/result paths>
shasum -a 256 <seven source paths>
stat -f '%z %N' <seven source paths>
rg -n 'allFolderParams|allSurfaceParams|allFolderTypeParams' frontend
find docs/qa/screenshots -type f
git ls-files docs/qa/screenshots
file docs/qa/screenshots/*
git mv <three audited runners> <archive runners directory>
git mv <four audited results> <archive results directory>
python3 -m json.tool <archived JSON and QA schema>
git diff --exit-code HEAD -- <four A4 component/pagination paths>
git diff --name-status HEAD -- <C2 scope>
```

No network, server, compiler, browser, database, or generator command was run.

## 7. Findings and remaining risk

| Severity | Finding | Disposition |
| --- | --- | --- |
| P0 | none in C2 scope | closed |
| P1 | All 60 legacy QA images lack complete pixel provenance/rights receipts | preserved as `HOLD_UNKNOWN`; governance contract added; publication remains blocked |
| P1 | 26 `.png` paths contain JPEG bytes | preserved byte-for-byte; future governed rename/re-encode decision required |
| P2 | Historical prose names the old probe paths | retained as provenance; archive README supplies the current disposition |

## 8. Explicit status

```text
HISTORICAL_AI_PROBES_ARCHIVED=true
ARCHIVED_PROBE_FILE_COUNT=7
ARCHIVED_PROBE_BYTES_PRESERVED=true
ARCHIVED_PROBE_PRODUCTION_IMPORTS=0
DORMANT_BULK_ROUTE_GENERATORS=0
LOW_CARDINALITY_FOLDER_TYPE_GENERATOR_PRESERVED=true
A4_VISUAL_COMPONENTS_PRESERVED=true
QA_GOVERNANCE_SKELETON_ADDED=true
QA_IMAGE_COUNT=60
QA_IMAGES_UNCHANGED=true
SAFE_DELETE_EXECUTED=docs/.DS_Store
OTHER_UNTRACKED_DELETED=0
C2_RESIDUAL_PROCESSES=0
C2_STATUS=PASS
```

## 9. Actions explicitly not performed

- no `npm install`, package-lock update, Next dev/build, TypeScript check,
  browser automation, screenshot generation, or image download;
- no PostgreSQL, Docker, migration, data import/export, or frozen-asset write;
- no QA image delete, rename, re-encode, metadata rewrite, or visual judgment;
- no Search, A4 visual component, `/contents`, Folder Reader, direct-data
  coupling, 90.9 MB payload, v48 asset, or dirty-main cleanup;
- no independent `git add`, commit, push, merge, PR, or deploy. The seven R100
  renames are staged because `git mv` updates the index; the main controller
  will perform the consolidated index/allowlist review.
