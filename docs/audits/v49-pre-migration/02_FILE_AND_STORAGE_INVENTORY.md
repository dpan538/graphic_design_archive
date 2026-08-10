# A2 — File and Storage Inventory

## Status

**PASS** — path coverage, classification, and the bounded duplicate scan are
complete for the defined A2 scope. All size+signature+path candidates, including
three pairs of large untracked historical SQLite files, received a content
SHA-256. The six databases are pairwise distinct within their candidate groups.
No source, frozen asset, or protected-main file was deleted, moved, rewritten,
or read as a migration input.

Scan window: 2026-08-10 to 2026-08-11 (Australia/Brisbane).

The machine-readable inventory is
[02_FILE_INVENTORY.tsv](./02_FILE_INVENTORY.tsv), SHA-256
`9e42b1e83b301c07e4ae1bb5696328b81f66e4f5172960eb6068bc9e29f0c7fa`.
It has 14,360 physical lines: one header and 14,359 data rows.

## Scope

- Enumerated all 3,419 tracked files at the initial v49 HEAD
  `f076ca3444aaa0f413bb61fe2cb568d6a9aa2720`.
- Enumerated the two audit-task files already present as v49 untracked inputs at
  the A2 snapshot and the single ignored file `docs/.DS_Store`. The inventory
  deliberately does not contain itself; task outputs created after the snapshot
  belong in `AUDIT_MANIFEST.json`.
- Enumerated every one of the protected dirty main's 10,937 non-ignored
  untracked paths without modifying that worktree.
- Recorded scope, relative path, Git/ignored status, byte size, UTC mtime,
  binary signature or extension MIME, inferred source owner, authority role,
  recovery reference, one allowed cleanup classification, reason, proposed
  action, deletion risk, duplicate group, identity basis, and candidate SHA-256.
- Used binary magic for SQLite, PNG, JPEG, GIF, PDF, and ZIP containers;
  extension MIME is explicitly labelled when magic was not inspected beyond the
  first 16 bytes. `.ts`, `.tsx`, and `.jsonl` ambiguity was normalized to
  TypeScript/TSX/NDJSON labels.
- This partition does not decide data semantics or database authority; A3 owns
  those decisions. It also does not replace A1's Git history/LFS analysis or
  A9's image-dimension and visual QA assessment.

## Evidence commands and method

Commands are shown without secret values. No environment-file content was
printed.

```text
git ls-files -z
git ls-files --others --exclude-standard -z
git ls-files --others --ignored --exclude-standard -z
git -C /Users/jarlgiovanni/Desktop/modern_GD_history \
  ls-files --others --exclude-standard -z
git ls-files -s -z
stat -f '%z %m %N' <enumerated path>
shasum -a 256 docs/audits/v49-pre-migration/02_FILE_INVENTORY.tsv
pgrep -fl '/tmp/a2_(inventory|hash_candidates)\.py'
```

The inventory routine used `lstat`, read at most 16 leading bytes per regular
file for signature classification, and escaped tabs/newlines in TSV fields.
Duplicate detection was deliberately two-stage:

1. Tracked v49 equality uses the Git index blob ID. Repeated blob identity is
   exact content evidence and does not reread large working-tree files.
2. Untracked/cross-scope candidates first require equal size plus MIME/signature
   and an exact/normalized basename match, or a visual-file signature.
3. The bounded candidate pass first hashed 1,325 groups/3,914 members no larger
   than 10,000,000 bytes (69,791,028 bytes). Filenames matching secret-risk
   patterns would have been skipped; zero selected members matched.
4. The three remaining SQLite groups/six members were then hashed in one
   read-only session (2,496,978,944 bytes). In total, all 1,328 stage-one groups
   and 3,920 members received SHA-256 evidence; no size-only candidate remains.

## Measured inventory

| Scope | Status population | Files | Bytes |
| --- | --- | ---: | ---: |
| v49 worktree | 3,419 tracked | 3,419 | 2,048,837,572 |
| v49 worktree snapshot | task evidence, untracked | 2 | 4,700 |
| v49 worktree | ignored `.DS_Store` | 1 | 8,196 |
| protected dirty main | non-ignored untracked | 10,937 | 20,631,454,200 |
| **Total TSV population** |  | **14,359** | **22,680,304,668** |

The v49 byte count excludes this A2 TSV and all audit files produced after the
enumeration snapshot. It is therefore a repository-input snapshot, not an audit
directory self-measurement.

### Cleanup classification ledger

| Classification | Files | Bytes | Meaning in this audit |
| --- | ---: | ---: | --- |
| `KEEP_ACTIVE` | 201 | 6,689,919 | Active source, governance, licence, or audit evidence |
| `MIGRATE` | 973 | 499,759,140 | Runtime data copies, TRACE release products, scripts, or legacy schema requiring an explicit destination |
| `ARCHIVE_READ_ONLY` | 12,998 | 14,206,109,066 | Frozen, raw, provenance, database, research, design, or historical evidence |
| `GENERATED_REPRODUCIBLE` | 0 | 0 | None asserted: a generated pathname alone did not prove an input+producer+version recipe |
| `DELETE_CANDIDATE` | 11 | 447,239 | One Finder metadata file and ten exact duplicate QA blobs; candidate only |
| `HOLD_UNKNOWN` | 176 | 7,967,299,304 | Protected-main paths whose owner, producer, or recovery chain is incomplete |

`DELETE_CANDIDATE` is not deletion approval. Each row carries a recovery
reference and risk. No untracked protected-main file was classified for
deletion.

### v49 storage concentrations

| Prefix or asset family | Files | Bytes | Finding |
| --- | ---: | ---: | --- |
| `data/` | 2,060 | 1,245,884,773 | Raw capture, legacy databases, reconciliation and research outputs; archive pending A3 lineage |
| `generated/` | 16 | 472,702,994 | Tracked snapshots, including frozen candidate JSON; not automatically reproducible |
| `frontend/public/data/` | 583 | 217,096,262 | Derived/runtime payloads embedded in the frontend tree |
| `frontend/src/data/` | 1 | 90,895,254 | Full `public_surface_mock_v0.json` embedded in source |
| `scripts/` | 197 | 3,605,638 | Pipeline/reconciliation code to migrate or retire by explicit ledger |
| `db/` | 16 | 4,186,721 | Legacy schema/validation evidence, not v49 executable authority |
| `docs/qa/` | 60 | 2,860,448 | QA evidence; seven exact-image duplicate groups were found |
| `docs/capture/` | 193 | 2,966,281 | Historical capture and v48 visual evidence |

Four tracked files exceed 100 MB:

- `data/prefreeze_candidate_v48.sqlite` — 421,801,984 bytes;
- `data/prefreeze_candidate_v46.sqlite` — 419,688,448 bytes;
- `generated/public_surfaces_prefreeze_candidate_v48.json` — 190,067,852 bytes;
- `generated/public_surfaces_prefreeze_candidate_v46.json` — 190,039,480 bytes.

LFS/history policy belongs to A1. A2 classifies both v48 frozen assets
`ARCHIVE_READ_ONLY` and does not propose storage mutation.

### Protected dirty-main concentration

| Top-level path | Untracked files | Bytes | A2 disposition |
| --- | ---: | ---: | --- |
| `data/` | 10,101 | 12,643,432,349 | Archive/hold; no pattern deletion |
| `generated/` | 52 | 7,786,577,640 | `HOLD_UNKNOWN`: producer and reproducibility are unproved |
| `frontend/` | 113 | 179,179,392 | `HOLD_UNKNOWN`: may be active dirty work |
| `Design/` | 260 | 17,880,322 | Archive as design evidence pending ownership |
| `scripts/` | 176 | 2,272,435 | Migrate only after reproducibility review |
| `tmp/` | 9 | 1,538,849 | `HOLD_UNKNOWN`; a temporary name is not deletion proof |
| all other roots | 226 | 573,213 | Research/design archive or owner review; exact rows are in the TSV |

The final “all other roots” aggregate is intentionally not used as a gate; its
constituents are recorded individually in the TSV. The material findings are
that 77 main-untracked files are at least 100 MB and account for
19,596,676,794 bytes, and 32 main-untracked files have an SQLite-3 signature.
None has a proved Git recovery reference. They cannot be migration inputs merely
because of a version-like filename.

## Duplicate and signature evidence

### Exact tracked Git blobs

- 113 exact blob groups, 283 members.
- 276,206,239 bytes is the upper bound obtained by retaining one member per
  group. It is **not** safely reclaimable space because many paths are deliberate
  runtime, release, or provenance placements.
- One group dominates the number: four exact 90,895,254-byte copies of
  `public_surface_mock_v0.json`, for an upper-bound duplicate payload of
  272,685,762 bytes:
  `data/public_surface_mock_v0.json`,
  `frontend/public/data/public_surface_mock_v0.json`,
  `frontend/src/data/public_surface_mock_v0.json`, and
  `generated/public_surfaces_v1.json`.

Those four paths are `MIGRATE`, not `DELETE_CANDIDATE`. They expose direct
frontend/data coupling and must remain derived projections rather than becoming
additional canonical inputs.

### Confirmed untracked/cross-scope SHA-256 groups

- 213 SHA-256-confirmed groups, 528 members.
- 22,050,790 bytes is the retain-one upper bound, not a deletion authorization.
- The largest confirmed groups include identical historical narrative-authority
  CSVs (v29/v30 and v26/v27), identical v40/v41 topology audit CSVs, and four
  identical v40–v43 geography review-hold JSON files.
- Raw-capture duplicates remain `ARCHIVE_READ_ONLY`: identical bytes at two
  capture paths can still carry distinct provenance/selection context.

### Large candidates proved distinct

| Former candidate | Bytes each | Paths | Status |
| --- | ---: | --- | --- |
| `SIZECAND-0001` | 419,733,504 | `data/prefreeze_candidate_v38.sqlite`; `data/prefreeze_candidate_v45.sqlite` | distinct SHA-256 values |
| `SIZECAND-0002` | 419,704,832 | `data/prefreeze_candidate_v40.sqlite`; `data/prefreeze_candidate_v41.sqlite` | distinct SHA-256 values |
| `SIZECAND-0003` | 409,051,136 | `data/prefreeze_candidate_v29.sqlite`; `data/prefreeze_candidate_v30.sqlite` | distinct SHA-256 values |

All six are protected-main untracked files, remain `ARCHIVE_READ_ONLY`, and are
not required for the v48-to-v49 canonical migration. Equal byte length would
have been a false duplicate signal; no later dedupe task may collapse these
pairs on the basis of filename, version, size, or SQLite signature.

### QA and MIME/signature anomalies

- Seven tracked Git-blob groups contain 17 exact QA image members. Ten non-keeper
  rows are listed as `DELETE_CANDIDATE`; this includes the exact identical
  `round10-mobile-region-stack-before-swipe.jpg` and
  `round10-mobile-region-stack-after-swipe.jpg` pair.
- 253 `.png` paths contain a JPEG signature: 122 in v49 and 131 in protected
  main. This includes v48 capture images, tracked QA rounds, frontend QA, and
  protected-main design screenshots. No file was renamed or re-encoded. A9 must
  decide manifest and evidence consequences.
- `docs/.DS_Store` is the only ignored v49 file observed and the only low-risk
  non-QA deletion candidate.

## Priority findings

| ID | Priority | Status | Affected paths | Risk | Recommended action |
| --- | --- | --- | --- | --- | --- |
| A2-P0-01 | P0 | OPEN CONTROL | Four exact `public_surface_mock_v0.json` placements | A derived Search/runtime population could be mistaken for a canonical database; frontend remains directly coupled to a 90.9 MB source copy | Enforce A3 authority allowlist: JSON v48 canonical input only; migrate these four derived placements behind the release repository |
| A2-P0-02 | P0 | OPEN CONTROL | Protected main's 10,937 untracked paths, especially 32 SQLite files and 52 generated files | No proved Git recovery; accidental source selection or cleanup would be irreversible | Keep the entire worktree out of migration inputs; create a separately authorized archive/lineage manifest before any action |
| A2-P0-03 | P0 | PASS IN A2 | Five frozen assets represented by exact paths in the TSV | Cleanup or dedupe could mutate required checkpoint evidence | All are classified immutable/archive or migration-only; perform no cleanup |
| A2-P1-01 | P1 | PARTIAL | 176 `HOLD_UNKNOWN` rows, 7,967,299,304 bytes | Producer, owner, recovery, or active-work status is incomplete | Owner triage and recovery manifest; do not infer reproducibility from directory names |
| A2-P1-02 | P1 | PASS | Six historical SQLite files in three former `SIZECAND` groups | Equal size/signature could have been misreported as exact duplication | SHA-256 proves all three pairs distinct; retain separately and preserve lineage |
| A2-P1-03 | P1 | OPEN | 253 PNG-extension/JPEG-signature paths | MIME claims, QA manifests, and duplicate-frame review can be misleading | A9 should record actual MIME and decide whether a later non-frozen evidence repair is allowed |
| A2-P1-04 | P1 | OPEN | 113 Git duplicate groups and 213 SHA duplicate groups | Blind dedupe would erase intentional release placements or capture provenance | Use producer/consumer lineage and one explicit keeper before any cleanup execution |
| A2-P2-01 | P2 | CANDIDATE ONLY | `docs/.DS_Store` | Repository noise | Delete only in a separately authorized reversible cleanup and verify status afterward |
| A2-P2-02 | P2 | CANDIDATE ONLY | Ten exact duplicate QA rows | Redundant frames consume evidence surface and can overstate coverage | A9 confirms semantic redundancy and checksum-manifest coverage before deletion |

## Recommended repository actions

1. Treat this TSV as the path-level allow/hold ledger for later cleanup. Any
   deletion plan must name a row, current checksum/blob, keeper or recovery
   reference, responsible owner, and acceptance test.
2. Make migration input selection path- and hash-allowlisted. Never discover
   candidate databases/JSON by globbing `data/prefreeze_candidate_v*` or
   `generated/public_surfaces*`.
3. Move frontend payloads only in the later runtime-repository phase. Preserve
   the current bytes until data parity and route contracts pass independently.
4. Create a protected-main archival intake task before cleanup. Start with the
   77 files at least 100 MB, 32 SQLite files, and 52 generated-path holds.
5. Require a producer version, immutable input references, command/config, and
   parity receipt before changing any row to `GENERATED_REPRODUCIBLE`.

## Actions explicitly not performed

- Did not modify, stage, delete, move, rename, or hash every file in the dirty
  main worktree.
- Did not delete any `DELETE_CANDIDATE`.
- Did not modify v48 JSON, SQLite, shards, manifests, receipts, QA files, source,
  package files, CI, or deployment configuration.
- Did not open SQLite, run integrity/VACUUM/migration, export or regenerate data,
  or create sidecars.
- Did not run npm, Next, TypeScript, PostgreSQL, Docker, browser automation,
  image download, pHash, blurhash, full build, or server processes.
- Did not print environment or secret values.
- Did not infer that equal size, matching version names, an IIIF/API endpoint, or
  a `generated/` directory proves byte equality, authority, rights, or
  reproducibility.

## Residual process receipt

`pgrep -fl '/tmp/a2_(inventory|hash_candidates)\.py'` returned no process after
the scan. A2 started no server, compiler, database, Docker, browser, or generator
process. Residual A2 processes: **0**.
