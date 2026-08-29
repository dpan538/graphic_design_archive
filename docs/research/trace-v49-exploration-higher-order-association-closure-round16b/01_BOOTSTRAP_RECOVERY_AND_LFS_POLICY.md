# Bootstrap, recovery, publication, and LFS verification

## Result

The Round 16B bootstrap gate passes. This result establishes a recoverable and publication-safe starting lineage; it makes no association-closure claim.

| Control | Result |
|---|---:|
| Authorized source SHA | `5419770959bdb8998b693fb2275b47e29b92367c` |
| Authorized source tree | `977d7e8e045c71857959750b775cd4df3d036686` |
| Verified `origin/main` | `8de5d1dedffc6fd70d8b03cd63fdec74c0d40f6e` |
| Complete source-bundle bytes | 104,499,100 |
| Source-bundle SHA-256 | `ee18bc93e5ae3e366dd7259311a48599ab6b9df2f5bf4403aa4725bc9dab3579` |
| Restored source commits | 224 |
| Restore `git fsck --full --strict` | PASS |
| Current LFS paths | 30 |
| Hydrated LFS bytes verified | 2,004,889,799 |
| Canonical LFS pointer/hash/size matches | 30 / 30 / 30 |
| Source and current `git lfs fsck` | PASS |
| Reachable ordinary blobs at or above 100,000,000 bytes | 0 |
| Largest inherited ordinary blob | 90,895,254 bytes |
| Execution-log verification | PASS, 6 events, 0 failures |

The durable bundle is stored outside the Git worktree at `/Users/jarlgiovanni/Desktop/trace_round16b_preservation/trace-round16b-source-lineage-54197709.bundle`. The bundle preserves complete Git history and LFS pointers. Hydrated LFS availability is independently covered by `source-lfs-manifest.tsv`, its SHA-256 manifest identity, and `git lfs fsck`.

## Remote and publication proof

The complete remote inventory is retained as `source-remote-ref-map.tsv`. The first external publication receipt proves that the Round 16B branch was absent immediately before the initial ordinary push. Three additive governance commits were then published in linear order. Their imported receipts prove:

- each prior remote tip was absent or an ancestor of the new local tip;
- each local and remote tip matched after publication;
- `origin/main` remained unchanged;
- the rollback tag remained absent;
- unrelated remote-ref differences were zero;
- force push, history rewriting, deployment, and rollback-tag publication were false.

Two small corrections to the bootstrap verifier were made as additive commits after the first publication. The first replaced the impossible post-publication requirement that `HEAD` still equal the source with a source-ancestry check. The second correctly bound the initial-absence receipt by ancestry rather than requiring its earlier head to equal the current head. Neither published commit was amended, rebased, squashed, or rewritten.

## Hosting-limit policy

Round 16B introduces a pre-commit gate before any candidate or census ledger exists:

- warn when a changed hydrated file reaches 25,000,000 bytes;
- require Git LFS at 50,000,000 bytes;
- block a newly introduced ordinary Git blob at 90,000,000 bytes;
- require zero reachable ordinary blobs at or above 100,000,000 bytes;
- shard deterministic ledgers around 25 MB and bind every shard with ordered row, byte, and SHA-256 metadata.

The inherited 90,895,254-byte ordinary blob is immutable source history, not a precedent or exception for new content. New large audit artifacts and generated read models already have dedicated LFS patterns.

## Boundary for the next checkpoint

Research may now audit Round 9–16 evidence surfaces and define the higher-order association method. Candidate generation, evidence disposition, product representation, and closure status remain open. Round 16A counts are baseline measurements only.
