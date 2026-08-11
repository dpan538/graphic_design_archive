# Deferred cleanup ledger

Status: **LOCKED — NOT EXECUTED**

Counting unit: one independently gated cleanup scope per row

`DEFERRED_CLEANUP_COUNT=9`

The population columns describe evidence boundaries and intentionally are not added together: some scopes overlap, especially the QA duplicates within `HOLD_UNKNOWN`. A future cleanup must name one row, prove its gate, and produce a separate recovery/action receipt. An unlisted file with no proved recovery is automatically deferred and cannot be deleted by inference.

| ID | Deferred scope | Measured population | Why deferred | Required acceptance boundary |
|---|---|---:|---|---|
| `D-001` | Legacy `public_surface_mock_v0.json` placements | 4 × 90,895,254 bytes | active derived runtime/Search projection; adapter cutover absent | sealed `ArchiveRepository` projection, route/search parity, consumer cutover and rollback |
| `D-002` | Direct frontend-data coupling | 35 files: 26 consumers + 9 producers | paths/decoders/writers still couple UI and static tree | zero direct consumers/producers outside approved adapters; data CI owns release generation |
| `D-003` | `/contents` bulk route | 1 route; at least 26,041 membership links | unbounded delivery/crawl surface | bounded SSR/keyset contract, crawlability and route parity |
| `D-004` | Folder Reader bulk behavior | 1 route family; maximum observed folder 5,740 members | request/render payload remains unbounded | bounded windows, stable ordering, navigation and accessibility parity |
| `D-005` | Search and TRACE derived assets | Search 8,636; TRACE 580 declared assets including 576 shards | release-aware Repository/API replacement not implemented | pinned release contract, byte/count parity, no derived-to-canonical write path |
| `D-006` | Exact duplicate QA paths | 10 paths in 7 duplicate groups | identical bytes do not prove identical scenario/oracle meaning | scenario-to-hash manifest, owner/rights decision and explicit keeper mapping |
| `D-007` | Effective `HOLD_UNKNOWN` inventory | 186 paths | ownership, provenance, rights, recovery or scenario meaning unresolved | per-path owner, authority, recovery and disposition approval |
| `D-008` | Protected dirty-main untracked work | 10,937 paths | about 20.6 GB of uncommitted owner work outside this worktree | separate owner-led archive/lineage authorization; locked fingerprints must remain equal |
| `D-009` | Frozen v48 assets | 5 named freeze assets, plus related shards/receipts | canonical input, reconciliation and integrity evidence | never cleaned in place; governed migration/release retention policy only |

## Cross-cutting prohibition

No file may be deleted, deduplicated, moved or rewritten merely because it is large, generated-looking, duplicated, inaccessible, rights-unknown or absent from a current import scan. Recovery identity and an owner-approved acceptance boundary are mandatory. `git clean`, reset, unresolved globs, workspace-root deletion and protected-main cleanup remain prohibited.

## This phase's only executed deletion

`docs/.DS_Store` is deliberately absent from the deferred ledger because Phase 1D executed and receipted that single exact-path deletion. It was ignored/untracked macOS metadata, not source or evidence. No other untracked file was deleted.
